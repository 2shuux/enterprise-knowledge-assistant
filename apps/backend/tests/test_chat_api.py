"""RAG chat flow through the API with fake providers end to end."""

ADMIN = {"email": "admin@example.com", "password": "adminpass1", "full_name": "Admin"}
OTHER = {"email": "other@example.com", "password": "otherpass1", "full_name": "Other"}


def auth_headers(client, user):
    client.post("/api/v1/auth/register", json=user)
    r = client.post(
        "/api/v1/auth/login", json={"email": user["email"], "password": user["password"]}
    )
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def seed_document(client, headers):
    client.post(
        "/api/v1/documents",
        headers=headers,
        files={"file": ("policy.txt", b"Leave policy: 20 days per year. " * 50, "text/plain")},
    )


def test_ask_returns_grounded_answer_with_citations(client):
    headers = auth_headers(client, ADMIN)
    seed_document(client, headers)

    conv = client.post("/api/v1/conversations", headers=headers, json={}).json()
    r = client.post(
        f"/api/v1/conversations/{conv['id']}/messages",
        headers=headers,
        json={"content": "What is the leave policy?"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["role"] == "ASSISTANT"
    assert "20 days" in body["content"]
    assert len(body["citations"]) >= 1
    first = body["citations"][0]
    assert first["document_name"] == "policy.txt"
    assert first["page_number"] >= 1
    assert first["excerpt"]
    assert 0 < body["confidence"] <= 1.0


def test_history_persists_user_and_assistant_messages(client):
    headers = auth_headers(client, ADMIN)
    seed_document(client, headers)
    conv = client.post("/api/v1/conversations", headers=headers, json={}).json()
    client.post(
        f"/api/v1/conversations/{conv['id']}/messages",
        headers=headers,
        json={"content": "What is the leave policy?"},
    )

    messages = client.get(
        f"/api/v1/conversations/{conv['id']}/messages", headers=headers
    ).json()
    assert [m["role"] for m in messages] == ["USER", "ASSISTANT"]

    # first question became the conversation title
    convs = client.get("/api/v1/conversations", headers=headers).json()
    assert convs[0]["title"] == "What is the leave policy?"


def test_empty_index_short_circuits_gracefully(client):
    headers = auth_headers(client, ADMIN)  # no document uploaded
    conv = client.post("/api/v1/conversations", headers=headers, json={}).json()
    r = client.post(
        f"/api/v1/conversations/{conv['id']}/messages",
        headers=headers,
        json={"content": "Anything?"},
    )
    assert r.status_code == 200
    assert "upload" in r.json()["content"].lower()
    assert r.json()["citations"] == []


def test_users_cannot_see_each_others_conversations(client):
    admin_headers = auth_headers(client, ADMIN)
    conv = client.post("/api/v1/conversations", headers=admin_headers, json={}).json()

    other_headers = auth_headers(client, OTHER)
    r = client.get(f"/api/v1/conversations/{conv['id']}/messages", headers=other_headers)
    assert r.status_code == 404  # not 403 — we don't even confirm it exists
