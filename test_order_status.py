
import json
import subprocess
from database.db import get_db_connection

BASE_URL = "http://127.0.0.1:5000"
ORDER_ID = 1

# Lay trang thai don hang hien tai
conn = get_db_connection()
order = conn.execute(
    "SELECT id, status FROM orders WHERE id = ?",
    (ORDER_ID,)
).fetchone()
conn.close()

if not order:
    raise SystemExit("Khong tim thay don hang!")

print("Trang thai hien tai:", order["status"])

# Lay CSRF token va kiem tra Admin
result = subprocess.check_output([
    "curl.exe", "-sS",
    "-b", "admin_cookies.txt",
    BASE_URL + "/api/auth/me"
])

data = json.loads(result)

if not data.get("success") or data.get("user", {}).get("role") != "ADMIN":
    raise SystemExit("Admin chua dang nhap!")

csrf_token = data["csrf_token"]

# Chon trang thai moi
if order["status"] == "PAID":
    new_status = "SHIPPING"
elif order["status"] == "SHIPPING":
    new_status = "DELIVERED"
else:
    raise SystemExit("Don hang khong o trang thai can kiem thu!")

print("Chuyen trang thai:", order["status"], "->", new_status)

if input("Xac nhan cap nhat? (yes/no): ").strip().lower() != "yes":
    raise SystemExit("Da huy thao tac.")

# Gui API cap nhat trang thai
response = subprocess.run([
    "curl.exe",
    "-sS",
    "-i",
    "--fail-with-body",
    "-b", "admin_cookies.txt",
    "-X", "PATCH",
    BASE_URL + f"/api/admin/orders/{ORDER_ID}/status",
    "-H", "Content-Type: application/json",
    "-H", "X-CSRF-Token: " + csrf_token,
    "-d", json.dumps({"status": new_status})
], capture_output=True, text=True)

print("=== KET QUA API ===")
print(response.stdout)
print(response.stderr)
print("Ma thoat curl:", response.returncode)

# Kiem tra lai trang thai va ton kho trong SQL
conn = get_db_connection()

updated = conn.execute(
    "SELECT id, status FROM orders WHERE id = ?",
    (ORDER_ID,)
).fetchone()

stock = conn.execute(
    "SELECT stock_quantity FROM product_variants WHERE id = 32"
).fetchone()

conn.close()

print("Don hang sau cap nhat:", dict(updated))
print("Ton kho hien tai:", stock["stock_quantity"])
