import asyncio
from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
from aiokafka.errors import KafkaConnectionError
from os import environ
import logging


async def start(client) -> None:
    for _ in range(120):
        try:
            await client.start()
            break
        except KafkaConnectionError:
            # Kafka is still down, has user set variable that allows us to wait for it?
            if environ.get("AVMON_WAIT_FOR_DBS", "0") == "0":
                raise
            else:
                logging.warning("Could not connect to Kafka, retrying after 1s")
                await asyncio.sleep(1.0)
    else:  # No break
        logging.critical("Could not connect to Kafka after retrying")
        exit("Could not connect to Kafka after retrying")

    logging.info("Connected to Kafka")


def bootstrap_servers() -> str:
    return environ.get("AVMON_KAFKA", "localhost") + ":9092"


async def producer() -> AIOKafkaConsumer:
    client = AIOKafkaProducer(bootstrap_servers=bootstrap_servers())
    await start(client)
    return client


async def consumer(topic: str) -> AIOKafkaConsumer:
    client = AIOKafkaConsumer(topic, bootstrap_servers=bootstrap_servers())
    await start(client)
    return client
