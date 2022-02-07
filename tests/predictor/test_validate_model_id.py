from unittest import TestCase
from src.types.exceptions import ValidationError
from src.predictor.model_id import validate_model_id


class TestPredictorValidateModelId(TestCase):
    def test_ok(self):
        validate_model_id('_az09')
        validate_model_id('a' * 4)
        validate_model_id('a' * 31)

    def test_too_short_error(self):
        with self.assertRaises(ValidationError):
            validate_model_id('a' * 3)

    def test_too_long_error(self):
        with self.assertRaises(ValidationError):
            validate_model_id('a' * 32)

    def test_start_with_num_error(self):
        with self.assertRaises(ValidationError):
            validate_model_id('0aaa')

    def test_character_error(self):
        with self.assertRaises(ValidationError):
            validate_model_id('-' * 4)
