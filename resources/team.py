import fasteners
from flask import current_app as app
from flask.views import MethodView
from flask_smorest import Blueprint, abort
import json
import logging
from uuid import uuid4

from .player import players
from .schemas import TeamSchema, TeamUpdateSchema, PlayerSchema
from .schemas import serialize, string_parser


TEAMS_FILENAME = "storage/teams.json"
blp = Blueprint("team", __name__, description="Operations on teams.")
logger = logging.getLogger(__name__)

try:
    with open(TEAMS_FILENAME, "r") as f:
        teams = json.load(f, object_hook=string_parser)
except FileNotFoundError:
    teams = {}
except json.decoder.JSONDecodeError as e:
    logger.error(f"Error loading teams: {e}")
    teams = {}


@blp.route("/team")
class AllTeams(MethodView):
    @blp.response(200, TeamSchema(many=True))
    def get(self):
        app.logger.info("Getting all the teams...")
        app.logger.info(f"Found {len(teams)} teams.")
        return teams.values()

    @blp.arguments(TeamSchema)
    @blp.response(201, TeamSchema)
    def post(self, team_info):
        team_id = str(uuid4())
        app.logger.info(f"Creating team {team_id!r}...")
        team = {**team_info, "id": team_id}
        lock = fasteners.InterProcessReaderWriterLock(TEAMS_FILENAME)
        with lock.write_lock():
            teams[team_id] = team
            save()
        app.logger.debug(f"Created team: {team}")
        return team, 201


@blp.route("/team/<uuid:team_id>")
class Team(MethodView):
    @blp.response(200, TeamSchema)
    def get(self, team_id):
        team_id = str(team_id)
        app.logger.info(f"Getting team {team_id!r}...")
        try:
            team = teams[team_id]
        except KeyError:
            message = f"Team {team_id!r} not found!"
            app.logger.error(message)
            abort(404, message=message)
        app.logger.debug(f"Team: {team}")
        return team

    def delete(self, team_id):
        team_id = str(team_id)
        app.logger.info(f"Deleting team {team_id}...")
        lock = fasteners.InterProcessReaderWriterLock(TEAMS_FILENAME)
        with lock.write_lock():
            try:
                del teams[team_id]
            except KeyError:
                message = f"Team {team_id!r} not found!"
                app.logger.error(message)
                abort(404, message=message)
            save()
        message = f"Deleted team: {team_id!r}"
        app.logger.debug(message)
        return {"message": message}

    @blp.arguments(TeamUpdateSchema)
    @blp.response(200, schema=TeamSchema)
    def put(self, team_info, team_id):
        team_id = str(team_id)
        app.logger.info(f"Updating team {team_id!r}...")
        app.logger.debug(f"Update value: {team_info}")
        lock = fasteners.InterProcessReaderWriterLock(TEAMS_FILENAME)
        with lock.write_lock():
            try:
                team = teams[team_id]
            except KeyError:
                message = f"Team {team_id!r} not found!"
                app.logger.error(message)
                abort(404, message=message)
            team |= team_info
            save()
        app.logger.debug(f"Team updated: {team}")
        return team


@blp.route("/team/<uuid:team_id>/players")
class TeamPlayers(MethodView):
    @blp.response(200, PlayerSchema(many=True))
    def get(self, team_id):
        team_id = str(team_id)
        app.logger.info(f"Getting all players from team {team_id!r}...")
        if not team_id in teams:
            message = f"Team {team_id!r} not found!"
            app.logger.debug(message)
            abort(404, message=message)
        team_players = {
            player_id: player
            for player_id, player in players.items()
            if "team_id" in player and player["team_id"] == team_id
        }
        app.logger.info(f"Found {len(team_players)} players.")
        app.logger.debug(f"Players: {team_players}")
        return team_players.values(), 200


def save():
    with open(TEAMS_FILENAME, "w") as f:
        json.dump(teams, f, indent=2, sort_keys=True, default=serialize)
