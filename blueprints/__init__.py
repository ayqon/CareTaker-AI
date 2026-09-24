from .api import api_bp
from .auth import auth_bp
from .cqc import cqc_bp
from .supervisor import supervisor_bp
from .training import training_bp
from .worker import worker_bp

__all__ = ["auth_bp", "worker_bp", "supervisor_bp", "cqc_bp", "training_bp", "api_bp"]
