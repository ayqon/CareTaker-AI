import json
from flask import Blueprint, abort, current_app, flash, redirect, render_template, request, url_for
from flask_login import current_user

from blueprints.auth import role_required
from models import Task, TrainingProgram, User, WorkLog, db
from services.security_service import SecurityService

supervisor_bp = Blueprint("supervisor", __name__)


@supervisor_bp.route("/supervisor", methods=["GET"])
@role_required("supervisor")
def supervisor_dashboard():
    workers = User.query.filter_by(role="worker").order_by(User.username).all()
    tasks = Task.query.order_by(Task.created_at.desc()).all()
    programs = TrainingProgram.query.order_by(TrainingProgram.created_at.desc()).all()
    final_reports = (
        WorkLog.query.filter_by(cqc_status="final")
        .order_by(WorkLog.created_at.desc())
        .all()
    )
    return render_template(
        "supervisor.html",
        workers=workers,
        tasks=tasks,
        programs=programs,
        final_reports=final_reports,
    )


@supervisor_bp.route("/supervisor/tasks/create", methods=["GET", "POST"])
@role_required("supervisor")
def create_task():
    if request.method == "POST":
        raw_description = request.form.get("description", "").strip()
        if not raw_description:
            flash("Please enter a task description.", "error")
            return redirect(url_for("supervisor.create_task"))

        # Prompt injection safety validation
        is_safe, reason = SecurityService.check_prompt_injection(raw_description)
        if not is_safe:
            flash(f"Security Alert: {reason}. Task creation rejected.", "error")
            return redirect(url_for("supervisor.create_task"))

        gemini_svc = current_app.extensions["gemini_service"]

        try:
            # AI structuring
            structured = gemini_svc.structure_task(raw_description)

            # Generate embedding for task matching
            embedding = gemini_svc.generate_embedding(raw_description)

            task = Task(
                title=structured.get("title", "Untitled Task"),
                description=raw_description,
                structured_points=json.dumps(structured.get("points", [])),
                priority=structured.get("priority", "medium"),
                estimated_duration=structured.get("estimated_duration", ""),
                created_by=current_user.id,
            )
            task.set_embedding(embedding)
            db.session.add(task)
            db.session.commit()

            flash(
                f"Task '{task.title}' created with {len(structured.get('points', []))} action points.",
                "success",
            )
            return redirect(url_for("supervisor.supervisor_dashboard"))

        except Exception as e:
            flash(f"Error creating task: {str(e)}", "error")
            return redirect(url_for("supervisor.create_task"))

    return render_template("create_task.html")


@supervisor_bp.route("/supervisor/tasks/<int:task_id>")
@role_required("supervisor")
def view_task(task_id):
    task = db.get_or_404(Task, task_id)
    logs = WorkLog.query.filter_by(task_id=task_id).order_by(WorkLog.created_at.desc()).all()
    return render_template("view_task.html", task=task, logs=logs)


@supervisor_bp.route("/supervisor/tasks/<int:task_id>/complete", methods=["POST"])
@role_required("supervisor")
def complete_task(task_id):
    task = db.get_or_404(Task, task_id)
    task.status = "completed"
    db.session.commit()
    flash(f"Task '{task.title}' marked as completed.", "success")
    return redirect(url_for("supervisor.supervisor_dashboard"))


@supervisor_bp.route("/supervisor/reports/<int:log_id>")
@role_required("supervisor")
def supervisor_view_report(log_id):
    """Supervisor views a worker's CQC report with cryptographic audit validation."""
    log = db.get_or_404(WorkLog, log_id)
    if log.cqc_report_final:
        report = log.get_cqc_report_final()
        is_final = True
    elif log.cqc_report:
        report = log.get_cqc_report()
        is_final = False
    else:
        abort(404)
    return render_template(
        "cqc_report.html", log=log, report=report, is_final=is_final
    )
