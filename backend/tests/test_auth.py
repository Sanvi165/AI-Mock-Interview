from app.services import auth_service


def _register(client, username="amy", email="amy@example.com", password="secret123"):
    return client.post(
        "/api/auth/register",
        json={"username": username, "email": email, "password": password},
    )


def _login(client, identifier, password="secret123"):
    return client.post("/api/auth/login", json={"identifier": identifier, "password": password})


def test_sign_up_returns_token_and_user(anon_client):
    response = _register(anon_client)
    assert response.status_code == 201
    body = response.json()
    assert body["token"]
    assert body["user"]["email"] == "amy@example.com"
    assert body["user"]["username"] == "amy"
    assert "password_hash" not in body["user"]


def test_duplicate_email_is_rejected_case_insensitively(anon_client):
    assert _register(anon_client).status_code == 201
    response = _register(anon_client, username="other", email="AMY@Example.COM")
    assert response.status_code == 409
    assert "already exists" in response.json()["detail"]


def test_duplicate_username_is_rejected_case_insensitively(anon_client):
    assert _register(anon_client).status_code == 201
    response = _register(anon_client, username="AMY", email="other@example.com")
    assert response.status_code == 409
    assert "username" in response.json()["detail"].lower()


def test_invalid_email_is_rejected(anon_client):
    response = _register(anon_client, email="not-an-email")
    assert response.status_code == 422
    assert "email" in response.json()["detail"].lower()


def test_invalid_username_is_rejected(anon_client):
    response = _register(anon_client, username="bad name")
    assert response.status_code == 422
    assert "username" in response.json()["detail"].lower()


def test_short_password_is_rejected(anon_client):
    response = _register(anon_client, password="123")
    assert response.status_code == 422
    assert "password" in response.json()["detail"].lower()


def test_login_with_email(anon_client):
    _register(anon_client)
    response = _login(anon_client, "amy@example.com")
    assert response.status_code == 200
    assert response.json()["token"]


def test_login_with_username_ignores_case(anon_client):
    _register(anon_client)
    response = _login(anon_client, "AMY")
    assert response.status_code == 200
    assert response.json()["user"]["username"] == "amy"


def test_login_with_email_ignores_case(anon_client):
    _register(anon_client)
    assert _login(anon_client, "Amy@Example.com").status_code == 200


def test_login_fails_with_wrong_password(anon_client):
    _register(anon_client)
    response = _login(anon_client, "amy", password="wrong-password")
    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect username/email or password."


def test_login_fails_for_unknown_account(anon_client):
    assert _login(anon_client, "nobody").status_code == 401
    assert _login(anon_client, "nobody@example.com").status_code == 401


def test_protected_endpoints_require_login(anon_client):
    assert anon_client.get("/api/history").status_code == 401
    assert anon_client.post("/api/interviews", json={}).status_code == 401


def test_invalid_token_is_rejected(anon_client):
    response = anon_client.get("/api/history", headers={"Authorization": "Bearer not-a-real-token"})
    assert response.status_code == 401


def test_me_returns_the_logged_in_user(client):
    body = client.get("/api/auth/me").json()
    assert body["email"] == "tester@example.com"
    assert body["username"] == "tester"


def test_logout_invalidates_the_token(client):
    login = _login(client, "tester")
    headers = {"Authorization": f"Bearer {login.json()['token']}"}
    assert client.get("/api/auth/me", headers=headers).status_code == 200
    assert client.post("/api/auth/logout", headers=headers).status_code == 200
    assert client.get("/api/auth/me", headers=headers).status_code == 401


def test_users_cannot_see_each_others_interviews(client, setup_payload):
    created = client.post("/api/interviews", json=setup_payload).json()
    session_id = created["id"]

    other = client.post(
        "/api/auth/register",
        json={"username": "bob", "email": "bob@example.com", "password": "secret123"},
    ).json()
    other_headers = {"Authorization": f"Bearer {other['token']}"}

    assert client.get(f"/api/interviews/{session_id}", headers=other_headers).status_code == 404
    assert client.get("/api/history", headers=other_headers).json() == []
    assert client.get("/api/progress", headers=other_headers).json()["total_sessions"] == 0
    # The owner can still open it.
    assert client.get(f"/api/interviews/{session_id}").status_code == 200


def test_password_hashing():
    stored = auth_service.hash_password("secret123")
    assert "secret123" not in stored
    assert auth_service.verify_password("secret123", stored)
    assert not auth_service.verify_password("other", stored)
    assert stored != auth_service.hash_password("secret123")  # random salt each time