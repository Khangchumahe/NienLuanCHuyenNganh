
import json
import urllib.request
import urllib.error
from database.db import get_db_connection

URL = "http://127.0.0.1:5000/api/payment/simulate-callback"
ORDER_ID = 1

conn = get_db_connection()

payment = conn.execute(
    """SELECT transaction_code, status
       FROM payments
       WHERE order_id = ?
       ORDER BY id DESC LIMIT 1""",
    (ORDER_ID,)
).fetchone()

order = conn.execute(
    "SELECT id, status FROM orders WHERE id = ?",
    (ORDER_ID,)
).fetchone()

conn.close()

if not payment or not order:
    raise SystemExit("Khong tim thay don hang hoac giao dich!")

print("Order:", dict(order))
print("Payment:", dict(payment))

if order["status"] != "PENDING_PAYMENT" or payment["status"] != "PENDING":
    raise SystemExit("Don hang khong o trang thai cho thanh toan!")

if input("Xac nhan thanh toan thu nghiem? (yes/no): ").strip().lower() != "yes":
    raise SystemExit("Da huy.")

payload = {
    "transaction_code": payment["transaction_code"],
    "status": "SUCCESS"
}

request = urllib.request.Request(
    URL,
    data=json.dumps(payload).encode("utf-8"),
    headers={"Content-Type": "application/json"},
    method="POST"
)

try:
    with urllib.request.urlopen(request, timeout=15) as response:
        print("HTTP:", response.status)
        print(response.read().decode("utf-8"))
except urllib.error.HTTPError as error:
    print("HTTP error:", error.code)
    print(error.read().decode("utf-8"))
    raise SystemExit("Thanh toan khong thanh cong.")
except urllib.error.URLError as error:
    raise SystemExit(f"Khong ket noi duoc Flask: {error}")

conn = get_db_connection()

order_after = conn.execute(
    "SELECT id, status FROM orders WHERE id = ?",
    (ORDER_ID,)
).fetchone()

payment_after = conn.execute(
    "SELECT status FROM payments WHERE order_id = ? ORDER BY id DESC LIMIT 1",
    (ORDER_ID,)
).fetchone()

stock_after = conn.execute(
    "SELECT stock_quantity FROM product_variants WHERE id = 32"
).fetchone()

conn.close()

print("Order sau thanh toan:", dict(order_after))
print("Payment sau thanh toan:", dict(payment_after))
print("Ton kho sau thanh toan:", stock_after["stock_quantity"])
