"""
Global GPA / CGPA conversion engine.

These tables are approximate equivalency guides commonly used by
international credential evaluators. They are estimates for planning
purposes — not an official evaluation, and not a guarantee of how any
specific university or scholarship will read a transcript.
"""
from dataclasses import dataclass


def lerp_table(x: float, table: list[tuple[float, float]]) -> float:
    if x <= table[0][0]:
        return table[0][1]
    if x >= table[-1][0]:
        return table[-1][1]
    for (x0, y0), (x1, y1) in zip(table, table[1:]):
        if x0 <= x <= x1:
            t = (x - x0) / (x1 - x0)
            return y0 + t * (y1 - y0)
    return table[-1][1]


UK_PERCENT_TABLE = [(0, 0), (40, 1.0), (45, 2.0), (50, 2.7), (60, 3.3), (70, 3.7), (100, 4.0)]
US_PERCENT_TABLE = [(0, 0), (60, 1.0), (65, 1.7), (70, 2.3), (80, 3.0), (90, 3.7), (100, 4.0)]
FRANCE_TABLE = [(0, 0), (10, 2.0), (12, 3.0), (14, 3.5), (16, 3.9), (20, 4.0)]
ITALY_TABLE = [(0, 0), (66, 2.0), (80, 2.5), (90, 3.0), (100, 3.6), (110, 4.0)]
GERMANY_TABLE = [(1, 4.0), (1.5, 3.5), (2, 3.0), (2.5, 2.5), (3, 2.0), (3.5, 1.5), (4, 1.0), (5, 0)]
ECTS_LETTER_GPA = {"A": 3.9, "B": 3.3, "C": 3.0, "D": 2.0, "E": 1.0, "F": 0.0}


@dataclass
class GradingSystem:
    id: str
    label: str
    input_type: str  # "percent" | "number" | "select"
    to_gpa: callable
    min: float = 0
    max: float = 100
    options: list[str] | None = None


SYSTEMS: list[GradingSystem] = [
    GradingSystem("uk-percent", "Percentage — UK / Commonwealth (UK, Kenya, Nigeria, Ghana, Uganda, Tanzania, South Africa)",
                  "percent", lambda v: lerp_table(v, UK_PERCENT_TABLE), 0, 100),
    GradingSystem("us-percent", "Percentage — US style (USA, Canada, Middle East, general)",
                  "percent", lambda v: lerp_table(v, US_PERCENT_TABLE), 0, 100),
    GradingSystem("india-cgpa10", "CGPA out of 10 (India)",
                  "number", lambda v: min(4.0, (v / 10) * 4), 0, 10),
    GradingSystem("pk-bd-gpa4", "GPA out of 4.0 (Pakistan, Bangladesh)",
                  "number", lambda v: min(4.0, v), 0, 4),
    GradingSystem("us-gpa4", "GPA out of 4.0 (USA and others)",
                  "number", lambda v: min(4.0, v), 0, 4),
    GradingSystem("cn-gpa5", "GPA out of 5.0 (China and others)",
                  "number", lambda v: min(4.0, (v / 5) * 4), 0, 5),
    GradingSystem("kr-gpa45", "GPA out of 4.5 (South Korea)",
                  "number", lambda v: min(4.0, (v / 4.5) * 4), 0, 4.5),
    GradingSystem("au-gpa7", "GPA out of 7.0 (Australia)",
                  "number", lambda v: min(4.0, (v / 7) * 4), 0, 7),
    GradingSystem("de-15", "German scale — 1.0 (best) to 5.0 (fail)",
                  "number", lambda v: lerp_table(v, GERMANY_TABLE), 1, 5),
    GradingSystem("fr-20", "Out of 20 (France)",
                  "number", lambda v: lerp_table(v, FRANCE_TABLE), 0, 20),
    GradingSystem("it-110", "Out of 110 (Italy — Laurea)",
                  "number", lambda v: lerp_table(v, ITALY_TABLE), 0, 110),
    GradingSystem("es-10", "Out of 10 (Spain)",
                  "number", lambda v: min(4.0, (v / 10) * 4), 0, 10),
    GradingSystem("ects-letter", "ECTS letter grade — A to F (general Europe)",
                  "select", lambda v: ECTS_LETTER_GPA[v], options=["A", "B", "C", "D", "E", "F"]),
]

_SYSTEMS_BY_ID = {s.id: s for s in SYSTEMS}


def reverse_lerp_to_us_percent(gpa: float) -> float:
    table = US_PERCENT_TABLE
    if gpa <= table[0][1]:
        return table[0][0]
    if gpa >= table[-1][1]:
        return table[-1][0]
    for (x0, y0), (x1, y1) in zip(table, table[1:]):
        if y0 <= gpa <= y1:
            t = (gpa - y0) / (y1 - y0)
            return x0 + t * (x1 - x0)
    return table[-1][0]


def gpa_to_ects(gpa: float) -> str:
    if gpa >= 3.7: return "A"
    if gpa >= 3.3: return "B"
    if gpa >= 2.7: return "C"
    if gpa >= 2.0: return "D"
    if gpa >= 1.0: return "E"
    return "F"


def gpa_to_percentile_note(gpa: float) -> str:
    if gpa >= 3.7:
        return ("Roughly top 10% globally — a strong fit for the most competitive fully-funded "
                "awards (Chevening, Fulbright, Gates Cambridge, Rhodes, Schwarzman).")
    if gpa >= 3.3:
        return "Roughly top 25% globally — competitive for most fully-funded scholarships, especially with a solid IELTS/TOEFL score."
    if gpa >= 2.7:
        return "Above average globally — a realistic shot at many partial and regional scholarships."
    if gpa >= 2.0:
        return "Around the global average — some need- or region-based scholarships are within reach."
    return "Below the threshold most fully-funded scholarships set — a foundation year or a stronger final-year performance would help."


class UnknownSystemError(ValueError):
    pass


class InvalidValueError(ValueError):
    pass


def compute_conversion(system_id: str, raw_value: str) -> dict:
    sys = _SYSTEMS_BY_ID.get(system_id)
    if not sys:
        raise UnknownSystemError(f"Unknown grading system: {system_id}")

    if sys.input_type == "select":
        if raw_value not in (sys.options or []):
            raise InvalidValueError(f"'{raw_value}' is not a valid option for {system_id}")
        gpa = max(0.0, min(4.0, sys.to_gpa(raw_value)))
    else:
        try:
            value = float(raw_value)
        except (TypeError, ValueError):
            raise InvalidValueError(f"'{raw_value}' is not a valid number")
        gpa = max(0.0, min(4.0, sys.to_gpa(value)))

    if system_id in ("uk-percent", "us-percent"):
        percent = float(raw_value)
    else:
        percent = reverse_lerp_to_us_percent(gpa)

    return {
        "gpa": round(gpa, 2),
        "percent": round(percent),
        "ects": gpa_to_ects(gpa),
        "percentile_note": gpa_to_percentile_note(gpa),
    }
