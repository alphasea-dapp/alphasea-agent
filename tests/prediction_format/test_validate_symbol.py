from unittest import TestCase
from src.prediction_format import validate_symbol, ValidationError


class TestPredictionFormatValidateSymbol(TestCase):
    def test_ok(self):
        validate_symbol('BTC123')

    def test_space(self):
        with self.assertRaises(ValidationError):
            validate_symbol(' BTC')

    def test_too_long(self):
        with self.assertRaises(ValidationError):
            validate_symbol('BTCBTCBTC')

    def test_empty(self):
        with self.assertRaises(ValidationError):
            validate_symbol('')
