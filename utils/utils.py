import json

def load_employees():
    try:
        with open('data/employee.json', 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        return []

def save_employees(employees):
    with open('../data/employee.json', 'w') as file:
        json.dump(employees, file)