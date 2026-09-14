"""
Transparent, rules-based scholarship match scoring and the "readiness
score" (a star-rated self-assessment, similar to a credit score).
Both are heuristics — not a trained model, not a guarantee.
"""
from app.models import AcademicProfile, GpaProfile, Scholarship


def _norm(s: str | None) -> str:
    return (s or "").lower()


def _level_matches(scholarship_level: str, seeking_level: str) -> bool:
    sl, wanted = _norm(scholarship_level), _norm(seeking_level)
    if wanted in sl:
        return True
    if wanted == "postdoc" and ("postdoc" in sl or "research" in sl):
        return True
    if "any" in sl:
        return True
    return False


def _field_matches(scholarship_field: str, profile_field: str) -> str:
    sf, pf = _norm(scholarship_field), _norm(profile_field)
    if not pf:
        return "unknown"
    if "all fields" in sf:
        return "open"
    first_sf = sf.split(",")[0].strip()
    if pf in sf or first_sf in pf:
        return "match"
    for word in [w for w in sf.replace("/", " ").replace(",", " ").split() if len(w) > 3]:
        if word in pf:
            return "match"
    return "none"


def compute_match_score(scholarship: Scholarship, gpa: GpaProfile | None, academic: AcademicProfile | None) -> dict:
    score = 50

    if gpa:
        g = gpa.gpa
        if g >= 3.7: score += 20
        elif g >= 3.3: score += 12
        elif g >= 2.7: score += 4
        elif g >= 2.0: score -= 4
        else: score -= 18

    if academic and academic.level:
        score += 18 if _level_matches(scholarship.level, academic.level) else -12

    if academic and academic.field:
        fm = _field_matches(scholarship.field, academic.field)
        if fm == "open": score += 8
        elif fm == "match": score += 10
        elif fm == "none": score -= 6

    if academic and academic.ielts:
        if academic.ielts >= 7.0: score += 6
        elif academic.ielts >= 6.5: score += 3
        elif academic.ielts < 6.0: score -= 6

    if academic:
        if (academic.publications or 0) > 0: score += 3
        if academic.leadership and academic.leadership != "None": score += 3
        if academic.volunteering and academic.volunteering != "None": score += 2
        if (academic.work_years or 0) >= 2: score += 2

    score = max(2, min(98, round(score)))
    tier = "green" if score >= 70 else "yellow" if score >= 45 else "red"
    return {"score": score, "tier": tier}


def compute_readiness(gpa: GpaProfile | None, academic: AcademicProfile | None) -> dict | None:
    if not gpa or not academic:
        return None
    cats = []

    g = gpa.gpa
    cats.append({"label": "CGPA", "stars": 5 if g >= 3.7 else 4 if g >= 3.3 else 3 if g >= 2.7 else 2 if g >= 2.0 else 1})

    pubs = academic.publications or 0
    cats.append({"label": "Research", "stars": 5 if pubs >= 3 else 4 if pubs == 2 else 3 if pubs == 1 else 1})

    cats.append({"label": "Leadership", "stars": 5 if academic.leadership == "Extensive" else 3 if academic.leadership == "Some" else 1})

    ielts = academic.ielts
    if ielts is None:
        ielts_stars = 2
    elif ielts >= 8: ielts_stars = 5
    elif ielts >= 7: ielts_stars = 4
    elif ielts >= 6.5: ielts_stars = 3
    elif ielts >= 6: ielts_stars = 2
    else: ielts_stars = 1
    cats.append({"label": "IELTS", "stars": ielts_stars})

    cats.append({"label": "Volunteering", "stars": 5 if academic.volunteering == "Regular" else 3 if academic.volunteering == "Occasional" else 1})

    wy = academic.work_years or 0
    cats.append({"label": "Work Experience", "stars": 5 if wy >= 6 else 4 if wy >= 4 else 3 if wy >= 2 else 2 if wy >= 1 else 1})

    cats.append({"label": "Recommendation Letters", "stars": 5 if academic.has_recommendation_letters else 2})
    cats.append({"label": "Statement of Purpose", "stars": 4 if academic.has_sop else 1})
    cats.append({"label": "CV / Resume", "stars": 5 if academic.has_cv else 2})

    overall = round(sum(c["stars"] for c in cats) / (len(cats) * 5) * 100)
    return {"overall": overall, "categories": cats}
