"""
Promote an existing registered user to admin.

There is no seeded/demo admin account anywhere in this codebase — the
first admin has to be a real person who has already signed up through
the app, promoted by whoever controls the database.

Usage (from the backend/ directory, with your venv active and .env loaded):

    python -m app.scripts.make_admin you@yourdomain.com

To revoke admin rights:

    python -m app.scripts.make_admin you@yourdomain.com --revoke
"""
import argparse
import sys

from app.database import SessionLocal
from app.models import User


def main():
    parser = argparse.ArgumentParser(description="Promote or demote a user's admin status.")
    parser.add_argument("email", help="Email of an already-registered user")
    parser.add_argument("--revoke", action="store_true", help="Remove admin rights instead of granting them")
    args = parser.parse_args()

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == args.email.lower()).first()
        if not user:
            print(f"No user found with email {args.email}. They need to sign up in the app first.")
            sys.exit(1)

        user.is_admin = not args.revoke
        db.commit()
        action = "revoked from" if args.revoke else "granted to"
        print(f"Admin access {action} {user.email}.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
