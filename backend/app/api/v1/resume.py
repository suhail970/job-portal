from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlmodel import Session, select, func
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import io
import json
from pypdf import PdfReader
from app.core.database import get_session
from app.core.tenant import get_current_user, require_roles
from app.models.entities import Resume, StudentProfile, Department, User
from app.models.enums import UserRole
from app.ai.agents.resume_leaf import parse_resume_text, extract_academic_and_contact_fields

router = APIRouter(prefix="/resume", tags=["Resume AI"])

class ParseTextRequest(BaseModel):
    raw_text: str
    provider: Optional[str] = None
    custom_config: Optional[dict] = None


def _apply_extracted_profile(
    student: StudentProfile,
    extracted: Dict[str, Any],
    session: Session,
) -> List[str]:
    """Applies validated resume-extracted academic & contact fields without modifying standing_arrears."""
    applied: List[str] = []
    if extracted.get("cgpa") is not None:
        cgpa = float(extracted["cgpa"])
        if 0.0 < cgpa <= 10.0:
            student.cgpa = cgpa
            applied.append("cgpa")
    if extracted.get("graduation_year") is not None:
        yr = int(extracted["graduation_year"])
        if 2020 <= yr <= 2032:
            student.graduation_year = yr
            applied.append("graduation_year")
    if extracted.get("department_code"):
        dept = session.exec(
            select(Department).where(
                Department.college_id == student.college_id,
                func.upper(Department.code) == str(extracted["department_code"]).strip().upper(),
            )
        ).first()
        if dept:
            student.department_id = dept.id
            applied.append("department")
    if extracted.get("phone_number"):
        student.phone_number = str(extracted["phone_number"])[:30]
        applied.append("phone_number")
    if extracted.get("github_url"):
        student.github_url = str(extracted["github_url"])[:200]
        applied.append("github_url")
    if extracted.get("linkedin_url"):
        student.linkedin_url = str(extracted["linkedin_url"])[:200]
        applied.append("linkedin_url")

    if applied:
        session.add(student)
        session.commit()
        session.refresh(student)
    return applied


@router.post("/upload")
async def upload_resume(
    file: UploadFile = File(...),
    auto_apply: bool = Form(default=False),
    custom_config_json: Optional[str] = Form(default=None),
    current_user: User = Depends(require_roles([UserRole.STUDENT, UserRole.JOB_SEEKER])),
    session: Session = Depends(get_session)
):
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only PDF resumes are supported")

    student = session.exec(select(StudentProfile).where(StudentProfile.user_id == current_user.id)).first()
    student_id = student.id if student else current_user.id
    college_id = current_user.college_id or "global"

    # Read PDF content
    content = await file.read()
    raw_text = ""
    try:
        reader = PdfReader(io.BytesIO(content))
        for page in reader.pages:
            text = page.extract_text()
            if text:
                raw_text += text + "\n"
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Failed to read PDF: {str(e)}")

    custom_config = None
    if custom_config_json:
        try:
            custom_config = json.loads(custom_config_json)
        except Exception:
            custom_config = None

    if len(raw_text.strip()) < 40:
        extracted_academic = {
            "cgpa": None,
            "graduation_year": None,
            "department_code": None,
            "phone_number": None,
            "github_url": None,
            "linkedin_url": None,
            "standing_arrears": None,
            "warnings": [
                "Could not extract selectable text from this PDF (it may be a scanned image). Please enter your academic fields manually or upload a text-based PDF."
            ],
        }
        parsed_data = {
            "skills": [],
            "ats_score": 0.0,
            "summary": "Unreadable or image-only PDF.",
            "strengths": [],
            "improvements": ["Re-export your resume as a selectable text PDF rather than a scanned image."],
        }
    else:
        parsed_data = await parse_resume_text(raw_text, custom_config=custom_config)
        extracted_academic = parsed_data.get("academic_profile") or extract_academic_and_contact_fields(raw_text)

    applied_fields: List[str] = []
    if auto_apply and student:
        applied_fields = _apply_extracted_profile(student, extracted_academic, session)

    # Save to database
    resume = Resume(
        student_id=student_id,
        college_id=college_id,
        filename=file.filename,
        raw_text=raw_text[:8000],
        parsed_skills=json.dumps(parsed_data.get("skills", [])),
        ats_score=parsed_data.get("ats_score", 75.0),
        summary=parsed_data.get("summary", "")
    )
    session.add(resume)
    session.commit()
    session.refresh(resume)

    return {
        "message": "Resume parsed successfully",
        "resume_id": resume.id,
        "filename": resume.filename,
        "ats_score": resume.ats_score,
        "skills": parsed_data.get("skills", []),
        "summary": resume.summary,
        "strengths": parsed_data.get("strengths", []),
        "improvements": parsed_data.get("improvements", []),
        "extracted_academic": extracted_academic,
        "applied_fields": applied_fields,
        "applied_to_profile": len(applied_fields) > 0,
    }

@router.post("/parse-text")
async def parse_text_resume(
    req: ParseTextRequest,
    current_user: User = Depends(get_current_user)
):
    if len(req.raw_text.strip()) < 30:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Resume text is too short")
        
    parsed_data = await parse_resume_text(
        req.raw_text,
        preferred_provider=req.provider,
        custom_config=req.custom_config
    )
    return parsed_data

@router.get("/my-resume")
def get_my_resume(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    student = session.exec(select(StudentProfile).where(StudentProfile.user_id == current_user.id)).first()
    student_id = student.id if student else current_user.id

    resume = session.exec(
        select(Resume).where(Resume.student_id == student_id).order_by(Resume.uploaded_at.desc())
    ).first()

    if not resume:
        return {"has_resume": False}

    skills = []
    try:
        skills = json.loads(resume.parsed_skills)
    except Exception:
        pass

    return {
        "has_resume": True,
        "resume_id": resume.id,
        "filename": resume.filename,
        "ats_score": resume.ats_score,
        "skills": skills,
        "summary": resume.summary,
        "uploaded_at": resume.uploaded_at
    }

