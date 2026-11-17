from unittest.mock import Mock


def _logged_in_client(role):
    from app import app
    from database import db

    result = db.create_user(f"{role.lower()}-hidden@example.test", "password-123", "Test User")
    assert result["success"]
    user_id = db.get_user_by_email(f"{role.lower()}-hidden@example.test")["id"]
    conn = db.get_db_connection()
    try:
        conn.execute("UPDATE users SET role=? WHERE id=?", (role, user_id))
        conn.commit()
        product_id = conn.execute("SELECT id FROM products LIMIT 1").fetchone()[0]
        conn.execute("UPDATE products SET is_published=0 WHERE id=?", (product_id,))
        conn.commit()
    finally:
        conn.close()
    client = app.test_client()
    with client.session_transaction() as sess:
        sess["user_id"] = user_id
    return client, product_id


def _ensure_social_tables():
    from database.db import get_db_connection
    from product_social import SCHEMA

    conn = get_db_connection()
    try:
        conn.executescript(SCHEMA)
    finally:
        conn.close()


def test_hidden_product_detail_is_private_to_management_roles():
    client, product_id = _logged_in_client("CUSTOMER")
    _ensure_social_tables()
    assert client.get(f"/api/products/{product_id}").status_code == 404
    assert client.get(f"/api/products/{product_id}/reviews").status_code == 404
    summary = client.get("/api/products/social-summary").json["products"]
    assert product_id not in {row["id"] for row in summary}
    admin, admin_product_id = _logged_in_client("ADMIN")
    assert admin_product_id == product_id
    assert admin.get(f"/api/products/{product_id}").status_code == 200
    staff, _ = _logged_in_client("STAFF")
    assert staff.get(f"/api/products/{product_id}").status_code == 200


def test_register_attempts_are_limited_per_ip_and_expire(monkeypatch):
    import app as app_module

    now = [100.0]
    monkeypatch.setattr(app_module, "_login_rate_now", lambda: now[0])
    with app_module._login_failures_lock:
        app_module._login_failures.clear()
    client = app_module.app.test_client()
    payload = {"email": "new@example.test", "password": "password-123", "full_name": "New User"}
    for _ in range(5):
        assert client.post("/api/auth/register", json=payload).status_code != 429
    limited = client.post("/api/auth/register", json=payload)
    assert limited.status_code == 429
    assert limited.json["success"] is False
    assert int(limited.headers["Retry-After"]) > 0
    now[0] += 601
    assert client.post("/api/auth/register", json=payload).status_code != 429


def test_gemini_permission_failure_opens_circuit_and_uses_template(monkeypatch):
    from services import agentic_rag

    now = [500.0]
    monkeypatch.setattr(agentic_rag, "monotonic", lambda: now[0], raising=False)
    monkeypatch.setattr(agentic_rag.RAGEngine, "generate_response", lambda self, query: {
        "answer": "Dự phòng", "recommended_products": [], "rag_trace": {"generation_mode": "template"}
    })
    class PermissionError(Exception):
        code = 403
    engine = agentic_rag.AgenticRAGEngine()
    engine.client = object()
    engine._route = Mock(side_effect=PermissionError("PERMISSION_DENIED"))
    first = engine.chat_with_agent("Tìm áo cotton")
    assert first["rag_trace"]["generation_mode"] == "template"
    second = engine.chat_with_agent("Tìm áo cotton")
    assert engine._route.call_count == 1
    assert second["rag_trace"]["generation_mode"] == "template"
    now[0] += 601
    engine._route = Mock(return_value=None)
    engine.chat_with_agent("Tìm áo cotton")
    assert engine._route.call_count == 1


def test_gemini_temporary_timeout_does_not_open_long_circuit(monkeypatch):
    from services import agentic_rag

    monkeypatch.setattr(agentic_rag.RAGEngine, "generate_response", lambda self, query: {
        "answer": "Dự phòng", "recommended_products": [], "rag_trace": {"generation_mode": "template"}
    })
    class TimeoutError(Exception):
        code = 408
    engine = agentic_rag.AgenticRAGEngine()
    engine.client = object()
    engine._route = Mock(side_effect=TimeoutError("temporary timeout"))
    engine.chat_with_agent("Tìm áo cotton")
    engine.chat_with_agent("Tìm áo cotton")
    assert engine._route.call_count == 2


def test_gemini_quota_exhaustion_is_a_circuit_breaker_error():
    from services.agentic_rag import AgenticRAGEngine

    class QuotaError(Exception):
        code = 429

    assert AgenticRAGEngine._is_gemini_credential_or_quota_error(
        QuotaError("RESOURCE_EXHAUSTED: quota exceeded"), 429
    )
    assert not AgenticRAGEngine._is_gemini_credential_or_quota_error(
        TimeoutError("temporary timeout"), 429
    )

