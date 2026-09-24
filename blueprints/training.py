import json
from flask import Blueprint, abort, current_app, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from blueprints.auth import role_required
from models import TrainingContent, TrainingProgram, User, db

training_bp = Blueprint("training", __name__)


@training_bp.route("/supervisor/training/create", methods=["GET", "POST"])
@role_required("supervisor")
def create_training():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        key_points = request.form.get("key_points", "").strip()

        if not title or not description:
            flash("Title and description are required.", "error")
            return redirect(url_for("training.create_training"))

        program = TrainingProgram(
            title=title,
            description=description,
            key_points=json.dumps([p.strip() for p in key_points.split("\n") if p.strip()] if key_points else []),
            created_by=current_user.id,
        )
        db.session.add(program)
        db.session.commit()

        flash(f"Training program '{title}' created.", "success")
        return redirect(url_for("training.view_training", program_id=program.id))

    return render_template("create_training.html")


@training_bp.route("/supervisor/training/<int:program_id>")
@role_required("supervisor")
def view_training(program_id):
    program = db.get_or_404(TrainingProgram, program_id)
    contents = TrainingContent.query.filter_by(program_id=program_id).all()
    workers = User.query.filter_by(role="worker").all()
    return render_template(
        "view_training.html", program=program, contents=contents, workers=workers
    )


@training_bp.route("/supervisor/training/<int:program_id>/generate", methods=["POST"])
@role_required("supervisor")
def generate_training_content(program_id):
    """Generate personalised training scripts and Veo videos for workers."""
    program = db.get_or_404(TrainingProgram, program_id)
    workers = User.query.filter_by(role="worker").all()

    if not workers:
        flash("No workers found to generate content for.", "error")
        return redirect(url_for("training.view_training", program_id=program_id))

    gemini_svc = current_app.extensions["gemini_service"]
    storage_svc = current_app.extensions["storage_service"]

    generated_count = 0
    for w in workers:
        existing = TrainingContent.query.filter_by(
            program_id=program_id, worker_id=w.id
        ).first()
        if existing and existing.status == "ready":
            continue

        try:
            content = existing or TrainingContent(
                program_id=program_id,
                worker_id=w.id,
                language=w.preferred_language or "en",
                age_group=str(w.age) if w.age else "unknown",
                gender=w.gender or "unknown",
            )
            content.status = "generating"
            if not existing:
                db.session.add(content)
            db.session.flush()

            # Step 1: Generate personalised script
            script_data = gemini_svc.generate_training_script(
                program.title,
                program.get_key_points(),
                w,
            )
            content.script = json.dumps(script_data)

            # Step 2: Generate training video using Veo
            video_result = gemini_svc.generate_training_video(
                program.title, script_data.get("summary", "")
            )
            if video_result:
                video_bytes, video_mime = video_result
                content.video_mime = video_mime
                url_or_path, _ = storage_svc.upload_video(video_bytes, video_mime)
                if url_or_path:
                    content.video_url = url_or_path

            content.status = "ready"
            generated_count += 1

        except Exception as e:
            print(f"[Training] Error generating content for worker {w.id}: {e}")
            if existing or content:
                content.status = "failed"

        db.session.commit()

    flash(
        f"Generated personalised training content for {generated_count} worker(s).",
        "success",
    )
    return redirect(url_for("training.view_training", program_id=program_id))


@training_bp.route("/training/content/<int:content_id>/video")
@login_required
def training_video(content_id):
    """Serve or redirect to training video."""
    content = db.get_or_404(TrainingContent, content_id)
    if not content.video_url:
        abort(404)
    storage_svc = current_app.extensions["storage_service"]
    public_url = storage_svc.get_public_url(content.video_url)
    return redirect(public_url)
