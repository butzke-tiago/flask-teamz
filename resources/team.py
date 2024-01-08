from flask import current_app as app, render_template, flash, redirect, url_for
from flask_accept import accept_fallback
from flask_login import login_required, current_user
from flask_smorest import Blueprint, abort
from flask.views import MethodView
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


@blp.route("/team/")
class AllTeams(MethodView):
    @accept_fallback
    def get(self):
        app.logger.info("Getting all the teams...")
        teams = TeamModel.query.all()
        app.logger.info(f"Found {len(teams)} teams.")
        return render_template("team/all.html", teams=teams, title="Teams")

    @get.support("application/json")
    @blp.response(200, TeamSchema(many=True))
    def get_json(self):
        app.logger.info("Getting all the teams...")
        teams = TeamsModel.query.all()
        app.logger.info(f"Found {len(teams)} teams.")
        return teams

    @accept_fallback
    @login_required
    @blp.arguments(TeamSchema, location="form")
    def post(self, team_info):
        app.logger.debug(team_info)
        app.logger.debug(current_user.id)
        team = TeamModel(owner_id=current_user.id, **team_info)
        try:
            db.session.add(team)
            db.session.commit()
        except IntegrityError as e:
            app.logger.error(e)
            flash("Team already exists!")
            return (
                render_template(
                    "team/create.html",
                    title="Create your Team",
                    states=BRAZILIAN_STATES,
                    team=team,
                ),
                201,
            )
        except SQLAlchemyError as e:
            app.logger.error(e)
            return (
                render_template(
                    "team/create.html",
                    title="Create your Team",
                    message=f"{e}",
                    states=BRAZILIAN_STATES,
                ),
                500,
            )
        app.logger.debug(f"Created team: {team}")
        flash(f"Team {team.name!r} created!")
        return redirect(url_for("user.User"))

    @post.support("application/json")
    @blp.arguments(TeamSchema)
    @blp.response(201, TeamSchema)
    def post_json(self, team_info):
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
        if (
            "edit" in kwargs
            and current_user.is_authenticated
            and (not team.owner_id or current_user.id == team.owner_id)
        ):
            return render_template(
                "team/edit.html",
                title=f"Team: {team.name}",
                states=BRAZILIAN_STATES,
                team=team,
            )
        else:
            return render_template(
                "team/view.html",
                title=f"Team: {team.name}",
                states=BRAZILIAN_STATES,
                team=team,
            )

    @get.support("application/json")
    @blp.response(200, TeamSchema)
    def get_json(self, team_id):
        app.logger.info(f"Getting team {team_id!r}...")
        team = TeamModel.query.get_or_404(team_id)
        return team

    @login_required
    def delete(self, team_id):
        app.logger.info(f"Deleting team {team_id}...")
        team = TeamModel.query.get_or_404(team_id)
        db.session.delete(team)
        db.session.commit()
        message = f"Deleted team: {team_id!r}"
        app.logger.debug(message)
        flash(f"Team {team.name!r} deleted!")
        return {"message": message}

    @blp.arguments(TeamUpdateSchema)
    @blp.response(200, schema=TeamSchema)
    @login_required
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
        if "logo" in team_info:
            team.logo = team_info["logo"]
        team.owner_id = current_user.id
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


@blp.route("/team/create")
class CreateTeam(MethodView):
    @accept_fallback
    @login_required
    def get(self):
        return render_template(
            "team/create.html",
            title="Create your Team",
            states=BRAZILIAN_STATES,
            team=TeamModel(id=0),
        )
