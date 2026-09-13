from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import models
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


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


Base.metadata.create_all(bind=engine)

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


def register_and_login():
    username = "share_test_user"
    password = "TestPassword123!"

    client.post(
        "/auth/register",
        json={
            "username": username,
            "email": "share_test@example.com",
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


def test_create_share_link():
    token = register_and_login()

    scan_response = client.post(
        "/scans",
        json={
            "title": "Shared test scan",
            "severity": "high",
            "affected_component": "test component",
        },
        headers=auth_headers(token),
    )

    assert scan_response.status_code == 201

    scan_id = scan_response.json()["id"]

    response = client.post(
        f"/scans/{scan_id}/share",
        json={},
        headers=auth_headers(token),
    )

    print("SHARE RESPONSE:", response.status_code, response.text)

    assert response.status_code == 200
    assert "share_url" in response.json()
def test_password_protected_share_link_locks_after_failed_attempts():
    token = register_and_login()

    scan_response = client.post(
        "/scans",
        json={
            "title": "Protected shared scan",
            "severity": "high",
            "affected_component": "test component",
        },
        headers=auth_headers(token),
    )

    assert scan_response.status_code == 201
    scan_id = scan_response.json()["id"]

    response = client.post(
        f"/scans/{scan_id}/share",
        json={"password": "CorrectPassword123!"},
        headers=auth_headers(token),
    )

    assert response.status_code == 200

    share_url = response.json()["share_url"]
    share_token = share_url.rstrip("/").split("/")[-1]

    # First four incorrect passwords are rejected.
    for _ in range(4):
        response = client.get(
            f"/share/{share_token}",
            params={"password": "WrongPassword"},
        )
        assert response.status_code == 403

    # The fifth incorrect password triggers the lockout.
    response = client.get(
        f"/share/{share_token}",
        params={"password": "WrongPassword"},
    )
    assert response.status_code == 429

    # Correct password is also blocked while the link is locked.
    response = client.get(
        f"/share/{share_token}",
        params={"password": "CorrectPassword123!"},
    )
    assert response.status_code == 429