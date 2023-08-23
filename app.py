from flask import Flask, request, session, render_template
from marshmallow import ValidationError
from schema import schema
import utils.utils as utility
from validation import validation
from flask_jwt_extended import JWTManager, jwt_required, create_access_token
from flask_restx import Api, Resource, fields
from flask_cors import CORS
from datetime import datetime, timedelta


app = Flask(__name__, template_folder='templates', static_url_path='/static', static_folder='static')
app.secret_key = '123123123asdasdasd!!!!'
app.config['JWT_SECRET_KEY'] = '123123123asdasdasd!!!!'

CORS(app)

jwt = JWTManager(app)


api = Api(
    app,
    version='1.0',
    title='3Cloud Mock API',
    description='3Cloud QEs Mock API Service by Ansel Fernandez',
    docs='/',
    swagger_ui_bundle='swagger/favicon.ico'
)


user_model = api.model('User', {
    'username': fields.String(required=True, description='Username'),
    'password': fields.String(required=True, description='Password')
})

employee_model = api.model('Employee', {
    'name': fields.String(required=True, description='Employee Name'),
    'position': fields.String(required=True, description='Employee Position'),
    'achievements': fields.List(fields.String, required=True, description='Employee Achievements')
})

response_model = api.model('Response', {
    'message': fields.String(description='Response message'),
    'author': fields.String(description='Author of the message'),
    'status': fields.String(description='Status of the request')
})

public_space = api.namespace('public', description='Exposed API Endpoints', path='/public')

private_space = api.namespace('private', description='Private API Endpoints', path='/private')

employee_space = api.namespace('employees', description='Employees API Endpoints', path='/employees')
employees_data = utility.load_employees()
registered_users = {}

@public_space.route('/login')
class UserLogin(Resource):
    @public_space.expect(user_model, validate=True)
    @public_space.response(200, 'Success', response_model)
    @public_space.response(401, 'Unauthorized - Invalid credentials')
    def post(self):
        """User login"""
        try:
            data = schema.Login().load(request.json)
        except ValidationError as err:
            return validation.throw_error_exception(err.messages)

        username = data['username']
        password = data['password']

        if username not in registered_users or registered_users[username] != password:
            return {'error': 'Invalid credentials. Please check your username and password.'}, 401

        # Token expiration to 30 minutes
        expires = timedelta(minutes=30)
        access_token = create_access_token(identity=username, expires_delta=expires)
        session['access_token'] = access_token
        session['access_token_expiration'] = (datetime.utcnow() + expires).timestamp()
        return {'message': 'Login successful'}, 200

@public_space.route('/register')
class UserRegistration(Resource):
    @public_space.expect(user_model, validate=True)
    @public_space.response(200, 'Success', response_model)
    @public_space.response(409, 'Conflict - Invalid username')
    def post(self):
        """Register a new user"""
        try:
            data = schema.Registration().load(request.json)
        except ValidationError as err:
            return validation.throw_error_exception(err.messages)

        username = data['username']
        password = data['password']

        if username in registered_users:
            return {'error': 'Invalid username.'}, 409

        registered_users[username] = password
        return {'message': 'Registration successful'}, 200

@private_space.route('/profile')
class UserProfile(Resource):
    @private_space.response(200, 'Success - User authenticated')
    @private_space.response(401, 'Unauthorized - Authentication token not found')
    @private_space.response(403, 'Forbidden - Authentication token expired or invalid')
    def get(self):
        """Get user profile"""
        access_token = session.get('access_token')
        token_exp = session.get('access_token_expiration')

        if not access_token:
            return {'error': 'Authentication token not found. Please log in.'}, 401

        if not token_exp:
            return {'error': 'Authentication token expired. Please log in again.'}, 403

        current_time = datetime.utcnow().timestamp()

        if current_time > token_exp:
            return {'error': 'Authentication token expired. Please log in again.'}, 403

        return {'message': 'User profile data goes here', 'access_token': access_token}, 200

# Add the "Employees" endpoints to the "Employees" namespace
@employee_space.route('/')
class Employees(Resource):
    @jwt_required()
    def get(self):
        """Get all employees"""
        return employees_data

    @jwt_required()
    @employee_space.expect(employee_model, validate=True)
    @employee_space.response(201, 'Created', response_model)
    def post(self):
        """Add a new employee"""
        try:
            data = request.json
        except ValidationError as err:
            return validation.throw_error_exception(err.messages)

        employee_name = data['name']
        employee_designation = data['designation']

        new_employee = {
            'name': employee_name,
            'designation': employee_designation
        }

        employees_data.append(new_employee)
        return {'message': 'Employee added successfully.'}, 201

@employee_space.route('/<employee_name>')
class EmployeeByName(Resource):
    @employee_space.response(200, 'Success', response_model)
    def get(self, employee_name):
        """Get an employee's information by name"""
        for employee in employees_data:
            if employee['name'] == employee_name:
                return employee, 200
        employee_space.abort(404, 'Employee not found.')

    @jwt_required()
    @employee_space.expect(employee_model, validate=True)
    @employee_space.response(200, 'Updated', response_model)
    def put(self, employee_name):
        """Update an employee by name"""
        for employee in employees_data:
            if employee['name'] == employee_name:
                employee['name'] = request.json['name']
                employee['position'] = request.json['position']
                employee['achievements'] = request.json['achievements']
                return {'message': 'Employee updated successfully.'}, 200
        employee_space.abort(404, 'Employee not found.')

    @employee_space.expect(employee_model, validate=True)
    @employee_space.response(200, 'Updated', response_model)
    def patch(self, employee_name):
        """Update an employee's information by name"""
        for employee in employees_data:
            if employee['name'] == employee_name:
                if 'name' in request.json:
                    employee['name'] = request.json['name']
                if 'position' in request.json:
                    employee['position'] = request.json['position']
                if 'achievements' in request.json:
                    employee['achievements'] = request.json['achievements']
                return {'message': 'Employee information updated successfully.'}, 200
        employee_space.abort(404, 'Employee not found.')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
