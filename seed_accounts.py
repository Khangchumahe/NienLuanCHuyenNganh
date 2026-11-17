"""Seed configured demo accounts from environment variables; CLI only."""

import os

from dotenv import load_dotenv

load_dotenv()

from database.db import ensure_schema, get_user_by_email, _create_user_with_role


ACCOUNT_GROUPS = (
    ("ADMIN", "ADMIN"),
    ("STAFF", "STAFF"),
    ("CUSTOMER", "CUSTOMER"),
)


def main():
    ensure_schema()
    had_errors = False

    for prefix, role in ACCOUNT_GROUPS:
        email = (os.environ.get(f"{prefix}_EMAIL") or "").strip()
        password = os.environ.get(f"{prefix}_PASSWORD") or ""
        missing = []
        if not email:
            missing.append(f"{prefix}_EMAIL")
        if not password:
            missing.append(f"{prefix}_PASSWORD")
        if missing:
            print(f"Bỏ qua nhóm {prefix}: thiếu {', '.join(missing)}.")
            continue

        existing = get_user_by_email(email)
        if existing:
            print(
                f"Tài khoản {email} (vai trò {existing['role']}) đã tồn tại; "
                "giữ nguyên mật khẩu và vai trò."
            )
            continue

        if len(password) < 8:
            print(
                f"Không tạo nhóm {prefix}: mật khẩu phải có ít nhất 8 ký tự."
            )
            had_errors = True
            continue

        name = (os.environ.get(f"{prefix}_NAME") or "").strip() or email.split("@", 1)[0]
        phone = (os.environ.get(f"{prefix}_PHONE") or "").strip() or None
        result = _create_user_with_role(email, password, name, phone, role=role)
        if result.get("success"):
            print(f"Đã tạo {role}: {email}")
        else:
            print(f"Không tạo được nhóm {prefix}: {result.get('error', 'dữ liệu không hợp lệ')}.")
            had_errors = True

    return 1 if had_errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
