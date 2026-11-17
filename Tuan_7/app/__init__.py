import os

import click
from flask import Flask

from .config import DefaultConfig
from .errors import register_error_handlers
from .extensions import db, migrate
from .products import products_bp


def create_app(config=None):
    app = Flask(__name__)
    app.config.from_object(config or os.environ.get("APP_CONFIG", DefaultConfig))
    app.json.sort_keys = False
    db.init_app(app)
    migrate.init_app(app, db)
    register_error_handlers(app)
    app.register_blueprint(products_bp)

    @app.cli.command("init-db")
    def init_db():
        db.create_all()
        click.echo("database initialised")

    return app
