import os
import sqlite3
import subprocess
import sys
from pathlib import Path

from database import db


ROOT = Path(__file__).resolve().parents[1]
GROUPS = {
    "ADMIN": ("admin@example.test", "StrongAdminPass1!", "Demo Admin", "0900000001"),
    "STAFF": ("staff@example.test", "StrongStaffPass2!", "Demo Staff", "0900000002"),
    "CUSTOMER": ("customer@example.test", "StrongCustomerPass3!", "Demo Customer", "0900000003"),
}


def _seed_env(database_path, groups=None):
    env = os.environ.copy()
    env.update({
        "AURA_DB_PATH": str(database_path),
        "APP_ENV": "test",
        "SECRET_KEY": "seed-test-secret",
        "FLASK_SECRET_KEY": "seed-test-secret",
        "ZALOPAY_KEY1": "seed-test-key1",
        "ZALOPAY_KEY2": "seed-test-key2",
        "GEMINI_API_KEY": "",
        "PYTHON_DOTENV_DISABLED": "1",
    })
    for group in ("ADMIN", "STAFF", "CUSTOMER"):
        for suffix in ("EMAIL", "PASSWORD", "NAME", "PHONE"):
            env[f"{group}_{suffix}"] = ""
    for group, values in (groups or GROUPS).items():
        for suffix, value in zip(("EMAIL", "PASSWORD", "NAME", "PHONE"), values):
            env[f"{group}_{suffix}"] = value
    return env


def _run_seed(database_path, groups=None):
    return subprocess.run(
        [sys.executable, "seed_accounts.py"], cwd=ROOT,
        env=_seed_env(database_path, groups), capture_output=True, text=True,
    )


def _users(database_path):
    with sqlite3.connect(database_path) as conn:
        return {
            row[0]: (row[1], row[2])
            for row in conn.execute("SELECT email, role, password_hash FROM users")
        }


def test_seed_cli_creates_roles_idempotently_without_leaking_passwords(tmp_path):
    database_path = tmp_path / "seeded.db"
    first = _run_seed(database_path)
    assert first.returncode == 0, first.stderr
    users = _users(database_path)
    assert {email: value[0] for email, value in users.items()} == {
        values[0]: role for role, values in GROUPS.items()
    }
    for role, (email, password, _, _) in GROUPS.items():
        password_hash = users[email][1]
        assert password_hash.startswith("pbkdf2_sha256$")
        assert db._check_password(password, password_hash)
        assert password not in first.stdout + first.stderr
        assert password_hash not in first.stdout + first.stderr
        assert email in first.stdout and role in first.stdout

    with sqlite3.connect(database_path) as conn:
        conn.execute(
            "UPDATE users SET role='STAFF' WHERE email=?",
            (GROUPS["ADMIN"][0],),
        )
    users = _users(database_path)

    changed = {
        role: (values[0], "DifferentPassword9!", values[2], values[3])
        for role, values in GROUPS.items()
    }
    second = _run_seed(database_path, changed)
    assert second.returncode == 0, second.stderr
    after = _users(database_path)
    assert after == users
    assert "đã tồn tại" in second.stdout.lower()
    assert all(password not in second.stdout + second.stderr for _, password, _, _ in changed.values())


def test_seeded_admin_can_use_admin_routes_customer_cannot_and_registration_stays_customer(
    tmp_path, monkeypatch
):
    database_path = tmp_path / "auth-seed.db"
    result = _run_seed(database_path)
    assert result.returncode == 0, result.stderr

    monkeypatch.setattr(db, "DB_PATH", str(database_path))
    db.ensure_schema()
    from app import app

    client = app.test_client()
    admin_email, admin_password = GROUPS["ADMIN"][:2]
    admin_login = client.post("/api/auth/login", json={
        "email": admin_email, "password": admin_password,
    })
    assert admin_login.status_code == 200
    csrf = admin_login.get_json()["csrf_token"]
    assert client.get("/api/admin/stats").status_code == 200

    client.post("/api/auth/logout", headers={"X-CSRF-Token": csrf})
    customer_email, customer_password = GROUPS["CUSTOMER"][:2]
    customer_login = client.post("/api/auth/login", json={
        "email": customer_email, "password": customer_password,
    })
    assert customer_login.status_code == 200
    assert client.get("/api/admin/stats").status_code == 403

    client.post("/api/auth/logout", headers={
        "X-CSRF-Token": customer_login.get_json()["csrf_token"],
    })
    staff_email, staff_password = GROUPS["STAFF"][:2]
    staff_login = client.post("/api/auth/login", json={
        "email": staff_email, "password": staff_password,
    })
    assert staff_login.status_code == 200
    assert client.get("/api/admin/stats").status_code == 403

    registered = client.post("/api/auth/register", json={
        "email": "role-injection@example.test",
        "password": "WebCustomerPass4!",
        "full_name": "Role Injection Test",
        "role": "ADMIN",
    })
    assert registered.status_code == 201
    assert _users(database_path)["role-injection@example.test"][0] == "CUSTOMER"


def test_seed_cli_rejects_weak_password_without_creating_account(tmp_path):
    database_path = tmp_path / "weak-password.db"
    weak_group = {"ADMIN": ("weak@example.test", "short7!", "Weak User", "0900000004")}
    result = _run_seed(database_path, weak_group)
    assert result.returncode != 0
    assert "ít nhất 8 ký tự" in (result.stdout + result.stderr)
    assert "short7!" not in (result.stdout + result.stderr)
    assert "weak@example.test" not in _users(database_path)


def test_schema_upgrade_preserves_old_users_and_accepts_staff_role(tmp_path):
    database_path = tmp_path / "old-users-schema.db"
    with sqlite3.connect(database_path) as conn:
        legacy_schema = (ROOT / "database" / "schema.sql").read_text(encoding="utf-8")
        legacy_schema = legacy_schema.replace(
            "('ADMIN', 'STAFF', 'CUSTOMER')", "('ADMIN', 'CUSTOMER')"
        )
        conn.executescript(legacy_schema)
        admin_id = conn.execute(
            "INSERT INTO users (email,password_hash,full_name,role) VALUES (?,?,?,?)",
            ("legacy-admin@example.test", "existing-hash", "Legacy Admin", "ADMIN"),
        ).lastrowid
        conn.execute(
            """INSERT INTO orders
               (id,order_code,customer_name,customer_phone,customer_address,total_amount,payment_method)
               VALUES (1,'ORD-LEGACY','Legacy','0900000000','Address',100,'COD')"""
        )
        conn.execute(
            "INSERT INTO customer_order_links (order_id,user_id) VALUES (1,?)",
            (admin_id,),
        )

    env = _seed_env(database_path, groups={})
    script = r'''
import json, sqlite3
from database.db import ensure_schema
ensure_schema()
con = sqlite3.connect(__import__('os').environ['AURA_DB_PATH'])
con.execute("INSERT INTO users (email,password_hash,full_name,role) VALUES (?,?,?,?)", ('staff@example.test','opaque','Staff','STAFF'))
con.commit()
rows = con.execute('SELECT email,password_hash,role FROM users ORDER BY email').fetchall()
links = con.execute('SELECT order_id,user_id FROM customer_order_links').fetchall()
foreign_key_errors = con.execute('PRAGMA foreign_key_check').fetchall()
print(json.dumps({'users': rows, 'links': links, 'fk_errors': foreign_key_errors}))
'''
    result = subprocess.run(
        [sys.executable, "-c", script], cwd=ROOT, env=env,
        capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stderr
    payload = __import__("json").loads(result.stdout)
    rows = {row[0]: (row[1], row[2]) for row in payload["users"]}
    assert rows["legacy-admin@example.test"] == ("existing-hash", "ADMIN")
    assert rows["staff@example.test"] == ("opaque", "STAFF")
    assert payload["links"] == [[1, 1]]
    assert payload["fk_errors"] == []
