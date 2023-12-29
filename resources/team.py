from flask import current_app as app, render_template
from flask_accept import accept_fallback
from flask.views import MethodView
from flask_smorest import Blueprint, abort
import logging
from models import TeamModel, TeamsModel, PlayersModel, TeamPlayersModel
from .db import db
from .schemas import (
    TeamSchema,
    TeamUpdateSchema,
    PlayerSchema,
    EditSchema,
    BRAZILIAN_STATES,
)
from sqlalchemy.exc import SQLAlchemyError, IntegrityError


blp = Blueprint("team", __name__, description="Operations on teams.")
logger = logging.getLogger(__name__)


@blp.route("/team/")
class AllTeams(MethodView):
    @accept_fallback
    def get(self):
        teams = TeamModel.query.all()
        return render_template("teams.html", teams=teams, title="Teams")

    @get.support("application/json")
    @blp.response(200, TeamSchema(many=True))
    def get_json(self):
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
    @accept_fallback
    @blp.arguments(EditSchema, location="query", as_kwargs=True)
    def get(self, team_id, **kwargs):
        team = TeamModel.query.get_or_404(team_id)
        app.logger.debug(f"Team: {team}")
        if "edit" in kwargs:
            return render_template(
                "edit_team.html",
                title=f"Team: {team.name}",
                states=["Select..."] + list(BRAZILIAN_STATES),
                team=team,
            )
        else:
            return render_template(
                "team.html",
                title=f"Team: {team.name}",
                states=["Select..."] + list(BRAZILIAN_STATES),
                team=team,
            )

    @get.support("application/json")
    @blp.response(200, TeamSchema)
    def get_json(self, team_id):
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
        if "name" in team_info:
            team.name = team_info["name"]
        if "stadium" in team_info:
            team.stadium = team_info["stadium"]
        if "city" in team_info:
            team.city = team_info["city"]
        if "state" in team_info:
            team.state = team_info["state"]
        if "foundation_date" in team_info:
            team.foundation_date = team_info["foundation_date"]
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
