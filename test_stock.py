
import json
import subprocess
from database.db import get_db_connection

BASE_URL = "http://127.0.0.1:5000"
VARIANT_ID = 1

# 1. Kiem tra so luong ton kho ban dau
conn = get_db_connection()
row = conn.execute(
    "SELECT stock_quantity FROM product_variants WHERE id = ?",
    (VARIANT_ID,)
).fetchone()
conn.close()

if row is None:
    raise SystemExit("Khong tim thay bien the ID 1!")

old_stock = row["stock_quantity"]
new_stock = old_stock + 5

print("Ton kho ban dau:", old_stock)
print("Ton kho moi:", new_stock)

# 2. Lay CSRF cua Admin
result = subprocess.check_output([
    "curl.exe", "-sS",
    "-b", "admin_cookies.txt",
    BASE_URL + "/api/auth/me"
])

data = json.loads(result)

if not data.get("success") or data.get("user", {}).get("role") != "ADMIN":
    raise SystemExit("Admin chua dang nhap!")

csrf_token = data["csrf_token"]

# 3. Gui yeu cau cap nhat ton kho
response = subprocess.run([
    "curl.exe",
    "-sS",
    "-i",
    "--fail-with-body",
    "-b", "admin_cookies.txt",
    "-X", "PATCH",
    BASE_URL + f"/api/admin/variants/{VARIANT_ID}/stock",
    "-H", "Content-Type: application/json",
    "-H", "X-CSRF-Token: " + csrf_token,
    "-d", json.dumps({"stock_quantity": new_stock})
], capture_output=True, text=True)

print("=== KET QUA API ===")
print(response.stdout)
print(response.stderr)

# 4. Kiem tra lai SQLite va Trigger
conn = get_db_connection()

stock = conn.execute(
    "SELECT stock_quantity FROM product_variants WHERE id = ?",
    (VARIANT_ID,)
).fetchone()

logs = conn.execute(
    """SELECT id, variant_id, change_quantity,
              remaining_stock, reason
       FROM inventory_logs
       WHERE variant_id = ?
       ORDER BY id DESC LIMIT 1""",
    (VARIANT_ID,)
).fetchone()

conn.close()

print("Ton kho trong SQL:", stock["stock_quantity"])
print("Log Trigger:", dict(logs) if logs else None)
