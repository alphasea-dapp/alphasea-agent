from unittest import TestCase
from unittest.mock import patch
from ...helpers import (
    create_web3,
    create_contract,
    create_event_indexer,
    generate_redis_namespace,
    BaseHardhatTestCase
)


class TestEventIndexerCache(BaseHardhatTestCase):
    def setUp(self):
        super().setUp()

        redis_namespace = generate_redis_namespace()

        w3 = create_web3()
        contract = create_contract(w3)
        event_indexer = create_event_indexer(
            w3, contract,
            redis_namespace=redis_namespace,
            get_logs_limit=1,
        )
        self.event_indexer = event_indexer
        self.w3 = w3

        w3_recreate = create_web3()
        contract_recreate = create_contract(w3_recreate)
        event_indexer_recreate = create_event_indexer(
            w3_recreate, contract_recreate,
            redis_namespace=redis_namespace,
            get_logs_limit=1,
        )
        self.event_indexer_recreate = event_indexer_recreate
        self.w3_recreate = w3_recreate

    def test_ok(self):
        df = self.event_indexer.fetch_tournaments()
        self.assertEqual(df['execution_start_at'].iloc[0], 30 * 60)

        with patch('src.store.event_indexer.get_events') as mocked_get_events:
            df = self.event_indexer_recreate.fetch_tournaments()
            self.assertEqual(df['execution_start_at'].iloc[0], 30 * 60)
            mocked_get_events.assert_not_called()
