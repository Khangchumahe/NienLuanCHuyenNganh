
import json
import subprocess

BASE_URL = "http://127.0.0.1:5000"

# Lay CSRF token cua Admin dang dang nhap
result = subprocess.check_output([
    "curl.exe", "-s",
    "-b", "admin_cookies.txt",
    BASE_URL + "/api/auth/me"
])

data = json.loads(result)

if not data.get("success") or data.get("user", {}).get("role") != "ADMIN":
    raise SystemExit("Admin chua dang nhap!")

csrf_token = data["csrf_token"]

# Du lieu san pham mau
product = {
    "category_id": 1,
    "name": "Ao Polo Nam Basic",
    "slug": "ao-polo-nam-basic-test",
    "price": 350000,
    "discount_price": 299000,
    "material": "Cotton",
    "description": "Ao polo nam phu hop di hoc va di lam",
    "style": "Casual",
    "size_guide": "S M L XL",
    "image_url": ""
}

# Gui yeu cau them san pham

result = subprocess.run([
    "curl.exe",
    "-i",
    "--fail-with-body",
    "-b", "admin_cookies.txt",
    "-X", "POST",
    BASE_URL + "/api/admin/products",
    "-H", "Content-Type: application/json",
    "-H", "X-CSRF-Token: " + csrf_token,
    "-d", json.dumps(product)
], capture_output=True, text=True)

print("=== KET QUA API ===")
print(result.stdout)
print("=== LOI CURL (NEU CO) ===")
print(result.stderr)
print("Ma thoat curl:", result.returncode)
