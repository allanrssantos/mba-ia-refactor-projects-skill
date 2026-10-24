"""Entry point e composition root da Task Manager API."""
import logging

from flask import Flask
from flask_cors import CORS

from config.settings import settings
from database import db
from middlewares.error_handler import register_error_handlers
from routes import register_routes


def create_app(config=None):
    app = Flask(__name__)
    app.config.update(
        SQLALCHEMY_DATABASE_URI=settings.DATABASE_URI,
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        SECRET_KEY=settings.SECRET_KEY,
    )
    if config:
        app.config.update(config)

    CORS(app, origins=settings.cors_origins)
    db.init_app(app)
    register_routes(app)
    register_error_handlers(app)

    with app.app_context():
        db.create_all()

    return app


app = create_app()

if __name__ == '__main__':
    logging.basicConfig(level=settings.LOG_LEVEL, format='%(asctime)s %(levelname)s %(name)s: %(message)s')
    app.run(host=settings.HOST, port=settings.PORT, debug=settings.DEBUG)
