from flask import Blueprint, jsonify
from app.services import NotFoundError, ConflictError, ValidationError

bp_errors = Blueprint("errors", __name__)

def register_error_handlers(app):
    @app.errorhandler(NotFoundError)
    def handle_not_found(err):
        return jsonify(error=str(err)), 404

    @app.errorhandler(ConflictError)
    def handle_conflict(err):
        return jsonify(error=str(err)), 409

    @app.errorhandler(ValidationError)
    def handle_validation(err):
        return jsonify(error=str(err)), 400

    @app.errorhandler(Exception)
    def handle_unexpected(err):
        return jsonify(error="internal_error"), 500

    app.register_blueprint(bp_errors)
