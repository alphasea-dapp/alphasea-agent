import re
from ..types.exceptions import ValidationError


def validate_model_id(model_id):
    if not re.match(r'^[a-zA-Z0-9]{4,31}$', model_id):
        raise ValidationError('invalid model_id')
