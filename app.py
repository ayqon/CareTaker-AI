import json
import os
from dotenv import load_dotenv
from flask import Flask
from flask_login import LoginManager
from flask_migrate import Migrate

load_dotenv()

from blueprints import api_bp, auth_bp, cqc_bp, supervisor_bp, training_bp, worker_bp
from config import config_by_name
from models import User, db
from services import GeminiService, StorageService


def create_app(config_name=None):
    """Application factory for CareTaker."""
    if config_name is None:
        config_name = os.environ.get("FLASK_ENV", "development")

    app = Flask(__name__)
    app.config.from_object(config_by_name.get(config_name, config_by_name["default"]))

    # Initialize extensions
    db.init_app(app)
    Migrate(app, db)

    login_manager = LoginManager()
    login_manager.login_view = "auth.index"
    login_manager.login_message_category = "error"
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    # Initialize Core Services & register to app extensions
    gemini_svc = GeminiService(
        project_id=app.config.get("GOOGLE_CLOUD_PROJECT"),
        location=app.config.get("GOOGLE_CLOUD_LOCATION"),
        flash_model=app.config.get("FLASH_MODEL", "gemini-2.5-flash"),
        embedding_model=app.config.get("EMBEDDING_MODEL", "gemini-embedding-001"),
        veo_model=app.config.get("VEO_MODEL", "veo-3.1-generate-001"),
    )
    storage_svc = StorageService(bucket_name=app.config.get("GCS_BUCKET", ""))

    app.extensions["gemini_service"] = gemini_svc
    app.extensions["storage_service"] = storage_svc

    # Custom Jinja2 filter for JSON parsing in templates
    @app.template_filter("from_json")
    def from_json_filter(s):
        if not s:
            return {}
        if isinstance(s, dict) or isinstance(s, list):
            return s
        try:
            return json.loads(s)
        except (json.JSONDecodeError, TypeError):
            return {}

    # Register Blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(worker_bp)
    app.register_blueprint(supervisor_bp)
    app.register_blueprint(cqc_bp)
    app.register_blueprint(training_bp)
    app.register_blueprint(api_bp)

    with app.app_context():
        db.create_all()

    return app


app = create_app()

if __name__ == "__main__":
    debug = os.environ.get("FLASK_DEBUG", "1") == "1"
    port = int(os.environ.get("PORT", 5001))
    app.run(debug=debug, host="0.0.0.0", port=port)
