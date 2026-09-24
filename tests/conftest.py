import pytest
from app import create_app
from models import Task, User, WorkLog, db


@pytest.fixture
def app():
    """Create and configure a test Flask application."""
    app = create_app("testing")

    with app.app_context():
        db.create_all()

        # Seed test supervisor
        supervisor = User(
            username="supervisor_test",
            role="supervisor",
            preferred_language="en",
        )
        supervisor.set_password("testpass123")
        db.session.add(supervisor)

        # Seed test worker
        worker = User(
            username="worker_test",
            role="worker",
            preferred_language="es",
            age=29,
            gender="female",
        )
        worker.set_password("testpass123")
        db.session.add(worker)

        db.session.commit()

        yield app

        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()


@pytest.fixture
def auth_worker(client):
    """Logs in as worker_test."""
    client.post("/", data={"username": "worker_test", "password": "testpass123"}, follow_redirects=True)
    return client


@pytest.fixture
def auth_supervisor(client):
    """Logs in as supervisor_test."""
    client.post("/", data={"username": "supervisor_test", "password": "testpass123"}, follow_redirects=True)
    return client
