"""Auth flow tests — the complete lifecycle a real client goes through."""

ALICE = {"email": "alice@example.com", "password": "s3cretpass!", "full_name": "Alice"}
BOB = {"email": "bob@example.com", "password": "anotherpass!", "full_name": "Bob"}


def register(client, user):
    return client.post("/api/v1/auth/register", json=user)


def login(client, user):
    return client.post(
        "/api/v1/auth/login", json={"email": user["email"], "password": user["password"]}
    )


def test_first_user_becomes_admin_second_is_user(client):
    r1 = register(client, ALICE)
    assert r1.status_code == 201
    assert r1.json()["role"] == "ADMIN"

    r2 = register(client, BOB)
    assert r2.status_code == 201
    assert r2.json()["role"] == "USER"


def test_duplicate_email_rejected(client):
    register(client, ALICE)
    r = register(client, ALICE)
    assert r.status_code == 409


def test_login_returns_tokens_and_user(client):
    register(client, ALICE)
    r = login(client, ALICE)
    assert r.status_code == 200
    body = r.json()
    assert body["access_token"] and body["refresh_token"]
    assert body["user"]["email"] == ALICE["email"]


def test_wrong_password_rejected_with_generic_message(client):
    register(client, ALICE)
    r = client.post(
        "/api/v1/auth/login", json={"email": ALICE["email"], "password": "wrong-password"}
    )
    assert r.status_code == 401
    # same message as unknown email → no account enumeration
    assert "Invalid email or password" in r.json()["detail"]


def test_me_requires_token(client):
    assert client.get("/api/v1/auth/me").status_code == 401


def test_me_with_token(client):
    register(client, ALICE)
    token = login(client, ALICE).json()["access_token"]
    r = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert r.json()["email"] == ALICE["email"]


def test_refresh_rotation_old_token_dies(client):
    register(client, ALICE)
    first = login(client, ALICE).json()["refresh_token"]

    # first refresh works and returns a NEW pair
    r1 = client.post("/api/v1/auth/refresh", json={"refresh_token": first})
    assert r1.status_code == 200
    second = r1.json()["refresh_token"]
    assert second != first

    # replaying the consumed token must fail — this is the rotation guarantee
    r2 = client.post("/api/v1/auth/refresh", json={"refresh_token": first})
    assert r2.status_code == 401

    # the new token still works
    r3 = client.post("/api/v1/auth/refresh", json={"refresh_token": second})
    assert r3.status_code == 200


def test_logout_revokes_refresh_token(client):
    register(client, ALICE)
    rt = login(client, ALICE).json()["refresh_token"]
    assert client.post("/api/v1/auth/logout", json={"refresh_token": rt}).status_code == 204
    assert client.post("/api/v1/auth/refresh", json={"refresh_token": rt}).status_code == 401
