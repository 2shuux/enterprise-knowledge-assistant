"""End-to-end document flow through the API, with fake AI providers.
TestClient runs FastAPI background tasks synchronously after the response,
so by the time upload returns we can immediately assert the final status."""

ADMIN = {"email": "admin@example.com", "password": "adminpass1", "full_name": "Admin"}
USER = {"email": "user@example.com", "password": "userpass12", "full_name": "User"}


def make_token(client, user):
    client.post("/api/v1/auth/register", json=user)
    r = client.post(
        "/api/v1/auth/login", json={"email": user["email"], "password": user["password"]}
    )
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def upload(client, headers, name="policy.txt", content=b"Leave policy: 20 days per year. " * 50):
    return client.post(
        "/api/v1/documents", headers=headers, files={"file": (name, content, "text/plain")}
    )


def test_admin_can_upload_and_document_gets_indexed(client, fake_store):
    headers = make_token(client, ADMIN)
    r = upload(client, headers)
    assert r.status_code == 202
    doc_id = r.json()["id"]

    # background pipeline already ran (TestClient executes it synchronously)
    detail = client.get(f"/api/v1/documents/{doc_id}", headers=headers).json()
    assert detail["status"] == "INDEXED"
    assert detail["chunk_count"] > 0
    assert len(fake_store.records) == detail["chunk_count"]  # vectors landed


def test_normal_user_cannot_upload_but_can_list(client):
    make_token(client, ADMIN)  # first account takes the ADMIN slot
    user_headers = make_token(client, USER)

    assert upload(client, user_headers).status_code == 403  # RBAC wall

    r = client.get("/api/v1/documents", headers=user_headers)
    assert r.status_code == 200


def test_duplicate_upload_rejected(client):
    headers = make_token(client, ADMIN)
    assert upload(client, headers).status_code == 202
    assert upload(client, headers).status_code == 409  # same bytes → same checksum


def test_delete_removes_vectors_too(client, fake_store):
    headers = make_token(client, ADMIN)
    doc_id = upload(client, headers).json()["id"]
    assert len(fake_store.records) > 0

    assert client.delete(f"/api/v1/documents/{doc_id}", headers=headers).status_code == 204
    assert len(fake_store.records) == 0  # no orphaned vectors
    assert client.get(f"/api/v1/documents/{doc_id}", headers=headers).status_code == 404


def test_reindex_rebuilds_chunks(client, fake_store):
    headers = make_token(client, ADMIN)
    doc_id = upload(client, headers).json()["id"]
    first_count = client.get(f"/api/v1/documents/{doc_id}", headers=headers).json()["chunk_count"]

    r = client.post(f"/api/v1/documents/{doc_id}/reindex", headers=headers)
    assert r.status_code == 202
    detail = client.get(f"/api/v1/documents/{doc_id}", headers=headers).json()
    assert detail["status"] == "INDEXED"
    assert detail["chunk_count"] == first_count  # same file → same chunking
    assert len(fake_store.records) == first_count  # old vectors replaced, not duplicated


def test_garbage_pdf_fails_the_request_with_clear_error(client):
    headers = make_token(client, ADMIN)
    r = client.post(
        "/api/v1/documents",
        headers=headers,
        files={"file": ("fake.pdf", b"this is not a pdf", "application/pdf")},
    )
    assert r.status_code == 415
