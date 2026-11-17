import json
import os
import sqlite3
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _run_app_against_database(database_path):
    env = os.environ.copy()
    env.update({
        "AURA_DB_PATH": str(database_path),
        "APP_ENV": "test",
        "SECRET_KEY": "schema-bootstrap-test-secret",
        "FLASK_SECRET_KEY": "schema-bootstrap-test-secret",
        "ZALOPAY_KEY1": "schema-bootstrap-key1",
        "ZALOPAY_KEY2": "schema-bootstrap-key2",
        "GEMINI_API_KEY": "",
        "FLASK_DEBUG": "0",
        "PYTHON_DOTENV_DISABLED": "1",
    })
    script = r'''
import json, os, sqlite3
path = os.environ["AURA_DB_PATH"]
def counts():
    con = sqlite3.connect(path)
    names = [r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")]
    result = {name: con.execute('SELECT COUNT(*) FROM "' + name + '"').fetchone()[0] for name in names}
    con.close()
    return result
before = counts()
import app
response = app.app.test_client().get('/api/products')
after = counts()
print(json.dumps({"status": response.status_code, "before": before, "after": after}))
'''
    return subprocess.run(
        [sys.executable, "-c", script], cwd=ROOT, env=env,
        capture_output=True, text=True,
    )


def test_app_bootstraps_legacy_head_database_without_losing_existing_rows(tmp_path):
    legacy_db = tmp_path / "legacy-store.db"
    with legacy_db.open("wb") as output:
        result = subprocess.run(
            ["git", "show", "HEAD:database/store.db"], cwd=ROOT,
            stdout=output, stderr=subprocess.PIPE, check=False,
        )
    assert result.returncode == 0, result.stderr.decode(errors="replace")

    with sqlite3.connect(legacy_db) as conn:
        tables = {row[0] for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )}
        assert "customer_order_links" not in tables
        # Keep app startup focused on schema repair; otherwise the normal lazy
        # expiry of aged pending demo orders legitimately adds audit rows.
        if "orders" in tables:
            conn.execute(
                "UPDATE orders SET created_at='2999-01-01 00:00:00' "
                "WHERE status='PENDING_PAYMENT'"
            )
            conn.commit()
        original_counts = {
            table: conn.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0]
            for table in tables if not table.startswith("sqlite_")
        }

    result = _run_app_against_database(legacy_db)
    assert result.returncode == 0, result.stderr
    output = json.loads(result.stdout.strip().splitlines()[-1])
    assert output["status"] == 200
    assert {key: output["after"][key] for key in original_counts} == original_counts
    assert "customer_order_links" in output["after"]


def test_app_bootstraps_an_existing_empty_sqlite_database(tmp_path):
    empty_db = tmp_path / "empty-store.db"
    sqlite3.connect(empty_db).close()

    result = _run_app_against_database(empty_db)
    assert result.returncode == 0, result.stderr
    output = json.loads(result.stdout.strip().splitlines()[-1])
    assert output["status"] == 200
    assert "customer_order_links" in output["after"]
