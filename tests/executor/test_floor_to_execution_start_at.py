from unittest import TestCase
from src.executor.utils import floor_to_execution_start_at


class TestExecutorFloorToExecutionStartAt(TestCase):
    def test_ok(self):
        tournament = {
            'prediction_time': 1,
            'sending_time': 5,
            'execution_preparation_time': 4,
            'execution_time': 20,
        }
        self.assertEqual(floor_to_execution_start_at(10, tournament), (10, 0))
        self.assertEqual(floor_to_execution_start_at(20, tournament), (10, 0.5))
        self.assertEqual(floor_to_execution_start_at(29, tournament), (10, 0.95))
        self.assertEqual(floor_to_execution_start_at(30, tournament), (30, 0))
        self.assertEqual(floor_to_execution_start_at(49, tournament), (30, 0.95))
        self.assertEqual(floor_to_execution_start_at(50, tournament), (50, 0))
