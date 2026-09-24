from app import create_app
from models import Task, User, WorkLog, db

app = create_app()

with app.app_context():
    db.create_all()

    # Create Supervisor if not exists
    if not User.query.filter_by(username="supervisor1").first():
        sup = User(
            username="supervisor1",
            role="supervisor",
            preferred_language="en",
        )
        sup.set_password("password123")
        db.session.add(sup)
        print("Created demo supervisor: supervisor1 / password123")

    # Create Worker if not exists
    if not User.query.filter_by(username="worker1").first():
        worker = User(
            username="worker1",
            role="worker",
            preferred_language="en",
            age=32,
            gender="female",
        )
        worker.set_password("password123")
        db.session.add(worker)
        print("Created demo worker: worker1 / password123")

    db.session.commit()
    print("Database ready!")
