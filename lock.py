from time import sleep


class Lock:
    """

    A representation of a named database lock. Supports retrying lock
    acquisition up to a timeout.

    Use by its methods or as a contextmanager.

    Examples:

    # a lock named 'worker', to be owned by 'my-id', timeout after 20 seconds retrying once per second
    lock = Lock(db=db, key='worker', owner='my-id', timeout=20, retry_interval=1)

    if lock.is_free() and lock.try_obtain_lock():
        # the lock is acquired here.
    else:
        # we could not obtain the lock before timeout

    #or

    with lock:
        # the lock is acquired here
        # if the lock could not be acquired, an Exception is raised
        # the lock is unlocked as we exit this scope


    """
    def __init__(self, db, key, owner, timeout=None, retry_interval=None):
        self.db = db
        self.key = key
        self.owner = owner
        self.timeout = timeout
        self.retry_interval = retry_interval

    def __enter__(self):
        if not self.try_obtain_lock():
            raise Exception('Timed out waiting for lock')

    def __exit__(self, *args):
        self.unlock()

    def lock(self):
        """
        Lock a named lock using the given db handle, creating it if necessary.

        Locking a lock that is currently held by a different worker (identified
        by worker_hash) fails

        Locking a lock that is currently held by the same user is a no-op

        Args:
            key: a string naming the lock
            worker_hash: an string identifying the worker that currently holds the lock
            db: a mock_db.DB handle

        Returns True if the lock was successfully acquired, False otherwise

        """
        try:
            self.db.insert_one({ '_id': self.key, 'locked': True, 'owner': self.owner })
            return True
        except Exception:
            match = self.db.update_one({ '_id': self.key, 'locked': False }, { 'locked': True, 'owner': self.owner })
            return match

    def unlock(self):
        """
        Unlock a named lock using the given db handle. Only the worker currently holding the lock can unlock it

        Unlocking a named lock that does not exist is a no-op

        Unlocking a lock that is currently held by a different worker (identified by worker_hash) fails

        Args:
            key: a string naming the lock
            worker_hash: a string identifying the worker that currently holds the lock
            db: a mock_db.DB handle
        """
        lock = self.db.find_one({ '_id': self.key })

        if lock == None:
            return

        if lock['owner'] != self.owner:
            raise Exception(f'{self.key} locked by a different owner!')

        self.db.update_one({ '_id': self.key }, { 'locked': False })


    def try_obtain_lock(self):
        """
        Try to obtain the lock, retrying every self.retry_interval seconds up to
        self.timeout seconds

        Returns: 
            True - if the lock was obtained
            False - if we timed out before we could acquire the lock
        """
        wait_time = 0
        lock_result = False
        while wait_time < self.timeout:
            lock_result = self.is_free() and self.lock()
            if lock_result:
                break
            wait_time = wait_time + self.retry_interval
            sleep(self.retry_interval)

        return lock_result

    def is_free(self):
        """
        Return whether the lock is free

        Args:
            key: a string naming the lock
            worker_hash: a string identifying the worker that wants to know if the lock is free
            db: a mock_db.DB handle
        """

        lock = self.db.find_one({ '_id': self.key })
        return lock == None or not lock['locked']
