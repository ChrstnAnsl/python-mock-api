from flask import Flask, request, session
from marshmallow import ValidationError
from schema import schema
import utils.utils as utility
from validation import validation
from flask_jwt_extended import JWTManager, jwt_required, create_access_token
from flask_restx import Api, Resource, fields
from flask_cors import CORS
from datetime import datetime, timedelta
import models as model

app = Flask(__name__)
CORS(app)

app.secret_key = '8a9c8d9c-2eae-11ee-be56-0242ac120002'
app.config['JWT_SECRET_KEY'] = '772f614a-980c-4de7-80e7-fec271bd295a'
jwt = JWTManager(app)

registered_users = {}
employees_data = utility.load_employees()

api = Api(app, version='1.0', title='3cloud Mock API', description='3Cloud QEs Mock API Service by Ansel Fernandez')

public_space = api.namespace('public', description='Exposed API Endpoints', path='/public')
@public_space.route('/login')
class UserLogin(Resource):
    @public_space.expect(model.user_model, validate=True)
    @public_space.response(200, 'Success', model.response_model)
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
        return {'message': 'Login successful'}, 200

@public_space.route('/register')
class UserRegistration(Resource):
    @public_space.expect(model.user_model, validate=True)
    @public_space.response(200, 'Success', model.response_model)
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

private_space = api.namespace('private', description='Private API Endpoints', path='/private')
@private_space.route('/profile')
class UserProfile(Resource):
    @private_space.response(200, 'Success - User authenticated')
    @private_space.response(401, 'Unauthorized - Authentication token not found')
    def get(self):
        """Get user profile"""
        access_token = session.get('access_token')

        if not access_token:
            return {'error': 'Authentication token not found. Please log in.'}, 401

        token_exp = session.get('access_token_expiration')

        if not token_exp or datetime.utcnow().timestamp() > token_exp:
            return {'error': 'Authentication token expired. Please log in again.'}, 401

        current_time = datetime.utcnow()
        token_exp_datetime = datetime.fromtimestamp(token_exp)

        if current_time > token_exp_datetime:
            return {'error': 'Authentication token expired. Please log in again.'}, 401
        
        return {'access_token': access_token}, 200

employee_space = api.namespace('employees', description='Employees API Endpoints', path='/employees')
@employee_space.route('/')
class Employees(Resource):
    @jwt_required()
    def get(self):
        """Get all employees"""
        return employees_data

    @jwt_required()
    @employee_space.expect(model.employee_model, validate=True)
    @employee_space.response(201, 'Created', model.response_model)
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
    @employee_space.response(200, 'Success', model.response_model)
    def get(self, employee_name):
        """Get an employee's information by name"""
        for employee in employees_data:
            if employee['name'] == employee_name:
                return employee, 200
        employee_space.abort(404, 'Employee not found.')

    @jwt_required()
    @employee_space.expect(model.employee_model, validate=True)
    @employee_space.response(200, 'Updated', model.response_model)
    def put(self, employee_name):
        """Update an employee by name"""
        for employee in employees_data:
            if employee['name'] == employee_name:
                employee['name'] = request.json['name']
                employee['position'] = request.json['position']
                employee['achievements'] = request.json['achievements']
                return {'message': 'Employee updated successfully.'}, 200
        employee_space.abort(404, 'Employee not found.')

    @employee_space.expect(model.employee_model, validate=True)
    @employee_space.response(200, 'Updated', model.response_model)
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
