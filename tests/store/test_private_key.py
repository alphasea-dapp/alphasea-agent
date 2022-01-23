import random
import string
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

        redis_namespace = 'test_' + ''.join(random.choices(string.ascii_lowercase, k=32))
        store = create_store(w3, contract, redis_namespace=redis_namespace)
        orig_public_key = bytes(store._private_key.public_key)

        store = create_store(w3, contract, redis_namespace=redis_namespace)
        self.assertEqual(bytes(store._private_key.public_key), orig_public_key)

    def test_different_namespace(self):
        w3 = create_web3()
        contract = create_contract(w3)

        redis_namespace = 'test_' + ''.join(random.choices(string.ascii_lowercase, k=32))
        store = create_store(w3, contract, redis_namespace=redis_namespace)
        orig_public_key = bytes(store._private_key.public_key)

        redis_namespace2 = 'test_' + ''.join(random.choices(string.ascii_lowercase, k=32))
        store = create_store(w3, contract, redis_namespace=redis_namespace2)
        self.assertNotEqual(bytes(store._private_key.public_key), orig_public_key)
