import pytest
from models import User, db


def test_login_and_logout(client):
    """Test standard user login and session termination."""
    # Attempt invalid login
    res = client.post("/", data={"username": "invalid", "password": "wrong"}, follow_redirects=True)
    assert b"Invalid username or password" in res.data

    # Valid worker login
    res = client.post("/", data={"username": "worker_test", "password": "testpass123"}, follow_redirects=True)
    assert res.status_code == 200
    assert b"worker_test" in res.data

    # Logout
    res = client.get("/logout", follow_redirects=True)
    assert res.status_code == 200
    assert b"Welcome Back" in res.data


def test_rbac_access_control(auth_worker, client):
    """Verify that worker cannot access supervisor endpoints (RBAC 403)."""
    # Worker attempting to view supervisor dashboard
    res = auth_worker.get("/supervisor")
    assert res.status_code == 403

    # Worker attempting to create supervisor task
    res = auth_worker.get("/supervisor/tasks/create")
    assert res.status_code == 403


def test_worker_profile_update(auth_worker, client):
    """Test updating worker language and demographic profile."""
    res = auth_worker.post(
        "/worker/profile",
        data={"preferred_language": "pl", "age": 35, "gender": "male"},
        follow_redirects=True,
    )
    assert res.status_code == 200
    assert b"Profile updated" in res.data
