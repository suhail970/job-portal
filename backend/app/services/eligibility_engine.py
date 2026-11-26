import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple
from app.models.entities import PlacementDrive


@dataclass
class AcademicSnapshot:
    """Lightweight academic snapshot for real-time eligibility previews without mutating DB."""
    cgpa: float = 0.0
    standing_arrears: int = 0
    history_arrears: int = 0
    tenth_percentage: Optional[float] = None
    secondary_qualification_type: str = "HSC"
    twelfth_percentage: Optional[float] = None
    target_companies: Optional[str] = None
    target_min_ctc: Optional[float] = None


def parse_ctc_lpa_range(salary_package: Optional[str]) -> Tuple[Optional[float], Optional[float]]:
    """
    Extracts (min_lpa, max_lpa) from package strings such as '8.5 LPA - 12 LPA' or '7.5 LPA'.
    Returns (None, None) when numeric LPA cannot be parsed reliably.
    """
    if not salary_package:
        return None, None
    text = str(salary_package).strip()
    if not text:
        return None, None

    # Prefer numbers explicitly associated with LPA or ranges when LPA appears
    has_lpa = bool(re.search(r"\blpa\b", text, re.IGNORECASE))
    if not has_lpa:
        # Avoid confusing USD/hourly figures like '$80k - $100k' or '$50/hr' with Indian LPA
        if "$" in text or "usd" in text.lower() or "eur" in text.lower() or "/hr" in text.lower():
            return None, None

    nums = [float(m) for m in re.findall(r"\b(\d{1,3}(?:\.\d{1,2})?)\b", text)]
    valid_nums = [n for n in nums if 0.5 <= n <= 300.0]
    if not valid_nums:
        return None, None
    return min(valid_nums), max(valid_nums)


def _normalize_departments(allowed_departments: Optional[str]) -> List[str]:
    if not allowed_departments:
        return []
    tokens = [t.strip().upper() for t in re.split(r"[,;/|]+", allowed_departments) if t.strip()]
    return tokens


def evaluate_drive_eligibility(
    student: Any,
    department_code: Optional[str],
    drive: PlacementDrive,
) -> Dict[str, Any]:
    """
    Pure, deterministic, rule-based eligibility validator.
    Reads company criteria exclusively from the PlacementDrive record; never hardcodes company names.
    Optional thresholds (min_tenth_percentage, min_twelfth_percentage, max_history_arrears) are skipped when None.
    """
    failed_reasons: List[str] = []
    passed_checks: List[str] = []

    student_cgpa = float(getattr(student, "cgpa", 0.0) or 0.0)
    standing_arrears = int(getattr(student, "standing_arrears", 0) or 0)
    history_arrears = int(getattr(student, "history_arrears", 0) or 0)
    tenth_pct = getattr(student, "tenth_percentage", None)
    qual_type = str(getattr(student, "secondary_qualification_type", "HSC") or "HSC").strip().upper()
    if qual_type not in ("HSC", "DIPLOMA"):
        qual_type = "HSC"
    qual_label = "Diploma" if qual_type == "DIPLOMA" else "12th (HSC)"
    twelfth_pct = getattr(student, "twelfth_percentage", None)
    dept_upper = (department_code or "").strip().upper()

    # 1. CGPA Check (required on drive)
    min_cgpa = float(drive.min_cgpa if drive.min_cgpa is not None else 0.0)
    if student_cgpa < min_cgpa:
        failed_reasons.append(f"CGPA {student_cgpa:.2f} is below required minimum {min_cgpa:.2f}")
    else:
        passed_checks.append(f"CGPA {student_cgpa:.2f} >= {min_cgpa:.2f}")

    # 2. Standing Arrears Check (required on drive)
    max_arrears = int(drive.max_arrears if drive.max_arrears is not None else 0)
    if standing_arrears > max_arrears:
        failed_reasons.append(f"Standing arrears ({standing_arrears}) exceed max allowed ({max_arrears})")
    else:
        passed_checks.append(f"Standing arrears {standing_arrears} <= {max_arrears}")

    # 3. History of Arrears Check (optional - skipped if None on drive)
    max_hist = getattr(drive, "max_history_arrears", None)
    if max_hist is not None:
        if history_arrears > int(max_hist):
            failed_reasons.append(f"History of arrears ({history_arrears}) exceed max allowed ({int(max_hist)})")
        else:
            passed_checks.append(f"History arrears {history_arrears} <= {int(max_hist)}")

    # 4. Department / Branch Check
    allowed_depts = _normalize_departments(drive.allowed_departments)
    if allowed_depts and "ALL" not in allowed_depts and "ANY" not in allowed_depts:
        if not dept_upper:
            failed_reasons.append(f"Branch not set (Drive allows: {', '.join(allowed_depts)})")
        elif dept_upper not in allowed_depts:
            failed_reasons.append(f"Branch {dept_upper} not in eligible branches ({', '.join(allowed_depts)})")
        else:
            passed_checks.append(f"Branch {dept_upper} eligible")

    # 5. 10th Standard % Check (optional - skipped if None on drive)
    min_tenth = getattr(drive, "min_tenth_percentage", None)
    if min_tenth is not None:
        if tenth_pct is None:
            failed_reasons.append(f"10th % missing (Drive requires min {float(min_tenth):.1f}%)")
        elif float(tenth_pct) < float(min_tenth):
            failed_reasons.append(f"10th % ({float(tenth_pct):.1f}%) is below required {float(min_tenth):.1f}%")
        else:
            passed_checks.append(f"10th {float(tenth_pct):.1f}% >= {float(min_tenth):.1f}%")

    # 6. 12th / Diploma Track & Percentage Check
    accepts_diploma = getattr(drive, "accepts_diploma", True)
    if accepts_diploma is None:
        accepts_diploma = True
    if qual_type == "DIPLOMA" and not accepts_diploma:
        failed_reasons.append("Drive requires 12th (HSC); Diploma track not accepted")

    min_twelfth = getattr(drive, "min_twelfth_percentage", None)
    if min_twelfth is not None:
        if twelfth_pct is None:
            failed_reasons.append(f"{qual_label} % missing (Drive requires min {float(min_twelfth):.1f}%)")
        elif float(twelfth_pct) < float(min_twelfth):
            failed_reasons.append(f"{qual_label} % ({float(twelfth_pct):.1f}%) is below required {float(min_twelfth):.1f}%")
        else:
            passed_checks.append(f"{qual_label} {float(twelfth_pct):.1f}% >= {float(min_twelfth):.1f}%")

    # 7. Package Goal Match Badge (purely advisory preference, NEVER restricts eligibility)
    target_ctc = getattr(student, "target_min_ctc", None)
    package_goal_match: Optional[bool] = None
    package_goal_label: Optional[str] = None
    if target_ctc is not None and float(target_ctc) > 0:
        min_lpa, max_lpa = parse_ctc_lpa_range(drive.salary_package)
        ref_lpa = max_lpa if max_lpa is not None else min_lpa
        if ref_lpa is not None:
            if ref_lpa >= float(target_ctc):
                package_goal_match = True
                package_goal_label = f"Meets Target CTC (>= {float(target_ctc):.1f} LPA)"
            else:
                package_goal_match = False
                package_goal_label = f"Below Target CTC ({ref_lpa:.1f} < {float(target_ctc):.1f} LPA)"

    # 8. Target Company Match Flag (advisory highlight)
    target_companies_raw = getattr(student, "target_companies", None) or ""
    target_tokens = [t.strip().lower() for t in re.split(r"[,;/|]+", target_companies_raw) if t.strip()]
    company_lower = (drive.company_name or "").lower()
    is_target_company = any(tok in company_lower for tok in target_tokens)

    return {
        "drive_id": drive.id,
        "company_name": drive.company_name,
        "role_title": drive.role_title,
        "location": drive.location,
        "salary_package": drive.salary_package,
        "drive_date": drive.drive_date.isoformat() if drive.drive_date else None,
        "is_eligible": len(failed_reasons) == 0,
        "status_label": "Eligible" if len(failed_reasons) == 0 else "Not Eligible",
        "reasons": failed_reasons,
        "passed_checks": passed_checks,
        "package_goal_match": package_goal_match,
        "package_goal_label": package_goal_label,
        "is_target_company": is_target_company,
        "criteria": {
            "min_cgpa": min_cgpa,
            "max_arrears": max_arrears,
            "max_history_arrears": max_hist,
            "min_tenth_percentage": min_tenth,
            "min_twelfth_percentage": min_twelfth,
            "allowed_departments": drive.allowed_departments,
            "accepts_diploma": accepts_diploma,
        },
    }


def compute_eligibility_dashboard(
    student: Any,
    department_code: Optional[str],
    drives: List[PlacementDrive],
) -> Dict[str, Any]:
    """
    Computes aggregate eligibility KPIs and per-drive eligibility breakdowns from real database drives.
    """
    evaluations = [evaluate_drive_eligibility(student, department_code, d) for d in drives]
    total_drives = len(evaluations)
    eligible_evals = [e for e in evaluations if e["is_eligible"]]
    eligible_count = len(eligible_evals)
    not_eligible_count = total_drives - eligible_count
    eligibility_percentage = round((eligible_count / total_drives) * 100.0, 1) if total_drives > 0 else 0.0

    # Distinct eligible company names in order
    seen_companies = set()
    eligible_companies: List[str] = []
    for e in eligible_evals:
        c = e["company_name"]
        if c not in seen_companies:
            seen_companies.add(c)
            eligible_companies.append(c)

    target_matches = [e for e in evaluations if e["is_target_company"]]
    target_eligible = [e for e in target_matches if e["is_eligible"]]

    return {
        "total_drives": total_drives,
        "eligible_count": eligible_count,
        "not_eligible_count": not_eligible_count,
        "eligibility_percentage": eligibility_percentage,
        "eligible_companies": eligible_companies,
        "target_matches_count": len(target_matches),
        "target_eligible_count": len(target_eligible),
        "results": evaluations,
    }

