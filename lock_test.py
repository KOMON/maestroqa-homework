from starter_code import lock, unlock, lock_is_free
from mock_db import DB
from unittest import TestCase

import uuid

class LockTestCase(TestCase):
    def setUp(self):
        self.db = DB()
        self.worker_hash = uuid.uuid1()
        self.other_worker_hash = uuid.uuid1()
        
    def test_lock_can_create_a_new_lock(self):
        lock('worker', self.worker_hash, self.db)
        new_lock = self.db.find_one({ '_id': 'worker' })
        self.assertIsNotNone(new_lock)

    def test_lock_sets_the_locked_field_to_true(self):
        lock('worker', self.worker_hash, self.db)
        new_lock = self.db.find_one({ '_id': 'worker' })
        self.assertTrue(new_lock.get('locked', None))

    def test_lock_sets_the_owner_field_to_match_the_worker_hash(self):
        lock('worker', self.worker_hash, self.db)
        new_lock = self.db.find_one({ '_id': 'worker' })
        self.assertEqual(new_lock.get('owner', None), self.worker_hash)

    def test_lock_updates_an_existing_unlocked_lock(self):
        lock('worker', self.worker_hash, self.db)
        self.db.update_one({ '_id': 'worker' }, { 'locked': False })

        lock('worker', self.other_worker_hash, self.db)

        new_lock = self.db.find_one({ '_id': 'worker' })
        self.assertTrue(new_lock['locked'])
        self.assertEqual(new_lock['owner'], self.other_worker_hash)

    def test_unlock_sets_the_locked_field_to_false(self):
        lock('worker', self.worker_hash, self.db)
        unlock('worker', self.worker_hash, self.db)

        new_lock = self.db.find_one({ '_id': 'worker' })
        self.assertFalse(new_lock['locked'])

    def test_unlock_handles_locks_that_do_not_exist(self):
        unlock('worker', self.worker_hash, self.db)

        new_lock = self.db.find_one({ '_id': 'worker' })
        self.assertIsNone(new_lock)

    def test_unlock_raises_if_locked_by_a_different_owner(self):
        lock('worker', self.worker_hash, self.db)
        with self.assertRaisesRegex(Exception, '^.* locked by a different owner!$'):
            unlock('worker', self.other_worker_hash, self.db)

    def test_lock_is_free_returns_true_if_lock_is_unlocked(self):
        lock('worker', self.worker_hash, self.db)
        unlock('worker', self.worker_hash, self.db)

        self.assertTrue(lock_is_free('worker', self.other_worker_hash, self.db))

    def test_lock_is_free_returns_false_if_lock_is_locked(self):
        lock('worker', self.worker_hash, self.db)

        self.assertFalse(lock_is_free('worker', self.other_worker_hash, self.db))
            
    def test_lock_is_free_handles_non_existent_lock(self):
        result = lock_is_free('worker', self.worker_hash, self.db)
        self.assertTrue(result)

        
        
