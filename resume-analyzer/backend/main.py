from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from utils.parser import extract_text, get_text_preview
from utils.scoring import structure_score
from utils.grammar import grammar_score
from utils.readability import readability_score
from utils.ai_analysis import analyze_resume
from utils.ats_checks import ats_essentials

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Safe unpack helpers ───────────────────────────────────────────────────────
# These handle both old utils (return plain int) and new ones (return tuple)

def _unpack2(result, default_score=0):
    """Unpack (score, details) — works if result is just an int too."""
    if isinstance(result, tuple):
        score, details = result[0], result[1]
    else:
        score, details = result, {}
    return int(score), details


def _unpack3(result):
    """Unpack (score, count, details) for grammar_score."""
    if isinstance(result, tuple) and len(result) == 3:
        return int(result[0]), int(result[1]), result[2]
    elif isinstance(result, tuple) and len(result) == 2:
        return int(result[0]), 0, {}
    else:
        return int(result), 0, {}


def _safe_dict(d):
    """Ensure a dict has only string keys and JSON-serializable values."""
    if not isinstance(d, dict):
        return {}
    return {str(k): v for k, v in d.items()}


# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/")
def home():
    return {"message": "Resume Analyzer backend running 🚀"}


@app.post("/upload")
async def upload(file: UploadFile = File(...)):

    # ── 1. Validate ───────────────────────────────────────────────────────────
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    # ── 2. Extract text ───────────────────────────────────────────────────────
    try:
        text = extract_text(file)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF extraction failed: {str(e)}")

    if not text or len(text.strip()) < 20:
        raise HTTPException(
            status_code=422,
            detail="No readable text found. Make sure the PDF is text-based, not a scanned image."
        )

    # ── 3. Scores ─────────────────────────────────────────────────────────────
    try:
        structure,   structure_details   = _unpack2(structure_score(text))
    except Exception:
        structure,   structure_details   = 0, {}

    try:
        grammar, grammar_errors, grammar_details = _unpack3(grammar_score(text))
    except Exception:
        grammar, grammar_errors, grammar_details = 0, 0, {}

    try:
        readability, readability_details = _unpack2(readability_score(text))
    except Exception:
        readability, readability_details = 0, {}

    # ── 4. ATS essentials ─────────────────────────────────────────────────────
    try:
        ats_essentials_score, ats_details_raw = ats_essentials(text, file.filename)
        ats_essentials_score = float(ats_essentials_score)
        # Ensure ats_details is a plain dict with string keys
        ats_details = _safe_dict(ats_details_raw)
    except Exception:
        ats_essentials_score, ats_details = 0.0, {}

    # ── 5. AI analysis ────────────────────────────────────────────────────────
    try:
        ai_result = analyze_resume(text)
        if not isinstance(ai_result, dict):
            ai_result = {}
    except Exception:
        ai_result = {"strengths": [], "weaknesses": [], "suggestions": []}

    # ── 6. Composite ATS score ────────────────────────────────────────────────
    # All sub-scores are 0–100
    ats_score = round(
        structure            * 0.30 +
        grammar              * 0.25 +
        readability          * 0.20 +
        ats_essentials_score * 0.25,
        2
    )

    # ── 7. Return JSON-safe response ──────────────────────────────────────────
    return {
        "text_preview":      get_text_preview(text, chars=300),

        "structure_score":   structure,
        "grammar_score":     grammar,
        "grammar_errors":    grammar_errors,
        "readability_score": readability,
        "ats_score":         ats_score,

        "structure_details":   _safe_dict(structure_details),
        "grammar_details":     _safe_dict(grammar_details),
        "readability_details": _safe_dict(readability_details),
        "ats_essentials":      ats_details,

        "ai_analysis": {
            "strengths":   list(ai_result.get("strengths",   [])),
            "weaknesses":  list(ai_result.get("weaknesses",  [])),
            "suggestions": list(ai_result.get("suggestions", [])),
        },
    }