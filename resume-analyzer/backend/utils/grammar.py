import language_tool_python
import re

# ── Init LanguageTool once (expensive — module-level singleton) ───────────────
_tool = None

def _get_tool():
    global _tool
    if _tool is None:
        _tool = language_tool_python.LanguageTool("en-US")
    return _tool


# ── Noise filters ─────────────────────────────────────────────────────────────
# These rule IDs fire constantly on resumes (ALL CAPS headings, acronyms,
# proper nouns, URLs, phone numbers) and are not real errors.
IGNORED_RULE_IDS = {
    "UPPERCASE_SENTENCE_START",
    "ENGLISH_WORD_REPEAT_BEGINNING_RULE",
    "EN_UNPAIRED_BRACKETS",
    "COMMA_PARENTHESIS_WHITESPACE",
    "WHITESPACE_RULE",
    "DOUBLE_PUNCTUATION",
    "EN_QUOTES",
    "ARROWS",
    "DASH_RULE",
    "WORD_CONTAINS_UNDERSCORE",
    "URL",
    "EN_SPECIFIC_CASE",           # proper nouns like company/university names
    "MORFOLOGIK_RULE_EN_US",      # overly aggressive spell-check on tech terms
}

# Tech terms & abbreviations that LanguageTool wrongly flags as misspellings
TECH_WHITELIST = {
    "python", "javascript", "typescript", "nodejs", "reactjs", "vuejs",
    "mongodb", "postgresql", "mysql", "redis", "fastapi", "django", "flask",
    "numpy", "pandas", "scikit", "tensorflow", "pytorch", "keras",
    "kubernetes", "docker", "github", "gitlab", "bitbucket", "aws", "gcp",
    "azure", "html", "css", "api", "ui", "ux", "crud", "orm", "jwt",
    "oauth", "ci", "cd", "devops", "frontend", "backend", "fullstack",
    "repo", "npm", "tailwind", "bootcamp", "hackathon", "leetcode",
    "cgpa", "gpa", "b.tech", "m.tech", "b.e", "m.e", "internship",
}


def _is_noise(match, text: str) -> bool:
    """Return True if the match should be ignored."""
    # Ignored rule IDs  (snake_case: rule_id)
    if match.rule_id in IGNORED_RULE_IDS:
        return True

    # Extract the flagged word
    flagged = text[match.offset: match.offset + match.error_length].lower().strip()

    # Whitelisted tech terms
    if flagged in TECH_WHITELIST:
        return True

    # Looks like a URL / email / phone
    if re.search(r"https?://|www\.|@|\+?\d[\d\s\-]{6,}", flagged):
        return True

    # All-caps abbreviations like "AWS", "HTML", "CGPA"
    if re.fullmatch(r"[A-Z]{2,6}\.?", text[match.offset: match.offset + match.error_length]):
        return True

    return False


# ── Severity bucketing ────────────────────────────────────────────────────────
SEVERITY = {
    "misspelling": "high",
    "grammar":     "high",
    "typographical": "medium",
    "style":       "low",
    "punctuation": "low",
}

SEVERITY_WEIGHT = {
    "high":   3,
    "medium": 2,
    "low":    1,
}


# ── Main function ─────────────────────────────────────────────────────────────

def grammar_score(text: str) -> tuple[int, int, dict]:
    """
    Check grammar and spelling using LanguageTool.

    Returns:
        score       (int, 0–100)
        error_count (int, filtered serious errors only)
        details     (dict)
            issues  – list of up to 8 flagged issues with context
            tips    – actionable improvement tips
            summary – one-line human-readable verdict
    """
    tool = _get_tool()
    raw_matches = tool.check(text)

    # Filter noise
    filtered = [m for m in raw_matches if not _is_noise(m, text)]

    # Only count real errors (grammar + spelling), but track style too
    serious = [m for m in filtered if m.rule_issue_type in ("misspelling", "grammar", "typographical")]
    style   = [m for m in filtered if m.rule_issue_type in ("style", "punctuation")]

    error_count = len(serious)
    style_count = len(style)

    # ── Weighted penalty ──────────────────────────────────────────────────────
    # Each serious error has a weight based on severity; deduct from 100
    penalty = 0
    for m in serious:
        sev = SEVERITY.get(m.rule_issue_type, "medium")
        penalty += SEVERITY_WEIGHT[sev]

    # Style issues deduct less
    penalty += style_count * 0.5

    # Scale: 0 penalty = 100, heavy penalty bottoms out at 5
    raw_score = max(5, 100 - int(penalty * 3.5))
    score = min(100, raw_score)

    # ── Build issues list ─────────────────────────────────────────────────────
    issues = []
    for m in serious[:8]:
        # Extract a short context window around the error
        start  = max(0, m.offset - 20)
        end    = min(len(text), m.offset + m.error_length + 20)
        ctx    = text[start:end].replace("\n", " ").strip()
        flagged = text[m.offset: m.offset + m.error_length]

        issues.append({
            "message":    m.message,
            "flagged":    flagged,
            "context":    f"…{ctx}…",
            "suggestions": m.replacements[:3] if m.replacements else [],
            "severity":   SEVERITY.get(m.rule_issue_type, "medium"),
        })

    # ── Tips ──────────────────────────────────────────────────────────────────
    tips = []

    if error_count == 0 and style_count == 0:
        tips.append("Excellent — no grammar or spelling issues detected")
    elif error_count == 0:
        tips.append("No grammar errors; minor style improvements possible")
    elif error_count <= 3:
        tips.append("A few minor errors — proofread once before submitting")
    elif error_count <= 8:
        tips.append("Several grammar/spelling errors found — carefully proofread the full resume")
        tips.append("Use Grammarly or Hemingway Editor for a second pass")
    else:
        tips.append("High number of errors — consider rewriting key sections")
        tips.append("Run through Grammarly and read aloud to catch mistakes")
        tips.append("Ask a friend or mentor to proofread before applying")

    if style_count > 5:
        tips.append(f"{style_count} style/punctuation suggestions — consistent formatting improves readability")

    # ── Summary ───────────────────────────────────────────────────────────────
    if score >= 90:
        summary = "Very clean — minimal language issues"
    elif score >= 75:
        summary = "Good grammar with a few issues to fix"
    elif score >= 55:
        summary = "Moderate errors — needs careful proofreading"
    elif score >= 35:
        summary = "Significant grammar issues — consider a full rewrite"
    else:
        summary = "Poor language quality — major revision needed"

    return score, error_count, {
        "issues":      issues,
        "tips":        tips,
        "summary":     summary,
        "style_count": style_count,
    }