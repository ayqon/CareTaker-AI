import json
import pytest
from models import Task, User, WorkLog, db


def test_full_cqc_workflow(auth_worker, app):
    """Integration test of CQC workflow:
    1. Worker submits log.
    2. Generates CQC Draft.
    3. Reviews CQC Report.
    4. Submits Recommendation responses.
    5. Finalizes report with cryptographic seal.
    """
    with app.app_context():
        worker = User.query.filter_by(username="worker_test").first()
        task = Task(
            title="Morning Medication & Hydration",
            description="Administer morning blister pack and ensure 300ml water intake.",
            priority="high",
            created_by=worker.id,
        )
        db.session.add(task)
        db.session.commit()

        log = WorkLog(
            worker_id=worker.id,
            original_text="Di las pastillas y vaso de agua a las 8am.",
            translated_text="Gave the pills and a glass of water at 8am.",
            task_id=task.id,
            match_score=0.89,
        )
        db.session.add(log)
        db.session.commit()
        log_id = log.id

    # 1. Generate CQC draft report
    res = auth_worker.post(f"/worker/log/{log_id}/cqc-report", follow_redirects=True)
    assert res.status_code == 200

    with app.app_context():
        saved_log = db.session.get(WorkLog, log_id)
        assert saved_log.cqc_status == "draft"
        assert saved_log.audit_hash is not None
        assert "Care Activity" in saved_log.cqc_report

    # 2. Trigger CQC Review
    res = auth_worker.post(f"/worker/log/{log_id}/cqc-review", follow_redirects=True)
    assert res.status_code == 200

    with app.app_context():
        saved_log = db.session.get(WorkLog, log_id)
        assert saved_log.cqc_status == "in_review"
        assert len(saved_log.recommendations) > 0
        rec_id = saved_log.recommendations[0].id

    # 3. Respond to recommendation
    res = auth_worker.post(
        f"/worker/log/{log_id}/cqc-review/respond",
        data={f"status_{rec_id}": "addressed", f"response_{rec_id}": "Confirmed 300ml fluid intake."},
        follow_redirects=True,
    )
    assert res.status_code == 200

    # 4. Finalise report
    res = auth_worker.post(f"/worker/log/{log_id}/cqc-report/finalise", follow_redirects=True)
    assert res.status_code == 200

    with app.app_context():
        saved_log = db.session.get(WorkLog, log_id)
        assert saved_log.cqc_status == "final"
        assert saved_log.cqc_report_final is not None
        assert saved_log.audit_hash is not None
