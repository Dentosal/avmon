from typing import Dict, Any

import asyncio
from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
from aiokafka.helpers import create_ssl_context
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
    host = environ.get("AVMON_KAFKA", "localhost")
    if ":" not in host:
        host += ":9092"
    return host


def options() -> Dict[str, Any]:
    result = {"bootstrap_servers": bootstrap_servers()}

    if environ.get("AVMON_KAFKA_SSL", "0") != "0":
        result["security_protocol"] = "SSL"
        result["ssl_context"] = create_ssl_context(
            cafile="./keys/ca-cert",
            certfile="./keys/access-cert",
            keyfile="./keys/access-key",
            password="123123",
        )

    return result


async def producer() -> AIOKafkaConsumer:
    client = AIOKafkaProducer(**options())
    await start(client)
    return client


async def consumer(topic: str) -> AIOKafkaConsumer:
    client = AIOKafkaConsumer(topic, **options())
    await start(client)
    return client
