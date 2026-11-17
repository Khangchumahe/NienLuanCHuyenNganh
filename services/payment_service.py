"""
ZaloPay & MoMo Virtual Payment Sandbox Simulator
Tích hợp chuẩn cổng thanh toán chính thức của ZaloPay & MoMo Sandbox:
- AppID, Key1, Key2 theo tài liệu nhà phát hành ZaloPay
- Sinh chữ ký điện tử HMAC-SHA256 (MAC) theo chuẩn giao thức ZaloPay & Webhook IPN
- Tích hợp bộ thẻ tín dụng mẫu có sẵn (Visa, Mastercard, JCB, Napas ATM, Ví ZaloPay QR)
- Xác thực 3D-Secure OTP và kiểm tra tính toàn vẹn giao dịch
"""

import hashlib
import hmac
import json
import logging
import os
import re
import secrets
import time
from datetime import datetime
from database.db import sp_process_payment_webhook

_development = os.environ.get('APP_ENV', '').lower() == 'development'

logger = logging.getLogger(__name__)


def _load_payment_keys():
    names = ('SECRET_KEY', 'ZALOPAY_KEY1', 'ZALOPAY_KEY2')
    keys = {name: os.environ.get(name, '').strip() for name in names}
    missing = [name for name, value in keys.items() if not value]
    if missing and not _development:
        raise RuntimeError(
            'Thiếu cấu hình khóa bắt buộc: ' + ', '.join(missing)
        )
    if missing:
        for name in missing:
            keys[name] = secrets.token_hex(32)
        logger.warning(
            'Thiếu khóa thanh toán trong môi trường development (%s); '
            'đã sinh khóa tạm thời riêng cho tiến trình.', ', '.join(missing)
        )
    return keys


_PAYMENT_KEYS = _load_payment_keys()

# Sandbox credentials are supplied through the environment. The development app
# keeps the simulator usable without credentials; it does not call the gateway.
ZALOPAY_SANDBOX_CONFIG = {
    "app_id": int(os.environ.get('ZALOPAY_APP_ID') or (2553 if _development else 0)),
    "key1": _PAYMENT_KEYS['ZALOPAY_KEY1'],
    "key2": _PAYMENT_KEYS['ZALOPAY_KEY2'],
    "endpoint": "https://sb-openapi.zalopay.vn/v2/create",
    "gateway_name": "ZaloPay Sandbox Gateway",
    "version": "2.0"
}

# Cấu hình MoMo Sandbox
MOMO_SANDBOX_CONFIG = {
    "partner_code": os.environ.get('MOMO_PARTNER_CODE', 'MOMO' if _development else ''),
    "access_key": os.environ.get('MOMO_ACCESS_KEY', ''),
    "secret_key": os.environ.get('MOMO_SECRET_KEY', ''),
    "endpoint": "https://test-payment.momo.vn/v2/gateway/api/create"
}

# Key bảo mật mặc định dự phòng cho checksum
SECRET_KEY = _PAYMENT_KEYS['SECRET_KEY']

# =====================================================================
# DANH SÁCH THẺ TÍN DỤNG & TÀI KHOẢN MẪU HOẠT ĐỘNG ĐƯỢC (TEST CARDS)
# =====================================================================
OFFICIAL_TEST_CARDS = [
    {
        "id": "visa_success",
        "category": "CREDIT",
        "brand": "Visa",
        "card_number": "4111 1111 1111 1111",
        "card_holder": "NGUYEN VAN A",
        "expiry_date": "12/28",
        "cvv": "123",
        "otp": "111111",
        "issuer": "Vietcombank Visa Platinum",
        "description": "Thẻ Visa Quốc Tế (Kịch bản thanh toán THÀNH CÔNG)",
        "behavior": "SUCCESS",
        "badge_color": "#1a1f71",
        "icon": "fa-brands fa-cc-visa"
    },
    {
        "id": "mastercard_success",
        "category": "CREDIT",
        "brand": "Mastercard",
        "card_number": "5555 5555 5555 5555",
        "card_holder": "TRAN THI B",
        "expiry_date": "10/27",
        "cvv": "456",
        "otp": "111111",
        "issuer": "Techcombank Mastercard World",
        "description": "Thẻ Mastercard Quốc Tế (Kịch bản thanh toán THÀNH CÔNG)",
        "behavior": "SUCCESS",
        "badge_color": "#eb001b",
        "icon": "fa-brands fa-cc-mastercard"
    },
    {
        "id": "jcb_success",
        "category": "CREDIT",
        "brand": "JCB",
        "card_number": "3528 0000 0000 0000",
        "card_holder": "LE VAN C",
        "expiry_date": "08/29",
        "cvv": "789",
        "otp": "111111",
        "issuer": "ACB JCB Ultimate",
        "description": "Thẻ JCB Quốc Tế (Kịch bản thanh toán THÀNH CÔNG)",
        "behavior": "SUCCESS",
        "badge_color": "#007940",
        "icon": "fa-brands fa-cc-jcb"
    },
    {
        "id": "napas_ncb_success",
        "category": "ATM",
        "brand": "Napas",
        "card_number": "9704 1985 2619 1432 198",
        "card_holder": "NGUYEN VAN A",
        "expiry_date": "07/30",
        "cvv": "",
        "otp": "123456",
        "issuer": "Ngân hàng Quốc Dân (NCB)",
        "description": "Thẻ ATM Nội địa Napas NCB (Mẫu chính thức Napas Sandbox)",
        "behavior": "SUCCESS",
        "badge_color": "#0284c7",
        "icon": "fa-solid fa-credit-card"
    },
    {
        "id": "napas_vcb_success",
        "category": "ATM",
        "brand": "Napas",
        "card_number": "9704 3666 1234 5678",
        "card_holder": "NGUYEN VAN A",
        "expiry_date": "03/30",
        "cvv": "",
        "otp": "123456",
        "issuer": "Ngân hàng Ngoại Thương (Vietcombank)",
        "description": "Thẻ ATM Nội địa Vietcombank Napas",
        "behavior": "SUCCESS",
        "badge_color": "#16a34a",
        "icon": "fa-solid fa-credit-card"
    },
    {
        "id": "visa_declined",
        "category": "CREDIT",
        "brand": "Visa",
        "card_number": "4000 0000 0000 0002",
        "card_holder": "HOANG VAN TEST",
        "expiry_date": "12/28",
        "cvv": "123",
        "otp": "111111",
        "issuer": "Demo Card - Lỗi tài khoản",
        "description": "Thẻ lỗi mô phỏng: Từ chối do số dư không đủ (Kiểm tra Rollback kho)",
        "behavior": "INSUFFICIENT_FUNDS",
        "badge_color": "#dc2626",
        "icon": "fa-brands fa-cc-visa"
    }
]

OFFICIAL_WALLETS = [
    {
        "id": "zalopay_wallet",
        "name": "Ví điện tử ZaloPay",
        "phone": "0912345678",
        "balance": "5.000.000 VNĐ",
        "otp": "111111",
        "behavior": "SUCCESS"
    },
    {
        "id": "momo_wallet",
        "name": "Ví điện tử MoMo",
        "phone": "0909999888",
        "balance": "8.500.000 VNĐ",
        "otp": "111111",
        "behavior": "SUCCESS"
    }
]

# =====================================================================
# HÀM TẠO CHỮ KÝ SỐ MAC THEO CHUẨN ZALOPAY & VNPAY/MOMO
# =====================================================================
def generate_zalopay_mac(app_id, app_trans_id, app_user, amount, app_time, embed_data, item, key=None):
    """
    Tạo chữ ký MAC HMAC-SHA256 chuẩn ZaloPay v2:
    Format: app_id|app_trans_id|app_user|amount|app_time|embed_data|item
    """
    key = key or ZALOPAY_SANDBOX_CONFIG["key1"]
    embed_str = json.dumps(embed_data) if isinstance(embed_data, dict) else str(embed_data)
    item_str = json.dumps(item) if isinstance(item, list) else str(item)
    data = f"{app_id}|{app_trans_id}|{app_user}|{amount}|{app_time}|{embed_str}|{item_str}"
    mac = hmac.new(key.encode('utf-8'), data.encode('utf-8'), hashlib.sha256).hexdigest()
    return mac

def verify_zalopay_callback_mac(data_str, received_mac, key=None):
    """Kiểm tra chữ ký MAC trả về từ Webhook IPN bằng Key2 của ZaloPay"""
    key = key or ZALOPAY_SANDBOX_CONFIG["key2"]
    expected_mac = hmac.new(key.encode('utf-8'), data_str.encode('utf-8'), hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected_mac, received_mac)

def generate_checksum(transaction_code, amount):
    """Tạo chữ ký số mô phỏng nhanh để bảo mật dữ liệu giao dịch"""
    data = f"{transaction_code}|{amount}|{SECRET_KEY}"
    return hashlib.sha256(data.encode('utf-8')).hexdigest()

def verify_checksum(transaction_code, amount, received_checksum):
    """Kiểm tra chữ ký số chống giả mạo giao dịch"""
    expected = generate_checksum(transaction_code, amount)
    return hmac.compare_digest(expected, received_checksum)

# =====================================================================
# TẠO ĐƠN HÀNG THANH TOÁN CHUẨN ZALOPAY SANDBOX
# =====================================================================
def create_zalopay_order_payload(order_code, transaction_code, amount, customer_info=None, items=None):
    """
    Tạo payload đơn hàng ZaloPay chuẩn định dạng SDK `zalopay.js`:
    ZaloPay.payOrder({ appid, apptransid, mac, amount, zptranstoken, ... })
    """
    customer_info = customer_info or {}
    app_id = ZALOPAY_SANDBOX_CONFIG["app_id"]
    
    # Định dạng apptransid của ZaloPay: yyMMdd_xxxxxx
    now = datetime.now()
    yyMMdd = now.strftime("%y%m%d")
    clean_trans = transaction_code.replace("-", "").replace("_", "")[-6:]
    app_trans_id = f"{yyMMdd}_{clean_trans}"
    
    app_time = int(time.time() * 1000)
    app_user = customer_info.get("name", "DemoCustomer")
    
    embed_data = {
        "redirecturl": "http://127.0.0.1:5000/",
        "order_code": order_code,
        "transaction_code": transaction_code
    }
    item_data = items if items else [{"itemid": order_code, "itemname": "Thời trang AURA", "itemprice": amount, "itemquantity": 1}]
    
    mac = generate_zalopay_mac(
        app_id=app_id,
        app_trans_id=app_trans_id,
        app_user=app_user,
        amount=amount,
        app_time=app_time,
        embed_data=embed_data,
        item=item_data
    )
    
    zp_trans_token = f"zp_tok_{hashlib.md5(f'{app_trans_id}_{app_time}'.encode()).hexdigest()[:20]}"
    
    return {
        "appid": app_id,
        "apptransid": app_trans_id,
        "appuser": app_user,
        "apptime": app_time,
        "amount": amount,
        "description": f"Thanh toán đơn hàng #{order_code} tại AURA FASHION",
        "embeddata": json.dumps(embed_data),
        "item": json.dumps(item_data),
        "mac": mac,
        "zptranstoken": zp_trans_token,
        "orderurl": f"https://sbgateway.zalopay.vn/pay?token={zp_trans_token}",
        "test_cards": OFFICIAL_TEST_CARDS,
        "test_wallets": OFFICIAL_WALLETS,
        "gateway_info": {
            "name": ZALOPAY_SANDBOX_CONFIG["gateway_name"],
            "version": ZALOPAY_SANDBOX_CONFIG["version"],
            "key1_masked": ZALOPAY_SANDBOX_CONFIG["key1"][:6] + "..." + ZALOPAY_SANDBOX_CONFIG["key1"][-4:]
        }
    }

# =====================================================================
# XỬ LÝ THANH TOÁN BẰNG THẺ TÍN DỤNG MẪU HOẶC VÍ ĐIỆN TỬ
# =====================================================================
def _luhn_valid(number):
    if not number.isdigit() or not 12 <= len(number) <= 19:
        return False
    digits = [int(value) for value in number]
    checksum = 0
    for index, value in enumerate(reversed(digits)):
        if index % 2:
            value *= 2
            if value > 9:
                value -= 9
        checksum += value
    return checksum % 10 == 0


def _expiry_is_valid(expiry, today=None):
    match = re.fullmatch(r'(0[1-9]|1[0-2])/(\d{2}|\d{4})', str(expiry or '').strip())
    if not match:
        return False
    month = int(match.group(1))
    year_text = match.group(2)
    year = int(year_text) + (2000 if len(year_text) == 2 else 0)
    current = today or datetime.now()
    return (year, month) >= (current.year, current.month)


def process_card_or_wallet_payment(transaction_code, payment_type, card_data=None, wallet_data=None, otp="", *, customer_user_id):
    """
    Xác thực và xử lý thanh toán qua thẻ tín dụng/ghi nợ mẫu hoặc ví ZaloPay/MoMo:
    - Kiểm tra số thẻ, hạn thẻ, CVV và OTP 3D-Secure
    - Nếu khớp với thẻ từ chối (insufficient funds) -> trả về mã lỗi
    - Nếu thành công -> gọi Stored Procedure cập nhật đơn hàng thành PAID
    """
    if payment_type == 'WALLET':
        phone = (wallet_data or {}).get('phone', '')
        wallet = next((item for item in OFFICIAL_WALLETS if item['phone'] == phone), None)
        if not wallet:
            return {'success': False, 'error_code': 'INVALID_WALLET', 'message': 'Ví thanh toán không hợp lệ.'}
        expected_otp = wallet['otp']
        card_brand = wallet['name']
    else:
        if payment_type not in ('ATM', 'CREDIT', 'CREDIT_CARD') or not isinstance(card_data, dict):
            return {'success': False, 'error_code': 'INVALID_CARD', 'message': 'Thông tin thẻ thanh toán không hợp lệ.'}
        raw_number = card_data.get('card_number')
        cleaned_card_num = re.sub(r'[\s-]', '', raw_number) if isinstance(raw_number, str) else ''
        category = 'ATM' if payment_type == 'ATM' else 'CREDIT'
        sample = next((item for item in OFFICIAL_TEST_CARDS
                       if item['category'] == category
                       and re.sub(r'[\s-]', '', item['card_number']) == cleaned_card_num), None)
        if not sample or (category == 'CREDIT' and not _luhn_valid(cleaned_card_num)):
            return {'success': False, 'error_code': 'INVALID_CARD', 'message': 'Số thẻ không khớp thẻ mẫu được hỗ trợ.'}
        if not _expiry_is_valid(card_data.get('expiry_date')):
            return {'success': False, 'error_code': 'EXPIRED_CARD', 'message': 'Thẻ đã hết hạn hoặc ngày hết hạn không hợp lệ.'}
        if category == 'CREDIT' and card_data.get('cvv') != sample.get('cvv'):
            return {'success': False, 'error_code': 'INVALID_CVV', 'message': 'Mã bảo mật CVV không chính xác.'}
        expected_otp = sample['otp']
        card_brand = sample['brand']

    if str(otp) != expected_otp:
        return {
            'success': False, 'error_code': 'INVALID_OTP',
            'message': 'Mã OTP không chính xác. Vui lòng dùng mã mẫu đúng với phương thức đã chọn.',
        }

    if payment_type != 'WALLET' and sample.get('behavior') == 'INSUFFICIENT_FUNDS':
        return {
            "success": False,
            "error_code": "INSUFFICIENT_FUNDS",
            "message": "Giao dịch bị từ chối: Số dư trong tài khoản thẻ không đủ để thanh toán (Kịch bản Test từ chối thẻ)!"
        }

    # 3. Kích hoạt Stored Procedure & Trigger cập nhật Database
    result = sp_process_payment_webhook(transaction_code, "SUCCESS", customer_user_id=customer_user_id)
    if result["success"]:
        return {
            "success": True,
            "message": "Thanh toán thành công qua cổng Sandbox chính thức!",
            "transaction_code": transaction_code,
            "order_id": result["order_id"],
            "payment_type": payment_type,
            "card_brand": card_brand
        }
    else:
        return {
            "success": False,
            "error_code": result.get("error_code", "DATABASE_ERROR"),
            "message": result.get("error", "Lỗi cập nhật trạng thái cơ sở dữ liệu")
        }

def process_mock_payment_callback(transaction_code, status="SUCCESS", *, customer_user_id):
    """
    Xử lý phản hồi từ cổng thanh toán ảo:
    Gọi Stored Procedure để cập nhật trạng thái đơn hàng và kích hoạt Trigger
    """
    result = sp_process_payment_webhook(transaction_code, status, customer_user_id=customer_user_id)
    return result
