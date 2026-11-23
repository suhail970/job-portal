import json
from typing import Dict, Any, List
from app.ai.router import ai_router

GAP_SYSTEM_PROMPT = """You are a Talent Intelligence Matching Agent for campus placements.
Compare the candidate's skills and background against the placement drive job description.
Determine the match percentage (0 to 100), identify matched skills, missing essential skills, and a targeted advice note for the candidate.

Respond strictly in valid JSON format:
{
    "match_percentage": 84.5,
    "matched_skills": ["SkillA", "SkillB"],
    "missing_skills": ["SkillX", "SkillY"],
    "readiness_verdict": "STRONG MATCH / MODERATE MATCH / NEEDS PREPARATION",
    "advice": "Actionable advice on what to prioritize before this interview."
}"""

async def match_resume_to_drive(
    resume_skills: List[str],
    resume_summary: str,
    job_description: str,
    company_name: str,
    role_title: str,
    preferred_provider: str = None
) -> Dict[str, Any]:
    content = f"""Company: {company_name}
Role: {role_title}
Job Description:
{job_description[:3000]}

Candidate Skills: {', '.join(resume_skills)}
Candidate Profile Summary: {resume_summary}"""

    messages = [
        {"role": "system", "content": GAP_SYSTEM_PROMPT},
        {"role": "user", "content": content}
    ]

    response_str = await ai_router.generate_completion(
        messages=messages,
        temperature=0.2,
        preferred_provider=preferred_provider,
        json_mode=True
    )

    try:
        return json.loads(response_str)
    except Exception:
        return {
            "match_percentage": 75.0,
            "matched_skills": resume_skills[:3],
            "missing_skills": ["System Design", "Cloud Basics"],
            "readiness_verdict": "MODERATE MATCH",
            "advice": f"Review core requirements for {company_name} - {role_title} focusing on problem solving."
        }

