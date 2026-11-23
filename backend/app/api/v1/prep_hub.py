from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select, func
from typing import List, Optional
from datetime import datetime, timezone, timedelta
from pydantic import BaseModel
import json
from app.core.database import get_session
from app.core.tenant import get_current_user, require_roles
from app.models.entities import PlacementPreparationPlan, StudentProfile, Resume, PlacementDrive, User
from app.models.enums import UserRole, CountdownTarget
from app.ai.agents.orchestrator import generate_countdown_plan

router = APIRouter(prefix="/prep-hub", tags=["Placement Intelligence Hub"])

class GeneratePlanRequest(BaseModel):
    company_name: str
    role_title: str
    timeframe: CountdownTarget = CountdownTarget.THREE_DAYS
    drive_id: Optional[str] = None
    custom_notes: Optional[str] = None
    provider: Optional[str] = None
    custom_config: Optional[dict] = None

class ToggleTaskRequest(BaseModel):
    task_id: str

@router.post("/generate")
async def create_countdown_plan(
    req: GeneratePlanRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    student = session.exec(select(StudentProfile).where(StudentProfile.user_id == current_user.id)).first()
    student_id = student.id if student else current_user.id
    college_id = current_user.college_id or "global"

    # Fetch student skills from latest resume
    resume = session.exec(
        select(Resume).where(Resume.student_id == student_id).order_by(Resume.uploaded_at.desc())
    ).first()
    student_skills = []
    if resume:
        try:
            student_skills = json.loads(resume.parsed_skills)
        except Exception:
            pass

    # Fetch drive description & metadata if linked
    job_desc = req.custom_notes or f"Recruitment for {req.company_name} - {req.role_title}. Technical assessments, DSA, system fundamentals, and behavioral interview."
    drive_date = datetime.now(timezone.utc)
    company_website = None
    selection_rounds = None
    if req.drive_id:
        drive = session.get(PlacementDrive, req.drive_id)
        if drive:
            job_desc = drive.job_description
            drive_date = drive.drive_date
            company_website = drive.company_website
            selection_rounds = drive.selection_rounds

    # Call AI Orchestrator Agent (with Universal Playbook & Skill Gap Analysis)
    plan_data = await generate_countdown_plan(
        company_name=req.company_name,
        role_title=req.role_title,
        timeframe=req.timeframe,
        job_description=job_desc,
        student_skills=student_skills,
        company_website=company_website,
        selection_rounds=selection_rounds,
        preferred_provider=req.provider,
        custom_config=req.custom_config
    )

    plan_record = PlacementPreparationPlan(
        student_id=student_id,
        college_id=college_id,
        company_name=req.company_name,
        role_title=req.role_title,
        target_timeframe=req.timeframe,
        drive_date=drive_date,
        generated_roadmap=json.dumps(plan_data),
        completed_tasks="[]",
        overall_progress=0.0
    )
    session.add(plan_record)
    session.commit()
    session.refresh(plan_record)

    return {
        "message": "Countdown preparation plan generated successfully!",
        "plan_id": plan_record.id,
        "timeframe": req.timeframe.value,
        "company_name": req.company_name,
        "role_title": req.role_title,
        "roadmap": plan_data
    }

@router.get("/my-plans")
def list_my_plans(
    current_user: User = Depends(require_roles([UserRole.STUDENT, UserRole.JOB_SEEKER])),
    session: Session = Depends(get_session)
):
    student = session.exec(select(StudentProfile).where(StudentProfile.user_id == current_user.id)).first()
    student_id = student.id if student else current_user.id

    plans = session.exec(
        select(PlacementPreparationPlan).where(PlacementPreparationPlan.student_id == student_id).order_by(PlacementPreparationPlan.created_at.desc())
    ).all()

    results = []
    for p in plans:
        roadmap = {}
        completed = []
        try:
            roadmap = json.loads(p.generated_roadmap)
            completed = json.loads(p.completed_tasks)
        except Exception:
            pass

        results.append({
            "id": p.id,
            "company_name": p.company_name,
            "role_title": p.role_title,
            "timeframe": p.target_timeframe.value,
            "overall_progress": p.overall_progress,
            "completed_tasks_count": len(completed),
            "created_at": p.created_at,
            "roadmap": roadmap,
            "completed_tasks": completed
        })

    return results

@router.post("/{plan_id}/toggle-task")
def toggle_plan_task(
    plan_id: str,
    req: ToggleTaskRequest,
    current_user: User = Depends(require_roles([UserRole.STUDENT, UserRole.JOB_SEEKER])),
    session: Session = Depends(get_session)
):
    plan = session.get(PlacementPreparationPlan, plan_id)
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")

    completed = []
    try:
        completed = json.loads(plan.completed_tasks)
    except Exception:
        pass

    if req.task_id in completed:
        completed.remove(req.task_id)
    else:
        completed.append(req.task_id)

    # Calculate new progress percentage
    total_tasks = 1
    try:
        roadmap = json.loads(plan.generated_roadmap)
        tasks_in_roadmap = []
        for d in roadmap.get("days", []):
            tasks_in_roadmap.extend(d.get("tasks", []))
        total_tasks = max(1, len(tasks_in_roadmap))
    except Exception:
        pass

    progress = round((len(completed) / total_tasks) * 100.0, 1)

    plan.completed_tasks = json.dumps(completed)
    plan.overall_progress = min(100.0, progress)
    session.add(plan)
    session.commit()
    session.refresh(plan)

    return {
        "plan_id": plan.id,
        "completed_tasks": completed,
        "overall_progress": plan.overall_progress
    }

@router.get("/playbook")
async def get_company_playbook_endpoint(
    company_name: str,
    role_title: Optional[str] = "Software Developer",
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Returns the Universal Company Playbook for ANY company.
    If already cached, returns instantly (< 50ms). If new, autonomously profiles and caches.
    """
    from app.ai.agents.company_research_leaf import get_or_create_company_playbook
    drive = session.exec(
        select(PlacementDrive).where(func.lower(PlacementDrive.company_name) == company_name.strip().lower())
    ).first()
    website = drive.company_website if drive else None
    rounds = drive.selection_rounds if drive else None
    desc = drive.job_description if drive else f"Software engineering and placement opportunities at {company_name}."

    playbook = await get_or_create_company_playbook(
        company_name=company_name,
        role_title=role_title,
        job_description=desc,
        company_website=website,
        selection_rounds=rounds
    )
    return playbook

class AskCompanyRequest(BaseModel):
    company_name: str
    question: str
    role_title: Optional[str] = "Software Developer"
    provider: Optional[str] = None
    custom_config: Optional[dict] = None

@router.post("/ask-company")
async def ask_company_question(
    req: AskCompanyRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Interactive Q&A: Student asks any doubt about a company, role, hiring rounds,
    work culture, interview tips, or bond/agreement and receives an instant mentor answer.
    """
    from app.ai.agents.company_research_leaf import get_or_create_company_playbook
    from app.ai.router import ai_router

    drive = session.exec(
        select(PlacementDrive).where(func.lower(PlacementDrive.company_name) == req.company_name.strip().lower())
    ).first()
    website = drive.company_website if drive else None
    rounds = drive.selection_rounds if drive else None
    desc = drive.job_description if drive else f"Software engineering and placement opportunities at {req.company_name}."

    playbook = await get_or_create_company_playbook(
        company_name=req.company_name,
        role_title=req.role_title,
        job_description=desc,
        company_website=website,
        selection_rounds=rounds,
        preferred_provider=req.provider,
        custom_config=req.custom_config
    )

    system_prompt = f"""You are the Senior Campus Placement Mentor for SkillBridge AI.
A student is preparing for an upcoming recruitment drive at {req.company_name} for the role of {req.role_title}.

COMPANY INTELLIGENCE DOSSIER:
Company: {req.company_name}
Domain: {playbook.get('industry_domain', 'Technology')}
Culture & Focus: {playbook.get('culture_summary', '')}
Known Hiring Rounds: {json.dumps(playbook.get('hiring_rounds', []))}
Top Rejection Pitfalls: {json.dumps(playbook.get('top_rejection_pitfalls', []))}
High Frequency Questions: {json.dumps(playbook.get('top_interview_questions', []))}

INSTRUCTIONS:
1. Answer the student's question directly, honestly, and in short, simple English.
2. If asking about interview rounds, what to study, dress code, bond/agreement, or work-life balance, provide clear practical advice.
3. Keep the tone encouraging, realistic, and mentor-like. Avoid generic fluff. Maximum 2-3 concise paragraphs."""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": req.question}
    ]

    try:
        answer_text = await ai_router.generate_completion(
            messages=messages,
            temperature=0.4,
            preferred_provider=req.provider,
            custom_config=req.custom_config
        )
    except Exception as e:
        answer_text = f"For {req.company_name}, focus on core computer science fundamentals, modular OOP code, and clear explanation of your past projects. Make sure to prepare for their primary rounds: {', '.join([r['name'] for r in playbook.get('hiring_rounds', [])])}."

    return {
        "company_name": req.company_name,
        "role_title": req.role_title,
        "question": req.question,
        "answer": answer_text,
        "verification_links": playbook.get("verification_links", []),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }



