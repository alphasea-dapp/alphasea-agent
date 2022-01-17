import re
from ..types.exceptions import ValidationError


def validate_model_id(model_id):
    if not re.match(r'^[a-z_][a-z0-9_]{3,30}$', model_id):
        raise ValidationError('invalid model_id')
