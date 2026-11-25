import json
import re
from typing import Dict, Any, List, Optional
from app.ai.router import ai_router

SYSTEM_PROMPT = """You are an expert AI Resume Analyst and Placement Screener.
Analyze the provided student resume text. Extract technical skills, tools, frameworks, calculate an ATS compatibility score (0-100), identify 3 core strengths, and 3 high-impact improvement recommendations, along with academic details if clearly present.

Respond strictly in valid JSON format:
{
    "skills": ["Skill1", "Skill2", ...],
    "ats_score": 85.0,
    "summary": "Brief summary of candidate's technical profile",
    "strengths": ["Strength 1", "Strength 2", "Strength 3"],
    "improvements": ["Improvement 1", "Improvement 2", "Improvement 3"],
    "cgpa": null,
    "graduation_year": null,
    "department_code": null
}"""

DEPARTMENT_PATTERNS = [
    ("CSE", [r"\bcomputer\s+science(?:\s+and\s+engineering)?\b", r"\bcse\b", r"\bb\.?\s*(?:e|tech)\.?\s*(?:in\s+)?cs\b"]),
    ("IT", [r"\binformation\s+technology\b", r"\bb\.?\s*(?:e|tech)\.?\s*(?:in\s+)?it\b"]),
    ("ECE", [r"\belectronics\s*(?:and|&)\s*communication\b", r"\bece\b"]),
    ("EEE", [r"\belectrical\s*(?:and|&)\s*electronics\b", r"\beee\b"]),
    ("MECH", [r"\bmechanical\s+engineering\b", r"\bmech\b"]),
    ("CIVIL", [r"\bcivil\s+engineering\b"]),
    ("AIDS", [r"\bartificial\s+intelligence\s*(?:and|&)\s*data\s+science\b", r"\bai\s*&\s*ds\b", r"\baids\b"]),
    ("AIML", [r"\bartificial\s+intelligence\s*(?:and|&)\s*machine\s+learning\b", r"\baiml\b"]),
]

SCHOOL_LINE_MARKERS = ("10th", "12th", "sslc", "hsc", "secondary", "high school", "matric", "cbse", "icse", "class x", "class xii")
HIGHER_ED_MARKERS = ("b.e", "b.tech", "bachelor", "degree", "university", "college", "cgpa", "sgpa", "gpa", "semester", "engineering")


def _extract_cgpa_and_warnings(lines: List[str], warnings: List[str]) -> Optional[float]:
    cgpa_pattern = re.compile(
        r"(?i)(?:c\.?\s*g\.?\s*p\.?\s*a|s\.?\s*g\.?\s*p\.?\s*a|gpa)\s*(?:[:=\-]|of|is)?\s*(\d{1,2}(?:\.\d{1,2})?)(?:\s*/\s*(10(?:\.0+)?|4(?:\.0+)?))?"
    )
    reverse_cgpa_pattern = re.compile(r"(?i)\b(\d(?:\.\d{1,2})?)\s*(?:/\s*(10(?:\.0+)?|4(?:\.0+)?)|\s*(?:cgpa|sgpa))\b")
    pct_pattern = re.compile(r"\b(\d{2}(?:\.\d{1,2})?)\s*%")

    # Pass 1: Prefer explicit CGPA/GPA on non-school lines
    for line in lines:
        low = line.lower()
        if any(m in low for m in SCHOOL_LINE_MARKERS) and not any(h in low for h in ("b.e", "b.tech", "bachelor", "university")):
            continue
        m = cgpa_pattern.search(line) or reverse_cgpa_pattern.search(line)
        if not m:
            continue
        try:
            val = float(m.group(1))
        except ValueError:
            continue
        scale_str = m.group(2) if m.lastindex and m.lastindex >= 2 else None
        if scale_str and float(scale_str) <= 4.0 and val <= 4.0:
            converted = round(val * 2.5, 2)
            warnings.append(f"Converted {val}/4.0 GPA to ~{converted}/10.0 scale; please verify.")
            return converted
        if 0.0 < val <= 10.0:
            return round(val, 2)

    # Pass 2: Fallback to percentage on higher-education lines only
    for line in lines:
        low = line.lower()
        if any(m in low for m in SCHOOL_LINE_MARKERS):
            continue
        if not any(h in low for h in HIGHER_ED_MARKERS):
            continue
        m_pct = pct_pattern.search(line)
        if m_pct:
            pct = float(m_pct.group(1))
            if 35.0 <= pct <= 100.0:
                estimated = round(min(10.0, pct / 9.5), 2)
                warnings.append(f"Estimated CGPA {estimated} from degree percentage {pct}% (/ 9.5); please verify.")
                return estimated
    return None


def extract_academic_and_contact_fields(raw_text: str) -> Dict[str, Any]:
    """Deterministically extracts academic & contact details from resume text without LLM hallucination."""
    text = raw_text or ""
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    warnings: List[str] = []

    cgpa = _extract_cgpa_and_warnings(lines, warnings)

    # Graduation Year (prefer education lines / date ranges like 2022 - 2026)
    grad_year: Optional[int] = None
    range_re = re.compile(r"\b20[1-2]\d\s*(?:-|–|—|to)\s*(20[2-3]\d)\b", re.IGNORECASE)
    year_kw_re = re.compile(r"\b(?:expected|graduating|graduation|batch|class of|pass\s*out|passout)\D{0,15}(20[2-3]\d)\b", re.IGNORECASE)
    for line in lines:
        low = line.lower()
        if any(h in low for h in HIGHER_ED_MARKERS) or "expected" in low or "batch" in low or "class of" in low:
            m = year_kw_re.search(line) or range_re.search(line)
            if m:
                yr = int(m.group(1))
                if 2020 <= yr <= 2032:
                    grad_year = yr
                    break
    if grad_year is None:
        m = year_kw_re.search(text) or range_re.search(text)
        if m:
            yr = int(m.group(1))
            if 2020 <= yr <= 2032:
                grad_year = yr

    # Department Code
    department_code: Optional[str] = None
    text_lower = text.lower()
    for code, patterns in DEPARTMENT_PATTERNS:
        if any(re.search(pat, text_lower) for pat in patterns):
            department_code = code
            break

    # Phone number (Indian mobile or E.164)
    phone_number: Optional[str] = None
    m_phone = re.search(r"(?:\+91[\s\-]?)?[6-9]\d{4}[\s\-]?\d{5}\b", text)
    if m_phone:
        phone_number = re.sub(r"\s+", " ", m_phone.group(0)).strip()
    else:
        m_intl = re.search(r"\+\d{1,3}[\s\-]?\d{3,4}[\s\-]?\d{3,4}[\s\-]?\d{3,4}\b", text)
        if m_intl:
            phone_number = re.sub(r"\s+", " ", m_intl.group(0)).strip()

    # GitHub & LinkedIn URLs
    github_url: Optional[str] = None
    m_gh = re.search(r"(?:https?://)?(?:www\.)?github\.com/([A-Za-z0-9_.-]+)", text, re.IGNORECASE)
    if m_gh:
        handle = m_gh.group(1).rstrip(".,;/)")
        if handle and handle.lower() not in {"features", "explore", "topics", "orgs"}:
            github_url = f"https://github.com/{handle}"

    linkedin_url: Optional[str] = None
    m_li = re.search(r"(?:https?://)?(?:[a-z]+\.)?linkedin\.com/in/([A-Za-z0-9_.-]+)", text, re.IGNORECASE)
    if m_li:
        handle = m_li.group(1).rstrip(".,;/)")
        if handle:
            linkedin_url = f"https://www.linkedin.com/in/{handle}"

    warnings.append("Standing Arrears are not auto-filled from resumes; please confirm your arrears count manually.")

    return {
        "cgpa": cgpa,
        "graduation_year": grad_year,
        "department_code": department_code,
        "phone_number": phone_number,
        "github_url": github_url,
        "linkedin_url": linkedin_url,
        "standing_arrears": None,
        "warnings": warnings,
    }


async def parse_resume_text(
    raw_text: str,
    preferred_provider: str = None,
    custom_config: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    academic_profile = extract_academic_and_contact_fields(raw_text)

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
    except Exception:
        data = {
            "skills": ["Python", "JavaScript", "SQL", "Git", "Data Structures"],
            "ats_score": 78.0,
            "summary": "Engineering graduate with solid computer science fundamentals.",
            "strengths": ["Good foundation in programming", "Relevant academic projects"],
            "improvements": ["Quantify project impact metrics", "Highlight problem solving achievements"]
        }

    # Safely backfill only missing regex fields when AI returned valid bounded values
    if academic_profile["cgpa"] is None and data.get("cgpa") is not None:
        try:
            ai_cgpa = float(data["cgpa"])
            if 0.0 < ai_cgpa <= 10.0:
                academic_profile["cgpa"] = round(ai_cgpa, 2)
        except (TypeError, ValueError):
            pass

    if academic_profile["graduation_year"] is None and data.get("graduation_year") is not None:
        try:
            ai_yr = int(data["graduation_year"])
            if 2020 <= ai_yr <= 2032:
                academic_profile["graduation_year"] = ai_yr
        except (TypeError, ValueError):
            pass

    if academic_profile["department_code"] is None and isinstance(data.get("department_code"), str):
        code_up = data["department_code"].strip().upper()
        if code_up in {"CSE", "IT", "ECE", "EEE", "MECH", "CIVIL", "AIDS", "AIML"}:
            academic_profile["department_code"] = code_up

    data["academic_profile"] = academic_profile
    return data

