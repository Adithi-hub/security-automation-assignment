import os
import sys

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.database import Base, get_db
from app.main import app


engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

Base.metadata.create_all(bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app, raise_server_exceptions=False)


def register_and_login():
    username = "testuser123"
    password = "TestPassword123!"

    client.post(
        "/auth/register",
        json={
            "username": username,
            "email": "test123@example.com",
            "password": password,
        },
    )

    response = client.post(
        "/auth/login",
        json={
            "username": username,
            "password": password,
        },
    )

    assert response.status_code == 200
    return response.json()["access_token"]


def auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


def test_create_scan():
    token = register_and_login()

    resp = client.post(
        "/scans",
        json={
            "title": "SQL Injection",
            "severity": "critical",
            "affected_component": "login endpoint",
        },
        headers=auth_headers(token),
    )

    assert resp.status_code == 201
    assert resp.json()["title"] == "SQL Injection"


def test_list_scans():
    token = register_and_login()

    resp = client.get(
        "/scans",
        headers=auth_headers(token),
    )

    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


def test_search_scans():
    token = register_and_login()

    client.post(
        "/scans",
        json={
            "title": "SQL Injection via login",
            "severity": "critical",
            "affected_component": "POST /auth/login",
        },
        headers=auth_headers(token),
    )

    resp = client.get(
        "/scans/search?q=SQL",
        headers=auth_headers(token),
    )

    assert resp.status_code == 200


def test_update_scan_status():
    token = register_and_login()

    scan_id = client.post(
        "/scans",
        json={
            "title": "Open redirect",
            "severity": "medium",
            "affected_component": "redirect handler",
        },
        headers=auth_headers(token),
    ).json()["id"]

    resp = client.patch(
        f"/scans/{scan_id}",
        json={"status": "in_progress"},
        headers=auth_headers(token),
    )

    assert resp.status_code == 200
    assert resp.json()["status"] == "in_progress"


def test_delete_scan():
    token = register_and_login()

    scan_id = client.post(
        "/scans",
        json={
            "title": "Stale finding",
            "severity": "low",
            "affected_component": "misc",
        },
        headers=auth_headers(token),
    ).json()["id"]

    resp = client.delete(
        f"/scans/{scan_id}",
        headers=auth_headers(token),
    )

    assert resp.status_code == 204


def test_rejects_none_algorithm_jwt():
    import base64
    import json

    def b64url(data):
        return base64.urlsafe_b64encode(data).rstrip(b"=").decode()

    header = b64url(
        json.dumps({
            "alg": "none",
            "typ": "JWT",
        }).encode()
    )

    payload = b64url(
        json.dumps({
            "sub": "testuser123",
        }).encode()
    )

    token = f"{header}.{payload}."

    resp = client.get(
        "/scans",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert resp.status_code == 401


def test_search_scans_handles_sql_injection_payload():
    token = register_and_login()

    malicious_query = "' OR '1'='1"

    resp = client.get(
        "/scans/search",
        params={"q": malicious_query},
        headers=auth_headers(token),
    )

    assert resp.status_code == 200
    assert isinstance(resp.json(), dict)
    assert resp.json()["count"] == 0
    assert resp.json()["results"] == []
def test_user_cannot_access_another_users_scan():
    user_a_token = register_and_login()

    scan_response = client.post(
        "/scans",
        json={
            "title": "Private scan",
            "severity": "high",
            "affected_component": "private component",
        },
        headers=auth_headers(user_a_token),
    )

    assert scan_response.status_code == 201
    scan_id = scan_response.json()["id"]

    client.post(
        "/auth/register",
        json={
            "username": "different_user",
            "email": "different@example.com",
            "password": "DifferentPassword123!",
        },
    )

    login_response = client.post(
        "/auth/login",
        json={
            "username": "different_user",
            "password": "DifferentPassword123!",
        },
    )

    assert login_response.status_code == 200
    user_b_token = login_response.json()["access_token"]

    response = client.get(
        f"/scans/{scan_id}",
        headers=auth_headers(user_b_token),
    )

    assert response.status_code == 404