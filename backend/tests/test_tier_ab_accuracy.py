import sys
import os
import json
import zipfile
import io
import asyncio
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from sqlmodel import Session, select
from app.main import app
from app.core.database import engine, init_db
from app.models.entities import PlacementDrive
from app.workers.ats_verifier import (
    classify_region_scope,
    is_valid_direct_url,
    extract_ats_form_schema,
    compute_job_accuracy_score,
)
from app.workers.job_fetcher import is_engineering_role, job_fetcher

client = TestClient(app)


def test_region_classification_accuracy():
    assert classify_region_scope("Indiana") == "GLOBAL", "Indiana US must NOT match India!"
    assert classify_region_scope("Indianapolis, IN") == "GLOBAL"
    assert classify_region_scope("Bengaluru, Karnataka, India") == "INDIA"
    assert classify_region_scope("Chennai (OMR)") == "INDIA"
    assert classify_region_scope("Remote") == "REMOTE"
    assert classify_region_scope("Remote (Worldwide)") == "REMOTE"
    assert classify_region_scope("Remote in US") == "GLOBAL"
    assert classify_region_scope("San Francisco, CA") == "GLOBAL"
    print("[PASS] Region scope classification (no Indiana/India false positives)")


def test_engineering_filter_and_url_validation():
    assert is_engineering_role("Software Development Engineer") is True
    assert is_engineering_role("Backend Engineer, Orbit") is True
    assert is_engineering_role("English - Language Specialist - Freelance AI Trainer Project") is False
    assert is_engineering_role("Content Reviewer - United States") is False
    assert is_engineering_role("Inside Sales Contractor") is False

    assert is_valid_direct_url("https://job-boards.greenhouse.io/gitlab/jobs/8638232002#app") is True
    assert is_valid_direct_url("https://nextstep.tcs.com/campus/#/") is True
    assert is_valid_direct_url("https://jobicy.com/jobs/123-role") is False
    assert is_valid_direct_url("https://remotive.com/remote-jobs/foo") is False
    assert is_valid_direct_url("https://www.google.com/search?q=zoho+apply") is False
    assert is_valid_direct_url("https://www.linkedin.com") is False
    print("[PASS] Role filter & direct URL validation")


def test_db_no_synthetic_clones_and_accuracy_populated():
    init_db()
    with Session(engine) as s:
        drives = s.exec(select(PlacementDrive)).all()
        assert len(drives) > 20
        clones = [d for d in drives if "tech track)" in (d.role_title or "").lower()]
        assert len(clones) == 0, f"Found {len(clones)} synthetic city clones!"
        low_unverified = [d for d in drives if (d.accuracy_score or 0) <= 0]
        assert len(low_unverified) == 0
    print(f"[PASS] Clean SQLite DB verified ({len(drives)} real drives, 0 synthetic clones)")


def test_api_region_filtering_form_schema_and_extension():
    login_res = client.post("/api/v1/auth/login-json", json={"email": "student@ceg.edu", "password": "Student@123"})
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Region counts
    rc_res = client.get("/api/v1/drives/region-counts", headers=headers)
    assert rc_res.status_code == 200
    rc = rc_res.json()
    assert rc["india"] > 0 and rc["global"] > 0
    print(f"[PASS] Region counts endpoint: india={rc['india']}, remote={rc['remote']}, global={rc['global']}")

    # 2. Default region=india_remote excludes GLOBAL
    def_res = client.get("/api/v1/drives", headers=headers)
    assert def_res.status_code == 200
    def_drives = def_res.json()
    assert len(def_drives) > 0
    assert all(d.get("region_scope") in ("INDIA", "REMOTE", None) for d in def_drives)
    print(f"[PASS] Default India+Remote filter returned {len(def_drives)} drives (0 GLOBAL leaks)")

    # 3. Separate Global Jobs filter
    glb_res = client.get("/api/v1/drives?region=global", headers=headers)
    assert glb_res.status_code == 200
    glb_drives = glb_res.json()
    assert len(glb_drives) > 0
    assert all(d.get("region_scope") == "GLOBAL" for d in glb_drives)
    print(f"[PASS] Separate Global Jobs filter returned {len(glb_drives)} global drives")

    # 4. Live ATS form-schema & student field mapping (prefer a Greenhouse drive if available)
    gh_drive = next((d for d in def_drives + glb_drives if d.get("source_platform") == "GREENHOUSE"), def_drives[0])
    schema_res = client.get(f"/api/v1/drives/{gh_drive['id']}/form-schema", headers=headers)
    assert schema_res.status_code == 200
    schema = schema_res.json()
    assert schema["student_summary"]["full_name"] == "Aravind Swaminathan"
    assert float(schema["student_summary"]["cgpa"]) > 0
    assert len(schema["fields"]) >= 5
    field_labels = [f["label"] for f in schema["fields"]]
    print(f"[PASS] Live ATS form-schema ({schema['schema_source']}): mapped {len(schema['fields'])} fields ({field_labels[:4]}...)")

    # 5. Live link & expiry verification endpoint
    ver_res = client.post(f"/api/v1/drives/{gh_drive['id']}/verify", headers=headers)
    assert ver_res.status_code == 200
    ver = ver_res.json()
    assert ver["accuracy_score"] >= 60
    assert "total_score" in ver["accuracy_breakdown"]
    print(f"[PASS] Live Drive Verify endpoint: accuracy_score={ver['accuracy_score']}/100")

    # 6. Chrome Extension Zip Download
    ext_res = client.get("/api/v1/drives/extension/download")
    assert ext_res.status_code == 200
    zf = zipfile.ZipFile(io.BytesIO(ext_res.content))
    names = zf.namelist()
    assert "manifest.json" in names and "content.js" in names and "popup.js" in names and "bridge.js" in names
    manifest = json.loads(zf.read("manifest.json"))
    assert manifest["manifest_version"] == 3
    print(f"[PASS] Chrome Extension Zip Download verified ({names})")


async def test_live_ats_fetchers():
    gh = await job_fetcher.fetch_from_greenhouse(limit=3, company_slugs=["gitlab"])
    assert len(gh) > 0 and gh[0]["source_platform"] == "GREENHOUSE"
    assert "Ingested via official Greenhouse" not in gh[0]["job_description"], "Should use real ?content=true description!"

    ash = await job_fetcher.fetch_from_ashby(limit=3, company_slugs=["supabase", "notion"])
    assert len(ash) > 0 and ash[0]["source_platform"] == "ASHBY"

    sr = await job_fetcher.fetch_from_smartrecruiters(limit=3, company_slugs=["BoschGroup"])
    assert len(sr) > 0 and sr[0]["region_scope"] == "INDIA"

    sim = await job_fetcher.fetch_from_simplify_github(limit=6)
    assert len(sim) > 0 and sim[0]["source_platform"] == "SIMPLIFY_GITHUB"
    print(f"[PASS] Live ATS Fetchers: Greenhouse={len(gh)}, Ashby={len(ash)}, SmartRecruiters(India)={len(sr)}, SimplifyJobs={len(sim)}")


if __name__ == "__main__":
    test_region_classification_accuracy()
    test_engineering_filter_and_url_validation()
    test_db_no_synthetic_clones_and_accuracy_populated()
    asyncio.run(test_live_ats_fetchers())
    test_api_region_filtering_form_schema_and_extension()
    print("\n🎉 ALL TIER A + TIER B VERIFICATION TESTS PASSED (100%)!")
