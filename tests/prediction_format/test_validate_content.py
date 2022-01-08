from unittest import TestCase
from src.prediction_format import validate_content, ValidationError


class TestPredictionFormatValidateContent(TestCase):
    def test_ok(self):
        content = b"""position,symbol
0.2,ETH
0.3,XRP
0.1,BTC"""
        validate_content(content)

    def test_decode_error(self):
        content = b"""\xff"""
        with self.assertRaisesRegex(ValidationError, 'decode failed'):
            validate_content(content)

    def test_read_csv_error(self):
        content = b'"'
        with self.assertRaisesRegex(ValidationError, 'read_csv failed'):
            validate_content(content)

    def test_empty(self):
        content = b"""symbol,not_found
"""
        with self.assertRaisesRegex(ValidationError, 'empty'):
            validate_content(content)

    def test_position_not_found(self):
        content = b"""symbol,not_found
BTC,0.1"""
        with self.assertRaisesRegex(ValidationError, 'position column not found'):
            validate_content(content)

    def test_symbol_not_found(self):
        content = b"""not_found,position
BTC,0.1"""
        with self.assertRaisesRegex(ValidationError, 'symbol column not found'):
            validate_content(content)

    def test_column_count(self):
        content = b"""symbol,position,extra
BTC,0.1,0.2"""
        with self.assertRaisesRegex(ValidationError, 'column count must be 2'):
            validate_content(content)

    def test_contains_nan(self):
        content = b"""symbol,position
BTC,"""
        with self.assertRaisesRegex(ValidationError, 'contains NaN'):
            validate_content(content)

    def test_duplicated_symbol(self):
        content = b"""symbol,position
BTC,0.1
BTC,0.1"""
        with self.assertRaisesRegex(ValidationError, 'duplicated symbol'):
            validate_content(content)

    def test_contains_non_number(self):
        content = b"""symbol,position
BTC,non_number"""
        with self.assertRaisesRegex(ValidationError, 'contains non number'):
            validate_content(content)

    def test_contains_inf(self):
        content = b"""symbol,position
BTC,inf"""
        with self.assertRaisesRegex(ValidationError, 'contains inf'):
            validate_content(content)

    def test_contains_neg_inf(self):
        content = b"""symbol,position
BTC,-inf"""
        with self.assertRaisesRegex(ValidationError, 'contains inf'):
            validate_content(content)

    def test_position_sum(self):
        content = b"""symbol,position
BTC,-0.5
ETH,0.6"""
        with self.assertRaisesRegex(ValidationError, 'sum of abs\(position\) must be in \[-1, 1\]'):
            validate_content(content)

    def test_invalid_symbol(self):
        content = b"""symbol,position
 BTC,0.1"""
        with self.assertRaisesRegex(ValidationError, 'invalid symbol'):
            validate_content(content)
