from os import environ
import asyncio
import asyncpg
import logging


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
    for _ in range(120):
        try:
            conn = await asyncpg.connect(
                user=environ.get("POSTGRES_USER", "user"),
                password=environ["POSTGRES_PASSWORD"],
                database=environ.get("POSTGRES_DB", "avmon"),
                host=environ.get("POSTGRES_HOST", "127.0.0.1"),
            )
            break
        except:
            # Postgres is still down, has user set variable that allows us to wait for it?
            if environ.get("AVMON_WAIT_FOR_DBS", "0") == "0":
                raise
            else:
                logging.warning("Could not connect to Postgres, retrying after 1s")
                await asyncio.sleep(1.0)
    else:  # No break
        logging.critical("Could not connect to Postgres after retrying")
        exit("Could not connect to Postgres after retrying")

    logging.info("Connected to Postgres, creating tables")

    await init_sql(conn)

    logging.info("Tables created")

    return conn
