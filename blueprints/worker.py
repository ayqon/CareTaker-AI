from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for
from flask_login import current_user

from blueprints.auth import role_required
from models import Task, TrainingContent, User, WorkLog, db
from services.security_service import SecurityService

worker_bp = Blueprint("worker", __name__)


@worker_bp.route("/worker", methods=["GET"])
@role_required("worker")
def worker_dashboard():
    logs = (
        WorkLog.query.filter_by(worker_id=current_user.id)
        .order_by(WorkLog.created_at.desc())
        .all()
    )
    tasks = Task.query.filter(Task.status != "completed").order_by(Task.created_at.desc()).all()
    training_contents = (
        TrainingContent.query.filter_by(worker_id=current_user.id)
        .order_by(TrainingContent.created_at.desc())
        .all()
    )
    return render_template(
        "worker.html", logs=logs, tasks=tasks, training_contents=training_contents
    )


@worker_bp.route("/worker/log", methods=["POST"])
@role_required("worker")
def worker_submit_log():
    """Worker submits work via text or audio. AI translates and matches to tasks."""
    original_text = ""
    original_language = ""
    translated_text = ""

    audio_file = request.files.get("audio")
    text_input = request.form.get("work_text", "").strip()

    gemini_svc = current_app.extensions["gemini_service"]

    try:
        if audio_file and audio_file.filename:
            audio_bytes = audio_file.read()
            mime_type = audio_file.content_type or "audio/webm"
            result = gemini_svc.transcribe_and_translate_audio(audio_bytes, mime_type)
            original_text = result.get("original_text", "")
            original_language = result.get("detected_language", "unknown")
            translated_text = result.get("translated_text", "")
        elif text_input:
            # 1. Security Check: Prompt injection guardrail
            is_safe, reason = SecurityService.check_prompt_injection(text_input)
            if not is_safe:
                flash(f"Security Alert: {reason}. Submission blocked.", "error")
                return redirect(url_for("worker.worker_dashboard"))

            # 2. PII / PHI Redaction Guardrail
            sanitized_input, has_pii, _ = SecurityService.redact_pii(text_input)

            # Process text input
            result = gemini_svc.translate_text(sanitized_input)
            original_text = text_input
            original_language = result.get("detected_language", "unknown")
            translated_text = result.get("translated_text", sanitized_input)
        else:
            flash("Please provide text or audio input.", "error")
            return redirect(url_for("worker.worker_dashboard"))

        # Generate embedding for the translated text
        work_embedding = gemini_svc.generate_embedding(translated_text)

        # Match to existing tasks
        all_tasks = Task.query.filter(Task.status != "completed").all()
        matched_task, match_score = gemini_svc.match_work_to_tasks(work_embedding, all_tasks)

        # Create work log
        log = WorkLog(
            worker_id=current_user.id,
            original_text=original_text,
            original_language=original_language,
            translated_text=translated_text,
            task_id=matched_task.id if matched_task and match_score > 0.4 else None,
            match_score=match_score if matched_task else None,
            pii_redacted=bool(text_input and has_pii if 'has_pii' in locals() else False),
        )
        log.set_embedding(work_embedding)
        db.session.add(log)

        # Update task status if matched
        if matched_task and match_score > 0.4:
            if matched_task.status == "pending":
                matched_task.status = "in_progress"
            db.session.add(matched_task)

        db.session.commit()

        if matched_task and match_score > 0.4:
            flash(
                f"Work logged and matched to task: '{matched_task.title}' (confidence: {match_score:.0%})",
                "success",
            )
        else:
            flash("Work logged successfully (no strong task match found).", "success")

    except Exception as e:
        flash(f"Error processing input: {str(e)}", "error")

    return redirect(url_for("worker.worker_dashboard"))


@worker_bp.route("/worker/profile", methods=["GET", "POST"])
@role_required("worker")
def worker_profile():
    if request.method == "POST":
        current_user.preferred_language = request.form.get(
            "preferred_language", "en"
        )
        age = request.form.get("age", "")
        current_user.age = int(age) if age else None
        current_user.gender = request.form.get("gender", "")
        db.session.commit()
        flash("Profile updated.", "success")
        return redirect(url_for("worker.worker_dashboard"))
    return render_template("worker_profile.html")
