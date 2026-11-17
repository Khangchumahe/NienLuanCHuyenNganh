from concurrent.futures import ThreadPoolExecutor
import re

import pytest

from database import db


def _user_id(email="review@example.test"):
    result = db.create_user(email, "review-password", "Review User")
    assert result["success"]
    return result["user_id"]


def _stock(variant_id=1):
    conn = db.get_db_connection()
    try:
        return conn.execute(
            "SELECT stock_quantity FROM product_variants WHERE id=?", (variant_id,)
        ).fetchone()[0]
    finally:
        conn.close()


def _order(user_id, items=None):
    return db.sp_create_order_and_deduct_stock(
        {"name": "Review User", "phone": "0900000000", "address": "Test address"},
        items or [{"variant_id": 1, "quantity": 1}],
        customer_user_id=user_id,
    )


def test_webhook_cancelled_is_idempotent_and_restores_stock_once():
    user_id = _user_id()
    starting_stock = _stock()
    order = _order(user_id)
    assert order["success"]
    after_order = _stock()

    first = db.sp_process_payment_webhook(
        order["transaction_code"], "CANCELLED", customer_user_id=user_id
    )
    second = db.sp_process_payment_webhook(
        order["transaction_code"], "CANCELLED", customer_user_id=user_id
    )

    assert first["success"]
    assert second["success"] and second["duplicate"] is True
    assert _stock() == starting_stock
    assert after_order == starting_stock - 1


def test_successful_payment_cannot_be_cancelled_by_later_callback():
    user_id = _user_id()
    order = _order(user_id)
    assert order["success"]

    paid = db.sp_process_payment_webhook(
        order["transaction_code"], "SUCCESS", customer_user_id=user_id
    )
    cancelled = db.sp_process_payment_webhook(
        order["transaction_code"], "CANCELLED", customer_user_id=user_id
    )

    conn = db.get_db_connection()
    try:
        order_status = conn.execute(
            "SELECT status FROM orders WHERE id=?", (order["order_id"],)
        ).fetchone()[0]
    finally:
        conn.close()
    assert paid["new_status"] == "PAID"
    assert cancelled["success"] and cancelled["duplicate"] is True
    assert cancelled["new_status"] == "PAID"
    assert order_status == "PAID"


@pytest.mark.parametrize("quantity", [-5, 0, "abc", 10**9, 1.5, True])
def test_invalid_quantities_are_rejected_without_changing_stock(quantity):
    before = _stock()
    result = db.sp_create_order_and_deduct_stock(
        {"name": "Review User"},
        [{"variant_id": 1, "quantity": quantity}],
    )
    assert not result["success"]
    assert _stock() == before


def test_duplicate_cart_lines_are_merged_before_stock_check():
    user_id = _user_id()
    before = _stock()
    result = _order(user_id, [
        {"variant_id": 1, "quantity": 1},
        {"variant_id": 1, "quantity": 1},
    ])
    assert result["success"]
    assert _stock() == before - 2
    conn = db.get_db_connection()
    try:
        rows = conn.execute(
            "SELECT quantity FROM order_items WHERE order_id=?", (result["order_id"],)
        ).fetchall()
    finally:
        conn.close()
    assert [row[0] for row in rows] == [2]


def test_order_and_transaction_codes_are_unique_uuid_based_values():
    user_id = _user_id()
    first = _order(user_id)
    second = _order(user_id)
    assert first["success"] and second["success"]
    assert re.fullmatch(r"ORD-[0-9A-F]{10}", first["order_code"])
    assert re.fullmatch(r"TRX-[0-9A-F]{10}", first["transaction_code"])
    assert first["order_code"] != second["order_code"]
    assert first["transaction_code"] != second["transaction_code"]


def test_simultaneous_checkout_cannot_oversell_single_unit():
    user_id = _user_id()
    conn = db.get_db_connection()
    try:
        conn.execute("UPDATE product_variants SET stock_quantity=1 WHERE id=1")
        conn.commit()
    finally:
        conn.close()

    def buy():
        return _order(user_id)

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: buy(), range(2)))
    assert sum(bool(result["success"]) for result in results) == 1
    assert _stock() == 0


def test_old_pending_order_is_cancelled_and_inventory_is_restored_lazily():
    user_id = _user_id()
    before = _stock()
    order = _order(user_id)
    assert order["success"]
    conn = db.get_db_connection()
    try:
        conn.execute(
            "UPDATE orders SET created_at='2000-01-01 00:00:00' WHERE id=?",
            (order["order_id"],),
        )
        conn.commit()
    finally:
        conn.close()

    db.get_all_products()
    db.get_all_products()
    assert _stock() == before
    conn = db.get_db_connection()
    try:
        statuses = conn.execute(
            "SELECT o.status, p.status FROM orders o JOIN payments p ON p.order_id=o.id WHERE o.id=?",
            (order["order_id"],),
        ).fetchone()
    finally:
        conn.close()
    assert tuple(statuses) == ("CANCELLED", "CANCELLED")


def test_admin_stats_and_rag_sync_require_existing_admin_role():
    from app import app

    client = app.test_client()
    assert client.get("/api/admin/stats").status_code == 401
    assert client.post("/api/ai/sync-rag", json={}).status_code == 401

    customer_id = _user_id()
    assert client.post("/api/auth/login", json={
        "email": "review@example.test", "password": "review-password"
    }).status_code == 200
    assert client.get("/api/admin/stats").status_code == 403

    conn = db.get_db_connection()
    try:
        conn.execute("UPDATE users SET role='ADMIN' WHERE id=?", (customer_id,))
        conn.commit()
    finally:
        conn.close()
    client.post("/api/auth/logout", headers={"X-CSRF-Token": ""})
    login = client.post("/api/auth/login", json={
        "email": "review@example.test", "password": "review-password"
    })
    csrf = login.get_json()["csrf_token"]
    assert client.get("/api/admin/stats").status_code == 200
    assert client.post("/api/ai/sync-rag", json={}, headers={"X-CSRF-Token": csrf}).status_code == 200


def test_simulated_payment_callback_requires_valid_checksum():
    from app import app
    from services.payment_service import generate_checksum

    user_id = _user_id()
    order = _order(user_id)
    client = app.test_client()
    client.post("/api/auth/login", json={
        "email": "review@example.test", "password": "review-password"
    })
    headers = {"X-CSRF-Token": ""}
    with client.session_transaction() as session:
        headers["X-CSRF-Token"] = session["csrf_token"]
    payload = {
        "transaction_code": order["transaction_code"],
        "status": "SUCCESS",
        "amount": order["total_amount"],
        "checksum": "invalid",
    }
    assert client.post("/api/payment/simulate-callback", json=payload, headers=headers).status_code == 403
    payload["checksum"] = generate_checksum(order["transaction_code"], order["total_amount"])
    assert client.post("/api/payment/simulate-callback", json=payload, headers=headers).status_code == 200


def test_sample_credit_card_checks_expiry_cvv_and_its_own_otp():
    from services import payment_service
    from unittest.mock import patch

    sample = payment_service.OFFICIAL_TEST_CARDS[0]
    card = {key: sample[key] for key in ("card_number", "card_holder", "expiry_date", "cvv", "brand")}
    with patch.object(payment_service, "sp_process_payment_webhook") as finalize:
        bad_cvv = payment_service.process_card_or_wallet_payment(
            "TRX-TEST", "CREDIT", {**card, "cvv": "999"}, otp="111111", customer_user_id=1
        )
        expired = payment_service.process_card_or_wallet_payment(
            "TRX-TEST", "CREDIT", {**card, "expiry_date": "01/20"}, otp="111111", customer_user_id=1
        )
        wrong_otp = payment_service.process_card_or_wallet_payment(
            "TRX-TEST", "CREDIT", card, otp="123456", customer_user_id=1
        )
    assert bad_cvv["error_code"] == "INVALID_CVV"
    assert expired["error_code"] == "EXPIRED_CARD"
    assert wrong_otp["error_code"] == "INVALID_OTP"
    finalize.assert_not_called()


def test_napas_card_requires_sample_match_and_napas_otp():
    from services import payment_service
    from unittest.mock import patch

    sample = next(card for card in payment_service.OFFICIAL_TEST_CARDS if card["category"] == "ATM")
    card = {key: sample[key] for key in ("card_number", "card_holder", "expiry_date", "brand")}
    with patch.object(payment_service, "sp_process_payment_webhook", return_value={
        "success": True, "order_id": 1, "new_status": "PAID", "duplicate": False,
    }) as finalize:
        wrong_otp = payment_service.process_card_or_wallet_payment(
            "TRX-TEST", "ATM", card, otp="111111", customer_user_id=1
        )
        accepted = payment_service.process_card_or_wallet_payment(
            "TRX-TEST", "ATM", card, otp="123456", customer_user_id=1
        )
    assert wrong_otp["error_code"] == "INVALID_OTP"
    assert accepted["success"]
    finalize.assert_called_once()


def test_wallet_requires_known_phone_and_matching_wallet_otp():
    from services import payment_service
    from unittest.mock import patch

    wallet = payment_service.OFFICIAL_WALLETS[0]
    with patch.object(payment_service, "sp_process_payment_webhook", return_value={
        "success": True, "order_id": 1, "new_status": "PAID", "duplicate": False,
    }) as finalize:
        bad_phone = payment_service.process_card_or_wallet_payment(
            "TRX-TEST", "WALLET", wallet_data={"phone": "0000000000"},
            otp="111111", customer_user_id=1,
        )
        bad_otp = payment_service.process_card_or_wallet_payment(
            "TRX-TEST", "WALLET", wallet_data=wallet,
            otp="123456", customer_user_id=1,
        )
        accepted = payment_service.process_card_or_wallet_payment(
            "TRX-TEST", "WALLET", wallet_data=wallet,
            otp="111111", customer_user_id=1,
        )
    assert bad_phone["error_code"] == "INVALID_WALLET"
    assert bad_otp["error_code"] == "INVALID_OTP"
    assert accepted["success"]
    finalize.assert_called_once()


def test_chat_limit_and_http_errors_use_consistent_json(monkeypatch):
    from app import app

    client = app.test_client()
    long_message = client.post("/api/ai/chat", json={"message": "x" * 501})
    assert long_message.status_code == 400
    assert long_message.is_json
    assert long_message.get_json() == {
        "success": False, "error": "Tin nhắn tối đa 500 ký tự"
    }

    missing = client.get("/not-a-real-page")
    assert missing.status_code == 404
    assert missing.is_json and missing.get_json()["success"] is False
    unsupported = client.post("/api/products")
    assert unsupported.status_code == 405
    assert unsupported.is_json and unsupported.get_json()["success"] is False

    # Use a separate Flask app so the production app's route map stays frozen.
    # Register its actual handler to keep this assertion tied to app behavior.
    from flask import Flask
    from app import handle_unexpected_error

    error_app = Flask("unexpected_error_test")
    error_app.register_error_handler(Exception, handle_unexpected_error)

    @error_app.get("/test/unexpected-error")
    def unexpected_error_for_test():
        raise RuntimeError("private exception details")

    failed = error_app.test_client().get("/test/unexpected-error")
    assert failed.status_code == 500
    assert failed.is_json
    assert "private exception details" not in failed.get_data(as_text=True)
    assert failed.get_json() == {
        "success": False, "error": "Đã xảy ra lỗi hệ thống. Vui lòng thử lại sau."
    }


def test_empty_secret_key_signature_is_rejected_by_payment_callback(monkeypatch):
    import hashlib
    import hmac
    from app import app

    user_id = _user_id("empty-key@example.test")
    order = _order(user_id)
    client = app.test_client()
    client.post("/api/auth/login", json={
        "email": "empty-key@example.test", "password": "review-password"
    })
    with client.session_transaction() as session:
        headers = {"X-CSRF-Token": session["csrf_token"]}

    message = f"{order['transaction_code']}|{order['total_amount']}|"
    empty_key_signature = hmac.new(b"", message.encode(), hashlib.sha256).hexdigest()
    response = client.post("/api/payment/simulate-callback", json={
        "transaction_code": order["transaction_code"],
        "status": "SUCCESS",
        "amount": order["total_amount"],
        "checksum": empty_key_signature,
    }, headers=headers)
    assert response.status_code == 403
    assert response.get_json()["success"] is False


def test_payment_service_requires_keys_outside_development():
    import os
    import subprocess
    import sys

    env = os.environ.copy()
    env.update({"APP_ENV": "production", "SECRET_KEY": "", "ZALOPAY_KEY1": "", "ZALOPAY_KEY2": ""})
    result = subprocess.run(
        [sys.executable, "-c", "import services.payment_service"],
        cwd=os.getcwd(), env=env, capture_output=True, text=True,
    )
    assert result.returncode != 0
    assert all(name in result.stderr for name in ("SECRET_KEY", "ZALOPAY_KEY1", "ZALOPAY_KEY2"))


def test_payment_service_generates_development_keys_and_rejects_bad_callback_signature():
    import os
    import subprocess
    import sys

    env = os.environ.copy()
    env.update({"APP_ENV": "development", "SECRET_KEY": "", "ZALOPAY_KEY1": "", "ZALOPAY_KEY2": ""})
    result = subprocess.run(
        [sys.executable, "-c", (
            "from services.payment_service import SECRET_KEY, ZALOPAY_SANDBOX_CONFIG, "
            "generate_checksum, verify_checksum; "
            "assert SECRET_KEY and ZALOPAY_SANDBOX_CONFIG['key1'] and ZALOPAY_SANDBOX_CONFIG['key2']; "
            "assert not verify_checksum('TRX-TEST', 10, 'wrong'); "
            "print('keys-present')"
        )],
        cwd=os.getcwd(), env=env, capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "keys-present"
    assert "Thiếu khóa thanh toán" in result.stderr
    assert re.search(r"\b[0-9a-f]{64}\b", result.stderr, re.IGNORECASE) is None


def test_unused_admin_token_is_not_advertised_or_injected_for_tests():
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    assert "ADMIN_TOKEN" not in (root / ".env.example").read_text(encoding="utf-8")
    assert "ADMIN_TOKEN" not in (root / "tests" / "conftest.py").read_text(encoding="utf-8")


def test_chat_rate_limit_returns_429_on_request_21_and_resets_after_window(monkeypatch):
    import app as app_module

    now = [100.0]
    monkeypatch.setattr(app_module, "monotonic", lambda: now[0])
    app_module._chat_requests.clear()
    monkeypatch.setattr(app_module.agentic_ai, "chat_with_agent", lambda *args: {"answer": "ok"})
    client = app_module.app.test_client()
    ip = "198.51.100.71"

    responses = [client.post("/api/ai/chat", json={"message": "xin chao"},
                             environ_overrides={"REMOTE_ADDR": ip}) for _ in range(20)]
    limited = client.post("/api/ai/chat", json={"message": "xin chao"},
                          environ_overrides={"REMOTE_ADDR": ip})
    assert all(response.status_code == 200 for response in responses)
    assert limited.status_code == 429
    assert limited.is_json and limited.get_json()["success"] is False

    now[0] += 60
    retried = client.post("/api/ai/chat", json={"message": "xin chao"},
                          environ_overrides={"REMOTE_ADDR": ip})
    assert retried.status_code == 200


def test_chat_rate_limiter_removes_every_expired_ip(monkeypatch):
    from collections import OrderedDict
    import app as app_module

    app_module._chat_requests.clear()
    app_module._chat_requests.update(OrderedDict([
        ("active-ip", (300.0, 1)),
        ("expired-ip", (100.0, 1)),
    ]))
    monkeypatch.setattr(app_module, "monotonic", lambda: 200.0)

    assert app_module._chat_rate_allowed("new-ip")
    assert "expired-ip" not in app_module._chat_requests
    assert app_module._chat_requests["active-ip"] == (300.0, 1)


@pytest.mark.parametrize("value", [None, "0", "false", "True", ""])
def test_debug_flag_is_disabled_unless_exactly_one(value):
    from app import debug_enabled

    assert debug_enabled(value) is False
    assert debug_enabled("1") is True
