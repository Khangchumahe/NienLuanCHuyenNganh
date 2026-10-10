"""
Virtual Payment Sandbox Simulator
Mô phỏng cổng thanh toán trực tuyến (tương tự VNPAY/MoMo/Stripe Test)
Hỗ trợ: Sinh mã giao dịch, tạo chữ ký số HMAC-SHA256, kiểm tra tính toàn vẹn và Webhook IPN
"""

import hashlib
import hmac
import time
from database.db import sp_process_payment_webhook

SECRET_KEY = "NIEN_LUAN_CHUYEN_NGANH_SANDBOX_SECRET_KEY_2026"

def generate_checksum(transaction_code, amount):
    """Tạo chữ ký số mô phỏng để bảo mật dữ liệu giao dịch"""
    data = f"{transaction_code}|{amount}|{SECRET_KEY}"
    return hashlib.sha256(data.encode('utf-8')).hexdigest()

def verify_checksum(transaction_code, amount, received_checksum):
    """Kiểm tra chữ ký số chống giả mạo giao dịch"""
    expected = generate_checksum(transaction_code, amount)
    return hmac.compare_digest(expected, received_checksum)

def process_mock_payment_callback(transaction_code, status="SUCCESS"):
    """
    Xử lý phản hồi từ cổng thanh toán ảo:
    Gọi Stored Procedure để cập nhật trạng thái đơn hàng và kích hoạt Trigger
    """
    result = sp_process_payment_webhook(transaction_code, status)
    return result
