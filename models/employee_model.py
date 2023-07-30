from flask_restx import fields

employee_model = {
    'name': fields.String(required=True, description='Employee Name'),
    'position': fields.String(required=True, description='Employee Position'),
    'achievements': fields.List(fields.String, required=True, description='Employee Achievements')
}