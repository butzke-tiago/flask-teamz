from flask import Flask, render_template
from flask_smorest import Api
from resources.team import blp as TeamBlueprint
from resources.player import blp as PlayerBlueprint

from resources.db import db


def create_app():
    app = Flask(__name__)

    app.config["API_TITLE"] = "TeamZ API"
    app.config["API_VERSION"] = "1.0"
    app.config["OPENAPI_VERSION"] = "3.0.3"
    app.config["OPENAPI_URL_PREFIX"] = "/"
    app.config["OPENAPI_SWAGGER_UI_PATH"] = "swagger-ui"
    app.config[
        "OPENAPI_SWAGGER_UI_URL"
    ] = "https://cdn.jsdelivr.net/npm/swagger-ui-dist/"
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///data.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db.init_app(app)

    @app.get("/")
    def home():
        return render_template("home.html", title="TeamZ")

    api = Api(app)

    with app.app_context():
        db.create_all()

    api.register_blueprint(TeamBlueprint)
    api.register_blueprint(PlayerBlueprint)

    return app
