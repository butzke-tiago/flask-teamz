import fasteners
from flask import current_app as app
from flask.views import MethodView
from flask_smorest import Blueprint, abort
import json
import logging
from uuid import uuid4

from .schemas import PlayerSchema, PlayerUpdateSchema
from .schemas import serialize, string_parser


PLAYERS_FILENAME = "storage/players.json"
blp = Blueprint("player", __name__, description="Operations on players.")
logger = logging.getLogger(__name__)

try:
    with open(PLAYERS_FILENAME, "r") as f:
        players = json.load(f, object_hook=string_parser)
except FileNotFoundError:
    players = {}
except json.decoder.JSONDecodeError as e:
    logger.error(f"Error loading players: {e}")
    players = {}


@blp.route("/player")
class AllPlayers(MethodView):
    @blp.response(200, PlayerSchema(many=True))
    def get(self):
        app.logger.info("Getting all the players...")
        app.logger.info(f"Found {len(players)} players.")
        return players.values()

    @blp.arguments(PlayerSchema)
    @blp.response(201, PlayerSchema)
    def post(self, player_info):
        player_id = str(uuid4())
        app.logger.info(f"Creating player {player_id!r}...")
        player = {**player_info, "id": player_id}
        lock = fasteners.InterProcessReaderWriterLock(PLAYERS_FILENAME)
        with lock.write_lock():
            players[player_id] = player
            save()
        app.logger.debug(f"Created player: {player}")
        return player, 201


@blp.route("/player/<uuid:player_id>")
class Player(MethodView):
    @blp.response(200, PlayerSchema)
    def get(self, player_id):
        player_id = str(player_id)
        app.logger.info(f"Getting player {player_id!r}...")
        try:
            player = players[player_id]
        except KeyError:
            message = f"Team {player_id!r} not found!"
            app.logger.error(message)
            abort(404, message=message)
        app.logger.debug(f"Player: {player}")
        return player

    def delete(self, player_id):
        player_id = str(player_id)
        app.logger.info(f"Deleting player {player_id}...")
        lock = fasteners.InterProcessReaderWriterLock(PLAYERS_FILENAME)
        with lock.write_lock():
            try:
                del players[player_id]
            except KeyError:
                message = f"Player {player_id!r} not found!"
                app.logger.error(message)
                abort(404, message=message)
            save()
        message = f"Deleted player: {player_id!r}"
        app.logger.debug(message)
        return {"message": message}

    @blp.arguments(PlayerUpdateSchema)
    @blp.response(200, schema=PlayerSchema)
    def put(self, player_info, player_id):
        player_id = str(player_id)
        app.logger.info(f"Updating player {player_id!r}...")
        app.logger.debug(f"Update value: {player_info}")
        lock = fasteners.InterProcessReaderWriterLock(PLAYERS_FILENAME)
        with lock.write_lock():
            try:
                player = players[player_id]
            except KeyError:
                message = f"Player {player_id!r} not found!"
                app.logger.error(message)
                abort(404, message=message)
            player |= player_info
            save()
        app.logger.debug(f"Player updated: {player}")
        return player


def save():
    with open(PLAYERS_FILENAME, "w") as f:
        json.dump(players, f, indent=2, sort_keys=True, default=serialize)
