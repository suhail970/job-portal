# SkillBridge AI — API Specifications & Contract Design

**Document Reference**: `SB-DOC-04`  
**Version**: 1.0.0  
**Base Protocol**: RESTful JSON over HTTPS / WebSockets for live voice streaming  
**Standard Port**: `8000` (FastAPI ASGI Engine)

---

## 1. Global Conventions & Headers

All requests to protected endpoints must supply the standard Bearer authorization header:
```http
Authorization: Bearer <JWT_ACCESS_TOKEN>
```

### Standard Response Envelope
```json
{
  "status": "success",
  "data": { ... },
  "message": "Operation completed successfully",
  "timestamp": "2026-11-23T08:00:00Z"
}
```

### Standard Error Envelope
```json
{
  "status": "error",
  "error_code": "TENANT_ACCESS_DENIED",
  "detail": "Requested drive belongs to another college domain.",
  "timestamp": "2026-11-23T08:00:00Z"
}
```

---

## 2. Endpoint Inventory

```mermaid
graph TD
    API[FastAPI v1 Gateway]
    API --> AUTH[/api/v1/auth]
    API --> COL[/api/v1/colleges]
    API --> DRV[/api/v1/drives]
    API --> STU[/api/v1/students]
    API --> RES[/api/v1/resume]
    API --> PREP[/api/v1/prep]
    API --> INT[/api/v1/interview]
    API --> SIM[/api/v1/simulation]
```

---

## 3. Core Endpoint Specifications

### 3.1 Authentication & Multi-Tenant Login
* `POST /api/v1/auth/login`
  * **Payload**:
    ```json
    {
      "email": "student@annauniv.edu",
      "password": "Password123!",
      "college_slug": "anna-univ"
    }
    ```
  * **Response (200 OK)**:
    ```json
    {
      "access_token": "eyJhbGciOi...",
      "token_type": "bearer",
      "user": {
        "id": "usr-9a01",
        "email": "student@annauniv.edu",
        "role": "STUDENT",
        "full_name": "Suresh Kannan",
        "college_id": "col-anna-001",
        "college_slug": "anna-univ"
      }
    }
    ```

* `POST /api/v1/auth/register`
  * **Payload**:
    ```json
    {
      "email": "new.student@annauniv.edu",
      "password": "SecurePassword#1",
      "full_name": "Priya Sharma",
      "role": "STUDENT",
      "college_slug": "anna-univ",
      "roll_number": "2021CSE089",
      "cgpa": 8.42,
      "graduation_year": 2026
    }
    ```

---

### 3.2 TPO Campus Drive Operations
* `GET /api/v1/drives/`
  * **Query Params**: `status=UPCOMING`, `min_ctc=6.0`
  * **Returns**: Array of active drives filtered by the student's authenticated tenant.

* `POST /api/v1/drives/` (TPO Only)
  * **Payload**:
    ```json
    {
      "company_name": "Zoho Corporation",
      "role_title": "Software Developer",
      "job_description": "Strong proficiency in C, Java, OOP concepts, and data structures.",
      "minimum_cgpa": 7.5,
      "max_backlogs": 0,
      "ctc_lpa": 8.5,
      "drive_date": "2026-12-05",
      "deadline": "2026-11-30"
    }
    ```

* `GET /api/v1/drives/{drive_id}/eligible-students`
  * **Returns**: Ranked list of student profiles meeting CGPA and backlog criteria, with calculated resume match percentages.

---

### 3.3 AI Resume Analysis & Gap Extraction
* `POST /api/v1/resume/analyze`
  * **Headers**: `Content-Type: multipart/form-data` or JSON raw text
  * **Payload**: `file: resume.pdf` OR `resume_text: "..."`, `job_description: "..."`, `model_override: "gemini" | "ollama"`
  * **Response (200 OK)**:
    ```json
    {
      "overall_match_score": 82,
      "verdict": "STRONG_MATCH",
      "matched_skills": ["Python", "FastAPI", "SQL", "Git"],
      "missing_skills": ["Docker", "Redis", "Kafka"],
      "ats_issues": [
        "Include quantitative metric in project description #2",
        "Ensure standard Arial/Calibri font encoding"
      ],
      "model_used": "gemini-1.5-flash"
    }
    ```

---

### 3.4 Company Countdown Preparation Hub
* `GET /api/v1/prep/roadmap?company=zoho&days=3`
  * **Returns**: 3-day structured curriculum with daily study objectives, recommended leetcode problem IDs, technical review sheets, and mock question checklists.

---

### 3.5 Voice Mock Interview Simulator
* `POST /api/v1/interview/start`
  * **Payload**:
    ```json
    {
      "company_name": "Amazon",
      "role_title": "SDE-1",
      "round_type": "TECHNICAL_DATA_STRUCTURES",
      "model_override": "gemini"
    }
    ```
  * **Response**:
    ```json
    {
      "session_id": "ses-8812-int",
      "first_question": "Can you explain how a Hash Map handles collision resolution in Java, and what the worst-case time complexity is?",
      "audio_prompt_url": null
    }
    ```

* `POST /api/v1/interview/respond`
  * **Payload**:
    ```json
    {
      "session_id": "ses-8812-int",
      "turn_number": 1,
      "student_answer_transcript": "In Java 8, hash collisions use linked lists which convert into red-black trees when the bin count exceeds 8.",
      "model_override": "gemini"
    }
    ```
  * **Response**:
    ```json
    {
      "feedback": "Accurate response regarding treeification threshold (TREEIFY_THRESHOLD = 8).",
      "score": 4.8,
      "next_question": "Great! Now, how does Rehashing work when the load factor reaches 0.75?"
    }
    ```

---

### 3.6 Sandboxed Code Execution
* `POST /api/v1/simulation/execute`
  * **Payload**:
    ```json
    {
      "language": "python",
      "code": "def solve(arr):\n    return sorted(arr)\nprint(solve([5, 2, 8, 1]))",
      "stdin": ""
    }
    ```
  * **Response**:
    ```json
    {
      "status": "success",
      "stdout": "[1, 2, 5, 8]\n",
      "stderr": "",
      "execution_time_ms": 42.1,
      "memory_kb": 1280
    }
    ```

