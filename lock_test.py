from lock import Lock
from mock_db import DB
from unittest import TestCase

import uuid

class LockTestCase(TestCase):
    def setUp(self):
        self.db = DB()
        self.worker_hash = uuid.uuid1()
        self.other_worker_hash = uuid.uuid1()
        self.key = 'worker'
        self.timeout = 5
        self.retry_interval = 1
        self.lock = Lock(
            db=self.db,
            key=self.key,
            owner=self.worker_hash,
            timeout=self.timeout,
            retry_interval = self.retry_interval
        )

        self.other_lock = Lock(
            db=self.db,
            key=self.key,
            owner=self.other_worker_hash,
            timeout=self.timeout,
            retry_interval = self.retry_interval
        )
        
    def test_lock_can_create_a_new_lock(self):
        self.lock.lock()
        new_lock = self.db.find_one({ '_id': 'worker' })
        self.assertIsNotNone(new_lock)

    def test_lock_sets_the_locked_field_to_true(self):
        self.lock.lock()
        new_lock = self.db.find_one({ '_id': 'worker' })
        self.assertTrue(new_lock.get('locked', None))

    def test_lock_sets_the_owner_field_to_match_the_worker_hash(self):
        self.lock.lock()
        new_lock = self.db.find_one({ '_id': 'worker' })
        self.assertEqual(new_lock.get('owner', None), self.worker_hash)

    def test_lock_updates_an_existing_unlocked_lock(self):
        self.lock.lock()
        self.db.update_one({ '_id': 'worker' }, { 'locked': False })

        self.other_lock.lock()

        new_lock = self.db.find_one({ '_id': 'worker' })
        self.assertTrue(new_lock['locked'])
        self.assertEqual(new_lock['owner'], self.other_worker_hash)

    def test_unlock_sets_the_locked_field_to_false(self):
        self.lock.lock()
        self.lock.unlock()
        
        new_lock = self.db.find_one({ '_id': 'worker' })
        self.assertFalse(new_lock['locked'])

    def test_unlock_handles_locks_that_do_not_exist(self):
        self.lock.unlock()

        new_lock = self.db.find_one({ '_id': 'worker' })
        self.assertIsNone(new_lock)

    def test_unlock_raises_if_locked_by_a_different_owner(self):
        self.lock.lock()
        with self.assertRaisesRegex(Exception, '^.* locked by a different owner!$'):
            self.other_lock.unlock()

    def test_is_free_returns_true_if_lock_is_unlocked(self):
        self.lock.lock()
        self.lock.unlock()

        self.assertTrue(self.other_lock.is_free())

    def test_lock_is_free_returns_false_if_lock_is_locked(self):
        self.lock.lock()

        self.assertFalse(self.other_lock.is_free())
            
    def test_lock_is_free_handles_non_existent_lock(self):
        result = self.other_lock.is_free()
        self.assertTrue(result)

        
        
