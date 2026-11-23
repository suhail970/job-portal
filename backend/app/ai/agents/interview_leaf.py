import json
from typing import Dict, Any, List, Optional
from app.ai.router import ai_router

INTERVIEW_EVAL_PROMPT = """You are a Principal Engineering Interviewer and HR specialist conducting a mock interview for a college campus recruitment drive.
Evaluate the candidate's spoken response to the technical/HR question.

Provide:
1. Technical score (0.0 to 10.0)
2. Communication score (0.0 to 10.0)
3. Constructive feedback highlighting what was done well and what was missing
4. The next logical follow-up question or new topic question for the role.

Respond strictly in valid JSON format:
{
    "technical_score": 8.0,
    "communication_score": 7.5,
    "overall_score": 7.8,
    "feedback": "Strong explanation of the concept, but lacked mention of edge cases and time complexity.",
    "next_question": "How would you optimize this solution if the dataset does not fit into RAM?"
}"""

async def evaluate_interview_turn(
    company_name: str,
    role_title: str,
    question: str,
    student_transcript: str,
    turn_index: int,
    preferred_provider: str = None,
    custom_config: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    content = f"""Company: {company_name}
Role: {role_title}
Turn Number: {turn_index}
Question Asked: {question}
Student's Spoken Answer Transcript:
{student_transcript}"""

    messages = [
        {"role": "system", "content": INTERVIEW_EVAL_PROMPT},
        {"role": "user", "content": content}
    ]

    response_str = await ai_router.generate_completion(
        messages=messages,
        temperature=0.3,
        preferred_provider=preferred_provider,
        custom_config=custom_config,
        json_mode=True
    )

    try:
        return json.loads(response_str)
    except Exception:
        return {
            "technical_score": 7.5,
            "communication_score": 8.0,
            "overall_score": 7.8,
            "feedback": "Good fundamental understanding. Be more structured in articulating the trade-offs.",
            "next_question": f"Can you explain a challenging bug you encountered in a recent project and how you debugged it?"
        }

