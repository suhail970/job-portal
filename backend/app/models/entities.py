from typing import Optional, List
from datetime import datetime, timezone
import uuid
import json
from sqlmodel import SQLModel, Field, Relationship
from app.models.enums import UserRole, DriveStatus, ApplicationStatus, CountdownTarget, TaskStatus

def generate_uuid() -> str:
    return str(uuid.uuid4())

# -------------------------------------------------------------
# College & Department Models
# -------------------------------------------------------------
class College(SQLModel, table=True):
    __tablename__ = "colleges"
    id: str = Field(default_factory=generate_uuid, primary_key=True)
    name: str = Field(index=True)
    code: str = Field(unique=True, index=True) # e.g. "CEG-001"
    address: Optional[str] = None
    website: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Department(SQLModel, table=True):
    __tablename__ = "departments"
    id: str = Field(default_factory=generate_uuid, primary_key=True)
    college_id: str = Field(foreign_key="colleges.id", index=True)
    name: str # e.g. "Computer Science and Engineering"
    code: str # e.g. "CSE"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# -------------------------------------------------------------
# User Model
# -------------------------------------------------------------
class User(SQLModel, table=True):
    __tablename__ = "users"
    id: str = Field(default_factory=generate_uuid, primary_key=True)
    email: str = Field(unique=True, index=True)
    hashed_password: str
    full_name: str
    role: UserRole = Field(default=UserRole.STUDENT, index=True)
    college_id: Optional[str] = Field(default=None, foreign_key="colleges.id", index=True)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# -------------------------------------------------------------
# Student Profile Model
# -------------------------------------------------------------
class StudentProfile(SQLModel, table=True):
    __tablename__ = "student_profiles"
    id: str = Field(default_factory=generate_uuid, primary_key=True)
    user_id: str = Field(foreign_key="users.id", unique=True, index=True)
    college_id: str = Field(foreign_key="colleges.id", index=True)
    department_id: Optional[str] = Field(default=None, foreign_key="departments.id", index=True)
    roll_number: str = Field(index=True)
    cgpa: float = Field(default=0.0)
    standing_arrears: int = Field(default=0)
    history_arrears: int = Field(default=0)
    graduation_year: int = Field(default=2026)
    phone_number: Optional[str] = None
    telegram_chat_id: Optional[str] = Field(default=None, index=True)
    bio: Optional[str] = None
    github_url: Optional[str] = None
    linkedin_url: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# -------------------------------------------------------------
# Placement Drive Model
# -------------------------------------------------------------
class PlacementDrive(SQLModel, table=True):
    __tablename__ = "placement_drives"
    id: str = Field(default_factory=generate_uuid, primary_key=True)
    college_id: str = Field(foreign_key="colleges.id", index=True)
    company_name: str = Field(index=True)
    role_title: str = Field(index=True)
    job_description: str
    location: Optional[str] = "Pan India / Hybrid"
    salary_package: Optional[str] = "6.5 LPA - 12 LPA"
    min_cgpa: float = Field(default=6.0)
    max_arrears: int = Field(default=0)
    allowed_departments: str = Field(default="CSE,IT,ECE") # Comma-separated or JSON
    drive_date: datetime
    registration_deadline: datetime
    status: DriveStatus = Field(default=DriveStatus.UPCOMING, index=True)
    application_url: Optional[str] = Field(default=None) # Direct external/company portal link
    company_website: Optional[str] = Field(default=None) # Official company website
    selection_rounds: Optional[str] = Field(default=None) # e.g. "Online Assessment -> Tech Interview -> HR"
    form_type: Optional[str] = Field(default="DIRECT_FORM") # "DIRECT_FORM" | "CORPORATE_PORTAL" | "CAMPUS_DRIVE"
    verification_status: Optional[str] = Field(default="VERIFIED_ACTIVE") # "VERIFIED_ACTIVE" | "PENDING_VERIFICATION"
    expected_fields: Optional[str] = Field(default=None) # JSON list or description of required fields
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# -------------------------------------------------------------
# Application Model
# -------------------------------------------------------------
class Application(SQLModel, table=True):
    __tablename__ = "applications"
    id: str = Field(default_factory=generate_uuid, primary_key=True)
    drive_id: str = Field(foreign_key="placement_drives.id", index=True)
    student_id: str = Field(foreign_key="student_profiles.id", index=True)
    college_id: str = Field(foreign_key="colleges.id", index=True)
    match_score: float = Field(default=0.0) # 0 to 100%
    status: ApplicationStatus = Field(default=ApplicationStatus.APPLIED, index=True)
    notes: Optional[str] = None
    applied_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# -------------------------------------------------------------
# Resume Model
# -------------------------------------------------------------
class Resume(SQLModel, table=True):
    __tablename__ = "resumes"
    id: str = Field(default_factory=generate_uuid, primary_key=True)
    student_id: str = Field(foreign_key="student_profiles.id", index=True)
    college_id: str = Field(foreign_key="colleges.id", index=True)
    filename: str
    raw_text: str
    parsed_skills: str = Field(default="[]") # JSON list of strings
    ats_score: float = Field(default=75.0) # 0 to 100
    summary: Optional[str] = None
    uploaded_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# -------------------------------------------------------------
# Placement Intelligence Hub (Countdown Preparation)
# -------------------------------------------------------------
class PlacementPreparationPlan(SQLModel, table=True):
    __tablename__ = "placement_preparation_plans"
    id: str = Field(default_factory=generate_uuid, primary_key=True)
    student_id: str = Field(foreign_key="student_profiles.id", index=True)
    college_id: str = Field(foreign_key="colleges.id", index=True)
    company_name: str
    role_title: str
    target_timeframe: CountdownTarget = Field(default=CountdownTarget.THREE_DAYS)
    drive_date: datetime
    generated_roadmap: str = Field(default="{}") # JSON of days and topics
    completed_tasks: str = Field(default="[]") # JSON list of task IDs
    overall_progress: float = Field(default=0.0)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# -------------------------------------------------------------
# Mock Interview Models
# -------------------------------------------------------------
class MockInterviewSession(SQLModel, table=True):
    __tablename__ = "mock_interview_sessions"
    id: str = Field(default_factory=generate_uuid, primary_key=True)
    student_id: str = Field(foreign_key="student_profiles.id", index=True)
    college_id: str = Field(foreign_key="colleges.id", index=True)
    company_name: str
    role_title: str
    overall_score: float = Field(default=0.0) # 0 to 10
    feedback_summary: Optional[str] = None
    status: str = Field(default="IN_PROGRESS") # IN_PROGRESS, COMPLETED
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class InterviewTurn(SQLModel, table=True):
    __tablename__ = "interview_turns"
    id: str = Field(default_factory=generate_uuid, primary_key=True)
    session_id: str = Field(foreign_key="mock_interview_sessions.id", index=True)
    turn_index: int
    ai_question: str
    student_transcript: Optional[str] = None
    score: Optional[float] = None
    feedback: Optional[str] = None

# -------------------------------------------------------------
# Task Queue (Hermes Kanban Pattern)
# -------------------------------------------------------------
class AsyncAgentTask(SQLModel, table=True):
    __tablename__ = "async_agent_tasks"
    id: str = Field(default_factory=generate_uuid, primary_key=True)
    task_type: str = Field(index=True) # e.g. "PARSE_RESUME", "BROADCAST_TELEGRAM", "EVALUATE_MOCK"
    payload: str = Field(default="{}")
    status: TaskStatus = Field(default=TaskStatus.PENDING, index=True)
    retry_count: int = Field(default=0)
    result: Optional[str] = None
    error: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

# -------------------------------------------------------------
# Hermes-Grade Cron Subsystem Models
# -------------------------------------------------------------
class CronJob(SQLModel, table=True):
    __tablename__ = "cron_jobs"
    id: str = Field(default_factory=generate_uuid, primary_key=True)
    name: str = Field(index=True)
    description: Optional[str] = None
    schedule_kind: str = Field(default="cron") # "cron", "interval", "delay"
    cron_expr: str = Field(default="0 9 * * *") # 5-field standard cron syntax
    target_location: Optional[str] = None # e.g. "Coimbatore", "Kolkata", "All"
    college_id: Optional[str] = Field(default="col-anna-001", index=True)
    enabled: bool = Field(default=True)
    state: str = Field(default="scheduled", index=True) # "scheduled", "paused", "running"
    next_run_at: datetime = Field(index=True)
    last_run_at: Optional[datetime] = None
    last_status: Optional[str] = None # "ok", "error", "silent"
    last_error: Optional[str] = None
    grace_minutes: int = Field(default=60) # Missed-occurrence grace window
    total_runs: int = Field(default=0)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class CronExecution(SQLModel, table=True):
    __tablename__ = "cron_executions"
    id: str = Field(default_factory=generate_uuid, primary_key=True)
    job_id: str = Field(foreign_key="cron_jobs.id", index=True)
    dispatch_kind: str = Field(default="scheduled") # "scheduled", "manual", "catch_up", "late"
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    finished_at: Optional[datetime] = None
    duration_ms: Optional[int] = None
    status: str = Field(default="running") # "ok", "error", "silent"
    new_drives_added: int = Field(default=0)
    summary: Optional[str] = None
    error_message: Optional[str] = None

# -------------------------------------------------------------
# Universal Company Playbook Model
# -------------------------------------------------------------
class CompanyPlaybook(SQLModel, table=True):
    __tablename__ = "company_playbooks"
    id: str = Field(default_factory=generate_uuid, primary_key=True)
    company_name: str = Field(index=True)
    industry_domain: Optional[str] = "Technology & Software Engineering"
    culture_summary: Optional[str] = None
    hiring_rounds: str = Field(default="[]") # JSON list of hiring round structures
    top_rejection_pitfalls: str = Field(default="[]") # JSON list of critical failure traps
    top_interview_questions: str = Field(default="[]") # JSON list of Q&A with tips
    curated_resources: str = Field(default="[]") # JSON list of practice links, GFG archives, LeetCode, docs
    college_insider_tips: Optional[str] = None # Optional college-specific placement senior advice
    is_verified: bool = Field(default=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


