import teamz
import logging
from flask_migrate import upgrade


def create_app():
    app = teamz.create_app()
    gunicorn_logger = logging.getLogger("gunicorn.error")
    app.logger.handlers = gunicorn_logger.handlers
    app.logger.setLevel(gunicorn_logger.level)

    with app.app_context():
        upgrade()

    return app
