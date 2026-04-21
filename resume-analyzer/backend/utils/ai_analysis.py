import re


# ── Keyword banks ─────────────────────────────────────────────────────────────

TECH_SKILLS = [
    "python", "java", "javascript", "typescript", "c++", "c#", "golang", "rust",
    "react", "angular", "vue", "node", "express", "django", "flask", "fastapi",
    "spring", "sql", "mysql", "postgresql", "mongodb", "redis", "firebase",
    "aws", "azure", "gcp", "docker", "kubernetes", "git", "linux",
    "machine learning", "deep learning", "tensorflow", "pytorch", "pandas",
    "numpy", "scikit", "html", "css", "tailwind", "rest api", "graphql",
]

SOFT_SKILLS = [
    "communication", "leadership", "teamwork", "problem solving", "critical thinking",
    "time management", "collaboration", "adaptability", "creativity",
]

ACTION_VERBS = [
    "built", "developed", "designed", "implemented", "created", "led", "managed",
    "improved", "optimized", "reduced", "increased", "deployed", "launched",
    "automated", "integrated", "architected", "delivered", "collaborated",
    "mentored", "researched", "analyzed", "engineered", "maintained",
]

QUANTIFIER_PATTERNS = [
    r"\d+\s*%",           # 30%
    r"\d+x\b",            # 3x
    r"\$[\d,]+",          # $5,000
    r"\d+\+?\s*(users?|customers?|clients?|people|members?|projects?|systems?)",
    r"(increased|decreased|reduced|improved|grew|boosted)\s.*\d+",
]

EDUCATION_KEYWORDS = [
    "bachelor", "master", "b.tech", "m.tech", "b.e", "m.e", "bsc", "msc",
    "degree", "university", "college", "cgpa", "gpa", "graduation",
]

CERTIFICATION_KEYWORDS = [
    "certified", "certification", "certificate", "aws certified", "google certified",
    "coursera", "udemy", "nptel", "hackerrank", "leetcode",
]

CONTACT_SECTIONS = {
    "email":    r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z]{2,}",
    "phone":    r"(\+?\d[\d\s\-().]{7,}\d)",
    "linkedin": r"linkedin\.com/in/",
    "github":   r"github\.com/",
    "portfolio": r"(portfolio|website|www\.|http)",
}

RESUME_SECTIONS = [
    "education", "experience", "project", "skill", "certification",
    "achievement", "award", "summary", "objective", "publication",
    "volunteer", "language", "interest", "hobby",
]


# ── Core analyzer ─────────────────────────────────────────────────────────────

def analyze_resume(text: str) -> dict:
    """
    Analyze resume text and return structured strengths, weaknesses,
    and suggestions based on comprehensive checks.
    """
    original = text
    lower = text.lower()

    strengths = []
    weaknesses = []
    suggestions = []

    # ── 1. Contact information ────────────────────────────────────────────────
    # Primary: look for actual address/URL patterns
    has_email     = bool(re.search(CONTACT_SECTIONS["email"],     original))
    has_phone     = bool(re.search(CONTACT_SECTIONS["phone"],     original))
    has_linkedin  = bool(re.search(CONTACT_SECTIONS["linkedin"],  lower))
    has_github    = bool(re.search(CONTACT_SECTIONS["github"],    lower))
    has_portfolio = bool(re.search(CONTACT_SECTIONS["portfolio"], lower))

    # Fallback: icon-font resumes render email/linkedin as label words, not real addresses.
    # Check first 300 chars for these labels as a secondary signal.
    top = lower[:300]
    has_email    = has_email    or bool(re.search(r"\bemail\b",    top))
    has_linkedin = has_linkedin or bool(re.search(r"\blinkedin\b", top))
    has_github   = has_github   or bool(re.search(r"\bgithub\b",   top))

    if has_email:
        strengths.append("Contact email is present")
    else:
        weaknesses.append("No email address found — add a real email, not just an icon label")
        suggestions.append("Add a professional email address (e.g. name@gmail.com)")

    if has_phone:
        strengths.append("Phone number is present")
    else:
        weaknesses.append("No phone number found")
        suggestions.append("Add a contact phone number")

    if has_linkedin:
        strengths.append("LinkedIn profile linked")
    else:
        weaknesses.append("LinkedIn profile missing")
        suggestions.append("Add your LinkedIn profile URL (linkedin.com/in/yourname)")

    if has_github or has_portfolio:
        strengths.append("Portfolio or GitHub profile linked")
    else:
        suggestions.append("Add a GitHub or portfolio link to showcase your work")

    # ── 2. Sections present ───────────────────────────────────────────────────
    found_sections = [s for s in RESUME_SECTIONS if s in lower]
    missing_critical = [s for s in ["education", "experience", "skill", "project"] if s not in found_sections]

    if len(found_sections) >= 5:
        strengths.append(f"Well-structured resume with {len(found_sections)} sections")
    elif len(found_sections) >= 3:
        strengths.append("Core resume sections are present")
    else:
        weaknesses.append("Resume is missing several important sections")
        suggestions.append("Add sections: Education, Experience, Skills, Projects, Summary")

    for sec in missing_critical:
        weaknesses.append(f"'{sec.capitalize()}' section is missing")
        suggestions.append(f"Add a dedicated {sec.capitalize()} section")

    # ── 3. Career objective / summary ─────────────────────────────────────────
    has_summary = any(w in lower for w in ["objective", "summary", "profile", "about me"])
    if has_summary:
        strengths.append("Career objective or summary is present")
    else:
        weaknesses.append("No career objective or summary found")
        suggestions.append("Add a 2–3 line career objective or professional summary at the top")

    # ── 4. Technical skills ───────────────────────────────────────────────────
    found_skills = [skill for skill in TECH_SKILLS if skill in lower]
    if len(found_skills) >= 6:
        strengths.append(f"Strong technical skill set ({len(found_skills)} technologies listed)")
    elif len(found_skills) >= 3:
        strengths.append(f"Technical skills present ({', '.join(found_skills[:3])} and more)")
    elif len(found_skills) >= 1:
        weaknesses.append(f"Only {len(found_skills)} technical skill(s) detected — too few")
        suggestions.append("Expand your Skills section with relevant languages, frameworks, and tools")
    else:
        weaknesses.append("No recognizable technical skills found")
        suggestions.append("Add a Skills section listing programming languages, frameworks, and tools")

    # ── 5. Soft skills ────────────────────────────────────────────────────────
    found_soft = [s for s in SOFT_SKILLS if s in lower]
    if len(found_soft) >= 2:
        strengths.append("Soft skills mentioned")
    else:
        suggestions.append("Mention relevant soft skills (e.g. leadership, communication, teamwork)")

    # ── 6. Action verbs ───────────────────────────────────────────────────────
    found_verbs = [v for v in ACTION_VERBS if v in lower]
    if len(found_verbs) >= 5:
        strengths.append("Strong use of action verbs throughout the resume")
    elif len(found_verbs) >= 2:
        strengths.append("Some action verbs used in descriptions")
    else:
        weaknesses.append("Bullet points lack action verbs")
        suggestions.append("Start every bullet point with a strong action verb (Built, Designed, Improved, Led…)")

    # ── 7. Quantified achievements ────────────────────────────────────────────
    has_numbers = any(re.search(p, lower) for p in QUANTIFIER_PATTERNS)
    if has_numbers:
        strengths.append("Resume includes quantified achievements (numbers/metrics)")
    else:
        weaknesses.append("No quantified achievements found")
        suggestions.append("Add metrics to your achievements (e.g. 'Improved performance by 30%', 'Served 500+ users')")

    # ── 8. Education ──────────────────────────────────────────────────────────
    has_education = any(w in lower for w in EDUCATION_KEYWORDS)
    if has_education:
        strengths.append("Education section is present and complete")
    else:
        weaknesses.append("Education details are missing or unclear")
        suggestions.append("Add your degree, institution name, year of graduation, and CGPA")

    # ── 9. Experience / internship ────────────────────────────────────────────
    has_experience = any(w in lower for w in ["experience", "intern", "internship", "worked at", "employed"])
    if has_experience:
        strengths.append("Work experience or internship is mentioned")
    else:
        weaknesses.append("No work experience or internship found")
        suggestions.append("Add internship experience or freelance projects to show practical exposure")

    # ── 10. Projects ──────────────────────────────────────────────────────────
    has_projects = "project" in lower
    project_count = len(re.findall(r"\bproject\b", lower))
    if project_count >= 2:
        strengths.append(f"Multiple projects listed ({project_count} found)")
    elif has_projects:
        strengths.append("Projects section is present")
        suggestions.append("Add 2–3 projects with tech stack, your role, and outcomes")
    else:
        weaknesses.append("No projects mentioned")
        suggestions.append("Add 2–3 projects with tech stack used, your role, and the impact")

    # ── 11. Certifications ────────────────────────────────────────────────────
    has_cert = any(w in lower for w in CERTIFICATION_KEYWORDS)
    if has_cert:
        strengths.append("Certifications or online courses are listed")
    else:
        suggestions.append("Add relevant certifications (e.g. AWS, Google, NPTEL, Coursera)")

    # ── 12. Resume length check ───────────────────────────────────────────────
    word_count = len(original.split())
    if word_count < 150:
        weaknesses.append("Resume is too short (under 150 words)")
        suggestions.append("Expand your resume with more details about experience, skills, and projects")
    elif word_count > 1000:
        weaknesses.append("Resume may be too long for a fresher/early-career profile")
        suggestions.append("Trim resume to 1 page — focus on the most impactful points")
    else:
        strengths.append(f"Resume length is appropriate ({word_count} words)")

    # ── Deduplicate & clean ───────────────────────────────────────────────────
    strengths   = list(dict.fromkeys(strengths))
    weaknesses  = list(dict.fromkeys(weaknesses))
    suggestions = list(dict.fromkeys(suggestions))

    # Fallback — should rarely trigger now
    if not strengths:
        strengths.append("Resume has basic structure in place")
    if not weaknesses:
        weaknesses.append("No critical issues found — focus on further optimization")
    if not suggestions:
        suggestions.append("Keep resume updated with latest projects and skills")

    return {
        "strengths":   strengths,
        "weaknesses":  weaknesses,
        "suggestions": suggestions,
    }