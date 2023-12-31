from datetime import timedelta
from flask import Flask, render_template, redirect, url_for
from flask_jwt_extended import JWTManager
from flask_login import LoginManager, current_user
from flask_smorest import Api
from resources.team import blp as TeamBlueprint
from resources.player import blp as PlayerBlueprint
from resources.user import blp as UserBlueprint
from flask_migrate import Migrate
from resources.db import db
from models import UserModel, BlocklistModel


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
    app.config["JWT_SECRET_KEY"] = "1234"
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=1)

    db.init_app(app)
    migrate = Migrate(app, db, render_as_batch=True)
    jwt_manager = JWTManager(app)

    @app.get("/")
    def home():
        if current_user.is_authenticated:
            return redirect(url_for("user.User"))
        else:
            return render_template("home.html", title="TeamZ")

    api = Api(app)

    api.register_blueprint(TeamBlueprint)
    api.register_blueprint(PlayerBlueprint)
    api.register_blueprint(UserBlueprint)

    login_manager = LoginManager()
    login_manager.login_view = "user.Login"
    login_manager.init_app(app)
    app.secret_key = "1234"

    @login_manager.user_loader
    def load_user(user_id):
        # since the user_id is just the primary key of our user table, use it in the query for the user
        return UserModel.query.get(int(user_id))

    @jwt_manager.token_in_blocklist_loader
    def check_if_token_revoked(jwt_header, jwt_payload: dict) -> bool:
        jti = jwt_payload["jti"]
        token = BlocklistModel.query.filter_by(jti=jti).scalar()
        return token is not None

    @jwt_manager.user_lookup_loader
    def user_lookup_callback(_jwt_header, jwt_data):
        identity = jwt_data["sub"]
        return UserModel.query.get(int(identity))

    return app
