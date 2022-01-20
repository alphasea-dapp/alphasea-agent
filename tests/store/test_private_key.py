from ..helpers import (
    create_web3,
    create_contract,
    create_store,
    BaseHardhatTestCase
)


class TestStorePrivateKey(BaseHardhatTestCase):
    def test_same_namespace(self):
        w3 = create_web3()
        contract = create_contract(w3)
        store = create_store(w3, contract, redis_namespace='test_store_private_key:')
        orig_public_key = bytes(store._private_key.public_key)

        store = create_store(w3, contract, redis_namespace='test_store_private_key:')
        self.assertEqual(bytes(store._private_key.public_key), orig_public_key)

    def test_different_namespace(self):
        w3 = create_web3()
        contract = create_contract(w3)
        store = create_store(w3, contract, redis_namespace='test_store_private_key1:')
        orig_public_key = bytes(store._private_key.public_key)

        store = create_store(w3, contract, redis_namespace='test_store_private_key2:')
        self.assertNotEqual(bytes(store._private_key.public_key), orig_public_key)
