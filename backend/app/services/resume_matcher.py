import json
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple
from app.models.entities import PlacementDrive, Resume
from app.ai.agents.resume_leaf import SKILL_TAXONOMY, extract_structured_resume_sections

# Pre-compile skill patterns once for sub-millisecond drive evaluation
_COMPILED_SKILLS: List[Tuple[str, re.Pattern]] = [
    (canonical, re.compile(pat, re.IGNORECASE))
    for canonical, pat in SKILL_TAXONOMY
]
_SKILL_REGEX_MAP: Dict[str, re.Pattern] = {canonical: pat for canonical, pat in _COMPILED_SKILLS}

_STOPWORDS = {
    "the", "and", "for", "with", "that", "this", "from", "have", "will", "your",
    "you", "are", "our", "all", "any", "into", "using", "experience", "role",
    "team", "work", "looking", "candidate", "skills", "knowledge", "strong",
    "good", "ability", "build", "building", "develop", "developing", "software",
    "engineer", "developer", "associate", "graduate", "fresher", "campus", "india",
    "remote", "hybrid", "full", "time", "job", "description", "required", "plus",
}

_ROLE_ARCHETYPES: Dict[str, Set[str]] = {
    "BACKEND": {
        "backend", "api", "rest api", "graphql", "microservices", "python", "java",
        "fastapi", "django", "flask", "spring boot", "golang", "node.js", "sql",
        "postgresql", "mysql", "mongodb", "redis", "distributed", "server",
    },
    "FRONTEND": {
        "frontend", "front-end", "ui", "react", "next.js", "angular", "vue.js",
        "javascript", "typescript", "tailwind css", "html/css", "web",
    },
    "FULLSTACK": {
        "full stack", "fullstack", "react", "next.js", "node.js", "python",
        "java", "sql", "mongodb", "rest api", "typescript", "javascript",
    },
    "AI_DATA": {
        "ai", "ml", "machine learning", "deep learning", "generative ai", "nlp",
        "llm", "rag", "tensorflow", "pytorch", "data analytics", "power bi",
        "tableau", "sql", "python",
    },
    "CLOUD_DEVOPS": {
        "cloud", "devops", "sre", "aws", "azure", "gcp", "docker", "kubernetes",
        "ci/cd", "linux", "microservices", "terraform",
    },
    "EMBEDDED": {
        "embedded", "embedded systems", "embedded linux", "c++", "c", "linux",
        "autosar", "iot", "microcontroller", "firmware",
    },
    "QA_TEST": {
        "qa", "testing", "automation", "selenium", "playwright", "sdet",
    },
}

DEFAULT_MATCH_THRESHOLD = 30.0


def _safe_json_list(raw: Optional[str]) -> List[str]:
    if not raw:
        return []
    try:
        parsed = json.loads(raw)
        if isinstance(parsed, list):
            return [str(x).strip() for x in parsed if isinstance(x, str) and str(x).strip()]
    except Exception:
        pass
    return []


def _extract_meaningful_tokens(text: str) -> Set[str]:
    tokens = set(re.findall(r"[a-zA-Z][a-zA-Z0-9+#./-]{1,30}", (text or "").lower()))
    return {t for t in tokens if len(t) >= 3 and t not in _STOPWORDS}


def _extract_canonical_skills(text: str) -> List[str]:
    low = (text or "").lower()
    found: List[str] = []
    for canonical, pat in _COMPILED_SKILLS:
        if pat.search(low):
            found.append(canonical)
    return found


def _infer_archetypes(text: str, skills_lower: Set[str]) -> Set[str]:
    combined = skills_lower | _extract_meaningful_tokens(text)
    low = (text or "").lower()
    matched_arch: Set[str] = set()
    for arch, keywords in _ROLE_ARCHETYPES.items():
        hits = 0
        for kw in keywords:
            if kw in combined or (len(kw) > 3 and kw in low):
                hits += 1
        if hits >= 2 or (arch == "FULLSTACK" and ("full stack" in low or "fullstack" in low)):
            matched_arch.add(arch)
    return matched_arch


@dataclass
class PreparedResumeProfile:
    resume_id: str
    filename: str
    skills: List[str]
    skills_lower: Set[str]
    internships: List[str]
    projects: List[str]
    certifications: List[str]
    achievements: List[str]
    internship_tokens: List[Tuple[str, Set[str], str]] = field(default_factory=list)
    project_tokens: List[Tuple[str, Set[str], str]] = field(default_factory=list)
    cert_tokens: List[Tuple[str, Set[str], str]] = field(default_factory=list)
    ach_tokens: List[Tuple[str, Set[str], str]] = field(default_factory=list)
    archetypes: Set[str] = field(default_factory=set)
    raw_lower: str = ""


def prepare_resume_profile(resume: Resume) -> PreparedResumeProfile:
    """
    Pre-indexes a Resume DB entity once per API request so matching across 200+ drives
    executes in single-digit milliseconds without repeated parsing or LLM calls.
    """
    skills = _safe_json_list(resume.parsed_skills)
    internships = _safe_json_list(getattr(resume, "parsed_internships", "[]"))
    projects = _safe_json_list(getattr(resume, "parsed_projects", "[]"))
    certifications = _safe_json_list(getattr(resume, "parsed_certifications", "[]"))
    achievements = _safe_json_list(getattr(resume, "parsed_achievements", "[]"))

    # Seamless auto-backfill for legacy resume rows created before structured columns existed
    if resume.raw_text and not (internships or projects or certifications or achievements):
        extracted = extract_structured_resume_sections(resume.raw_text)
        internships = extracted["internships"]
        projects = extracted["projects"]
        certifications = extracted["certifications"]
        achievements = extracted["achievements"]
        if not skills:
            skills = extracted["skills"]

    skills_lower = {s.lower() for s in skills}
    # Ensure any canonical taxonomy skills present inside raw_text/projects/internships are also recognized
    combined_body = " ".join([resume.raw_text or "", " ".join(skills), " ".join(internships), " ".join(projects)])
    for cs in _extract_canonical_skills(combined_body):
        if cs.lower() not in skills_lower:
            skills.append(cs)
            skills_lower.add(cs.lower())

    def _index_items(items: List[str]) -> List[Tuple[str, Set[str], str]]:
        return [(item, _extract_meaningful_tokens(item), item.lower()) for item in items]

    archetypes = _infer_archetypes(
        " ".join(internships + projects + [resume.summary or ""]),
        skills_lower,
    )

    return PreparedResumeProfile(
        resume_id=resume.id,
        filename=resume.filename,
        skills=skills,
        skills_lower=skills_lower,
        internships=internships,
        projects=projects,
        certifications=certifications,
        achievements=achievements,
        internship_tokens=_index_items(internships),
        project_tokens=_index_items(projects),
        cert_tokens=_index_items(certifications),
        ach_tokens=_index_items(achievements),
        archetypes=archetypes,
        raw_lower=(resume.raw_text or "").lower(),
    )


def compute_resume_job_match(
    profile: PreparedResumeProfile,
    drive: PlacementDrive,
    min_threshold: float = DEFAULT_MATCH_THRESHOLD,
) -> Dict[str, Any]:
    """
    Computes multi-factor relevance score (0-100) between a student's resume profile
    and a PlacementDrive, returning matched evidence and clear reasons.
    Completely decoupled from academic eligibility checks.
    """
    job_text = f"{drive.role_title or ''} {drive.job_description or ''} {drive.selection_rounds or ''}"
    job_lower = job_text.lower()
    jd_skills = _extract_canonical_skills(job_text)
    jd_tokens = _extract_meaningful_tokens(job_text)

    # 1. Technical Skills Overlap (up to 50 points)
    matched_skills: List[str] = []
    missing_skills: List[str] = []

    if jd_skills:
        for req_skill in jd_skills:
            if req_skill.lower() in profile.skills_lower:
                matched_skills.append(req_skill)
            else:
                missing_skills.append(req_skill)
        denom = max(1, min(len(jd_skills), 5))
        skill_score = min(50.0, (len(matched_skills) / denom) * 50.0)
    else:
        # Generic tech token matching when JD uses custom terminology
        token_hits = [s for s in profile.skills if s.lower() in jd_tokens]
        matched_skills = token_hits[:6]
        skill_score = min(50.0, len(matched_skills) * 12.5)

    # Signal 2: Internships & Projects Relevance (up to 25 points)
    jd_signal_terms = {s.lower() for s in jd_skills} | jd_tokens
    matched_internships: List[str] = []
    matched_projects: List[str] = []
    matched_experience: List[str] = []

    for orig, tok_set, low_str in profile.internship_tokens:
        overlap = tok_set & jd_signal_terms
        skill_in_item = [s for s in jd_skills if _SKILL_REGEX_MAP[s].search(low_str)]
        if len(overlap) >= 2 or skill_in_item:
            matched_internships.append(orig)
            matched_experience.append(f"Internship: {orig[:110]}")

    for orig, tok_set, low_str in profile.project_tokens:
        overlap = tok_set & jd_signal_terms
        skill_in_item = [s for s in jd_skills if _SKILL_REGEX_MAP[s].search(low_str)]
        if len(overlap) >= 2 or skill_in_item:
            matched_projects.append(orig)
            matched_experience.append(f"Project: {orig[:110]}")

    exp_score = min(15.0, len(matched_internships) * 10.0) + min(12.0, len(matched_projects) * 6.0)
    exp_score = min(25.0, exp_score)

    # Signal 3: Role Domain Fit (up to 15 points)
    job_archetypes = _infer_archetypes(job_text, {s.lower() for s in jd_skills})
    domain_overlap = profile.archetypes & job_archetypes
    # Fullstack engineers also match Backend/Frontend jobs cleanly
    if not domain_overlap and "FULLSTACK" in profile.archetypes and (job_archetypes & {"BACKEND", "FRONTEND"}):
        domain_overlap = job_archetypes & {"BACKEND", "FRONTEND"}
    domain_score = 15.0 if domain_overlap else (8.0 if (matched_skills and len(matched_skills) >= 2) else 0.0)

    # Signal 4: Certifications & Achievements Bonus (up to 10 points, applied when core relevance exists)
    matched_certs: List[str] = []
    matched_achs: List[str] = []
    for orig, tok_set, low_str in profile.cert_tokens:
        if (tok_set & jd_signal_terms) or any(_SKILL_REGEX_MAP[s].search(low_str) for s in jd_skills):
            matched_certs.append(orig)
            matched_experience.append(f"Certification: {orig[:100]}")
    if matched_skills or matched_internships or matched_projects:
        for orig, tok_set, low_str in profile.ach_tokens:
            if (tok_set & jd_signal_terms) or any(kw in low_str for kw in ("hackathon", "coding", "leetcode", "winner", "icpc", "gsoc")):
                matched_achs.append(orig)
                matched_experience.append(f"Achievement: {orig[:100]}")

    bonus_score = min(10.0, len(matched_certs) * 5.0 + len(matched_achs) * 5.0)

    total_score = round(min(100.0, skill_score + exp_score + domain_score + bonus_score), 1)
    has_genuine_match = bool(matched_skills or matched_internships or matched_projects)
    is_recommended = (total_score >= min_threshold) and has_genuine_match

    if total_score >= 70.0 and has_genuine_match:
        verdict = "Strong Match"
    elif total_score >= 45.0 and has_genuine_match:
        verdict = "Good Match"
    elif is_recommended:
        verdict = "Relevant Match"
    else:
        verdict = "Low Match"

    # Build explicit evidence-backed reasons
    reasons: List[str] = []
    if matched_skills:
        total_req = len(jd_skills) if jd_skills else len(matched_skills)
        reasons.append(f"Matched {len(matched_skills)}/{total_req} role skills: {', '.join(matched_skills[:5])}")
    if matched_internships:
        reasons.append(f"{len(matched_internships)} internship experience item(s) align with this role")
    if matched_projects:
        reasons.append(f"{len(matched_projects)} project(s) demonstrate relevant tech stack")
    if domain_overlap:
        clean_domains = ", ".join(sorted(d.replace("_", " ").title() for d in domain_overlap))
        reasons.append(f"Role domain alignment: {clean_domains}")
    if matched_certs:
        reasons.append(f"Relevant certification(s): {matched_certs[0][:60]}")
    if matched_achs:
        reasons.append(f"Verified achievement highlight: {matched_achs[0][:60]}")
    if not reasons:
        if missing_skills:
            reasons.append(f"No direct resume match; role seeks {', '.join(missing_skills[:4])}")
        else:
            reasons.append("No direct skill, internship, or project overlap found in resume")

    return {
        "match_percentage": total_score,
        "verdict": verdict,
        "is_recommended": is_recommended,
        "matched_skills": matched_skills,
        "missing_skills": missing_skills[:6],
        "matched_experience": matched_experience[:5],
        "reasons": reasons,
    }
