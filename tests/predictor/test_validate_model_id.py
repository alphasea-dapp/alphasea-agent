from unittest import TestCase
from ..helpers import (
    create_web3,
    create_contract,
    get_future_execution_start_at_timestamp,
    proceed_time,
    get_prediction_time_shift,
    get_sending_time_shift,
    get_shipping_time_shift,
    get_publication_time_shift,
    get_tournament_id,
    BaseHardhatTestCase
)
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
