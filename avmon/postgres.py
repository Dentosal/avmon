from os import environ
import asyncio
import asyncpg


async def init_sql(conn) -> None:
    await conn.execute(
        """CREATE TABLE IF NOT EXISTS status_history(
            url TEXT NOT NULL,
            reached BOOL NOT NULL,
            error TEXT,
            status INTEGER,
            regex_match BOOL,
            time_start TIMESTAMP WITHOUT TIME ZONE NOT NULL,
            time_end TIMESTAMP WITHOUT TIME ZONE NOT NULL,
            CHECK (reached OR error IS NOT NULL),
            CHECK ((NOT reached) OR status IS NOT NULL),
            CHECK (time_start <= time_end)
        )"""
    )


async def connect() -> asyncpg.Connection:
    conn = await asyncpg.connect(
        user=environ["POSTGRES_USER"],
        password=environ["POSTGRES_PASSWORD"],
        database=environ.get("POSTGRES_DB", "avmon"),
        host=environ.get("POSTGRES_HOST", "127.0.0.1"),
    )

    await init_sql(conn)

    return conn
