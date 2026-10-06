import logging
import uuid
from flask import jsonify, request
from werkzeug.exceptions import HTTPException

ERROR_BASE = "https://api.example.com/probs"
PROBLEM_JSON = "application/problem+json"

log = logging.getLogger("api.errors")

class ApiProblem(Exception):
    def __init__(self, status, title, detail=None, type_path=None, **extra):
        super().__init__(title)
        self.status = status
        self.title = title
        self.detail = detail
        self.type_path = type_path
        self.extra = extra
    @property
    def type(self):
        return f"{ERROR_BASE}/{self.type_path}" if self.type_path else "about:blank"

def _problem(status, title, detail=None, type_path=None, trace_id=None, **extra):
    body = {
        "type": f"{ERROR_BASE}/{type_path}" if type_path else "about:blank",
        "title": title,
        "status": status,
        "instance": request.path,
        "trace_id": trace_id or str(uuid.uuid4()),
    }
    if detail:
        body["detail"] = detail
    body.update(extra)

    resp = jsonify(body)
    resp.status_code = status
    resp.headers["Content-Type"] = PROBLEM_JSON
    return resp

def register_error_handlers(app):
    @app.errorhandler(ApiProblem)
    def handle_api_problem(err):
        return _problem(err.status, err.title, err.detail, err.type_path, **err.extra)
    @app.errorhandler(HTTPException)
    def handle_http_exception(err):
        return _problem(err.code, err.name, err.description)

    @app.errorhandler(Exception)
    def handle_unexpected(err):
        trace_id = str(uuid.uuid4())
        log.exception("Unhandled exception trace_id=%s path=%s", trace_id, request.path)
        return _problem(
            500,
            "Internal Server Error",
            "An unexpected error occurred. Please contact support with the trace_id.",
            "internal-error",
            trace_id=trace_id,
        )