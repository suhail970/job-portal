import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from app.main import app
from app.ai.agents.resume_leaf import extract_academic_and_contact_fields

client = TestClient(app)


def build_minimal_pdf(lines: list[str]) -> bytes:
    """Builds a minimal valid single-page PDF readable by pypdf.PdfReader."""
    escaped = []
    for i, ln in enumerate(lines):
        safe = ln.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
        dy = "0" if i == 0 else "-16"
        escaped.append(f"0 {dy} Td ({safe}) Tj")
    stream = "BT /F1 12 Tf 50 750 Td " + " ".join(escaped) + " ET"
    stream_bytes = stream.encode("latin-1")

    objs = [
        b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n",
        b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n",
        b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>\nendobj\n",
        f"4 0 obj\n<< /Length {len(stream_bytes)} >>\nstream\n".encode("latin-1") + stream_bytes + b"\nendstream\nendobj\n",
        b"5 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n",
    ]
    pdf = bytearray(b"%PDF-1.4\n")
    offsets = []
    for obj in objs:
        offsets.append(len(pdf))
        pdf.extend(obj)
    xref_pos = len(pdf)
    pdf.extend(f"xref\n0 {len(objs) + 1}\n0000000000 65535 f \n".encode("latin-1"))
    for off in offsets:
        pdf.extend(f"{off:010d} 00000 n \n".encode("latin-1"))
    pdf.extend(f"trailer\n<< /Size {len(objs) + 1} /Root 1 0 R >>\nstartxref\n{xref_pos}\n%%EOF\n".encode("latin-1"))
    return bytes(pdf)


def test_deterministic_extraction():
    sample1 = """
    Aravind Swaminathan
    Phone: +91 98765 11223 | github.com/aravind-dev | linkedin.com/in/aravind-ceg
    Education:
    B.E. Computer Science and Engineering, Anna University (2022 - 2026)
    CGPA: 9.15 / 10.0
    12th HSC: 95%
    Skills: Python, FastAPI, React, SQL
    """
    res1 = extract_academic_and_contact_fields(sample1)
    assert res1["cgpa"] == 9.15, f"Expected 9.15, got {res1}"
    assert res1["graduation_year"] == 2026, res1
    assert res1["department_code"] == "CSE", res1
    assert res1["phone_number"] == "+91 98765 11223", res1
    assert res1["github_url"] == "https://github.com/aravind-dev", res1
    assert res1["linkedin_url"] == "https://www.linkedin.com/in/aravind-ceg", res1
    assert res1["standing_arrears"] is None

    sample_pct = """
    B.Tech Information Technology, Expected Graduation 2027
    University Percentage: 85.5%
    """
    res2 = extract_academic_and_contact_fields(sample_pct)
    assert res2["cgpa"] == 9.0, res2
    assert res2["graduation_year"] == 2027, res2
    assert res2["department_code"] == "IT", res2
    assert any("Estimated CGPA" in w for w in res2["warnings"])

    sample_gpa4 = """
    B.E. Electronics and Communication Engineering (2023 - 2027)
    GPA: 3.6 / 4.0
    """
    res3 = extract_academic_and_contact_fields(sample_gpa4)
    assert res3["cgpa"] == 9.0, res3
    assert res3["department_code"] == "ECE", res3
    assert any("Converted" in w for w in res3["warnings"])
    print("[PASS] Deterministic academic & contact extractor (CGPA, %, 4.0 scale, dept, links)")


def test_pdf_upload_and_profile_sync():
    login = client.post("/api/v1/auth/login-json", json={"email": "student@ceg.edu", "password": "Student@123"})
    assert login.status_code == 200
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    orig = client.get("/api/v1/students/me", headers=headers).json()
    orig_profile = orig["profile"]

    # Ensure arrears=1 is preserved even when auto_apply=True runs
    set_err = client.put("/api/v1/students/me", headers=headers, json={"standing_arrears": 1})
    assert set_err.status_code == 200

    pdf_bytes = build_minimal_pdf([
        "Priya Nair",
        "Phone: +91 91234 56789",
        "GitHub: github.com/priya-codes",
        "LinkedIn: linkedin.com/in/priya-nair",
        "B.E. Electronics and Communication Engineering (2023 - 2027)",
        "CGPA: 8.95 / 10.0",
        "Skills: C++, Embedded Linux, Python, SQL",
    ])

    # 1. Review-first mode (auto_apply=false) does NOT overwrite profile
    res_preview = client.post(
        "/api/v1/resume/upload",
        headers=headers,
        files={"file": ("priya_resume.pdf", pdf_bytes, "application/pdf")},
        data={"auto_apply": "false"},
    )
    assert res_preview.status_code == 200, res_preview.text
    p_data = res_preview.json()
    assert p_data["applied_to_profile"] is False
    assert p_data["extracted_academic"]["cgpa"] == 8.95
    assert p_data["extracted_academic"]["graduation_year"] == 2027
    assert p_data["extracted_academic"]["department_code"] == "ECE"

    after_preview = client.get("/api/v1/students/me", headers=headers).json()["profile"]
    assert after_preview["cgpa"] == orig_profile["cgpa"]
    assert after_preview["standing_arrears"] == 1

    # 2. Auto-apply mode updates extracted fields but preserves standing_arrears
    res_apply = client.post(
        "/api/v1/resume/upload",
        headers=headers,
        files={"file": ("priya_resume.pdf", pdf_bytes, "application/pdf")},
        data={"auto_apply": "true"},
    )
    assert res_apply.status_code == 200, res_apply.text
    a_data = res_apply.json()
    assert a_data["applied_to_profile"] is True
    assert "cgpa" in a_data["applied_fields"]

    after_apply = client.get("/api/v1/students/me", headers=headers).json()
    assert after_apply["profile"]["cgpa"] == 8.95
    assert after_apply["profile"]["graduation_year"] == 2027
    assert after_apply["profile"]["standing_arrears"] == 1, "Standing arrears must NEVER be overwritten by resume!"

    # 3. Validation guard on PUT /students/me
    bad = client.put("/api/v1/students/me", headers=headers, json={"cgpa": 12.5})
    assert bad.status_code == 400

    # 4. Check /auth/me includes department_code
    me_res = client.get("/api/v1/auth/me", headers=headers)
    assert me_res.status_code == 200
    assert "department_code" in me_res.json()

    # Restore original student state
    restore = client.put(
        "/api/v1/students/me",
        headers=headers,
        json={
            "cgpa": orig_profile["cgpa"],
            "standing_arrears": orig_profile["standing_arrears"],
            "graduation_year": orig_profile["graduation_year"],
            "department_code": orig.get("department_code") or "CSE",
            "phone_number": orig_profile.get("phone_number") or "+91 98765 43210",
            "github_url": orig_profile.get("github_url") or "",
            "linkedin_url": orig_profile.get("linkedin_url") or "",
        },
    )
    assert restore.status_code == 200
    print("[PASS] Multipart PDF upload + review-first + auto_apply + standing_arrears protection")


if __name__ == "__main__":
    test_deterministic_extraction()
    test_pdf_upload_and_profile_sync()
    print("\nALL RESUME ACADEMIC SYNC TESTS PASSED!")

