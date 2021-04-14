from typing import Callable, Awaitable, NoReturn

from aioscheduler import TimedScheduler
from aiokafka import AIOKafkaProducer
import aiohttp
import asyncio
from asyncio.exceptions import TimeoutError
import time
import re

from . import config
from .message import EndpointStatus


async def endpoint_task(
    cfg: "config.EndpointConfig", output: Callable[[EndpointStatus], Awaitable[None]]
) -> NoReturn:
    """Polls endpoint based on the passed configuration, calling output callback on each iteration."""

    async with aiohttp.ClientSession() as session:
        while True:
            start_time = time.monotonic()

            result: EndpointStatus

            try:
                async with session.get(cfg.url, timeout=2.0) as response:
                    # Check if regex can be found in the body
                    is_match = None
                    if r := cfg.regex:
                        text = await response.text()
                        is_match = bool(re.search(r, text))

                    result = EndpointStatus(
                        url=cfg.url,
                        reached=True,
                        error=None,
                        status=response.status,
                        regex_match=is_match,
                        time_start=start_time,
                        time_end=time.monotonic(),
                    )
            except TimeoutError:
                result = EndpointStatus(
                    url=cfg.url,
                    reached=False,
                    error="timeout",
                    status=None,
                    regex_match=None,
                    time_start=start_time,
                    time_end=time.monotonic(),
                )

            await output(result)

            duration = time.monotonic() - start_time
            await asyncio.sleep(max(0, cfg.interval - duration))


async def main():
    cfg = config.load_or_die()

    producer = AIOKafkaProducer(bootstrap_servers="localhost:9092")
    await producer.start()
    try:

        async def send(msg: EndpointStatus) -> None:
            await producer.send_and_wait("messages", msg.to_json().encode())

        await asyncio.gather(*(endpoint_task(endpoint, send) for endpoint in cfg))
    finally:
        await producer.stop()


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
