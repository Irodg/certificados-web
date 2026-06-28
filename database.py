import os
import psycopg2


DATABASE_URL = os.environ.get("DATABASE_URL")


def conectar_db():
    return psycopg2.connect(
        DATABASE_URL,
        sslmode="require"
    )
