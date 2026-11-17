import json
from pathlib import Path

from services.chat_support import SHIPPING_POLICY, RETURN_POLICY, store_answer


def test_store_policy_answers_are_loaded_from_the_shared_json_configuration():
    policy_file = Path(__file__).resolve().parents[1] / "config" / "store_policies.json"
    policies = json.loads(policy_file.read_text(encoding="utf-8"))
    expected_return = "AURA hỗ trợ đổi trả trong 7 ngày với sản phẩm còn nguyên tem mác."
    expected_shipping = "AURA miễn phí vận chuyển cho đơn từ 500.000đ."

    assert policies["return_policy"] == expected_return
    assert policies["shipping_policy"] == expected_shipping
    assert RETURN_POLICY == expected_return
    assert SHIPPING_POLICY == expected_shipping
    assert store_answer("doi tra trong bao lau") == expected_return
    assert store_answer("mien phi van chuyen tu bao nhieu") == expected_shipping
