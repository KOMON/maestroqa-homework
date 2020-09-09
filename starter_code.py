import mock_db
import uuid
from worker import worker_main
from threading import Thread

def lock(key, worker_hash, db):
    """
    Lock a named lock using the given db handle, creating it if necessary.

    Locking a lock that is currently held by a different worker (identified by worker_hash) fails

    Locking a lock that is currently held by the same user is a no-op

    Args:
        key: a string naming the lock
        worker_hash: an string identifying the worker that currently holds the lock
        db: a mock_db.DB handle

    Returns True if the lock was successfully acquired, False otherwise
    """
    try:
        db.insert_one({ '_id': key, 'locked': True, 'owner': worker_hash })
        return True
    except Exception:
        match = db.update_one({ '_id': key, 'locked': False }, { 'locked': True, 'owner': worker_hash })
        return match

def unlock(key, worker_hash, db):
    """
    Unlock a named lock using the given db handle. Only the worker currently holding the lock can unlock it

    Unlocking a named lock that does not exist is a no-op

    Unlocking a lock that is currently held by a different worker (identified by worker_hash) fails

    Args:
        key: a string naming the lock
        worker_hash: a string identifying the worker that currently holds the lock
        db: a mock_db.DB handle
    """
    lock = db.find_one({ '_id': key })

    if lock == None:
        return

    if lock['owner'] != worker_hash:
        raise Exception(f'{key} locked by a different owner!')

    db.update_one({ '_id': key }, { 'locked': False })

def lock_is_free(key, worker_hash, db):
    """
        Return whether the lock is free

        Args:
            key: a string naming the lock
            worker_hash: a string identifying the worker that wants to know if the lock is free
            db: a mock_db.DB handle
    """
    lock = db.find_one({ '_id': key })
    return lock == None or not lock['locked']


def attempt_run_worker(worker_hash, give_up_after, db, retry_interval):
    """
        CHANGE MY IMPLEMENTATION, BUT NOT FUNCTION SIGNATURE

        Run the worker from worker.py by calling worker_main

        Args:
            worker_hash: a random string we will use as an id for the running worker
            give_up_after: if the worker has not run after this many seconds, give up
            db: an instance of MockDB
            retry_interval: continually poll the locking system after this many seconds
                            until the lock is free, unless we have been trying for more
                            than give_up_after seconds
    """
    if lock_is_free('worker', worker_hash, db) and lock('worker', worker_hash, db):
        try:
            worker_main(worker_hash, db)
        finally:
            unlock('worker', worker_hash, db)


if __name__ == "__main__":
    """
        DO NOT MODIFY

        Main function that runs the worker five times, each on a new thread
        We have provided hard-coded values for how often the worker should retry
        grabbing lock and when it should give up. Use these as you see fit, but
        you should not need to change them
    """

    db = mock_db.DB()
    threads = []
    for _ in range(25):
        t = Thread(target=attempt_run_worker, args=(uuid.uuid1(), 2000, db, 0.1))
        threads.append(t)
    for t in threads:
        t.start()
    for t in threads:
        t.join()
