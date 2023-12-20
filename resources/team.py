from flask import current_app as app
from flask.views import MethodView
from flask_smorest import Blueprint, abort
import logging
from models import TeamModel, TeamsModel, PlayersModel, TeamPlayersModel
from .db import db
from .schemas import TeamSchema, TeamUpdateSchema, PlayerSchema
from sqlalchemy.exc import SQLAlchemyError, IntegrityError


blp = Blueprint("team", __name__, description="Operations on teams.")
logger = logging.getLogger(__name__)


@blp.route("/team")
class AllTeams(MethodView):
    @blp.response(200, TeamSchema(many=True))
    def get(self):
        app.logger.info("Getting all the teams...")
        teams = TeamsModel.query.all()
        app.logger.info(f"Found {len(teams)} teams.")
        return teams

    @blp.arguments(TeamSchema)
    @blp.response(201, TeamSchema)
    def post(self, team_info):
        team = TeamsModel(**team_info)
        try:
            db.session.add(team)
            db.session.commit()
        except SQLAlchemyError as e:
            app.logger.error(e)
            abort(500, message=f"Error: {e}")
        app.logger.debug(f"Created team: {team}")
        return team, 201


@blp.route("/team/<int:team_id>")
class Team(MethodView):
    @blp.response(200, TeamSchema)
    def get(self, team_id):
        app.logger.info(f"Getting team {team_id!r}...")
        team = TeamModel.query.get_or_404(team_id)
        return team

    def delete(self, team_id):
        app.logger.info(f"Deleting team {team_id}...")
        team = TeamModel.query.get_or_404(team_id)
        db.session.delete(team)
        db.session.commit()
        message = f"Deleted team: {team_id!r}"
        app.logger.debug(message)
        return {"message": message}

    @blp.arguments(TeamUpdateSchema)
    @blp.response(200, schema=TeamSchema)
    def put(self, team_info, team_id):
        app.logger.info(f"Updating team {team_id!r}...")
        app.logger.debug(f"Update value: {team_info}")
        team = TeamsModel.query.get_or_404(team_id)
        team.name = team_info.get("name") or team.name
        team.stadium = team_info.get("stadium") or team.stadium
        team.city = team_info.get("city") or team.city
        team.state = team_info.get("state") or team.state
        team.foundation_date = team_info.get("foundation_date") or team.foundation_date
        try:
            db.session.add(team)
            db.session.commit()
        except IntegrityError as e:
            abort(400, message=f"Error: {e}")
        except SQLAlchemyError as e:
            abort(500, message=f"Error: {e}")
        app.logger.debug(f"Team updated: {team}")
        return team


@blp.route("/team/<int:team_id>/players")
class TeamPlayers(MethodView):
    @blp.response(200, PlayerSchema(many=True))
    def get(self, team_id):
        query = PlayersModel.query.filter_by(team_id=team_id)
        team = TeamPlayersModel.query.get_or_404(team_id)
        team_players = team.players.all()
        app.logger.debug(f"Players: {[player.__str__() for player in team_players]}")
        return team_players
