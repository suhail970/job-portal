import sys
import os
import time
import uuid
import zlib
from datetime import datetime, timezone, timedelta

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from sqlmodel import Session, select
from app.main import app
from app.core.database import engine
from app.models.entities import PlacementDrive, Resume, StudentProfile, User
from app.models.enums import DriveStatus
from app.ai.agents.resume_leaf import extract_structured_resume_sections
from app.services.resume_matcher import (
    prepare_resume_profile,
    compute_resume_job_match,
    DEFAULT_MATCH_THRESHOLD,
)

client = TestClient(app)


def build_minimal_pdf(lines):
    stream_lines = ["BT", "/F1 11 Tf", "50 750 Td"]
    for i, line in enumerate(lines):
        escaped = line.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
        if i == 0:
            stream_lines.append(f"({escaped}) Tj")
        else:
            stream_lines.append(f"0 -16 Td ({escaped}) Tj")
    stream_lines.append("ET")
    stream_bytes = "\n".join(stream_lines).encode("latin-1")
    compressed = zlib.compress(stream_bytes)

    objs = [
        b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n",
        b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n",
        b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>\nendobj\n",
        f"4 0 obj\n<< /Length {len(compressed)} /Filter /FlateDecode >>\nstream\n".encode("latin-1")
        + compressed
        + b"\nendstream\nendobj\n",
        b"5 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n",
    ]
    pdf = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for obj in objs:
        offsets.append(len(pdf))
        pdf.extend(obj)
    xref_pos = len(pdf)
    pdf.extend(f"xref\n0 {len(objs) + 1}\n0000000000 65535 f \n".encode("latin-1"))
    for off in offsets[1:]:
        pdf.extend(f"{off:010d} 00000 n \n".encode("latin-1"))
    pdf.extend(
        f"trailer\n<< /Size {len(objs) + 1} /Root 1 0 R >>\nstartxref\n{xref_pos}\n%%EOF\n".encode("latin-1")
    )
    return bytes(pdf)


def test_structured_extraction_no_dummy_data():
    sample = """
    Surya Prakash
    Skills: Java, Spring Boot, MySQL, Docker, REST API

    Internships
    - Backend Developer Intern at FinTech Corp building Java Spring Boot microservices and MySQL queries

    Projects
    - Payment Ledger Service using Spring Boot, Docker, and MySQL

    Certifications
    - Oracle Certified Java Programmer
    - AWS Certified Cloud Practitioner

    Achievements
    - Winner Smart India Hackathon 2025
    """
    sec = extract_structured_resume_sections(sample)
    assert "Java" in sec["skills"] and "Spring Boot" in sec["skills"]
    assert "FastAPI" not in sec["skills"], "Must NOT inject dummy skills not present in resume"
    assert len(sec["internships"]) >= 1
    assert len(sec["projects"]) >= 1
    assert len(sec["certifications"]) >= 2
    assert len(sec["achievements"]) >= 1
    print("[PASS] Deterministic resume structured extraction (no dummy data)")


def test_relevance_scoring_and_performance():
    resume = Resume(
        id="res-bench",
        student_id="stu-bench",
        college_id="col-bench",
        filename="backend_resume.pdf",
        raw_text="Python FastAPI PostgreSQL Docker Microservices REST API AWS",
        parsed_skills='["Python", "FastAPI", "PostgreSQL", "Docker", "REST API", "AWS"]',
        parsed_internships='["Backend Engineering Intern using Python, FastAPI and PostgreSQL microservices"]',
        parsed_projects='["High-throughput Cloud API Gateway with Docker and AWS"]',
        parsed_certifications='["AWS Certified Cloud Practitioner"]',
        parsed_achievements='["Finalist Hackathon 2025"]',
    )
    prepared = prepare_resume_profile(resume)
    now = datetime.now(timezone.utc)

    backend_drive = PlacementDrive(
        id="drv-be",
        college_id="col-bench",
        company_name="CloudScale",
        role_title="Backend Software Engineer",
        job_description="Build microservices using Python, FastAPI, PostgreSQL, Docker, REST API on AWS cloud.",
        min_cgpa=9.5,  # High CGPA to verify skill match is independent of academic eligibility
        max_arrears=0,
        allowed_departments="CSE",
        drive_date=now + timedelta(days=5),
        registration_deadline=now + timedelta(days=3),
        status=DriveStatus.ACTIVE,
    )
    embedded_drive = PlacementDrive(
        id="drv-emb",
        college_id="col-bench",
        company_name="AutoChips",
        role_title="Embedded Firmware Engineer",
        job_description="Develop AUTOSAR C firmware drivers and RTOS modules for automotive microcontrollers.",
        min_cgpa=6.0,
        max_arrears=1,
        allowed_departments="ECE",
        drive_date=now + timedelta(days=5),
        registration_deadline=now + timedelta(days=3),
        status=DriveStatus.ACTIVE,
    )

    m_high = compute_resume_job_match(prepared, backend_drive, min_threshold=DEFAULT_MATCH_THRESHOLD)
    assert m_high["match_percentage"] >= 70.0, m_high
    assert m_high["is_recommended"] is True
    assert "Python" in m_high["matched_skills"] and "FastAPI" in m_high["matched_skills"]
    assert len(m_high["matched_experience"]) >= 2
    assert len(m_high["reasons"]) >= 2

    m_low = compute_resume_job_match(prepared, embedded_drive, min_threshold=DEFAULT_MATCH_THRESHOLD)
    assert m_low["match_percentage"] < 30.0, m_low
    assert m_low["is_recommended"] is False

    # Benchmark 250 drives scoring speed (must run in milliseconds without LLM calls)
    t0 = time.perf_counter()
    for _ in range(250):
        compute_resume_job_match(prepared, backend_drive, min_threshold=DEFAULT_MATCH_THRESHOLD)
    elapsed_ms = (time.perf_counter() - t0) * 1000.0
    assert elapsed_ms < 500.0, f"Matching 250 drives took too long: {elapsed_ms:.1f}ms"
    print(f"[PASS] Relevance scoring & 250-drive benchmark ({elapsed_ms:.1f}ms total)")


def test_three_modes_no_resume_and_refresh_api():
    unique_email = f"match_test_{uuid.uuid4().hex[:8]}@ceg.edu"
    reg = client.post(
        "/api/v1/auth/register",
        json={
            "email": unique_email,
            "password": "TestPassword@123",
            "full_name": "Resume Matcher Tester",
            "role": "STUDENT",
            "college_code": "CEG-001",
            "department_code": "CSE",
            "roll_number": "2022CSE999",
        },
    )
    assert reg.status_code == 200, reg.text
    token = reg.json()["access_token"]
    user_id = reg.json()["user_id"]
    headers = {"Authorization": f"Bearer {token}"}

    try:
        # 1. No-resume state: All Jobs works; Both returns prompt (has_resume=False) & other_jobs populated
        no_res_both = client.get("/api/v1/drives/matched?match_mode=both", headers=headers)
        assert no_res_both.status_code == 200, no_res_both.text
        nb_data = no_res_both.json()
        assert nb_data["has_resume"] is False
        assert nb_data["personalized_matches"] == []
        assert len(nb_data["other_jobs"]) >= 3

        no_res_all = client.get("/api/v1/drives/matched?match_mode=all", headers=headers)
        assert no_res_all.status_code == 200
        assert len(no_res_all.json()["all_jobs"]) >= 3

        # 2. Upload Python/Backend/Cloud PDF resume
        pdf1 = build_minimal_pdf([
            "Resume Matcher Tester",
            "B.E. Computer Science and Engineering (2022 - 2026)",
            "CGPA: 6.2 / 10.0",  # Intentionally low to prove academic eligibility stays separate from skill matching!
            "Skills: Python, FastAPI, Docker, PostgreSQL, AWS, REST API",
            "Internships",
            "- Backend Developer Intern using Python and FastAPI microservices",
            "Projects",
            "- Distributed Queue Platform using PostgreSQL, Docker, and AWS",
            "Certifications",
            "- AWS Certified Cloud Practitioner",
            "Achievements",
            "- Winner Hackathon 2025",
        ])
        up1 = client.post(
            "/api/v1/resume/upload",
            headers=headers,
            files={"file": ("backend_v1.pdf", pdf1, "application/pdf")},
            data={"auto_apply": "false"},
        )
        assert up1.status_code == 200, up1.text
        u1_data = up1.json()
        assert "Python" in u1_data["skills"]
        assert len(u1_data["projects"]) >= 1
        assert len(u1_data["internships"]) >= 1

        # Test Mode: both (Default)
        both_res = client.get("/api/v1/drives/matched?match_mode=both", headers=headers)
        assert both_res.status_code == 200
        b_data = both_res.json()
        assert b_data["has_resume"] is True
        assert b_data["counts"]["personalized"] >= 1
        p_ids = {d["id"] for d in b_data["personalized_matches"]}
        o_ids = {d["id"] for d in b_data["other_jobs"]}
        assert not (p_ids & o_ids), "Personalized and Other lists must not overlap"

        # Verify sorting + threshold >= 30% + separation of academic eligibility
        scores = [d["resume_match"]["match_percentage"] for d in b_data["personalized_matches"]]
        assert scores == sorted(scores, reverse=True)
        assert all(s >= 30.0 for s in scores)
        high_cgpa_restricted = [
            d for d in b_data["personalized_matches"]
            if d["min_cgpa"] > 6.5
        ]
        if high_cgpa_restricted:
            sample_d = high_cgpa_restricted[0]
            assert sample_d["resume_match"]["is_recommended"] is True
            assert sample_d["eligibility"]["is_eligible"] is False, "Academic eligibility must stay separate from skill match!"

        # Test Mode: based_on_resume
        only_res = client.get("/api/v1/drives/matched?match_mode=based_on_resume", headers=headers).json()
        assert only_res["other_jobs"] == []
        assert len(only_res["personalized_matches"]) == len(b_data["personalized_matches"])

        # Test backward-compatible GET /api/v1/drives list endpoint
        list_compat = client.get("/api/v1/drives?match_mode=based_on_resume", headers=headers)
        assert list_compat.status_code == 200
        assert isinstance(list_compat.json(), list)
        assert len(list_compat.json()) == len(only_res["personalized_matches"])

        # 3. Upload updated React/Frontend resume & call refresh-analysis -> matches update dynamically!
        pdf2 = build_minimal_pdf([
            "Resume Matcher Tester",
            "Skills: React, Next.js, TypeScript, JavaScript, Tailwind CSS",
            "Projects",
            "- Interactive Analytics Dashboard built with React, Next.js, TypeScript",
        ])
        up2 = client.post(
            "/api/v1/resume/upload",
            headers=headers,
            files={"file": ("frontend_v2.pdf", pdf2, "application/pdf")},
            data={"auto_apply": "false"},
        )
        assert up2.status_code == 200
        ref = client.post("/api/v1/resume/refresh-analysis", headers=headers)
        assert ref.status_code == 200
        assert "React" in ref.json()["skills"]

        after_update = client.get("/api/v1/drives/matched?match_mode=both", headers=headers).json()
        assert after_update["resume_summary"]["filename"] == "frontend_v2.pdf"
        assert "React" in after_update["resume_summary"]["skills"]
        print("[PASS] 3 fetching modes, no-resume state, academic separation, backward compat & resume refresh")
    finally:
        # Clean up ephemeral test user/profile/resumes
        with Session(engine) as session:
            stu = session.exec(select(StudentProfile).where(StudentProfile.user_id == user_id)).first()
            if stu:
                for r in session.exec(select(Resume).where(Resume.student_id == stu.id)).all():
                    session.delete(r)
                session.delete(stu)
            usr = session.get(User, user_id)
            if usr:
                session.delete(usr)
            session.commit()


if __name__ == "__main__":
    test_structured_extraction_no_dummy_data()
    test_relevance_scoring_and_performance()
    test_three_modes_no_resume_and_refresh_api()
    print("\nALL RESUME-BASED JOB MATCHING TESTS PASSED!")

