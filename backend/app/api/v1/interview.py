from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from typing import List, Optional
from pydantic import BaseModel
from app.core.database import get_session
from app.core.tenant import get_current_user, require_roles
from app.models.entities import MockInterviewSession, InterviewTurn, StudentProfile, User
from app.models.enums import UserRole
from app.ai.agents.interview_leaf import evaluate_interview_turn

router = APIRouter(prefix="/interview", tags=["AI Voice Mock Interview"])

class StartInterviewRequest(BaseModel):
    company_name: str
    role_title: str

class SubmitTurnRequest(BaseModel):
    session_id: str
    turn_index: int
    question: str
    student_transcript: str
    provider: Optional[str] = None
    custom_config: Optional[dict] = None

@router.post("/start")
def start_interview_session(
    req: StartInterviewRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    student = session.exec(select(StudentProfile).where(StudentProfile.user_id == current_user.id)).first()
    student_id = student.id if student else current_user.id
    college_id = current_user.college_id or "global"

    mock_session = MockInterviewSession(
        student_id=student_id,
        college_id=college_id,
        company_name=req.company_name,
        role_title=req.role_title,
        status="IN_PROGRESS"
    )
    session.add(mock_session)
    session.commit()
    session.refresh(mock_session)

    # First opening question
    opening_question = f"Welcome to the mock interview for {req.company_name} for the position of {req.role_title}! Let's start with a brief introduction: Can you walk me through your technical background and a challenging project you have built?"

    first_turn = InterviewTurn(
        session_id=mock_session.id,
        turn_index=1,
        ai_question=opening_question
    )
    session.add(first_turn)
    session.commit()

    return {
        "session_id": mock_session.id,
        "company_name": req.company_name,
        "role_title": req.role_title,
        "turn_index": 1,
        "question": opening_question
    }

@router.post("/turn")
async def submit_interview_turn(
    req: SubmitTurnRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    mock_session = session.get(MockInterviewSession, req.session_id)
    if not mock_session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Interview session not found")

    turn = session.exec(
        select(InterviewTurn).where(
            InterviewTurn.session_id == req.session_id,
            InterviewTurn.turn_index == req.turn_index
        )
    ).first()

    if not turn:
        turn = InterviewTurn(
            session_id=req.session_id,
            turn_index=req.turn_index,
            ai_question=req.question
        )
        session.add(turn)

    # Evaluate student answer using AI Leaf Agent
    evaluation = await evaluate_interview_turn(
        company_name=mock_session.company_name,
        role_title=mock_session.role_title,
        question=req.question,
        student_transcript=req.student_transcript,
        turn_index=req.turn_index,
        preferred_provider=req.provider,
        custom_config=req.custom_config
    )

    turn.student_transcript = req.student_transcript
    turn.score = evaluation.get("overall_score", 7.5)
    turn.feedback = evaluation.get("feedback", "")
    session.add(turn)

    # Create next turn if turn_index < 5
    next_question = evaluation.get("next_question", "Do you have any questions for us regarding the engineering team?")
    next_turn_index = req.turn_index + 1
    
    if req.turn_index < 5:
        next_turn = InterviewTurn(
            session_id=mock_session.id,
            turn_index=next_turn_index,
            ai_question=next_question
        )
        session.add(next_turn)

    session.commit()

    return {
        "turn_index": req.turn_index,
        "score": turn.score,
        "feedback": turn.feedback,
        "technical_score": evaluation.get("technical_score", 7.0),
        "communication_score": evaluation.get("communication_score", 7.0),
        "has_next": req.turn_index < 5,
        "next_question": next_question if req.turn_index < 5 else None
    }

@router.post("/{session_id}/complete")
def complete_interview(
    session_id: str,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    mock_session = session.get(MockInterviewSession, session_id)
    if not mock_session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    turns = session.exec(
        select(InterviewTurn).where(InterviewTurn.session_id == session_id).order_by(InterviewTurn.turn_index.asc())
    ).all()

    scores = [t.score for t in turns if t.score is not None]
    avg_score = round(sum(scores) / max(1, len(scores)), 1)

    mock_session.overall_score = avg_score
    mock_session.status = "COMPLETED"
    mock_session.feedback_summary = f"Candidate demonstrated good technical foundation across {len(turns)} interview questions. Average performance rating: {avg_score}/10."
    session.add(mock_session)
    session.commit()
    session.refresh(mock_session)

    return {
        "session_id": mock_session.id,
        "company_name": mock_session.company_name,
        "role_title": mock_session.role_title,
        "overall_score": avg_score,
        "feedback_summary": mock_session.feedback_summary,
        "turns": turns
    }

