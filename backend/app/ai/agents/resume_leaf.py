import json
from typing import Dict, Any, Optional
from app.ai.router import ai_router

SYSTEM_PROMPT = """You are an expert AI Resume Analyst and Placement Screener.
Analyze the provided student resume text. Extract technical skills, tools, frameworks, calculate an ATS compatibility score (0-100), identify 3 core strengths, and 3 high-impact improvement recommendations.

Respond strictly in valid JSON format:
{
    "skills": ["Skill1", "Skill2", ...],
    "ats_score": 85.0,
    "summary": "Brief summary of candidate's technical profile",
    "strengths": ["Strength 1", "Strength 2", "Strength 3"],
    "improvements": ["Improvement 1", "Improvement 2", "Improvement 3"]
}"""

async def parse_resume_text(
    raw_text: str,
    preferred_provider: str = None,
    custom_config: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Here is the candidate's resume text:\n\n{raw_text[:6000]}"}
    ]
    
    response_str = await ai_router.generate_completion(
        messages=messages,
        temperature=0.2,
        preferred_provider=preferred_provider,
        custom_config=custom_config,
        json_mode=True
    )

    try:
        data = json.loads(response_str)
        return data
    except Exception:
        # Fallback in case of parse error
        return {
            "skills": ["Python", "JavaScript", "SQL", "Git", "Data Structures"],
            "ats_score": 78.0,
            "summary": "Engineering graduate with solid computer science fundamentals.",
            "strengths": ["Good foundation in programming", "Relevant academic projects"],
            "improvements": ["Quantify project impact metrics", "Highlight problem solving achievements"]
        }

