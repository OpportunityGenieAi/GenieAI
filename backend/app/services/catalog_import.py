"""
Loads curated scholarship batches from app/data/*.csv into the database.

- Safe to run on every startup: an existing scholarship is recognised by its NAME
  (accents/punctuation ignored) plus either the same provider or the same website host
  as its official link. Matches are updated only when a value actually changed;
  nothing is duplicated.
- If a name matches but provider AND website both differ, the row is inserted and a
  "possible duplicate" warning is printed in the logs so you can review it.
- New rows get created_at = the CSV's date_added (or now), which drives "latest first".
- Rows that fail validation are skipped and counted; one bad row never stops the rest.

CSV columns (header names must match):
  name, provider, country, level, field, funding, deadline_window, deadline_date,
  official_link, source_url, last_verified, tags, blurb, date_added, is_active
  - tags: separated by semicolons (Leadership;Stanford)
  - dates: YYYY-MM-DD (deadline_date only when an exact closing date is verified)
  - is_active: false retires a scholarship without deleting it
"""
import csv
import glob
import os
import re
import unicodedata
from datetime import datetime, time
from urllib.parse import urlparse

from sqlalchemy.orm import Session

from app.models import Scholarship

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")

REQUIRED = ["name", "provider", "country", "level", "deadline_window", "official_link"]


def _parse_date(value: str):
    value = (value or "").strip()
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return None


def _norm(text: str) -> str:
    """Lowercase, strip accents and punctuation, collapse spaces."""
    text = unicodedata.normalize("NFKD", text or "")
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


def _host(url: str) -> str:
    host = (urlparse(url or "").hostname or "").lower()
    return host[4:] if host.startswith("www.") else host


def _index(rows):
    index = {}
    for s in rows:
        index.setdefault(_norm(s.name), []).append(s)
    return index


def _find(index, values):
    """Return (match, possible_duplicate_names)."""
    candidates = index.get(_norm(values["name"]), [])
    new_host = _host(values["official_link"])
    for cand in candidates:
        same_provider = _norm(cand.provider) == _norm(values["provider"])
        same_site = bool(new_host) and _host(cand.official_link) == new_host
        if same_provider or same_site:
            return cand, False
    return None, bool(candidates)


def _clean_row(raw: dict):
    row = {k.strip(): (v or "").strip() for k, v in raw.items() if k}
    for field in REQUIRED:
        if not row.get(field):
            return None, f"missing {field}"
    if not row["official_link"].lower().startswith(("http://", "https://")):
        return None, "official_link must start with http(s)://"

    values = {
        "name": row["name"],
        "provider": row["provider"],
        "country": row["country"],
        "level": row["level"],
        "field": row.get("field") or "All fields",
        "funding": row.get("funding") or "Fully-funded",
        "deadline_window": row["deadline_window"],
        "official_link": row["official_link"],
        "source_url": row.get("source_url") or None,
        "blurb": row.get("blurb") or "",
        "tags": [t.strip() for t in row.get("tags", "").split(";") if t.strip()],
        "deadline_date": _parse_date(row.get("deadline_date", "")),
        "last_verified": _parse_date(row.get("last_verified", "")),
        "is_active": row.get("is_active", "true").lower() not in ("false", "0", "no"),
    }
    added = _parse_date(row.get("date_added", ""))
    created_at = datetime.combine(added, time(12, 0)) if added else None
    return (values, created_at), None


def import_catalog(db: Session) -> dict:
    files = sorted(glob.glob(os.path.join(DATA_DIR, "*.csv")))
    if not files:
        return {"inserted": 0, "updated": 0, "skipped": 0}

    index = _index(db.query(Scholarship).all())
    inserted = updated = skipped = 0

    for path in files:
        with open(path, newline="", encoding="utf-8-sig") as fh:
            for line_no, raw in enumerate(csv.DictReader(fh), start=2):
                try:
                    cleaned, problem = _clean_row(raw)
                    if problem:
                        skipped += 1
                        print(f"[catalog] {os.path.basename(path)} line {line_no} skipped: {problem}")
                        continue
                    values, created_at = cleaned
                    current, maybe_dup = _find(index, values)

                    if current is None:
                        if maybe_dup:
                            print(f"[catalog] possible duplicate (same name, different provider/site): "
                                  f"{values['name']} - {values['provider']}")
                        row = Scholarship(**values, created_at=created_at or datetime.utcnow())
                        db.add(row)
                        index.setdefault(_norm(values["name"]), []).append(row)
                        inserted += 1
                        continue

                    changed = False
                    for field, new_value in values.items():
                        if field in ("name", "provider"):
                            continue
                        if getattr(current, field) != new_value:
                            setattr(current, field, new_value)
                            changed = True
                    if changed:
                        current.updated_at = datetime.utcnow()
                        updated += 1
                except Exception as exc:  # one bad row must never block the rest
                    skipped += 1
                    print(f"[catalog] {os.path.basename(path)} line {line_no} error: {exc}")

    db.commit()
    print(f"[catalog] inserted {inserted}, updated {updated}, skipped {skipped}")
    return {"inserted": inserted, "updated": updated, "skipped": skipped}
