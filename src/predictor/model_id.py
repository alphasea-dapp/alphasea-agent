import re
from ..types.exceptions import ValidationError


def validate_model_id(model_id):
    if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]{3,30}$', model_id):
        raise ValidationError('invalid model_id')
