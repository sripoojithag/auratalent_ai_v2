import psycopg
from pgvector.psycopg import register_vector
from backend.config import settings


def get_db_connection():
    """
    Creates and yields a psycopg3 database connection with pgvector registered.
    Ensures safe resource cleanup and transactional semantics.
    """
    conn = psycopg.connect(settings.conn_info)
    register_vector(conn)
    try:
        yield conn
    finally:
        conn.close()


def execute_query(query: str, params: tuple = None):
    """
    Helper to execute a single query safely and return rows.
    """
    with psycopg.connect(settings.conn_info) as conn:
        register_vector(conn)
        with conn.cursor() as cur:
            cur.execute(query, params)
            if cur.description:
                columns = [desc[0] for desc in cur.description]
                return [dict(zip(columns, row)) for row in cur.fetchall()]
            return []
