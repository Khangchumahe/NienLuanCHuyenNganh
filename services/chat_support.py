"""Short answers for shop information that does not require a product search."""

import os
import re

INTRODUCTION = "Mình là AURA Stylist, trợ lý ảo AI của AURA. Mình hỗ trợ tìm quần áo, chọn size, kiểm tra tồn kho và tra cứu thông tin mua hàng."
RETURN_POLICY = "AURA hỗ trợ đổi trả trong 7 ngày với sản phẩm còn nguyên tem mác."
SHIPPING_POLICY = "AURA miễn phí vận chuyển cho đơn từ 500.000đ."
SENSITIVE_CARD = re.compile(r"\b(?:so the|the tin dung|card number|credit card)\b.*(?:\d[ -]?){13,19}")
RETURN_QUESTION = re.compile(
    r"\b(?:doi (?:tra|cha|hang|size|duoc|ko|khong)|tra (?:hang|duoc)|hoan tien|"
    r"doi ao|return policy|bung chi|loi (?:san pham|nha san xuat)|giao sai|nhan .*sai (?:mau|size)|"
    r"doi .*hoa don|hoa don .*doi)\b"
)
PROMOTION_QUESTION = re.compile(
    r"\b(?:khuyen mai|giam gia|uu dai|voucher|black friday|thanh vien|tich luy|welcome50|"
    r"hang (?:gold|silver|diamond|platinum)|gold|silver|diamond|platinum|sale|ma sinh nhat|giam \d+.*cua hang)\b"
)


def support_contact():
    phone = os.environ.get("AURA_SUPPORT_PHONE", "").strip()
    if phone:
        return f"Bạn có thể gọi {phone} để gặp nhân viên AURA."
    return "AURA chưa công bố kênh gặp nhân viên trong hệ thống. Nếu cần kiểm tra giao dịch, bạn có thể vào mục Đơn hàng trong tài khoản."


def identity_answer(text):
    if not text or re.fullmatch(r"(?:xin )?chao(?: ban| shop| aura)?|hello|hi", text):
        return "Chào bạn! Mình là AURA Stylist. Bạn cần mình hỗ trợ gì ạ?"
    if re.search(r"\b(?:tu gio .*ten la|tu bay gio .*ten la|doi ten|nhap vai|nhu nguoi yeu)\b", text):
        return "Mình vẫn là AURA Stylist và chỉ hỗ trợ mua sắm tại AURA nhé."
    if re.search(r"\b(?:nguoi that hay may|co phai nguoi that|la nguoi that|la robot|(?:ban|may|em|bot|aura stylist) la ai|ai tao ra|chatgpt|co cam xuc)\b", text):
        if "co cam xuc" in text:
            return "Mình là trợ lý AI nên không có cảm xúc như con người. Bạn cần hỗ trợ mua sắm gì ạ?"
        if "nguoi that" in text or "la robot" in text:
            phone = os.environ.get("AURA_SUPPORT_PHONE", "").strip()
            contact = f" Bạn có thể gọi {phone} nếu muốn gặp nhân viên." if phone else " AURA chưa công bố hotline trong hệ thống."
            return "Mình là AURA Stylist, trợ lý ảo AI của AURA." + contact
        return INTRODUCTION
    if re.search(r"\b(?:giup .*nhung gi|ho tro .*nhung gi|lam duoc gi|ho tro gi)\b", text):
        return "Mình hỗ trợ tìm sản phẩm, chọn size, kiểm tra còn hàng, tra cứu đơn và giải đáp về đổi trả, ưu đãi, giao hàng, thanh toán, cửa hàng."
    return None


def store_answer(text, previous=""):
    if re.search(r"\b(?:hotline|instagram|fanpage|email|gio mo cua|mo cua|dia chi|chi nhanh|cua hang o dau|nhan vien that)\b", text):
        if "nhan vien that" in text:
            return support_contact()
        if "hotline" in text:
            phone = os.environ.get("AURA_SUPPORT_PHONE", "").strip()
            return f"Hotline AURA là {phone}." if phone else "AURA chưa công bố số hotline trong hệ thống."
        if "mo cua" in text:
            return "AURA chưa công bố giờ mở cửa hoặc lịch ngày lễ trong hệ thống."
        if "dia chi" in text or "chi nhanh" in text or "cua hang o dau" in text:
            return "AURA chưa công bố địa chỉ chi nhánh trong hệ thống."
        return "AURA chưa công bố kênh liên hệ bạn hỏi trong hệ thống."

    if RETURN_QUESTION.search(text) or ("hang sale" in text and RETURN_QUESTION.search(previous)):
        if "return policy" in text:
            return "AURA accepts returns within 7 days for items with their original tags. Further conditions have yet to be published."
        if re.search(r"\b(?:bung chi|loi (?:san pham|nha san xuat)|giao sai|nhan .*sai (?:mau|size))\b", text):
            return "Bạn giữ ảnh sản phẩm và mã đơn để AURA kiểm tra lỗi hoặc giao sai nhé. Hệ thống chưa có thông tin về thời hạn và phí xử lý riêng."
        if re.search(r"\b(?:hoan tien|tien hoan|mat hoa don|mua online|mat phi|do boi|sale|giam \d+|doi size|\d+ ngay)\b", text):
            return RETURN_POLICY + " Chi tiết về trường hợp này cần được xác nhận theo đơn hàng."
        return RETURN_POLICY

    if "freeship" in text or "mien phi van chuyen" in text:
        return SHIPPING_POLICY
    if re.search(r"\b(?:thanh toan|tra gop)\b", text) and "kiem hang" not in text:
        if "tra gop" in text:
            return "AURA chưa có thông tin về trả góp. Website hiện hỗ trợ thanh toán mô phỏng khi đặt hàng."
        return "Website hiện hỗ trợ thanh toán mô phỏng trong luồng đặt hàng."
    if re.search(r"\b(?:ship|van chuyen|giao hang|giao noi thanh|kiem hang)\b", text):
        if re.search(r"\b(?:tre|qua te|qua lau)\b", text):
            return "Mình hiểu bạn đang chờ đơn. Bạn gửi mã ORD- để mình kiểm tra, hoặc xem mục Đơn hàng trong tài khoản AURA nhé."
        return "AURA chưa có thông tin xác nhận về phí, thời gian hoặc điều kiện giao hàng cho trường hợp bạn hỏi."
    if re.search(r"\bdon [a-z]+\d+\b", text):
        return "Bạn tra cứu trong mục Đơn hàng hoặc gửi mã AURA bắt đầu bằng ORD- để mình kiểm tra nhé."
    if PROMOTION_QUESTION.search(text):
        if "diem tich luy" in text:
            return "AURA chưa công bố quy định về thời hạn điểm tích lũy trong hệ thống."
        return "Bạn có thể xem giá ưu đãi đang hiển thị trên từng sản phẩm. AURA chưa có thông tin xác nhận về chương trình hoặc mã bạn hỏi."
    if re.search(r"\b(?:tra loi vo dung|bot gi ma ngu)\b", text):
        return "Bạn cho mình biết câu hỏi hoặc mẫu cần kiểm tra, mình sẽ hỗ trợ lại nhé."
    if re.search(r"\b(?:ceo|tong giam doc)\b", text):
        return "Mình chưa có thông tin xác nhận về người bạn hỏi."
    if re.search(r"\b(?:giat|bao quan)\b", text):
        if re.search(r"\blua\b", text):
            return "Bạn xem nhãn chăm sóc nhé. Với lụa, nên giặt tay nước lạnh, không vắt mạnh và phơi trong bóng râm."
        if re.search(r"\blen\b", text):
            return "Bạn xem nhãn chăm sóc nhé. Với len, nên giặt tay hoặc dùng túi giặt chế độ nhẹ, rồi phơi nằm ngang."
    return None
