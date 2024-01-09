from datetime import datetime
from flask import current_app as app, render_template, redirect, url_for, flash
from flask_accept import accept_fallback, accept
from flask_jwt_extended import (
    jwt_required,
    create_access_token,
    create_refresh_token,
    get_jwt,
    get_jwt_identity,
    get_jti,
)
from flask_login import login_required, login_user, logout_user, current_user
from flask.views import MethodView
from flask_smorest import Blueprint, abort
from models import TeamModel, TeamsModel, UserModel, BlocklistModel
from .db import db
from .schemas import TeamSchema, UserSchema, UserBaseSchema, NextSchema
from sqlalchemy.exc import SQLAlchemyError
from passlib.hash import pbkdf2_sha256
from .team import blp as TeamBlueprint
from .player import blp as PlayerBlueprint

blp = Blueprint("user", __name__, description="Operations on users.")
blp.register_blueprint(TeamBlueprint, url_prefix="/user")
blp.register_blueprint(PlayerBlueprint, url_prefix="/user")


@blp.route("/user/")
class User(MethodView):
    @accept_fallback
    @login_required
    def get(self):
        teams = TeamModel.query.filter_by(owner_id=current_user.id).all()
        return render_template(
            "team/all.html",
            title=f"{current_user.username}'s Teams",
            teams=teams,
            user=current_user,
        )

    @get.support("application/json")
    @jwt_required()
    @blp.response(200, TeamSchema(many=True))
    def get_json(self):
        app.logger.info("Getting all the teams...")
        teams = TeamsModel.query.filter_by(owner_id=get_jwt_identity()).all()
        app.logger.info(f"Found {len(teams)} teams.")
        return teams

    @accept_fallback
    @login_required
    def delete(self):
        app.logger.info(f"Deleting user {current_user.id}...")
        user = UserModel.query.get_or_404(current_user.id)
        logout_user()
        db.session.delete(user)
        db.session.commit()
        message = f"Deleted user: {current_user.id!r}"
        app.logger.debug(message)
        flash(f"User {current_user.username!r} deleted!")
        return redirect(url_for("home"))


@blp.route("/user/<int:user_id>")
class Teams(MethodView):
    @accept_fallback
    def get(self, user_id):
        user = UserModel.query.get_or_404(user_id)
        app.logger.debug(f"User: {user}")
        teams = TeamModel.query.filter_by(owner_id=user_id).all()
        return render_template(
            "team/all.html",
            title=f"{user.name}'s Teams",
            teams=teams,
            user=user,
        )

    @get.support("application/json")
    @jwt_required()
    @blp.response(200, UserSchema)
    def get_json(self, user_id):
        app.logger.info(f"Getting user {user_id!r}...")
        user = UserModel.query.get_or_404(user_id)
        user.username = user.name
        return user


@blp.route("/user/signup")
class Signup(MethodView):
    def get(self):
        if current_user.is_authenticated:
            return redirect(url_for("user.User"))
        else:
            return render_template("user/signup.html", title="Signup")

    @accept_fallback
    @blp.arguments(UserSchema, location="form")
    def post(self, user_info):
        app.logger.debug(user_info)
        user_name = user_info["username"]
        user_email = user_info["email"]
        if UserModel.query.filter_by(username=user_name).first():
            flash(f"A user with the name {user_name!r} already exists!")
            return redirect(url_for("user.Signup"))
        if UserModel.query.filter_by(email=user_email).first():
            flash(f"The email {user_email!r} is already associated with another user!!")
            return redirect(url_for("user.Signup"))
        user = UserModel(
            username=user_name,
            email=user_email,
            password=pbkdf2_sha256.hash(user_info["password"]),
        )
        try:
            db.session.add(user)
            db.session.commit()
        except SQLAlchemyError as e:
            app.logger.error(e)
            abort(500, message=f"Error:{e}")
        app.logger.debug(f"Created user: {user}")
        login_user(user)
        return redirect(url_for("team.CreateTeam"), code=302)

    @post.support("application/json")
    @blp.arguments(UserSchema)
    @blp.response(201, UserSchema)
    def post_json(self, user_info):
        user = UserModel(**user_info)
        try:
            db.session.add(user)
            db.session.commit()
        except SQLAlchemyError as e:
            app.logger.error(e)
            abort(500, message=f"Error: {e}")
        app.logger.debug(f"Created user: {user}")
        return user, 201


@blp.route("/user/login")
class Login(MethodView):
    def get(self):
        if current_user.is_authenticated:
            return redirect(url_for("user.User"))
        else:
            return render_template("user/login.html", title="Login")

    @accept_fallback
    @blp.arguments(UserBaseSchema, location="form")
    @blp.arguments(NextSchema, location="query", as_kwargs=True)
    def post(self, user_input, **kwargs):
        app.logger.debug(f"{kwargs}")
        user = UserModel.query.filter_by(username=user_input["username"]).first()
        if user and pbkdf2_sha256.verify(user_input["password"], user.password):
            login_user(user, remember="remember" in user_input)
            if "next" in kwargs:
                return redirect(kwargs["next"])
            return redirect(url_for("user.User"))
        flash("Username or password invalid!")
        return redirect(url_for("user.Login"))

    @post.support("application/json")
    @blp.arguments(UserBaseSchema)
    def post_json(self, user_input):
        user = UserModel.query.filter_by(username=user_input["username"]).first()
        if user and pbkdf2_sha256.verify(user_input["password"], user.password):
            refresh_token = create_refresh_token(identity=user.id)
            access_token = create_access_token(
                identity=user.id,
                fresh=True,
                additional_claims={"rjti": get_jti(refresh_token)},
            )
            app.logger.debug(access_token, refresh_token)
            # login_user(user, remember="remember" in user_input)
            return {"access_token": access_token, "refresh_token": refresh_token}
        return abort(401, message="Username or password invalid!")


@blp.route("/user/logout")
class Logout(MethodView):
    @accept_fallback
    @login_required
    def get(self):
        logout_user()
        flash("Logged out!")
        return redirect(url_for("home"))

    @accept("application/json")
    @jwt_required()
    def delete(self):
        now = datetime.now()
        db.session.add(BlocklistModel(jti=get_jwt()["jti"], created_at=now))
        db.session.add(BlocklistModel(jti=get_jwt()["rjti"], created_at=now))
        db.session.commit()
        return {"message": "Logged out!"}


@blp.route("/user/refresh")
class Refresh(MethodView):
    @accept("application/json")
    @jwt_required(refresh=True)
    def get(self):
        access_token = create_access_token(
            identity=get_jwt_identity(), additional_claims={"rjti": get_jwt()["jti"]}
        )
        return {"access_token": access_token}
