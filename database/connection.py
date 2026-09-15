import mysql.connector
from mysql.connector import pooling
from config import DB_CONFIG

_pool = None


def init_pool():
    """Khởi tạo connection pool."""
    global _pool
    if _pool is None:
        _pool = pooling.MySQLConnectionPool(
            pool_name='tutien_pool',
            pool_size=25,
            pool_reset_session=True,
            **DB_CONFIG
        )
        print('[DB] Connection pool initialized')


def get_connection():
    """Lấy connection từ pool."""
    if _pool is None:
        init_pool()
    return _pool.get_connection()


def close_pool():
    """Đóng pool khi shutdown."""
    global _pool
    if _pool is not None:
        _pool = None
        print('[DB] Connection pool closed')
def get_connection():
    if _pool is None:
        init_pool()
    import time
    t0 = time.time()
    conn = _pool.get_connection()
    elapsed = time.time() - t0
    if elapsed > 0.1:  # Chỉ log khi chờ > 0.1s
        print(f'[DB] get_connection waited {elapsed:.3f}s (pool exhausted!)')
    return conn