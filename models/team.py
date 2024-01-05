from resources.db import db
import json
from resources.schemas import serialize


class TeamsModel(db.Model):
    __tablename__ = "teams"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, unique=True, nullable=False)
    foundation_date = db.Column(db.Date)
    city = db.Column(db.String)
    state = db.Column(db.String)
    stadium = db.Column(db.String)
    logo = db.Column(db.String)
    owner_id = db.Column(db.Integer, db.ForeignKey("users.id"))

    def __str__(self):
        return json.dumps(
            {
                "id": self.id,
                "name": self.name,
                "stadium": self.stadium,
                "city": self.city,
                "state": self.state,
                "foundation_date": self.foundation_date,
                "logo": self.logo,
                "owner_id": self.owner_id,
            },
            default=serialize,
        )


class TeamModel(TeamsModel):
    players = db.relationship("PlayerModel", back_populates="team", lazy="dynamic")
    owner = db.relationship("UserModel", back_populates="teams")


class TeamPlayersModel(TeamsModel):
    players = db.relationship("PlayersModel", lazy="dynamic")
