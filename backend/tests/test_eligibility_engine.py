import sys
import os
from datetime import datetime, timezone, timedelta

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from sqlmodel import Session
from app.main import app
from app.core.database import engine
from app.models.entities import PlacementDrive
from app.models.enums import DriveStatus
from app.services.eligibility_engine import (
    AcademicSnapshot,
    evaluate_drive_eligibility,
    parse_ctc_lpa_range,
)
from app.ai.agents.resume_leaf import extract_academic_and_contact_fields

client = TestClient(app)


def test_unit_rule_engine():
    # Parse CTC tests
    assert parse_ctc_lpa_range("8.5 LPA - 12 LPA") == (8.5, 12.0)
    assert parse_ctc_lpa_range("7.5 LPA") == (7.5, 7.5)
    assert parse_ctc_lpa_range("$90k - $110k") == (None, None)

    now = datetime.now(timezone.utc)
    strict_drive = PlacementDrive(
        id="drv-strict",
        college_id="col-1",
        company_name="Acme Systems",
        role_title="SDE-1",
        job_description="Systems engineering",
        salary_package="6.5 LPA - 8.0 LPA",
        min_cgpa=7.5,
        max_arrears=0,
        max_history_arrears=1,
        min_tenth_percentage=75.0,
        min_twelfth_percentage=75.0,
        accepts_diploma=False,
        allowed_departments="CSE,IT",
        drive_date=now + timedelta(days=5),
        registration_deadline=now + timedelta(days=3),
        status=DriveStatus.ACTIVE,
    )

    # 1. Passing candidate (with target_min_ctc HIGHER than offer -> still Eligible, just Below Target CTC!)
    strong_student = AcademicSnapshot(
        cgpa=8.4,
        standing_arrears=0,
        history_arrears=1,
        tenth_percentage=88.0,
        secondary_qualification_type="HSC",
        twelfth_percentage=86.5,
        target_companies="Acme",
        target_min_ctc=12.0,
    )
    res_pass = evaluate_drive_eligibility(strong_student, "CSE", strict_drive)
    assert res_pass["is_eligible"] is True, res_pass
    assert res_pass["status_label"] == "Eligible"
    assert res_pass["reasons"] == []
    assert res_pass["package_goal_match"] is False, "CTC preference must NOT make student ineligible"
    assert "Below Target CTC" in (res_pass["package_goal_label"] or "")
    assert res_pass["is_target_company"] is True

    # 2. Failing Diploma track + multiple rule failures
    failing_diploma = AcademicSnapshot(
        cgpa=6.8,
        standing_arrears=1,
        history_arrears=3,
        tenth_percentage=70.0,
        secondary_qualification_type="DIPLOMA",
        twelfth_percentage=72.0,
    )
    res_fail = evaluate_drive_eligibility(failing_diploma, "MECH", strict_drive)
    assert res_fail["is_eligible"] is False
    assert res_fail["status_label"] == "Not Eligible"
    joined = " | ".join(res_fail["reasons"])
    assert "CGPA 6.80 is below required minimum 7.50" in joined
    assert "Standing arrears (1) exceed max allowed (0)" in joined
    assert "History of arrears (3) exceed max allowed (1)" in joined
    assert "Branch MECH not in eligible branches" in joined
    assert "10th % (70.0%) is below required 75.0%" in joined
    assert "Diploma track not accepted" in joined
    assert "Diploma % (72.0%) is below required 75.0%" in joined

    # 3. Optional thresholds None on drive -> MUST be skipped cleanly (never hardcoded)
    open_drive = PlacementDrive(
        id="drv-open",
        college_id="col-1",
        company_name="OpenTech",
        role_title="Developer",
        job_description="Web Dev",
        salary_package="10 LPA",
        min_cgpa=6.0,
        max_arrears=1,
        max_history_arrears=None,
        min_tenth_percentage=None,
        min_twelfth_percentage=None,
        accepts_diploma=True,
        allowed_departments="CSE,IT,ECE",
        drive_date=now + timedelta(days=5),
        registration_deadline=now + timedelta(days=3),
        status=DriveStatus.ACTIVE,
    )
    sparse_student = AcademicSnapshot(
        cgpa=6.5,
        standing_arrears=0,
        history_arrears=4,
        tenth_percentage=None,
        secondary_qualification_type="DIPLOMA",
        twelfth_percentage=None,
        target_min_ctc=8.0,
    )
    res_open = evaluate_drive_eligibility(sparse_student, "ECE", open_drive)
    assert res_open["is_eligible"] is True, res_open
    assert res_open["package_goal_match"] is True
    print("[PASS] Unit rule-based eligibility engine & optional-threshold skipping")


def test_resume_school_percentage_extraction():
    hsc_resume = """
    Karthik Raja
    B.E. Computer Science and Engineering (2022 - 2026)
    CGPA: 8.72 / 10.0
    12th Standard (HSC): 92.4%
    10th Standard (SSLC): 89.6%
    Phone: +91 98765 11223
    """
    ext_hsc = extract_academic_and_contact_fields(hsc_resume)
    assert ext_hsc["cgpa"] == 8.72, ext_hsc
    assert ext_hsc["tenth_percentage"] == 89.6, ext_hsc
    assert ext_hsc["twelfth_percentage"] == 92.4, ext_hsc
    assert ext_hsc["secondary_qualification_type"] == "HSC", ext_hsc
    assert ext_hsc["standing_arrears"] is None
    assert ext_hsc["history_arrears"] is None

    diploma_resume = """
    Meenakshi Sundaram
    B.Tech Information Technology (2023 - 2026) - CGPA: 8.15
    Diploma in Computer Engineering (Polytechnic): 87.5%
    SSLC 10th: 84.0%
    """
    ext_dip = extract_academic_and_contact_fields(diploma_resume)
    assert ext_dip["cgpa"] == 8.15, ext_dip
    assert ext_dip["tenth_percentage"] == 84.0, ext_dip
    assert ext_dip["twelfth_percentage"] == 87.5, ext_dip
    assert ext_dip["secondary_qualification_type"] == "DIPLOMA", ext_dip
    print("[PASS] Deterministic resume extraction for 10th %, HSC vs Diploma %, and CGPA")


def test_api_persistence_validation_preview_and_apply():
    # Login student & TPO
    stu_login = client.post("/api/v1/auth/login-json", json={"email": "student@ceg.edu", "password": "Student@123"})
    assert stu_login.status_code == 200
    stu_headers = {"Authorization": f"Bearer {stu_login.json()['access_token']}"}

    tpo_login = client.post("/api/v1/auth/login-json", json={"email": "tpo@ceg.edu", "password": "Tpo@123"})
    assert tpo_login.status_code == 200
    tpo_headers = {"Authorization": f"Bearer {tpo_login.json()['access_token']}"}

    orig = client.get("/api/v1/students/me", headers=stu_headers).json()
    orig_p = orig["profile"]

    try:
        # 1. Backend cross-field validation: history_arrears < standing_arrears MUST fail (400)
        bad_arrears = client.put(
            "/api/v1/students/me",
            headers=stu_headers,
            json={"standing_arrears": 2, "history_arrears": 1},
        )
        assert bad_arrears.status_code == 400, bad_arrears.text
        assert "cannot be less than standing arrears" in bad_arrears.json()["detail"]

        # Invalid percentage & qualification type
        bad_pct = client.put("/api/v1/students/me", headers=stu_headers, json={"tenth_percentage": 105.0})
        assert bad_pct.status_code == 400
        bad_qual = client.put("/api/v1/students/me", headers=stu_headers, json={"secondary_qualification_type": "BTECH"})
        assert bad_qual.status_code == 400

        # 2. Save full academic + career profile permanently
        upd = client.put(
            "/api/v1/students/me",
            headers=stu_headers,
            json={
                "tenth_percentage": 89.4,
                "secondary_qualification_type": "DIPLOMA",
                "twelfth_percentage": 86.2,
                "cgpa": 8.5,
                "standing_arrears": 0,
                "history_arrears": 1,
                "target_companies": "Zoho, Amazon",
                "target_min_ctc": 10.0,
            },
        )
        assert upd.status_code == 200, upd.text
        saved_p = client.get("/api/v1/students/me", headers=stu_headers).json()["profile"]
        assert saved_p["tenth_percentage"] == 89.4
        assert saved_p["secondary_qualification_type"] == "DIPLOMA"
        assert saved_p["twelfth_percentage"] == 86.2
        assert saved_p["history_arrears"] == 1
        assert saved_p["target_companies"] == "Zoho, Amazon"
        assert saved_p["target_min_ctc"] == 10.0

        # 3. Real-time preview endpoint does NOT mutate persisted DB values
        prev = client.post(
            "/api/v1/students/me/eligibility/preview",
            headers=stu_headers,
            json={"cgpa": 4.5, "standing_arrears": 3, "history_arrears": 3},
        )
        assert prev.status_code == 200, prev.text
        prev_data = prev.json()
        assert prev_data["total_drives"] >= 3
        assert prev_data["not_eligible_count"] >= 3
        still_saved = client.get("/api/v1/students/me", headers=stu_headers).json()["profile"]
        assert still_saved["cgpa"] == 8.5

        # 4. TPO creates a drive with specific 10th/12th/Diploma/History rules & test apply enforcement
        now = datetime.now(timezone.utc)
        created_drive = client.post(
            "/api/v1/drives",
            headers=tpo_headers,
            json={
                "company_name": "VerifyRule Corp",
                "role_title": "Graduate Trainee",
                "job_description": "Testing strict eligibility criteria.",
                "salary_package": "8.0 LPA",
                "min_cgpa": 7.5,
                "max_arrears": 0,
                "max_history_arrears": 0,
                "min_tenth_percentage": 80.0,
                "min_twelfth_percentage": 80.0,
                "accepts_diploma": False,
                "allowed_departments": "CSE,IT",
                "drive_date": (now + timedelta(days=10)).isoformat(),
                "registration_deadline": (now + timedelta(days=8)).isoformat(),
            },
        )
        assert created_drive.status_code == 200, created_drive.text
        test_drive_id = created_drive.json()["id"]

        try:
            # Dashboard shows VerifyRule Corp as Not Eligible with exact reasons
            dash = client.get("/api/v1/students/me/eligibility", headers=stu_headers).json()
            assert dash["total_drives"] >= 1
            matching = [r for r in dash["results"] if r["drive_id"] == test_drive_id]
            assert len(matching) == 1
            assert matching[0]["is_eligible"] is False
            assert any("History of arrears" in r for r in matching[0]["reasons"])
            assert any("Diploma track not accepted" in r for r in matching[0]["reasons"])
            assert matching[0]["package_goal_match"] is False  # 8.0 < target 10.0 LPA

            # Apply endpoint enforces the exact same rule engine
            apply_res = client.post(f"/api/v1/drives/{test_drive_id}/apply", headers=stu_headers)
            assert apply_res.status_code == 400
            assert "Ineligible:" in apply_res.json()["detail"]
        finally:
            # Clean up test drive from SQLite
            with Session(engine) as session:
                d_row = session.get(PlacementDrive, test_drive_id)
                if d_row:
                    session.delete(d_row)
                    session.commit()

        print("[PASS] API persistence, validation guards, real-time preview, dashboard, and apply enforcement")
    finally:
        # Restore original student profile state cleanly
        client.put(
            "/api/v1/students/me",
            headers=stu_headers,
            json={
                "cgpa": orig_p["cgpa"],
                "standing_arrears": orig_p["standing_arrears"],
                "history_arrears": orig_p.get("history_arrears", 0),
                "tenth_percentage": orig_p.get("tenth_percentage"),
                "secondary_qualification_type": orig_p.get("secondary_qualification_type") or "HSC",
                "twelfth_percentage": orig_p.get("twelfth_percentage"),
                "department_code": orig.get("department_code") or "CSE",
                "target_companies": orig_p.get("target_companies") or "",
                "target_min_ctc": orig_p.get("target_min_ctc"),
            },
        )


if __name__ == "__main__":
    test_unit_rule_engine()
    test_resume_school_percentage_extraction()
    test_api_persistence_validation_preview_and_apply()
    print("\nALL SMART PLACEMENT ELIGIBILITY TESTS PASSED!")
