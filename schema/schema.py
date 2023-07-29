from marshmallow import Schema, fields, validate
from validation import validation

class Registration(Schema):
    username = fields.Str(required=True, validate=validate.Length(min=4))
    password = fields.Str(required=True, validate=validation.validate_password)

class Login(Schema):
    username = fields.Str(required=True)
    password = fields.Str(required=True)