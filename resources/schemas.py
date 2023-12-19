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


class TeamSchema(Schema):
    id = fields.UUID(dump_only=True)
    name = fields.Str(required=True)
    foundation = fields.Date()
    stadium = fields.Str()
    city = fields.Str()
    state = fields.Str()


class TeamUpdateSchema(Schema):
    id = fields.UUID(dump_only=True)
    name = fields.Str()
    foundation = fields.Date()
    stadium = fields.Str()
    city = fields.Str()
    state = fields.Str(validate=OneOf(BRAZILIAN_STATES))


class PlayerSchema(Schema):
    id = fields.UUID(dump_only=True)
    name = fields.Str(required=True)
    position = fields.Str(
        required=True,
        validate=OneOf(PLAYER_POSITIONS),
    )
    birth_date = fields.Date()
    team_id = fields.UUID()


class PlayerUpdateSchema(Schema):
    id = fields.UUID(dump_only=True)
    name = fields.Str()
    position = fields.Str(validate=OneOf(PLAYER_POSITIONS))
    birth_date = fields.Date()
    team_id = fields.UUID()


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
