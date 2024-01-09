from resources.db import db
from resources.schemas import serialize
from flask_login import UserMixin
import json


class UsersModel(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, unique=True, nullable=False)
    email = db.Column(db.String, unique=True, nullable=False)
    password = db.Column(db.String, nullable=False)

    def __str__(self):
        return json.dumps(
            {
                "id": self.id,
                "username": self.username,
                "email": self.email,
                "password": self.password,
            },
            default=serialize,
        )


class UserModel(UsersModel):
    teams = db.relationship("TeamModel", back_populates="owner", lazy="dynamic")
