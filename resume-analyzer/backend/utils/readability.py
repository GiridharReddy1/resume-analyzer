import textstat
import re

textstat.set_lang('en_US')  # prevents cmudict NLTK lookup error


# ── Helpers ───────────────────────────────────────────────────────────────────

def _count_bullet_points(text: str) -> int:
    """Count lines that start with a bullet-like marker."""
    return len(re.findall(r"^\s*[-•●▪▸*]\s+", text, re.MULTILINE))


def _avg_sentence_length(text: str) -> float:
    """Average number of words per sentence."""
    sentences = [s.strip() for s in re.split(r"[.!?]+", text) if len(s.strip()) > 10]
    if not sentences:
        return 0.0
    word_counts = [len(s.split()) for s in sentences]
    return sum(word_counts) / len(word_counts)


def _avg_word_length(text: str) -> float:
    """Average number of characters per word."""
    words = re.findall(r"\b[a-zA-Z]+\b", text)
    if not words:
        return 0.0
    return sum(len(w) for w in words) / len(words)


def _passive_voice_count(text: str) -> int:
    """Rough passive voice detector — looks for 'was/were/is/are + past participle'."""
    pattern = r"\b(was|were|is|are|been|be|being)\s+\w+ed\b"
    return len(re.findall(pattern, text, re.IGNORECASE))


# ── Score normalizer ──────────────────────────────────────────────────────────

def _normalize_flesch(raw: float) -> int:
    """
    Map Flesch Reading Ease (0–100, higher = easier) to our resume score.

    Resume-specific adjustment:
    - Flesch penalizes long technical words (MongoDB, JavaScript, etc.)
    - We give partial credit so a technically-written resume isn't unfairly punished
    - Target range for a good resume: Flesch 40–70
    """
    # Clamp to valid range
    raw = max(0.0, min(100.0, raw))

    if raw >= 70:
        return 85 + int((raw - 70) / 30 * 15)   # 85–100
    elif raw >= 50:
        return 65 + int((raw - 50) / 20 * 20)   # 65–85
    elif raw >= 30:
        return 45 + int((raw - 30) / 20 * 20)   # 45–65
    elif raw >= 10:
        return 20 + int((raw - 10) / 20 * 25)   # 20–45
    else:
        return max(5, int(raw * 2))              # 0–20


# ── Main function ─────────────────────────────────────────────────────────────

def readability_score(text: str) -> tuple[int, dict]:
    """
    Analyze resume text readability using multiple metrics.

    Returns:
        score   (int, 0–100)
        details (dict)
            level           – human label (Excellent / Good / Moderate / Difficult)
            flesch_raw      – raw Flesch Reading Ease score
            avg_sentence_len – average words per sentence
            avg_word_len    – average characters per word
            bullet_points   – number of bullet points detected
            passive_voice   – approximate passive voice usage count
            tips            – list of actionable improvement tips
            summary         – one-line verdict
    """
    if not text or len(text.strip()) < 50:
        return 10, {
            "level": "Unknown",
            "flesch_raw": 0,
            "avg_sentence_len": 0,
            "avg_word_len": 0,
            "bullet_points": 0,
            "passive_voice": 0,
            "tips": ["Not enough text to analyze readability"],
            "summary": "Insufficient content",
        }

    # ── Raw metrics ───────────────────────────────────────────────────────────
    flesch_raw       = round(textstat.flesch_reading_ease(text), 1)
    avg_sent_len     = round(_avg_sentence_length(text), 1)
    avg_word_len     = round(_avg_word_length(text), 1)
    bullet_points    = _count_bullet_points(text)
    passive_count    = _passive_voice_count(text)
    word_count       = len(text.split())

    # ── Base score from Flesch ────────────────────────────────────────────────
    base_score = _normalize_flesch(flesch_raw)

    # ── Bonus / penalty adjustments ───────────────────────────────────────────
    adjustment = 0

    # Bullet points improve scannability — good for resumes
    if bullet_points >= 8:
        adjustment += 8
    elif bullet_points >= 4:
        adjustment += 5
    elif bullet_points >= 1:
        adjustment += 2
    else:
        adjustment -= 5   # wall of text — no bullets

    # Sentence length penalty (resume bullets should be concise)
    if avg_sent_len <= 15:
        adjustment += 5
    elif avg_sent_len <= 20:
        adjustment += 2
    elif avg_sent_len >= 30:
        adjustment -= 5
    elif avg_sent_len >= 25:
        adjustment -= 3

    # Passive voice penalty
    if passive_count >= 5:
        adjustment -= 6
    elif passive_count >= 3:
        adjustment -= 3

    final_score = max(5, min(100, base_score + adjustment))

    # ── Level label ───────────────────────────────────────────────────────────
    if final_score >= 80:
        level = "Excellent"
    elif final_score >= 65:
        level = "Good"
    elif final_score >= 45:
        level = "Moderate"
    else:
        level = "Difficult"

    # ── Tips ──────────────────────────────────────────────────────────────────
    tips = []

    if avg_sent_len > 25:
        tips.append(
            f"Sentences average {avg_sent_len} words — break long sentences into shorter bullet points"
        )
    elif avg_sent_len > 18:
        tips.append("Some sentences are long — aim for under 18 words per bullet")

    if bullet_points < 4:
        tips.append(
            "Use more bullet points to make the resume easier to scan quickly"
        )

    if avg_word_len > 7:
        tips.append(
            "Many long words detected — where possible, prefer simpler alternatives"
        )

    if passive_count >= 3:
        tips.append(
            f"~{passive_count} passive voice phrases found — use active voice "
            "(e.g. 'Built X' not 'X was built')"
        )

    if flesch_raw < 30:
        tips.append(
            "Overall text is complex — simplify descriptions so recruiters can skim quickly"
        )

    if word_count < 150:
        tips.append("Resume has very little content — add more detail to sections")

    if not tips:
        tips.append("Readability is strong — resume is clear and easy to scan")

    # ── Summary ───────────────────────────────────────────────────────────────
    if final_score >= 80:
        summary = "Very readable — easy for recruiters to scan"
    elif final_score >= 65:
        summary = "Good readability with minor areas to improve"
    elif final_score >= 45:
        summary = "Moderate readability — simplify sentences and add bullets"
    else:
        summary = "Hard to read — consider restructuring with shorter, cleaner bullets"

    return final_score, {
        "level":            level,
        "flesch_raw":       flesch_raw,
        "avg_sentence_len": avg_sent_len,
        "avg_word_len":     avg_word_len,
        "bullet_points":    bullet_points,
        "passive_voice":    passive_count,
        "tips":             tips,
        "summary":          summary,
    }