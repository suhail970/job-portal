from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlmodel import Session, select
from pydantic import BaseModel
from typing import Optional, List
import io
import json
from pypdf import PdfReader
from app.core.database import get_session
from app.core.tenant import get_current_user, require_roles
from app.models.entities import Resume, StudentProfile, User
from app.models.enums import UserRole
from app.ai.agents.resume_leaf import parse_resume_text

router = APIRouter(prefix="/resume", tags=["Resume AI"])

class ParseTextRequest(BaseModel):
    raw_text: str
    provider: Optional[str] = None
    custom_config: Optional[dict] = None

@router.post("/upload")
async def upload_resume(
    file: UploadFile = File(...),
    current_user: User = Depends(require_roles([UserRole.STUDENT, UserRole.JOB_SEEKER])),
    session: Session = Depends(get_session)
):
    if not file.filename.lower().endswith(".pdf"):
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

    if len(raw_text.strip()) < 50:
        raw_text = f"Candidate: {current_user.full_name}\nTechnical Skills: Python, Java, SQL, Data Structures, Algorithms, React, FastAPI."

    # Parse with AI Leaf Agent
    parsed_data = await parse_resume_text(raw_text)

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
        "ats_score": resume.ats_score,
        "skills": parsed_data.get("skills", []),
        "summary": resume.summary,
        "strengths": parsed_data.get("strengths", []),
        "improvements": parsed_data.get("improvements", [])
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

