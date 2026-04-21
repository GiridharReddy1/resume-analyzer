import re
import pdfplumber


# ── Text cleaner ──────────────────────────────────────────────────────────────

def _clean(text: str) -> str:
    """
    Clean raw PDF-extracted text:
    - Remove (cid:XXX) garbage characters from font encoding issues
    - Normalize unicode ligatures (ﬁ → fi, ﬂ → fl, etc.)
    - Collapse excessive whitespace while preserving line breaks
    - Remove null bytes and control characters
    """
    if not text:
        return ""

    # Remove (cid:N) artifacts — common in PDF font encoding
    text = re.sub(r"\(cid:\d+\)", "", text)

    # Normalize common ligatures that PDFs mess up
    ligatures = {
        "\ufb00": "ff", "\ufb01": "fi", "\ufb02": "fl",
        "\ufb03": "ffi", "\ufb04": "ffl", "\ufb05": "st",
        "\u2019": "'", "\u2018": "'", "\u201c": '"', "\u201d": '"',
        "\u2013": "-", "\u2014": "-", "\u2022": "-",   # en/em dash, bullet
        "\u00a0": " ",                                   # non-breaking space
    }
    for char, replacement in ligatures.items():
        text = text.replace(char, replacement)

    # Remove null bytes and non-printable control chars (keep \n \t)
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)

    # Collapse 3+ consecutive blank lines into 2
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Strip trailing spaces on each line
    lines = [line.rstrip() for line in text.splitlines()]
    text = "\n".join(lines)

    return text.strip()


# ── Extraction strategies ─────────────────────────────────────────────────────

def _extract_standard(pdf) -> str:
    """Standard pdfplumber extraction — works for most text-based PDFs."""
    pages = []
    for page in pdf.pages:
        t = page.extract_text(x_tolerance=2, y_tolerance=3)
        if t:
            pages.append(t)
    return "\n\n".join(pages)


def _extract_words(pdf) -> str:
    """
    Word-level extraction — better for multi-column or complex layouts.
    Reconstructs lines by sorting words by their Y then X position.
    """
    pages = []
    for page in pdf.pages:
        words = page.extract_words(
            x_tolerance=3,
            y_tolerance=3,
            keep_blank_chars=False,
            use_text_flow=True,
        )
        if not words:
            continue

        # Group words into lines by top-position (Y coordinate)
        lines: dict[float, list] = {}
        for w in words:
            y = round(w["top"], 1)
            lines.setdefault(y, []).append(w)

        # Sort lines top-to-bottom, words left-to-right
        sorted_lines = sorted(lines.items(), key=lambda x: x[0])
        reconstructed = []
        for _, line_words in sorted_lines:
            line_words.sort(key=lambda w: w["x0"])
            reconstructed.append(" ".join(w["text"] for w in line_words))

        pages.append("\n".join(reconstructed))

    return "\n\n".join(pages)


# ── Main extractor ────────────────────────────────────────────────────────────

def extract_text(file) -> str:
    """
    Extract clean text from an uploaded PDF resume.

    Strategy:
    1. Try standard extraction (fast, accurate for simple layouts)
    2. If result is too short or full of garbage, fall back to word-level
       extraction which handles multi-column and complex layouts better.

    Args:
        file: UploadFile from FastAPI (has a .file attribute)

    Returns:
        Cleaned plain text string. Never returns None.

    Raises:
        ValueError: If the file cannot be opened or is not a valid PDF.
        ValueError: If no text could be extracted (likely a scanned/image PDF).
    """
    try:
        # Reset stream position in case it was read before
        file.file.seek(0)

        with pdfplumber.open(file.file) as pdf:

            if len(pdf.pages) == 0:
                raise ValueError("PDF has no pages.")

            # ── Strategy 1: standard extraction ──────────────────────────────
            raw = _extract_standard(pdf)
            cleaned = _clean(raw)

            # ── Quality check ─────────────────────────────────────────────────
            # If we got very little text, the PDF might be multi-column or
            # image-heavy — try the word-level fallback
            word_count = len(cleaned.split())

            if word_count < 30:
                file.file.seek(0)
                with pdfplumber.open(file.file) as pdf2:
                    raw2 = _extract_words(pdf2)
                    cleaned2 = _clean(raw2)
                    # Use whichever gave more content
                    if len(cleaned2.split()) > word_count:
                        cleaned = cleaned2

            # Final check
            if len(cleaned.strip()) < 20:
                raise ValueError(
                    "No readable text found in this PDF. "
                    "It may be a scanned image — please use a text-based PDF."
                )

            return cleaned

    except ValueError:
        raise
    except Exception as e:
        raise ValueError(f"Failed to read PDF: {str(e)}")


# ── Preview helper ────────────────────────────────────────────────────────────

def get_text_preview(text: str, chars: int = 300) -> str:
    """
    Return a short preview of extracted text for the API response.
    Trims to the first `chars` characters at a word boundary.
    """
    if len(text) <= chars:
        return text
    trimmed = text[:chars]
    # Cut at last space to avoid mid-word truncation
    last_space = trimmed.rfind(" ")
    if last_space > chars // 2:
        trimmed = trimmed[:last_space]
    return trimmed + "…"