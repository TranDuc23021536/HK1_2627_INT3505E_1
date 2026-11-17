from flask import jsonify
from marshmallow import ValidationError
from werkzeug.exceptions import HTTPException


class ApiError(Exception):
    status_code = 500
    code = "internal_error"

    def __init__(self, message="", code=None, status=None):
        super().__init__(message)
        if code:
            self.code = code
        if status:
            self.status_code = status
        self.message = message


class NotFound(ApiError):
    status_code = 404
    code = "not_found"


class Conflict(ApiError):
    status_code = 409
    code = "conflict"


class OutOfStock(ApiError):
    status_code = 409
    code = "out_of_stock"


class Unprocessable(ApiError):
    status_code = 422
    code = "validation_error"


def error_response(code, detail, status):
    return jsonify({"error": code, "detail": detail}), status


def register_error_handlers(app):
    @app.errorhandler(ApiError)
    def on_api_error(err):
        return error_response(err.code, err.message, err.status_code)

    @app.errorhandler(ValidationError)
    def on_validation_error(err):
        return error_response("validation_error", err.messages, 422)

    @app.errorhandler(HTTPException)
    def on_http_error(err):
        code = err.name.lower().replace(" ", "_")
        return error_response(code, err.description, err.code)

    @app.errorhandler(Exception)
    def on_unhandled(err):
        app.logger.exception("unhandled")
        return error_response("internal_error", "unexpected server error", 500)
