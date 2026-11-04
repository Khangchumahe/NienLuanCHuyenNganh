"""One-time local test: creates only variants not already present."""
import json
import subprocess
from database.db import get_db_connection

BASE_URL = 'http://127.0.0.1:5000'
PRODUCT_ID = 9
samples = [
    {'sku': 'POLO-BLK-M', 'color': 'Đen', 'size': 'M', 'stock_quantity': 20},
    {'sku': 'POLO-BLK-L', 'color': 'Đen', 'size': 'L', 'stock_quantity': 15},
    {'sku': 'POLO-WHT-M', 'color': 'Trắng', 'size': 'M', 'stock_quantity': 10},
]

auth = json.loads(subprocess.check_output([
    'curl.exe', '-sS', '-b', 'admin_cookies.txt', BASE_URL + '/api/auth/me'
]))
if not auth.get('success') or auth.get('user', {}).get('role') != 'ADMIN':
    raise SystemExit('Admin chua dang nhap. Dang nhap lai de cap nhat admin_cookies.txt.')
token = auth['csrf_token']

for sample in samples:
    conn = get_db_connection()
    try:
        exists = conn.execute(
            'SELECT id FROM product_variants WHERE product_id=? AND (sku=? OR (lower(color)=lower(?) AND lower(size)=lower(?)))',
            (PRODUCT_ID, sample['sku'], sample['color'], sample['size'])
        ).fetchone()
    finally:
        conn.close()
    if exists:
        print('Bo qua da ton tai:', sample['sku'], 'id=', exists['id'])
        continue
    response = subprocess.run([
        'curl.exe', '-sS', '-b', 'admin_cookies.txt', '-X', 'POST',
        BASE_URL + f'/api/admin/products/{PRODUCT_ID}/variants',
        '-H', 'Content-Type: application/json',
        '-H', 'X-CSRF-Token: ' + token,
        '--data-binary', '@-'
    ], input=json.dumps(sample, ensure_ascii=False), capture_output=True, text=True, encoding='utf-8')
    if response.returncode:
        raise SystemExit('curl loi: ' + response.stderr)
   
print("=== KIEM TRA CURL ===")
print("Return code:", response.returncode)
print("STDOUT:", repr(response.stdout))
print("STDERR:", repr(response.stderr))

if response.returncode != 0 or not response.stdout.strip():
    raise SystemExit("API khong tra ve JSON hop le. Xem loi o tren.")

   
    answer = json.loads(response.stdout)
    print(sample['sku'], answer)
    if not answer.get('success'):
        raise SystemExit('Dung de kiem tra loi truoc khi tiep tuc.')

conn = get_db_connection()
try:
    rows = conn.execute('SELECT id, sku, color, size, stock_quantity FROM product_variants WHERE product_id=? ORDER BY id', (PRODUCT_ID,)).fetchall()
    print('Cac bien the trong SQL:', [dict(r) for r in rows])
finally:
    conn.close()
