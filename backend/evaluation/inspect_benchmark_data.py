from psycopg import sql

from backend.config import settings


TABLES_TO_INSPECT = [
    "jobs",
    "candidates",
    "resumes",
    "resume_chunks",
]


def main():
    with __import__("psycopg").connect(settings.conn_info) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                  AND table_type = 'BASE TABLE'
                  AND table_name = ANY(%s)
                ORDER BY table_name;
                """,
                (TABLES_TO_INSPECT,),
            )
            existing_tables = [row[0] for row in cur.fetchall()]

            print("=== AVAILABLE TABLES ===")

            for table_name in existing_tables:
                print(f"\nTable: {table_name}")

                cur.execute(
                    """
                    SELECT column_name, data_type
                    FROM information_schema.columns
                    WHERE table_schema = 'public'
                      AND table_name = %s
                    ORDER BY ordinal_position;
                    """,
                    (table_name,),
                )

                for column_name, data_type in cur.fetchall():
                    print(f"  {column_name}: {data_type}")

                cur.execute(
                    sql.SQL("SELECT COUNT(*) FROM {}").format(
                        sql.Identifier(table_name)
                    )
                )
                count = cur.fetchone()[0]
                print(f"  Row count: {count}")

    print("\nInspection complete. No candidate records were printed.")


if __name__ == "__main__":
    main()