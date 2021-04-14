import asyncio
from aiokafka import AIOKafkaConsumer

from .message import EndpointStatus


async def main():
    consumer = AIOKafkaConsumer(
        "messages",
        bootstrap_servers="localhost:9092",
    )

    await consumer.start()
    try:
        async for msg in consumer:
            if msg.topic == "messages":
                status = EndpointStatus.from_json(msg.value.decode())
                print("->", status)
    finally:
        await consumer.stop()


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
