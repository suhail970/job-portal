from enum import Enum

class UserRole(str, Enum):
    ADMIN = "ADMIN"
    COLLEGE_ADMIN = "COLLEGE_ADMIN"
    TPO = "TPO"
    FACULTY = "FACULTY"
    STUDENT = "STUDENT"
    JOB_SEEKER = "JOB_SEEKER"

class DriveStatus(str, Enum):
    DRAFT = "DRAFT"
    UPCOMING = "UPCOMING"
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"

class ApplicationStatus(str, Enum):
    APPLIED = "APPLIED"
    SHORTLISTED = "SHORTLISTED"
    ASSESSMENT_CLEARED = "ASSESSMENT_CLEARED"
    INTERVIEW_SCHEDULED = "INTERVIEW_SCHEDULED"
    OFFERED = "OFFERED"
    REJECTED = "REJECTED"

class CountdownTarget(str, Enum):
    ONE_DAY = "1_DAY"
    THREE_DAYS = "3_DAYS"
    SEVEN_DAYS = "7_DAYS"

class AIProvider(str, Enum):
    GEMINI = "gemini"
    GROQ = "groq"
    OPENROUTER = "openrouter"
    OLLAMA = "ollama"

class TaskStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

