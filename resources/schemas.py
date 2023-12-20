from marshmallow import Schema, fields
from marshmallow.validate import OneOf
from datetime import date, datetime
from uuid import UUID

PLAYER_POSITIONS = [
    "GK",
    "SW",
    "CB",
    "RB",
    "LB",
    "RWB",
    "LWB",
    "DM",
    "CM",
    "RM",
    "LM",
    "AM",
    "SS",
    "RW",
    "LW",
    "CF",
]

BRAZILIAN_STATES = [
    "AC",
    "AL",
    "AP",
    "AM",
    "BA",
    "CE",
    "DF",
    "ES",
    "GO",
    "MA",
    "MT",
    "MS",
    "MG",
    "PA",
    "PB",
    "PR",
    "PE",
    "PI",
    "RJ",
    "RN",
    "RS",
    "RO",
    "RR",
    "SC",
    "SP",
    "SE",
    "TO",
]


class TeamUpdateSchema(Schema):
    id = fields.Integer(dump_only=True)
    name = fields.Str()
    foundation_date = fields.Date()
    stadium = fields.Str()
    city = fields.Str()
    state = fields.Str(validate=OneOf(BRAZILIAN_STATES))


class TeamBaseSchema(TeamUpdateSchema):
    name = fields.Str(required=True)


class PlayerUpdateSchema(Schema):
    id = fields.Integer(dump_only=True)
    name = fields.Str()
    position = fields.Str(validate=OneOf(PLAYER_POSITIONS))
    birth_date = fields.Date()
    team_id = fields.Integer()


class PlayerBaseSchema(Schema):
    id = fields.Integer(dump_only=True)
    name = fields.Str(required=True)
    position = fields.Str(validate=OneOf(PLAYER_POSITIONS))
    birth_date = fields.Date()


class PlayerSchema(PlayerBaseSchema):
    team_id = fields.Integer(load_only=True)
    team = fields.Nested(TeamBaseSchema(), dump_only=True)


class TeamSchema(TeamBaseSchema):
    players = fields.List(fields.Nested(PlayerBaseSchema()), dump_only=True)


def serialize(obj):
    """JSON serializer for objects not serializable by default json code"""

    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    if isinstance(obj, UUID):
        return str(obj)
    raise TypeError("Type %s not serializable" % type(obj))


def string_parser(obj):
    if "birth_date" in obj:
        obj["birth_date"] = date.fromisoformat(obj["birth_date"])
    if "foundation" in obj:
        obj["foundation"] = date.fromisoformat(obj["foundation"])
    return obj
