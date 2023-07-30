from flask_restx import fields

user_model = {
    'username': fields.String(required=True, description='Username'),
    'password': fields.String(required=True, description='Password')
}