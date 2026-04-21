import re


# ── Section definitions ───────────────────────────────────────────────────────
# Each section has aliases, a weight, and whether it's critical

SECTIONS = {
    "contact": {
        "aliases": ["contact", "phone", "email", "address", "linkedin", "github"],
        "weight": 15,
        "critical": True,
    },
    "summary": {
        "aliases": ["summary", "objective", "career objective", "profile", "about me", "about"],
        "weight": 10,
        "critical": False,
    },
    "education": {
        "aliases": ["education", "academic", "qualification", "degree", "university", "college", "b.tech", "m.tech"],
        "weight": 15,
        "critical": True,
    },
    "experience": {
        "aliases": ["experience", "work experience", "internship", "employment", "worked at", "professional experience"],
        "weight": 15,
        "critical": True,
    },
    "skills": {
        "aliases": ["skills", "technical skills", "technologies", "tools", "competencies", "expertise"],
        "weight": 15,
        "critical": True,
    },
    "projects": {
        "aliases": ["project", "projects", "personal projects", "academic projects", "work done"],
        "weight": 15,
        "critical": True,
    },
    "certifications": {
        "aliases": ["certification", "certified", "certificate", "course", "training", "nptel", "coursera", "udemy"],
        "weight": 8,
        "critical": False,
    },
    "achievements": {
        "aliases": ["achievement", "award", "honor", "honour", "recognition", "accomplishment", "winner"],
        "weight": 5,
        "critical": False,
    },
    "extra": {
        "aliases": ["volunteer", "extracurricular", "activity", "club", "society", "hobby", "interest", "language"],
        "weight": 2,
        "critical": False,
    },
}

# ── Formatting quality checks ─────────────────────────────────────────────────

def _check_formatting(text: str, lower: str) -> tuple[int, list]:
    """
    Check formatting quality.
    Returns (bonus_points 0–10, issues list).
    """
    bonus = 0
    issues = []

    # Bullet points present
    bullets = len(re.findall(r"^\s*[-•●▪▸*]\s+", text, re.MULTILINE))
    if bullets >= 6:
        bonus += 4
    elif bullets >= 3:
        bonus += 2
    else:
        issues.append("Too few bullet points — use bullets to list responsibilities and achievements")

    # Consistent date formatting (e.g. 2022, Jan 2023, 2021–2023)
    dates = re.findall(r"\b(20\d{2}|19\d{2})\b", text)
    if len(dates) >= 2:
        bonus += 2
    else:
        issues.append("No dates detected — add graduation year, internship dates, and project timelines")

    # Name likely at top (first non-empty line has 2–4 capitalized words)
    first_lines = [l.strip() for l in text.splitlines() if l.strip()][:3]
    has_name = any(
        re.match(r"^[A-Z][a-z]+(\s[A-Z][a-z]+){1,3}$", line)
        for line in first_lines
    )
    if has_name:
        bonus += 2
    else:
        issues.append("Name may be missing or not clearly placed at the top of the resume")

    # No (cid:) artifacts remaining
    if "(cid:" in text:
        issues.append("PDF encoding artifacts detected — re-export the resume as a clean PDF")
        bonus -= 2

    # Not a wall of text (reasonable line count)
    lines = [l for l in text.splitlines() if l.strip()]
    if len(lines) >= 20:
        bonus += 2
    elif len(lines) < 10:
        issues.append("Very few lines detected — resume may be too sparse or extraction failed")

    return max(0, min(10, bonus)), issues


# ── Main function ─────────────────────────────────────────────────────────────

def structure_score(text: str) -> tuple[int, dict]:
    """
    Score the structural quality of a resume on a 0–100 scale.

    Returns:
        score   (int, 0–100)
        details (dict)
            found_sections   – list of section names detected
            missing_sections – list of critical missing sections
            section_scores   – per-section breakdown
            formatting_bonus – bonus from formatting quality
            formatting_issues – list of formatting problems
            tips             – actionable improvement tips
            summary          – one-line verdict
    """
    lower = text.lower()

    found_sections   = []
    missing_sections = []
    section_scores   = {}
    earned_weight    = 0
    total_weight     = sum(s["weight"] for s in SECTIONS.values())  # 100 before bonus

    tips = []

    # ── Section detection ─────────────────────────────────────────────────────
    for name, cfg in SECTIONS.items():
        detected = any(alias in lower for alias in cfg["aliases"])

        if detected:
            found_sections.append(name)
            earned_weight += cfg["weight"]
            section_scores[name] = {"found": True, "weight": cfg["weight"]}
        else:
            section_scores[name] = {"found": False, "weight": cfg["weight"]}
            if cfg["critical"]:
                missing_sections.append(name)
                tips.append(
                    f"Add a '{name.capitalize()}' section — "
                    f"it is one of the most important resume sections"
                )

    # ── Formatting quality ────────────────────────────────────────────────────
    fmt_bonus, fmt_issues = _check_formatting(text, lower)

    # Scale: section weight out of total_weight → 0–90, formatting adds up to 10
    section_part   = int((earned_weight / total_weight) * 90)
    final_score    = max(5, min(100, section_part + fmt_bonus))

    # ── Additional tips ───────────────────────────────────────────────────────
    if len(found_sections) >= 7:
        pass  # already comprehensive
    elif len(found_sections) >= 5:
        tips.append("Consider adding Certifications or Achievements to strengthen the profile")
    else:
        tips.append("Resume is missing several key sections — a complete resume typically has 6–8 sections")

    if fmt_issues:
        tips.extend(fmt_issues)

    if not tips:
        tips.append("Well-structured resume — all key sections are present and properly organized")

    # ── Level label ───────────────────────────────────────────────────────────
    if final_score >= 85:
        summary = "Excellent structure — comprehensive and well-organized"
    elif final_score >= 70:
        summary = "Good structure with a few sections to add"
    elif final_score >= 50:
        summary = "Moderate structure — several important sections missing"
    else:
        summary = "Poor structure — resume needs major reorganization"

    return final_score, {
        "found_sections":    found_sections,
        "missing_sections":  missing_sections,
        "section_scores":    section_scores,
        "formatting_bonus":  fmt_bonus,
        "formatting_issues": fmt_issues,
        "tips":              tips,
        "summary":           summary,
    }