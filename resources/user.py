from flask import current_app as app, render_template, redirect, session, url_for, flash
from flask_accept import accept_fallback
from flask_login import login_required, login_user, logout_user, current_user
from flask.views import MethodView
from flask_smorest import Blueprint, abort
from models import TeamModel, TeamsModel, UserModel
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
            title=f"{current_user.name}'s Teams",
            teams=teams,
            user=current_user,
        )

    @get.support("application/json")
    @blp.response(200, TeamSchema(many=True))
    def get_json(self):
        app.logger.info("Getting all the teams...")
        teams = TeamsModel.query.all()
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
        flash(f"User {current_user.name!r} deleted!")
        return redirect(url_for("home"))


@blp.route("/user/<int:user_id>")
class Teams(MethodView):
    @accept_fallback
    def get(self, user_id):
        user = UserModel.query.get_or_404(user_id)
        app.logger.debug(f"User: {user}")
        return "Under Construction"

    @get.support("application/json")
    @blp.response(200, UserSchema)
    def get_json(self, user_id):
        app.logger.info(f"Getting user {user_id!r}...")
        user = UserModel.query.get_or_404(user_id)
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
        if UserModel.query.filter_by(name=user_name).first():
            flash(f"A user with the name {user_name!r} already exists!")
            return redirect(url_for("user.Signup"))
        if UserModel.query.filter_by(email=user_email).first():
            flash(f"The email {user_email!r} is already associated with another user!!")
            return redirect(url_for("user.Signup"))
        user = UserModel(
            name=user_name,
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
        user = UserModel.query.filter_by(name=user_input["username"]).first()
        if user and pbkdf2_sha256.verify(user_input["password"], user.password):
            login_user(user, remember="remember" in user_input)
            if "next" in kwargs:
                return redirect(kwargs["next"])
            return redirect(url_for("user.User"))
        flash("Username or password invalid!")
        return redirect(url_for("user.Login"))


@blp.route("/user/logout")
class Logout(MethodView):
    @login_required
    def get(self):
        logout_user()
        flash("Logged out!")
        return redirect(url_for("home"))
