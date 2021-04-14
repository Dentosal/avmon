import datetime
import asyncio

from .message import EndpointStatus
from . import postgres, kafka
from . import config


async def main():
    config.load_dotenv()

    conn = await postgres.connect()
    consumer = await kafka.consumer("messages")

    try:
        async for msg in consumer:
            if msg.topic == "messages":
                status = EndpointStatus.from_json(msg.value.decode())
                print("->", status)
                await conn.execute(
                    """
                    INSERT INTO status_history (
                        url, reached, error, status, regex_match, time_start, time_end
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7)
                    """,
                    status.url,
                    status.reached,
                    status.error,
                    status.status,
                    status.regex_match,
                    datetime.datetime.utcfromtimestamp(status.time_start),
                    datetime.datetime.utcfromtimestamp(status.time_end),
                )
    finally:
        await consumer.stop()


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
