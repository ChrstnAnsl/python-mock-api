from flask import Flask, request, session
from marshmallow import ValidationError
from schema import schema
import utils.utils as utility
from validation import validation
from flask_jwt_extended import JWTManager, jwt_required, create_access_token
from flask_restx import Api, Resource, fields
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

app.secret_key = '123123123asdasdasd!!!!'
app.config['JWT_SECRET_KEY'] = '123123123asdasdasd!!!!'
jwt = JWTManager(app)

registered_users = {}
employees_data = utility.load_employees()

api = Api(app, version='1.0', title='3cloud Mock API', description='3Cloud QEs Mock API Service by Ansel Fernandez')

user_model = api.model('User', {
    'username': fields.String(required=True, description='Username'),
    'password': fields.String(required=True, description='Password')
})

employee_model = api.model('Employee', {
    'name': fields.String(required=True, description='Employee Name'),
    'designation': fields.String(required=True, description='Employee Designation')
})

response_model = api.model('Response', {
    'message': fields.String(description='Response message'),
    'author': fields.String(description='Author of the message'),
    'status': fields.String(description='Status of the request')
})

public_space = api.namespace('public', description='Exposed API Endpoints', path='/public')

private_space = api.namespace('private', description='Private API Endpoints', path='/private')

employee_space = api.namespace('employees', description='Employees API Endpoints', path='/employees')

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

        access_token = create_access_token(identity=username)
        session['access_token'] = access_token
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
    @private_space.response(200, 'Success', response_model)
    @private_space.response(401, 'Unauthorized - Authentication token not found')
    def get(self):
        """Get user profile"""
        access_token = session.get('access_token')

        if not access_token:
            return {'error': 'Authentication token not found. Please log in.'}, 401

        return {'access_token': access_token}, 200

# Add the "Employees" endpoints to the "Employees" namespace
@employee_space.route('/')
class Employees(Resource):
    @jwt_required()
    @employee_space.marshal_list_with(employee_model)
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
class Employee(Resource):
    @jwt_required()
    @employee_space.marshal_with(employee_model)
    @employee_space.response(404, 'Employee not found')
    def get(self, employee_name):
        """Get an employee by name"""
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
                employee['designation'] = request.json['designation']
                return {'message': 'Employee updated successfully.'}, 200
        employee_space.abort(404, 'Employee not found.')

    @jwt_required()
    @employee_space.expect(employee_model, validate=True)
    @employee_space.response(200, 'Updated', response_model)
    def patch(self, employee_name):
        """Update an employee's designation by name"""
        for employee in employees_data:
            if employee['name'] == employee_name:
                employee['designation'] = request.json['designation']
                return {'message': 'Employee designation updated successfully.'}, 200
        employee_space.abort(404, 'Employee not found.')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
