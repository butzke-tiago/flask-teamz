from flask import current_app as app, render_template
from flask_accept import accept_fallback
from flask_login import login_required
from flask.views import MethodView
from flask_smorest import Blueprint, abort
import logging

from .db import db
from models import PlayerModel, PlayersModel, TeamsModel
from sqlalchemy.exc import SQLAlchemyError

from .schemas import PlayerSchema, PlayerUpdateSchema, EditSchema, PLAYER_POSITIONS


blp = Blueprint("player", __name__, description="Operations on players.")
NO_TEAM = TeamsModel(id=None, name="")


@blp.route("/player/")
class AllPlayers(MethodView):
    @accept_fallback
    def get(self):
        app.logger.info("Getting all the players...")
        players = PlayerModel.query.all()
        app.logger.info(f"Found {len(players)} players.")
        return render_template("player/all.html", players=players, title="Players")

    @get.support("application/json")
    @blp.response(200, PlayerUpdateSchema(many=True))
    def get_json(self):
        app.logger.info("Getting all the players...")
        players = PlayersModel.query.all()
        app.logger.info(f"Found {len(players)} players.")
        return players

    @accept_fallback
    @login_required
    @blp.arguments(PlayerSchema, location="form")
    def post(self, player_info):
        app.logger.debug(player_info)
        player = PlayerModel(**player_info)
        if player.team_id == 0:
            player.team_id = None
        try:
            db.session.add(player)
            db.session.commit()
        except SQLAlchemyError as e:
            app.logger.error(e)
            teams = TeamsModel.query.all()
            return (
                render_template(
                    "player/create.html",
                    title="Create your Player",
                    message=f"{e}",
                    positions=PLAYER_POSITIONS,
                    teams=[NO_TEAM] + teams,
                    player=player,
                ),
                500,
            )
        app.logger.debug(f"Created player: {player}")
        players = PlayerModel.query.all()

        return (
            render_template(
                "player/all.html",
                players=players,
                title="Players",
                message=f"Player {player.name!r} created!",
            ),
            201,
        )

    @post.support("application/json")
    @blp.arguments(PlayerSchema)
    @blp.response(201, PlayerSchema)
    def post_json(self, player_info):
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
    @accept_fallback
    @blp.arguments(EditSchema, location="query", as_kwargs=True)
    def get(self, player_id, **kwargs):
        player = PlayerModel.query.get_or_404(player_id)
        teams = TeamsModel.query.all()
        app.logger.debug(f"Player: {player}")
        if "edit" in kwargs:
            return render_template(
                "player/edit.html",
                title=f"Player: {player.name}",
                positions=PLAYER_POSITIONS,
                teams=[NO_TEAM] + teams,
                player=player,
            )
        else:
            return render_template(
                "player/view.html",
                title=f"Player: {player.name}",
                positions=PLAYER_POSITIONS,
                teams=[NO_TEAM] + teams,
                player=player,
            )

    @get.support("application/json")
    @blp.response(200, PlayerSchema)
    def get_json(self, player_id):
        app.logger.info(f"Getting player {player_id!r}...")
        player = PlayerModel.query.get_or_404(player_id)
        app.logger.debug(f"Player: {player}")
        return player

    @login_required
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
    @login_required
    def put(self, player_info, player_id):
        app.logger.info(f"Updating player {player_id!r}...")
        app.logger.debug(f"Update value: {player_info}")
        player = PlayerModel.query.get_or_404(player_id)
        if "name" in player_info:
            player.name = player_info["name"]
        if "birth_date" in player_info:
            player.birth_date = player_info["birth_date"]
        if "position" in player_info:
            player.position = player_info["position"]
        if "team_id" in player_info:
            player.team_id = player_info["team_id"]
        if "portrait" in player_info:
            player.portrait = player_info["portrait"]
        try:
            db.session.add(player)
            db.session.commit()
        except SQLAlchemyError as e:
            abort(500, message=f"Error: {e}")
        app.logger.debug(f"Player updated: {player}")
        return player


@blp.route("/player/create")
class CreatePlayer(MethodView):
    @accept_fallback
    @login_required
    @blp.arguments(PlayerUpdateSchema, location="query", as_kwargs=True)
    def get(self, **kwargs):
        if "team_id" in kwargs:
            teams = [TeamsModel.query.get(kwargs["team_id"])]
        else:
            teams = [NO_TEAM] + TeamsModel.query.all()
        return render_template(
            "player/create.html",
            title="New Player",
            positions=PLAYER_POSITIONS,
            teams=teams,
            player=PlayerModel(),
        )
