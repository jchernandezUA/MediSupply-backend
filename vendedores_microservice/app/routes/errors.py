from flask import Blueprint, jsonify
from app.services import (
    NotFoundError,
    ConflictError,
    ValidationError,
    UnauthorizedError,
    ForbiddenError,
)

bp_errors = Blueprint("errors", __name__)

def register_error_handlers(app):
    """Registra los manejadores de errores globales de la aplicación."""
    
    @app.errorhandler(ValidationError)
    def handle_validation(err):
        return jsonify(error=str(err)), 400

    @app.errorhandler(UnauthorizedError)
    def handle_unauthorized(err):
        return jsonify(error=str(err)), 401

    @app.errorhandler(ForbiddenError)
    def handle_forbidden(err):
        return jsonify(error=str(err)), 403

    @app.errorhandler(NotFoundError)
    def handle_not_found(err):
        return jsonify(error=str(err)), 404

    @app.errorhandler(ConflictError)
    def handle_conflict(err):
        return jsonify(error=str(err)), 409

    @app.errorhandler(Exception)
    def handle_unexpected(err):
        # Log del error para debugging
        app.logger.error(f"Error inesperado: {err}", exc_info=True)
        return jsonify(error="internal_error"), 500

    app.register_blueprint(bp_errors)
