"""Bulk-set the funding amount shown on scholarship cards.

Run from the backend folder (with DATABASE_URL set, like import_scholarships.py):
  python set_funding_amounts.py --export amounts.csv          # writes every scholarship; fill the funding_amount column
  python set_funding_amounts.py amounts.csv                   # dry run: shows what would change
  python set_funding_amounts.py amounts.csv --commit          # saves

Examples for the funding_amount column:  €1,300/month   |   $25,000/year   |   €934/month + tuition
Rows with an empty funding_amount are ignored. Names must match the scholarship name exactly.
Open the CSV in Excel or Google Sheets and save it as CSV (UTF-8) so the € sign survives.
"""
import csv
import sys

from app.database import SessionLocal
from app.models import Scholarship


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    db = SessionLocal()
    try:
        if "--export" in sys.argv:
            path = args[0] if args else "amounts.csv"
            rows = db.query(Scholarship).order_by(Scholarship.name).all()
            with open(path, "w", newline="", encoding="utf-8-sig") as f:
                w = csv.writer(f)
                w.writerow(["name", "level", "funding", "funding_amount"])
                for s in rows:
                    w.writerow([s.name, s.level, s.funding, getattr(s, "funding_amount", "") or ""])
            print(f"Wrote {len(rows)} rows to {path}")
            return
        if not args:
            sys.exit(__doc__)
        by_name = {s.name.strip().lower(): s for s in db.query(Scholarship).all()}
        changed = missing = 0
        with open(args[0], newline="", encoding="utf-8-sig") as f:
            for row in csv.DictReader(f):
                amount = (row.get("funding_amount") or "").strip()
                if not amount:
                    continue
                s = by_name.get((row.get("name") or "").strip().lower())
                if not s:
                    missing += 1
                    print("NOT FOUND:", row.get("name"))
                    continue
                if (s.funding_amount or "") != amount:
                    print(f"{s.name}: {s.funding_amount or '-'} -> {amount}")
                    s.funding_amount = amount
                    changed += 1
        if "--commit" in sys.argv:
            db.commit()
            print(f"Saved {changed} changes ({missing} names not found).")
        else:
            db.rollback()
            print(f"Dry run: {changed} would change ({missing} names not found). Add --commit to save.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
