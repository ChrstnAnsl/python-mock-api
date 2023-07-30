from flask_restx import fields

response_model = {
    'message': fields.String(description='Response message'),
    'author': fields.String(description='Author of the message'),
    'status': fields.String(description='Status of the request')
}