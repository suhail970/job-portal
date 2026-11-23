import json
import logging
from typing import Dict, Any, List, Optional
from app.ai.router import ai_router
from app.models.enums import CountdownTarget
from app.ai.agents.company_research_leaf import get_or_create_company_playbook

logger = logging.getLogger("skillbridge.ai.orchestrator")

ORCHESTRATOR_SYSTEM_PROMPT = """You are the Senior Placement Preparation Planning Orchestrator for SkillBridge AI.
Your job is to generate a time-boxed, adaptive sprint preparation plan for a college student facing an upcoming campus recruitment drive.
You are equipped with a verified Company Intelligence Playbook containing the company's hiring rounds, culture, rejection pitfalls, and curated practice resources.

CRITICAL RULES:
1. Ground the preparation plan directly in the Company's verified hiring rounds and tech stack.
2. If remaining time is '1_DAY': Focus strictly on high-yield revision, company cheat sheets, must-know questions, and critical pitfalls. No heavy new concepts.
3. If remaining time is '3_DAYS': Focus on Day 1 (Core Coding & DSA), Day 2 (Domain/Stack Mastery & Machine Coding/System Design), Day 3 (Mock Interviews, STAR Behavioral & Rejection Pitfalls).
4. If remaining time is '7_DAYS': Comprehensive day-by-day sprint covering aptitude, daily LeetCode/GFG coding patterns, architecture viva, and full mock rounds.
5. For EVERY task, provide an actionable practice resource link (LeetCode, GeeksforGeeks, official docs, or cheat sheet).

Respond strictly in valid JSON format:
{
    "company_name": "Company",
    "role_title": "Role",
    "timeframe": "1_DAY / 3_DAYS / 7_DAYS",
    "strategy_overview": "Summary of the preparation strategy tailored to this company's hiring pattern",
    "days": [
        {
            "day_number": 1,
            "theme": "Day Focus Theme",
            "hours_required": 4,
            "tasks": [
                {
                    "id": "d1_t1",
                    "title": "Task title",
                    "category": "TECHNICAL / APTITUDE / CODING / HR / SYSTEM_DESIGN",
                    "estimated_mins": 45,
                    "description": "Specific instruction on what to practice and avoid",
                    "resource_name": "Name of practice resource or cheat sheet",
                    "resource_url": "Direct link e.g. https://leetcode.com/problem-list/top-interview-questions/ or https://www.geeksforgeeks.org/...",
                    "resource_type": "PRACTICE / CHEAT_SHEET / OFFICIAL_DOCS / GUIDE"
                }
            ]
        }
    ],
    "high_probability_questions": [
        {"question": "Sample Question", "category": "TECHNICAL / HR / SYSTEM_DESIGN", "tip": "How to answer"}
    ]
}"""

async def generate_countdown_plan(
    company_name: str,
    role_title: str,
    timeframe: CountdownTarget,
    job_description: str,
    student_skills: Optional[List[str]] = None,
    company_website: Optional[str] = None,
    selection_rounds: Optional[str] = None,
    preferred_provider: Optional[str] = None,
    custom_config: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """
    Two-Phase Countdown Plan Orchestration:
    Phase 1: Retrieve or autonomously synthesize the Universal Company Playbook.
    Phase 2: Generate time-boxed sprint with direct study links and skill gap diagnostics.
    """
    # 1. Fetch or synthesize Universal Company Playbook
    playbook = await get_or_create_company_playbook(
        company_name=company_name,
        role_title=role_title,
        job_description=job_description,
        company_website=company_website,
        selection_rounds=selection_rounds,
        preferred_provider=preferred_provider,
        custom_config=custom_config
    )

    # 2. Compute Skill Gap Analysis
    student_skills_list = [s.strip() for s in (student_skills or []) if s.strip()]
    gap_analysis = _compute_skill_gap(student_skills_list, job_description, playbook)

    # 3. Build enriched context for Orchestrator
    skills_context = f"Student Technical Stack: {', '.join(student_skills_list)}" if student_skills_list else "Student Technical Stack: Standard CS Fundamentals"
    playbook_summary = f"""Verified Company Intelligence:
Domain: {playbook.get('industry_domain', 'Technology')}
Culture & Focus: {playbook.get('culture_summary', '')}
Hiring Rounds: {json.dumps(playbook.get('hiring_rounds', []))}
Top Rejection Pitfalls: {json.dumps(playbook.get('top_rejection_pitfalls', []))}
Recommended Resources: {json.dumps(playbook.get('curated_resources', []))}"""

    user_prompt = f"""Generate a {timeframe.value} countdown preparation plan for:
Target Company: {company_name}
Target Role: {role_title}
Time Remaining: {timeframe.value}
{skills_context}

{playbook_summary}

Job Description Context:
{job_description[:1500]}"""

    messages = [
        {"role": "system", "content": ORCHESTRATOR_SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt}
    ]

    try:
        response_str = await ai_router.generate_completion(
            messages=messages,
            temperature=0.3,
            preferred_provider=preferred_provider,
            custom_config=custom_config,
            json_mode=True
        )
        plan_data = json.loads(response_str)
    except Exception as e:
        logger.warning(f"AI Plan orchestration fallback triggered: {e}")
        plan_data = _build_fallback_plan(company_name, role_title, timeframe, playbook)

    # Ensure company playbook, skill gap analysis and curated resources are attached
    plan_data["company_name"] = company_name
    plan_data["role_title"] = role_title
    plan_data["timeframe"] = timeframe.value
    plan_data["company_playbook"] = playbook
    plan_data["skill_gap_analysis"] = gap_analysis
    plan_data["curated_resources"] = playbook.get("curated_resources", [])
    plan_data["verification_links"] = playbook.get("verification_links", [])

    return plan_data


def _compute_skill_gap(student_skills: List[str], job_description: str, playbook: Dict[str, Any]) -> Dict[str, Any]:
    """Computes matched skills and high-priority missing skills for the candidate."""
    desc_lower = job_description.lower()
    common_tech_keywords = [
        "python", "java", "c++", "c#", ".net", "c", "javascript", "typescript", "react", "node.js", 
        "angular", "spring boot", "sql", "postgresql", "mongodb", "aws", "azure", "docker", "kubernetes", 
        "data structures", "algorithms", "system design", "microservices", "embedded linux", "git", "rest api"
    ]
    
    # Identify required skills from JD and playbook
    required_skills = []
    for kw in common_tech_keywords:
        if kw in desc_lower or any(kw in str(r).lower() for r in playbook.get("curated_resources", [])):
            required_skills.append(kw.title() if len(kw) > 3 else kw.upper())
            
    if not required_skills:
        required_skills = ["Data Structures", "Algorithms", "Java/Python", "SQL", "OOP Design"]

    student_lower = [s.lower() for s in student_skills]
    matched = []
    missing = []
    for req in required_skills:
        if req.lower() in student_lower or any(s in req.lower() for s in student_lower):
            matched.append(req)
        else:
            missing.append(req)

    total = len(required_skills)
    match_pct = round((len(matched) / total * 100), 1) if total > 0 else 75.0

    return {
        "matched_skills": matched,
        "missing_critical_skills": missing[:4],
        "readiness_percentage": match_pct,
        "summary": f"You match {len(matched)} of {total} core technical competencies for this role. Priority focus: {', '.join(missing[:3]) if missing else 'Final mock interviews & revision'}."
    }


def _build_fallback_plan(company_name: str, role_title: str, timeframe: CountdownTarget, playbook: Dict[str, Any]) -> Dict[str, Any]:
    """Generates structured fallback sprint when network/AI is temporarily offline."""
    resources = playbook.get("curated_resources") or [
        {"topic": "Top Interview Questions", "platform": "GeeksforGeeks", "url": "https://www.geeksforgeeks.org/top-100-interview-questions/", "type": "PRACTICE"},
        {"topic": "Core DSA Practice", "platform": "NeetCode", "url": "https://neetcode.io/practice", "type": "PRACTICE"}
    ]
    primary_res = resources[0]

    return {
        "company_name": company_name,
        "role_title": role_title,
        "timeframe": timeframe.value,
        "strategy_overview": f"Intensive {timeframe.value} placement sprint tailored to {company_name}'s hiring rounds and evaluation format.",
        "days": [
            {
                "day_number": 1,
                "theme": "Core Technical & Hiring Round Focus",
                "hours_required": 4,
                "tasks": [
                    {
                        "id": "d1_t1",
                        "title": f"Review {company_name} Round 1 Focus Topics",
                        "category": "CODING",
                        "estimated_mins": 90,
                        "description": f"Solve high-frequency coding patterns matching {company_name} assessment standards.",
                        "resource_name": primary_res.get("topic", "Coding Practice"),
                        "resource_url": primary_res.get("url", "https://neetcode.io/practice"),
                        "resource_type": primary_res.get("type", "PRACTICE")
                    },
                    {
                        "id": "d1_t2",
                        "title": "Core Technical CS Revision (DBMS, OOP, System Design)",
                        "category": "TECHNICAL",
                        "estimated_mins": 60,
                        "description": "Review ACID properties, indexing, memory management, and clean architecture.",
                        "resource_name": "System Design Roadmap",
                        "resource_url": "https://roadmap.sh/backend",
                        "resource_type": "CHEAT_SHEET"
                    }
                ]
            }
        ],
        "high_probability_questions": playbook.get("top_interview_questions") or [
            {"question": f"Why do you want to join {company_name}?", "category": "HR", "tip": "Highlight company culture and specific products."},
            {"question": "Explain internal memory layout and hash collision handling.", "category": "TECHNICAL", "tip": "Discuss chaining vs open addressing."}
        ]
    }
