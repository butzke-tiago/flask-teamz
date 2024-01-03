from resources.db import db
import json
from resources.schemas import serialize


class PlayersModel(db.Model):
    __tablename__ = "players"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    birth_date = db.Column(db.Date)
    position = db.Column(db.String)
    team_id = db.Column(db.Integer, db.ForeignKey("teams.id"))
    portrait = db.Column(db.String)

    def __str__(self):
        return json.dumps(
            {
                "id": self.id,
                "name": self.name,
                "birth_date": self.birth_date,
                "position": self.position,
                "team_id": self.team_id,
                "portrait": self.portrait,
            },
            default=serialize,
        )


class PlayerModel(PlayersModel):
    team = db.relationship("TeamModel", back_populates="players")
