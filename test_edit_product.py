
import json
import subprocess

BASE_URL = "http://127.0.0.1:5000"

# Lay thong tin Admin va CSRF token
result = subprocess.check_output([
    "curl.exe", "-s",
    "-b", "admin_cookies.txt",
    BASE_URL + "/api/auth/me"
])

data = json.loads(result)

if not data.get("success") or data.get("user", {}).get("role") != "ADMIN":
    raise SystemExit("Admin chua dang nhap!")

csrf_token = data["csrf_token"]

# Cap nhat gia san pham ID 9
product_update = {
    "price": 320000,
    "discount_price": 299000
}

response = subprocess.run([
    "curl.exe",
    "-sS",
    "-i",
    "--fail-with-body",
    "-b", "admin_cookies.txt",
    "-X", "PUT",
    BASE_URL + "/api/admin/products/9",
    "-H", "Content-Type: application/json",
    "-H", "X-CSRF-Token: " + csrf_token,
    "-d", json.dumps(product_update)
], capture_output=True, text=True)

print(response.stdout)
print(response.stderr)
print("Ma thoat curl:", response.returncode)
