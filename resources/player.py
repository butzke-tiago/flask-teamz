from flask import current_app as app
from flask.views import MethodView
from flask_smorest import Blueprint, abort
import logging

from .db import db
from models import PlayerModel, PlayersModel
from sqlalchemy.exc import SQLAlchemyError

from .schemas import PlayerSchema, PlayerUpdateSchema


PLAYERS_FILENAME = "storage/players.json"
blp = Blueprint("player", __name__, description="Operations on players.")
logger = logging.getLogger(__name__)


@blp.route("/player")
class AllPlayers(MethodView):
    @blp.response(200, PlayerUpdateSchema(many=True))
    def get(self):
        app.logger.info("Getting all the players...")
        players = PlayersModel.query.all()
        app.logger.info(f"Found {len(players)} players.")
        return players

    @blp.arguments(PlayerSchema)
    @blp.response(201, PlayerSchema)
    def post(self, player_info):
        player = PlayerModel(**player_info)
        try:
            db.session.add(player)
            db.session.commit()
        except SQLAlchemyError as e:
            app.logger.error(e)
            abort(500, message=f"Error:{e}")
        app.logger.debug(f"Created player: {player}")
        return player, 201


@blp.route("/player/<int:player_id>")
class Player(MethodView):
    @blp.response(200, PlayerSchema)
    def get(self, player_id):
        app.logger.info(f"Getting player {player_id!r}...")
        player = PlayerModel.query.get_or_404(player_id)
        app.logger.debug(f"Player: {player}")
        return player

    def delete(self, player_id):
        app.logger.info(f"Deleting player {player_id}...")
        player = PlayerModel.query.get_or_404(player_id)
        db.session.delete(player)
        db.session.commit()
        message = f"Deleted player: {player_id!r}"
        app.logger.debug(message)
        return {"message": message}

    @blp.arguments(PlayerUpdateSchema)
    @blp.response(200, schema=PlayerSchema)
    def put(self, player_info, player_id):
        app.logger.info(f"Updating player {player_id!r}...")
        app.logger.debug(f"Update value: {player_info}")
        player = PlayerModel.query.get_or_404(player_id)
        player.name = player_info.get("name") or player.name
        player.birth_date = player_info.get("birth_date") or player.birth_date
        player.position = player_info.get("position") or player.position
        player.team_id = player_info.get("team_id") or player.team_id
        try:
            db.session.add(player)
            db.session.commit()
        except SQLAlchemyError as e:
            abort(500, message=f"Error: {e}")
        app.logger.debug(f"Player updated: {player}")
        return player
