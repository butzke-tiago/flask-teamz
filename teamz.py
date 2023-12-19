from flask import Flask
from flask_smorest import Api
from resources.team import blp as TeamBlueprint
from resources.player import blp as PlayerBlueprint

app = Flask(__name__)

app.config["API_TITLE"] = "TeamZ API"
app.config["API_VERSION"] = "1.0"
app.config["OPENAPI_VERSION"] = "3.0.3"
app.config["OPENAPI_URL_PREFIX"] = "/"
app.config["OPENAPI_SWAGGER_UI_PATH"] = "swagger-ui"
app.config["OPENAPI_SWAGGER_UI_URL"] = "https://cdn.jsdelivr.net/npm/swagger-ui-dist/"


@app.get("/")
def home():
    return "Welcome to TeamZ App!"


api = Api(app)
api.register_blueprint(TeamBlueprint)
api.register_blueprint(PlayerBlueprint)
