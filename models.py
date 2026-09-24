import hashlib
import json
from datetime import datetime, timezone

from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash

db = SQLAlchemy()


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False, index=True)  # "worker" or "supervisor"

    # Worker profile fields (for personalisation)
    preferred_language = db.Column(db.String(10), default="en")  # BCP-47 code
    age = db.Column(db.Integer, nullable=True)
    gender = db.Column(db.String(20), nullable=True)
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    tasks_created = db.relationship(
        "Task", backref="creator", lazy=True, foreign_keys="Task.created_by"
    )
    work_logs = db.relationship("WorkLog", backref="worker", lazy=True, cascade="all, delete-orphan")
    training_programs_created = db.relationship(
        "TrainingProgram", backref="creator", lazy=True, foreign_keys="TrainingProgram.created_by"
    )
    training_contents = db.relationship(
        "TrainingContent", backref="worker", lazy=True, cascade="all, delete-orphan"
    )

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "role": self.role,
            "preferred_language": self.preferred_language,
            "age": self.age,
            "gender": self.gender,
        }

    def __repr__(self):
        return f"<User {self.username} ({self.role})>"


class Task(db.Model):
    __tablename__ = "tasks"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False, index=True)
    description = db.Column(db.Text, nullable=False)  # Original free-form input
    structured_points = db.Column(db.Text, nullable=True)  # JSON from Gemini
    status = db.Column(
        db.String(20), default="pending", index=True
    )  # pending, in_progress, completed
    priority = db.Column(db.String(20), default="medium", index=True)  # low, medium, high
    estimated_duration = db.Column(db.String(50), nullable=True)
    created_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc), index=True
    )
    # Embedding vector stored as JSON array of floats
    embedding_json = db.Column(db.Text, nullable=True)

    # Relationships
    work_logs = db.relationship("WorkLog", backref="task", lazy=True)

    def set_embedding(self, vector):
        self.embedding_json = json.dumps(vector) if vector is not None else None

    def get_embedding(self):
        if self.embedding_json:
            try:
                return json.loads(self.embedding_json)
            except (json.JSONDecodeError, TypeError):
                return None
        return None

    def get_structured_points(self):
        if self.structured_points:
            try:
                return json.loads(self.structured_points)
            except (json.JSONDecodeError, TypeError):
                return []
        return []

    @property
    def matched_logs_count(self):
        return len([log for log in self.work_logs if log.match_score and log.match_score > 0.4])

    def __repr__(self):
        return f"<Task {self.title} ({self.status})>"


class WorkLog(db.Model):
    __tablename__ = "work_logs"

    id = db.Column(db.Integer, primary_key=True)
    worker_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    task_id = db.Column(
        db.Integer, db.ForeignKey("tasks.id"), nullable=True, index=True
    )  # Matched via AI
    original_text = db.Column(db.Text, nullable=False)  # What worker typed/said
    original_language = db.Column(db.String(50), nullable=True)  # Detected language
    translated_text = db.Column(db.Text, nullable=True)  # English translation
    match_score = db.Column(db.Float, nullable=True, index=True)  # Cosine similarity score
    embedding_json = db.Column(db.Text, nullable=True)
    
    # CQC Regulatory Compliance Fields
    cqc_report = db.Column(db.Text, nullable=True)
    cqc_report_final = db.Column(db.Text, nullable=True)
    cqc_status = db.Column(db.String(20), default="none", index=True)  # none, draft, in_review, final
    
    # Security & Audit Fields (Secure by Design)
    audit_hash = db.Column(db.String(64), nullable=True)  # SHA-256 tamper-evident hash
    pii_redacted = db.Column(db.Boolean, default=False)
    
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc), index=True
    )

    # Relationships
    recommendations = db.relationship(
        "CQCRecommendation", backref="work_log", lazy=True, cascade="all, delete-orphan"
    )

    def set_embedding(self, vector):
        self.embedding_json = json.dumps(vector) if vector is not None else None

    def get_embedding(self):
        if self.embedding_json:
            try:
                return json.loads(self.embedding_json)
            except (json.JSONDecodeError, TypeError):
                return None
        return None

    def get_cqc_report(self):
        if self.cqc_report:
            try:
                return json.loads(self.cqc_report)
            except (json.JSONDecodeError, TypeError):
                return None
        return None

    def get_cqc_report_final(self):
        if self.cqc_report_final:
            try:
                return json.loads(self.cqc_report_final)
            except (json.JSONDecodeError, TypeError):
                return None
        return None

    def compute_audit_hash(self):
        """Computes SHA-256 tamper-evident cryptographic hash of the finalized care report."""
        content = self.cqc_report_final or self.cqc_report or self.translated_text or self.original_text
        payload = f"{self.id}:{self.worker_id}:{content}:{self.created_at.isoformat() if self.created_at else ''}"
        self.audit_hash = hashlib.sha256(payload.encode("utf-8")).hexdigest()
        return self.audit_hash

    def __repr__(self):
        return f"<WorkLog by user {self.worker_id} score={self.match_score}>"


class CQCRecommendation(db.Model):
    __tablename__ = "cqc_recommendations"

    id = db.Column(db.Integer, primary_key=True)
    work_log_id = db.Column(db.Integer, db.ForeignKey("work_logs.id"), nullable=False, index=True)
    
    # Recommendation details
    category = db.Column(db.String(30), nullable=False)  # practice_issue | missing_info | documentation_tip
    severity = db.Column(db.String(20), nullable=False)  # critical | important | minor
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)     # What the issue is
    learning_content = db.Column(db.Text)                # AI-generated educational explanation
    suggested_text = db.Column(db.Text)                  # What should be in the report
    report_section = db.Column(db.String(50))            # Which CQC report field this affects
    
    # Worker response & audit
    status = db.Column(db.String(20), default="pending", index=True)  # pending | addressed | acknowledged | dismissed
    completeness_score = db.Column(db.Integer, default=0)
    practice_score = db.Column(db.Integer, default=0)
    worker_response = db.Column(db.Text, nullable=True)  # Free-text response from worker
    
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"<CQCRecommendation {self.title} ({self.severity})>"


class TrainingProgram(db.Model):
    __tablename__ = "training_programs"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    key_points = db.Column(db.Text, nullable=True)  # JSON list of key points
    created_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc), index=True
    )

    # Relationships
    contents = db.relationship("TrainingContent", backref="program", lazy=True, cascade="all, delete-orphan")

    def get_key_points(self):
        if self.key_points:
            try:
                return json.loads(self.key_points)
            except (json.JSONDecodeError, TypeError):
                return []
        return []

    def __repr__(self):
        return f"<TrainingProgram {self.title}>"


class TrainingContent(db.Model):
    __tablename__ = "training_contents"

    id = db.Column(db.Integer, primary_key=True)
    program_id = db.Column(
        db.Integer, db.ForeignKey("training_programs.id"), nullable=False, index=True
    )
    worker_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    language = db.Column(db.String(10), nullable=False)
    age_group = db.Column(db.String(20), nullable=True)
    gender = db.Column(db.String(20), nullable=True)

    # Generated content
    script = db.Column(db.Text, nullable=True)  # Personalised training script
    video_url = db.Column(db.String(500), nullable=True)  # GCS object path or local path
    video_mime = db.Column(db.String(50), nullable=True)  # Actual MIME type from Veo

    status = db.Column(
        db.String(20), default="pending", index=True
    )  # pending, generating, ready, failed
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc), index=True
    )

    def get_script_data(self):
        if self.script:
            try:
                return json.loads(self.script)
            except (json.JSONDecodeError, TypeError):
                return {}
        return {}

    def __repr__(self):
        return f"<TrainingContent program={self.program_id} worker={self.worker_id} ({self.status})>"
