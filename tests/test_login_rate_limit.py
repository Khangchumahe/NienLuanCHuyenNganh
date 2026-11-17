import pytest


def _app_client(monkeypatch, verify_user):
    import app as app_module

    if hasattr(app_module, "_login_failures"):
        with app_module._login_failures_lock:
            app_module._login_failures.clear()
    monkeypatch.setattr(app_module, "verify_user", verify_user)
    app_module.app.config.update(TESTING=True)
    return app_module, app_module.app.test_client()


def test_sixth_failed_login_is_limited_and_window_expiry_allows_retry(monkeypatch):
    now = [1000.0]
    import app as app_module

    monkeypatch.setattr(app_module, "_login_rate_now", lambda: now[0], raising=False)
    app_module, client = _app_client(monkeypatch, lambda email, password: None)

    for attempt in range(5):
        response = client.post(
            "/api/auth/login",
            json={"email": "unknown@example.test", "password": "wrong"},
        )
        assert response.status_code == 401, attempt

    limited = client.post(
        "/api/auth/login",
        json={"email": "unknown@example.test", "password": "wrong"},
    )
    assert limited.status_code == 429
    assert limited.json == {
        "success": False,
        "error": "Bạn đăng nhập quá nhiều lần. Vui lòng thử lại sau.",
    }
    assert int(limited.headers["Retry-After"]) > 0

    now[0] += 301
    retry = client.post(
        "/api/auth/login",
        json={"email": "unknown@example.test", "password": "wrong"},
    )
    assert retry.status_code == 401


def test_successful_login_clears_failure_counters(monkeypatch):
    import app as app_module

    monkeypatch.setattr(app_module, "_login_rate_now", lambda: 2000.0, raising=False)
    user = {
        "id": 77,
        "email": "member@example.test",
        "full_name": "Member",
        "phone": "",
        "role": "CUSTOMER",
    }

    def verify(email, password):
        return user if email == user["email"] and password == "correct" else None

    app_module, client = _app_client(monkeypatch, verify)
    for _ in range(4):
        assert client.post(
            "/api/auth/login",
            json={"email": user["email"], "password": "wrong"},
        ).status_code == 401

    assert client.post(
        "/api/auth/login",
        json={"email": user["email"], "password": "correct"},
    ).status_code == 200

    for _ in range(5):
        assert client.post(
            "/api/auth/login",
            json={"email": user["email"], "password": "wrong"},
        ).status_code == 401
    assert client.post(
        "/api/auth/login",
        json={"email": user["email"], "password": "wrong"},
    ).status_code == 429


@pytest.mark.parametrize("mode", ["same_ip", "same_email"])
def test_login_limit_applies_by_ip_and_by_normalized_email(monkeypatch, mode):
    import app as app_module

    monkeypatch.setattr(app_module, "_login_rate_now", lambda: 3000.0, raising=False)
    app_module, client = _app_client(monkeypatch, lambda email, password: None)

    for attempt in range(5):
        email = f"user{attempt}@example.test" if mode == "same_ip" else "Shared@Example.test"
        address = "198.51.100.7" if mode == "same_ip" else f"198.51.100.{attempt + 1}"
        response = client.post(
            "/api/auth/login",
            json={"email": email, "password": "wrong"},
            environ_base={"REMOTE_ADDR": address},
        )
        assert response.status_code == 401

    email = "different@example.test" if mode == "same_ip" else "shared@example.test"
    address = "198.51.100.7" if mode == "same_ip" else "198.51.100.99"
    limited = client.post(
        "/api/auth/login",
        json={"email": email, "password": "wrong"},
        environ_base={"REMOTE_ADDR": address},
    )
    assert limited.status_code == 429


def test_wrong_email_and_wrong_password_use_the_same_message(monkeypatch):
    import app as app_module

    monkeypatch.setattr(app_module, "_login_rate_now", lambda: 4000.0, raising=False)
    app_module, client = _app_client(monkeypatch, lambda email, password: None)

    wrong_email = client.post(
        "/api/auth/login",
        json={"email": "missing@example.test", "password": "wrong"},
    )
    wrong_password = client.post(
        "/api/auth/login",
        json={"email": "member@example.test", "password": "wrong"},
    )
    assert wrong_email.status_code == wrong_password.status_code == 401
    assert wrong_email.json["error"] == wrong_password.json["error"]
