import json
import re
from typing import Dict, Any, List, Optional
from app.ai.router import ai_router

SYSTEM_PROMPT = """You are an expert AI Resume Analyst and Placement Screener.
Analyze the provided student resume text. Extract technical skills, tools, frameworks, calculate an ATS compatibility score (0-100), identify 3 core strengths, and 3 high-impact improvement recommendations, along with academic details if clearly present.

Respond strictly in valid JSON format:
{
    "skills": ["Skill1", "Skill2", ...],
    "internships": ["Role @ Company - key work", ...],
    "projects": ["Project Title - tech & outcome", ...],
    "certifications": ["Certification Name", ...],
    "achievements": ["Award / Hackathon / Coding Achievement", ...],
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

SCHOOL_LINE_MARKERS = ("10th", "12th", "sslc", "hsc", "secondary", "high school", "matric", "cbse", "icse", "class x", "class xii", "diploma", "polytechnic", "intermediate")
HIGHER_ED_MARKERS = ("b.e", "b.tech", "bachelor", "degree", "university", "college", "cgpa", "sgpa", "gpa", "semester", "engineering")


def _extract_percentage_from_line(line: str, label: str, warnings: List[str]) -> Optional[float]:
    pct_match = re.search(r"\b(\d{2,3}(?:\.\d{1,2})?)\s*%", line)
    if pct_match:
        val = float(pct_match.group(1))
        if 35.0 <= val <= 100.0:
            return round(val, 2)
    # Fallback: "Marks: 91.5" or "Score: 88.2" or "10.0 CGPA" on an explicit school line
    gpa_match = re.search(r"(?i)\b(\d{1,2}(?:\.\d{1,2})?)\s*(?:/\s*10(?:\.0+)?|\s*cgpa)\b", line)
    if gpa_match:
        gpa_val = float(gpa_match.group(1))
        if 3.5 <= gpa_val <= 10.0:
            est = round(min(100.0, gpa_val * 9.5), 2)
            warnings.append(f"Estimated {label} {est}% from CGPA {gpa_val}/10; please verify.")
            return est
    score_match = re.search(r"(?i)(?:percentage|pct|marks|score|aggregate)\s*(?:[:=\-]|of|is)?\s*(\d{2}(?:\.\d{1,2})?)\b", line)
    if score_match:
        val = float(score_match.group(1))
        if 35.0 <= val <= 100.0:
            return round(val, 2)
    return None


def _extract_school_percentages(lines: List[str], warnings: List[str]) -> tuple[Optional[float], Optional[float], str]:
    tenth_pct: Optional[float] = None
    twelfth_pct: Optional[float] = None
    qual_type: str = "HSC"

    re_12th = re.compile(r"(?i)\b(12th|hsc|class\s*xii|higher\s+secondary|intermediate|plus\s*two|\+2)\b")
    re_diploma = re.compile(r"(?i)\b(diploma|polytechnic)\b")
    re_10th = re.compile(r"(?i)\b(10th|sslc|class\s*x(?!i)|matric(?:ulation)?|secondary\s+school)\b")

    for line in lines:
        if tenth_pct is None and re_10th.search(line):
            val = _extract_percentage_from_line(line, "10th %", warnings)
            if val is not None:
                tenth_pct = val
        if twelfth_pct is None and re_diploma.search(line):
            val = _extract_percentage_from_line(line, "Diploma %", warnings)
            if val is not None:
                twelfth_pct = val
                qual_type = "DIPLOMA"
        elif twelfth_pct is None and re_12th.search(line):
            val = _extract_percentage_from_line(line, "12th (HSC) %", warnings)
            if val is not None:
                twelfth_pct = val
                qual_type = "HSC"

    return tenth_pct, twelfth_pct, qual_type


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
    tenth_percentage, twelfth_percentage, secondary_qualification_type = _extract_school_percentages(lines, warnings)

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

    warnings.append("Standing & History of Arrears are not auto-filled from resumes; please confirm them manually.")

    return {
        "cgpa": cgpa,
        "tenth_percentage": tenth_percentage,
        "twelfth_percentage": twelfth_percentage,
        "secondary_qualification_type": secondary_qualification_type,
        "graduation_year": grad_year,
        "department_code": department_code,
        "phone_number": phone_number,
        "github_url": github_url,
        "linkedin_url": linkedin_url,
        "standing_arrears": None,
        "history_arrears": None,
        "warnings": warnings,
    }


SKILL_TAXONOMY: List[tuple[str, str]] = [
    ("Python", r"\bpython\b"),
    ("Java", r"\bjava\b(?!script)"),
    ("C++", r"(?:c\+\+|cpp)"),
    ("C", r"(?<![a-zA-Z0-9+])c(?![a-zA-Z0-9+#])"),
    ("C#", r"\bc#"),
    ("JavaScript", r"\b(?:javascript|js)\b"),
    ("TypeScript", r"\b(?:typescript|ts)\b"),
    ("Golang", r"\b(?:golang|go)\b"),
    ("Rust", r"\brust\b"),
    ("Kotlin", r"\bkotlin\b"),
    ("React", r"\b(?:react\.?js|react)\b"),
    ("Next.js", r"\bnext\.?js\b"),
    ("Angular", r"\bangular\b"),
    ("Vue.js", r"\bvue\.?js\b"),
    ("Node.js", r"\bnode\.?js\b"),
    ("Express.js", r"\bexpress\.?js\b"),
    ("FastAPI", r"\bfastapi\b"),
    ("Django", r"\bdjango\b"),
    ("Flask", r"\bflask\b"),
    ("Spring Boot", r"\bspring\s*boot\b"),
    ("Tailwind CSS", r"\btailwind(?:\s*css)?\b"),
    ("HTML/CSS", r"\b(?:html5?|css3?)\b"),
    ("SQL", r"\bsql\b"),
    ("PostgreSQL", r"\bpostgres(?:ql)?\b"),
    ("MySQL", r"\bmysql\b"),
    ("MongoDB", r"\bmongodb\b"),
    ("Redis", r"\bredis\b"),
    ("Docker", r"\bdocker\b"),
    ("Kubernetes", r"\b(?:kubernetes|k8s)\b"),
    ("AWS", r"\b(?:aws|amazon\s+web\s+services)\b"),
    ("Azure", r"\bazure\b"),
    ("GCP", r"\b(?:gcp|google\s+cloud)\b"),
    ("Git", r"\b(?:git|github|gitlab)\b"),
    ("Linux", r"\blinux\b"),
    ("Embedded Linux", r"\bembedded\s+linux\b"),
    ("Embedded Systems", r"\b(?:embedded(?:\s+systems?)?|autosar|microcontrollers?|iot)\b"),
    ("Machine Learning", r"\b(?:machine\s+learning|ml)\b"),
    ("Deep Learning", r"\b(?:deep\s+learning|neural\s+networks?)\b"),
    ("TensorFlow", r"\btensorflow\b"),
    ("PyTorch", r"\bpytorch\b"),
    ("Generative AI", r"\b(?:generative\s+ai|genai|llm|langchain|rag)\b"),
    ("Data Structures & Algorithms", r"\b(?:data\s+structures|algorithms|dsa)\b"),
    ("OOP", r"\b(?:oop|oops|object[\s-]+oriented)\b"),
    ("System Design", r"\bsystem\s+design\b"),
    ("Microservices", r"\bmicroservices?\b"),
    ("REST API", r"\b(?:rest(?:ful)?\s*apis?)\b"),
    ("GraphQL", r"\bgraphql\b"),
    ("CI/CD", r"\b(?:ci/cd|github\s+actions|jenkins)\b"),
    ("Selenium", r"\bselenium\b"),
    ("Playwright", r"\bplaywright\b"),
    ("Power BI", r"\bpower\s*bi\b"),
    ("Tableau", r"\btableau\b"),
    ("Data Analytics", r"\b(?:data\s+analytics?|pandas|numpy|scikit-learn)\b"),
]

_SECTION_HEADERS = {
    "internships": re.compile(r"^(?:internships?|work\s+experience|experience|employment|industrial\s+training)\b[:\-]*$", re.IGNORECASE),
    "projects": re.compile(r"^(?:(?:academic|personal|key|major|software)\s+)?projects?\b[:\-]*$", re.IGNORECASE),
    "certifications": re.compile(r"^(?:certifications?|certificates?|licenses?\s*(?:&|and)?\s*certifications?|courses?)\b[:\-]*$", re.IGNORECASE),
    "achievements": re.compile(r"^(?:achievements?|awards?|honors?|accomplishments?|extracurriculars?|hackathons?|publications?)\b[:\-]*$", re.IGNORECASE),
}
_OTHER_HEADER_RE = re.compile(
    r"^(?:education|academic(?:\s+details|\s+background)?|skills|technical\s+skills|core\s+competencies|summary|profile|objective|contact|languages?|references?|declaration)\b[:\-]*$",
    re.IGNORECASE,
)


def extract_structured_resume_sections(raw_text: str) -> Dict[str, List[str]]:
    """
    Deterministically extracts grounded skills, internships, projects, certifications,
    and achievements from resume text without hallucination or dummy placeholders.
    """
    text = raw_text or ""
    text_lower = text.lower()

    skills: List[str] = []
    for canonical, pat in SKILL_TAXONOMY:
        if re.search(pat, text_lower, re.IGNORECASE):
            skills.append(canonical)

    sections: Dict[str, List[str]] = {
        "internships": [],
        "projects": [],
        "certifications": [],
        "achievements": [],
    }

    current_section: Optional[str] = None
    for raw_ln in text.splitlines():
        line = raw_ln.strip()
        if not line:
            continue

        clean_heading = re.sub(r"[:|\-]+$", "", line).strip()
        matched_heading = None
        if len(clean_heading.split()) <= 5:
            for sec_key, sec_re in _SECTION_HEADERS.items():
                if sec_re.match(clean_heading):
                    matched_heading = sec_key
                    break
            if not matched_heading and _OTHER_HEADER_RE.match(clean_heading):
                current_section = None
                continue

        if matched_heading:
            current_section = matched_heading
            continue

        if current_section:
            cleaned_item = re.sub(r"^[\u2022\u25cf\u25aa\-\*\d\.)\s]+", "", line).strip()
            if len(cleaned_item) >= 5 and len(sections[current_section]) < 12:
                sections[current_section].append(cleaned_item[:220])

    # Fallback inline mentions if no formal section headers existed (common in compact PDFs)
    if not sections["internships"]:
        for ln in text.splitlines():
            s = ln.strip()
            if re.search(r"\bintern(?:ship)?\b", s, re.IGNORECASE) and len(s) >= 8 and len(sections["internships"]) < 5:
                sections["internships"].append(re.sub(r"^[\u2022\-\*\s]+", "", s)[:220])
    if not sections["certifications"]:
        for ln in text.splitlines():
            s = ln.strip()
            if re.search(r"\b(?:certified|certification|certificate|aws\s+certified|oracle\s+certified|nptel|coursera)\b", s, re.IGNORECASE) and len(s) >= 8 and len(sections["certifications"]) < 5:
                sections["certifications"].append(re.sub(r"^[\u2022\-\*\s]+", "", s)[:220])

    return {
        "skills": skills,
        "internships": sections["internships"],
        "projects": sections["projects"],
        "certifications": sections["certifications"],
        "achievements": sections["achievements"],
    }


def _compute_deterministic_ats_score(structured: Dict[str, List[str]], academic: Dict[str, Any], raw_text: str) -> float:
    score = 35.0
    score += min(30.0, len(structured.get("skills", [])) * 4.0)
    if structured.get("projects"):
        score += min(12.0, len(structured["projects"]) * 4.0)
    if structured.get("internships"):
        score += min(10.0, len(structured["internships"]) * 5.0)
    if structured.get("certifications") or structured.get("achievements"):
        score += 5.0
    if academic.get("cgpa"):
        score += 4.0
    if academic.get("github_url") or academic.get("linkedin_url"):
        score += 4.0
    if len((raw_text or "").strip()) < 100:
        score = min(score, 45.0)
    return round(min(98.0, score), 1)


async def parse_resume_text(
    raw_text: str,
    preferred_provider: str = None,
    custom_config: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    academic_profile = extract_academic_and_contact_fields(raw_text)
    structured = extract_structured_resume_sections(raw_text)

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

    ai_data: Dict[str, Any] = {}
    try:
        parsed_json = json.loads(response_str)
        if isinstance(parsed_json, dict):
            ai_data = parsed_json
    except Exception:
        ai_data = {}

    # Detect ai_router's static zero-key dummy fallback signature so dummy skills never pollute real resumes
    _DUMMY_SIGNATURES = {
        ("Python", "FastAPI", "SQL", "Machine Learning", "Data Structures", "Next.js", "Docker", "Git"),
    }
    ai_skills = ai_data.get("skills") if isinstance(ai_data.get("skills"), list) else []
    is_static_fallback = tuple(ai_skills) in _DUMMY_SIGNATURES and "fastapi" not in (raw_text or "").lower()

    # Combine deterministic grounded skills with verified AI skills (if not dummy fallback)
    merged_skills: List[str] = list(structured["skills"])
    if not is_static_fallback:
        existing_lower = {s.lower() for s in merged_skills}
        for s in ai_skills:
            if isinstance(s, str) and s.strip() and s.strip().lower() not in existing_lower:
                merged_skills.append(s.strip())
                existing_lower.add(s.strip().lower())

    def _merge_list(det_list: List[str], ai_key: str) -> List[str]:
        out = list(det_list)
        if not is_static_fallback and isinstance(ai_data.get(ai_key), list):
            seen = {x.lower() for x in out}
            for item in ai_data[ai_key]:
                if isinstance(item, str) and item.strip() and item.strip().lower() not in seen:
                    out.append(item.strip()[:220])
                    seen.add(item.strip().lower())
        return out

    internships = _merge_list(structured["internships"], "internships")
    projects = _merge_list(structured["projects"], "projects")
    certifications = _merge_list(structured["certifications"], "certifications")
    achievements = _merge_list(structured["achievements"], "achievements")

    ats_score = (
        float(ai_data["ats_score"])
        if (not is_static_fallback and isinstance(ai_data.get("ats_score"), (int, float)))
        else _compute_deterministic_ats_score(structured, academic_profile, raw_text)
    )

    summary = (
        ai_data.get("summary")
        if (not is_static_fallback and ai_data.get("summary"))
        else (
            f"Candidate profile with {len(merged_skills)} technical skills"
            + (f" ({', '.join(merged_skills[:5])})" if merged_skills else "")
            + (f", {len(projects)} project(s)" if projects else "")
            + (f", and {len(internships)} internship(s)" if internships else "")
            + "."
        )
    )

    data: Dict[str, Any] = {
        "skills": merged_skills,
        "internships": internships,
        "projects": projects,
        "certifications": certifications,
        "achievements": achievements,
        "ats_score": ats_score,
        "summary": summary,
        "strengths": (
            ai_data.get("strengths")
            if (not is_static_fallback and isinstance(ai_data.get("strengths"), list))
            else [
                s for s in [
                    f"Verified technical stack: {', '.join(merged_skills[:5])}" if merged_skills else None,
                    f"Hands-on project portfolio ({len(projects)} item(s))" if projects else None,
                    f"Practical internship experience ({len(internships)} item(s))" if internships else None,
                ] if s
            ]
        ),
        "improvements": (
            ai_data.get("improvements")
            if (not is_static_fallback and isinstance(ai_data.get("improvements"), list))
            else [
                tip for tip in [
                    "Add measurable metrics to project outcomes" if projects else "Add 2-3 technical projects with tech stack tags",
                    "Include relevant industry certifications or hackathon achievements" if not (certifications or achievements) else None,
                ] if tip
            ]
        ),
    }

    # Safely backfill only missing regex fields when genuine AI output returned valid bounded values
    if not is_static_fallback:
        if academic_profile["cgpa"] is None and ai_data.get("cgpa") is not None:
            try:
                ai_cgpa = float(ai_data["cgpa"])
                if 0.0 < ai_cgpa <= 10.0:
                    academic_profile["cgpa"] = round(ai_cgpa, 2)
            except (TypeError, ValueError):
                pass

        if academic_profile["graduation_year"] is None and ai_data.get("graduation_year") is not None:
            try:
                ai_yr = int(ai_data["graduation_year"])
                if 2020 <= ai_yr <= 2032:
                    academic_profile["graduation_year"] = ai_yr
            except (TypeError, ValueError):
                pass

        if academic_profile["department_code"] is None and isinstance(ai_data.get("department_code"), str):
            code_up = ai_data["department_code"].strip().upper()
            if code_up in {"CSE", "IT", "ECE", "EEE", "MECH", "CIVIL", "AIDS", "AIML"}:
                academic_profile["department_code"] = code_up

    data["academic_profile"] = academic_profile
    return data

