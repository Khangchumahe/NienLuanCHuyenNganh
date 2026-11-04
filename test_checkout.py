
import json
import urllib.request
import urllib.error
from database.db import get_db_connection

URL = "http://127.0.0.1:5000/api/orders/checkout"
VARIANT_ID = 32

# Kiem tra ton kho va don hang truoc khi dat
conn = get_db_connection()
stock_before = conn.execute(
    "SELECT stock_quantity FROM product_variants WHERE id = ?",
    (VARIANT_ID,)
).fetchone()

if stock_before is None:
    conn.close()
    raise SystemExit("Khong tim thay bien the ID 32!")

orders_before = conn.execute(
    "SELECT COUNT(*) FROM orders"
).fetchone()[0]
conn.close()

print("Ton kho ban dau:", stock_before["stock_quantity"])
print("So don hang ban dau:", orders_before)

if input("Tao 1 don hang thu nghiem? (yes/no): ").strip().lower() != "yes":
    raise SystemExit("Da huy thao tac.")

# Du lieu checkout
payload = {
    "customer": {
        "name": "Nguyen Van A",
        "phone": "0901234567",
        "address": "123 Duong Mau, Can Tho"
    },
    "items": [
        {
            "variant_id": VARIANT_ID,
            "quantity": 1
        }
    ],
    "payment_method": "VIRTUAL_SANDBOX"
}

body = json.dumps(payload).encode("utf-8")

request = urllib.request.Request(
    URL,
    data=body,
    headers={"Content-Type": "application/json"},
    method="POST"
)

try:
    with urllib.request.urlopen(request, timeout=15) as response:
        print("HTTP status:", response.status)
        print("API response:", response.read().decode("utf-8"))
except urllib.error.HTTPError as error:
    print("HTTP error:", error.code)
    print(error.read().decode("utf-8"))
    raise SystemExit("Checkout khong thanh cong.")
except urllib.error.URLError as error:
    raise SystemExit(f"Khong ket noi duoc Flask: {error}")

# Kiem tra lai SQLite
conn = get_db_connection()

stock_after = conn.execute(
    "SELECT stock_quantity FROM product_variants WHERE id = ?",
    (VARIANT_ID,)
).fetchone()

orders = conn.execute(
    """SELECT id, order_code, status, total_amount
       FROM orders ORDER BY id DESC LIMIT 3"""
).fetchall()

conn.close()

print("Ton kho sau checkout:", stock_after["stock_quantity"])
print("Don hang moi nhat:", [dict(o) for o in orders])
