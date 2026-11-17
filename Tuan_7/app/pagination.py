from flask import request

from .errors import Unprocessable


def parse_pagination():
    try:
        page = int(request.args.get("page", 1))
        size = int(request.args.get("size", 20))
    except ValueError:
        raise Unprocessable("page and size must be integers")
    return max(1, page), min(100, max(1, size))
