from marshmallow import ValidationError
import re

def validate_password(value):
    if len(value) < 8:
        raise ValidationError('Password must be at least 8 characters')
    if not any(char.isupper() for char in value):
        raise ValidationError('Password must have at least one capital letter.')
    if not any(char.islower() for char in value):
            raise ValidationError('Password must contain at least lowercase letter.')
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', value):
        raise ValidationError('Password must have at least one special character.')

def throw_error_exception(error):
    if isinstance(error, ValidationError):
        messages = error.messages
    else:
        messages = error

    return {'error': messages}, 400