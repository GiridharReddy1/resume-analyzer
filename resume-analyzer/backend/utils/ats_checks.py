import re


# ── ATS Essentials Checker ────────────────────────────────────────────────────

def ats_essentials(text: str, filename: str) -> tuple[float, dict]:
    """
    Check ATS-critical resume essentials.
    Returns (score_out_of_100, checks_dict).

    Each check returns:
        { "passed": bool, "detail": str }
    """

    lower = text.lower()
    checks = {}
    weights = {}

    # ── 1. File format (weight: 20) ───────────────────────────────────────────
    weights["file_format"] = 20
    if filename.lower().endswith(".pdf"):
        checks["file_format"] = {
            "passed": True,
            "detail": "PDF format detected — fully ATS compatible",
        }
    elif filename.lower().endswith((".doc", ".docx")):
        checks["file_format"] = {
            "passed": False,
            "detail": "Word format detected — some ATS systems struggle with .docx; prefer PDF",
        }
    else:
        checks["file_format"] = {
            "passed": False,
            "detail": f"Unsupported file type (.{filename.rsplit('.', 1)[-1]}) — use PDF",
        }

    # ── 2. Email address (weight: 25) ─────────────────────────────────────────
    weights["email"] = 25
    email_match = re.search(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z]{2,}", text)
    email_label = bool(re.search(r"\bemail\b", text[:300].lower()))
    if email_match:
        checks["email"] = {
            "passed": True,
            "detail": f"Email found: {email_match.group()}",
        }
    elif email_label:
        checks["email"] = {
            "passed": True,
            "detail": "Email label detected — ensure actual email address is included for full ATS compatibility",
        }
    else:
        checks["email"] = {
            "passed": False,
            "detail": "No valid email address detected — add a professional email",
        }

    # ── 3. Phone number (weight: 15) ──────────────────────────────────────────
    weights["phone"] = 15
    phone_match = re.search(
        r"(\+?(\d[\s\-.]?){9,13}\d)",
        text
    )
    if phone_match:
        checks["phone"] = {
            "passed": True,
            "detail": f"Phone number detected",
        }
    else:
        checks["phone"] = {
            "passed": False,
            "detail": "No phone number found — add a contact number",
        }

    # ── 4. LinkedIn / GitHub links (weight: 20) ───────────────────────────────
    weights["links"] = 20
    has_linkedin = bool(re.search(r"linkedin\.com/in/", lower)) or bool(re.search(r"\blinkedin\b", text[:300].lower()))
    has_github   = bool(re.search(r"github\.com/", lower)) or bool(re.search(r"\bgithub\b", text[:300].lower()))

    if has_linkedin and has_github:
        checks["links"] = {
            "passed": True,
            "detail": "Both LinkedIn and GitHub profiles are linked",
        }
    elif has_linkedin:
        checks["links"] = {
            "passed": True,
            "detail": "LinkedIn profile linked — consider adding GitHub too",
        }
    elif has_github:
        checks["links"] = {
            "passed": True,
            "detail": "GitHub profile linked — consider adding LinkedIn too",
        }
    else:
        checks["links"] = {
            "passed": False,
            "detail": "No LinkedIn or GitHub links found — add profile URLs",
        }

    # ── 5. Design / length / structure (weight: 20) ───────────────────────────
    weights["design"] = 20
    word_count  = len(text.split())
    char_count  = len(text.strip())

    # Check for tables/graphics indicators (common ATS breakers)
    # Only flag if pipe characters appear on 3+ distinct lines (real table)
    # A single contact line like "Github | LinkedIn | Email" is NOT a table
    pipe_lines = [l for l in text.splitlines() if re.search(r"\|.*\|", l)]
    has_tables = len(pipe_lines) >= 3

    # Check basic section markers
    section_keywords = ["education", "experience", "skills", "projects", "objective", "summary"]
    sections_found   = sum(1 for kw in section_keywords if kw in lower)

    if word_count < 100:
        checks["design"] = {
            "passed": False,
            "detail": f"Resume too short ({word_count} words) — add more content",
        }
    elif word_count > 900:
        checks["design"] = {
            "passed": False,
            "detail": f"Resume may be too long ({word_count} words) — aim for 1 page for freshers",
        }
    elif has_tables:
        checks["design"] = {
            "passed": False,
            "detail": "Table-based layout detected — ATS systems may misread tables; use plain text",
        }
    elif sections_found < 3:
        checks["design"] = {
            "passed": False,
            "detail": f"Only {sections_found} standard sections detected — ensure clear section headings",
        }
    else:
        checks["design"] = {
            "passed": True,
            "detail": f"Clean structure with {sections_found} sections and {word_count} words",
        }

    # ── Score calculation (weighted) ──────────────────────────────────────────
    total_weight = sum(weights.values())  # 100
    earned = sum(
        weights[key]
        for key, val in checks.items()
        if val["passed"]
    )
    score = round((earned / total_weight) * 100, 2)

    return score, checks