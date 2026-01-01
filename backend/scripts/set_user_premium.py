import argparse
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.db import SessionLocal
from app.models import User


def main() -> None:
    parser = argparse.ArgumentParser(description="Toggle premium for a user.")
    parser.add_argument("--whatsapp-id", required=True, help="WhatsApp ID / wa_id")
    parser.add_argument("--premium", action="store_true", help="Set user as premium")
    parser.add_argument("--free", action="store_true", help="Set user as free")
    args = parser.parse_args()

    if args.premium == args.free:
        raise SystemExit("Provide exactly one of --premium or --free")

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.whatsapp_id == args.whatsapp_id).first()
        if not user:
            raise SystemExit("User not found")

        user.is_premium = args.premium
        db.add(user)
        db.commit()
        print(f"Updated {user.whatsapp_id} premium={user.is_premium}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
