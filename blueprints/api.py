from flask import Blueprint, jsonify
from flask_login import login_required

from blueprints.auth import role_required
from models import Task, User, WorkLog
from services.security_service import SecurityService

api_bp = Blueprint("api", __name__, url_prefix="/api")


@api_bp.route("/tasks/status", methods=["GET"])
@role_required("supervisor")
def api_tasks_status():
    """Return task status data for supervisor dashboard."""
    tasks = Task.query.all()
    result = []
    for t in tasks:
        logs = WorkLog.query.filter_by(task_id=t.id).all()
        result.append(
            {
                "id": t.id,
                "title": t.title,
                "status": t.status,
                "priority": t.priority,
                "logs_count": len(logs),
                "created_at": t.created_at.isoformat() if t.created_at else None,
            }
        )
    return jsonify(result)


@api_bp.route("/reports/<int:log_id>/verify-audit", methods=["GET"])
@login_required
def verify_report_audit(log_id):
    """Cryptographically verifies that the CQC report hasn't been altered."""
    log = db.get_or_404(WorkLog, log_id)
    if not log.audit_hash:
        return jsonify({"verified": False, "reason": "No cryptographic seal found"}), 404

    content = log.cqc_report_final or log.cqc_report or log.translated_text or log.original_text
    payload = f"{log.id}:{log.worker_id}:{content}:{log.created_at.isoformat() if log.created_at else ''}"
    is_valid = SecurityService.verify_audit_hash(payload, log.audit_hash)

    return jsonify({
        "log_id": log.id,
        "verified": is_valid,
        "audit_hash": log.audit_hash,
        "cqc_status": log.cqc_status,
        "timestamp": log.created_at.isoformat() if log.created_at else None,
    })
