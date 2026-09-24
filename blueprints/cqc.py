import json
from flask import Blueprint, abort, current_app, flash, redirect, render_template, request, url_for
from flask_login import current_user

from blueprints.auth import role_required
from models import CQCRecommendation, WorkLog, db
from services.security_service import SecurityService

cqc_bp = Blueprint("cqc", __name__)


@cqc_bp.route("/worker/log/<int:log_id>/cqc-report", methods=["POST"])
@role_required("worker")
def generate_cqc_report(log_id):
    """Generate a CQC Regulation 17 compliant report for a work log entry."""
    log = db.get_or_404(WorkLog, log_id)

    if log.worker_id != current_user.id:
        abort(403)

    gemini_svc = current_app.extensions["gemini_service"]

    try:
        report_data = gemini_svc.generate_cqc_report(log, current_user, log.task)
        log.cqc_report = json.dumps(report_data)
        log.cqc_status = "draft"
        log.compute_audit_hash()
        db.session.commit()
        flash("CQC-compliant draft report generated successfully.", "success")
    except Exception as e:
        flash(f"Error generating CQC report: {str(e)}", "error")

    return redirect(url_for("worker.worker_dashboard"))


@cqc_bp.route("/worker/log/<int:log_id>/cqc-report/view")
@role_required("worker")
def view_cqc_report(log_id):
    """Render a printable CQC report."""
    log = db.get_or_404(WorkLog, log_id)

    if log.worker_id != current_user.id:
        abort(403)
    if not log.cqc_report:
        abort(404)

    report = log.get_cqc_report()
    return render_template("cqc_report.html", log=log, report=report, is_final=False)


@cqc_bp.route("/worker/log/<int:log_id>/cqc-review", methods=["POST"])
@role_required("worker")
def trigger_cqc_review(log_id):
    """Trigger AI review of a CQC report."""
    log = db.get_or_404(WorkLog, log_id)
    if log.worker_id != current_user.id:
        abort(403)
    if not log.cqc_report:
        flash("Generate a CQC report first before requesting a review.", "error")
        return redirect(url_for("worker.worker_dashboard"))

    gemini_svc = current_app.extensions["gemini_service"]

    try:
        report = log.get_cqc_report()
        review_data = gemini_svc.review_cqc_report(log, report, current_user, log.task)

        # Delete any existing recommendations for this log
        CQCRecommendation.query.filter_by(work_log_id=log.id).delete()

        # Save each recommendation
        for rec in review_data.get("recommendations", []):
            recommendation = CQCRecommendation(
                work_log_id=log.id,
                category=rec.get("category", "documentation_tip"),
                severity=rec.get("severity", "minor"),
                title=rec.get("title", ""),
                description=rec.get("description", ""),
                learning_content=rec.get("learning_content", ""),
                suggested_text=rec.get("suggested_text", ""),
                report_section=rec.get("report_section", ""),
                completeness_score=review_data.get("overall_completeness_score", 0),
                practice_score=review_data.get("overall_practice_score", 0),
            )
            db.session.add(recommendation)

        log.cqc_status = "in_review"
        db.session.commit()

        flash(
            f"AI review complete: {len(review_data.get('recommendations', []))} recommendations generated.",
            "success",
        )
    except Exception as e:
        flash(f"Error generating review: {str(e)}", "error")

    return redirect(url_for("cqc.view_cqc_review", log_id=log_id))


@cqc_bp.route("/worker/log/<int:log_id>/cqc-review", methods=["GET"])
@role_required("worker")
def view_cqc_review(log_id):
    """View AI review recommendations."""
    log = db.get_or_404(WorkLog, log_id)
    if log.worker_id != current_user.id:
        abort(403)

    recommendations = (
        CQCRecommendation.query.filter_by(work_log_id=log.id)
        .order_by(
            db.case(
                (CQCRecommendation.severity == "critical", 0),
                (CQCRecommendation.severity == "important", 1),
                (CQCRecommendation.severity == "minor", 2),
            )
        )
        .all()
    )

    report = log.get_cqc_report() or {}

    completeness_score = recommendations[0].completeness_score if recommendations else 0
    practice_score = recommendations[0].practice_score if recommendations else 0

    return render_template(
        "cqc_review.html",
        log=log,
        report=report,
        recommendations=recommendations,
        completeness_score=completeness_score,
        practice_score=practice_score,
    )


@cqc_bp.route("/worker/log/<int:log_id>/cqc-review/respond", methods=["POST"])
@role_required("worker")
def respond_to_cqc_review(log_id):
    """Submit worker responses to all recommendations."""
    log = db.get_or_404(WorkLog, log_id)
    if log.worker_id != current_user.id:
        abort(403)

    recommendations = CQCRecommendation.query.filter_by(work_log_id=log.id).all()

    for rec in recommendations:
        status = request.form.get(f"status_{rec.id}", "pending")
        response_text = request.form.get(f"response_{rec.id}", "").strip()
        
        # Validate response for prompt injection
        if response_text:
            is_safe, _ = SecurityService.check_prompt_injection(response_text)
            if not is_safe:
                flash(f"Warning: Disallowed characters in response for '{rec.title}'.", "error")
                continue

        rec.status = status
        rec.worker_response = response_text if response_text else None

    db.session.commit()
    flash("Responses saved successfully.", "success")
    return redirect(url_for("cqc.view_cqc_review", log_id=log_id))


@cqc_bp.route("/worker/log/<int:log_id>/cqc-report/finalise", methods=["POST"])
@role_required("worker")
def finalise_cqc_report(log_id):
    """Regenerate the CQC report incorporating worker responses and sign with SHA-256 audit hash."""
    log = db.get_or_404(WorkLog, log_id)
    if log.worker_id != current_user.id:
        abort(403)
    if not log.cqc_report:
        flash("No CQC report to finalise.", "error")
        return redirect(url_for("worker.worker_dashboard"))

    recommendations = CQCRecommendation.query.filter_by(work_log_id=log.id).all()
    unanswered = [r for r in recommendations if r.status == "pending"]
    if unanswered:
        flash(
            f"Please address all {len(unanswered)} remaining recommendation(s) before finalising.",
            "error",
        )
        return redirect(url_for("cqc.view_cqc_review", log_id=log_id))

    gemini_svc = current_app.extensions["gemini_service"]

    try:
        original_report = log.get_cqc_report()
        recs_with_responses = [
            {
                "title": r.title,
                "category": r.category,
                "description": r.description,
                "suggested_text": r.suggested_text,
                "report_section": r.report_section,
                "status": r.status,
                "worker_response": r.worker_response or "",
            }
            for r in recommendations
        ]

        final_report = gemini_svc.regenerate_final_report(
            original_report, recs_with_responses, log, current_user
        )
        log.cqc_report_final = json.dumps(final_report)
        log.cqc_status = "final"
        log.compute_audit_hash()
        db.session.commit()

        flash("Final CQC report generated and cryptographically sealed.", "success")
    except Exception as e:
        flash(f"Error finalising report: {str(e)}", "error")

    return redirect(url_for("cqc.view_cqc_review", log_id=log_id))


@cqc_bp.route("/worker/log/<int:log_id>/cqc-report/final/view")
@role_required("worker")
def view_final_cqc_report(log_id):
    """Render the printable final CQC report."""
    log = db.get_or_404(WorkLog, log_id)
    if log.worker_id != current_user.id:
        abort(403)
    if not log.cqc_report_final:
        abort(404)

    report = log.get_cqc_report_final()
    return render_template("cqc_report.html", log=log, report=report, is_final=True)
