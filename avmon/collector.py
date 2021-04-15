from typing import Callable, Awaitable, NoReturn

import aiohttp
import asyncio
from asyncio.exceptions import TimeoutError
import time
import re
import logging


from . import kafka
from . import config
from .message import EndpointStatus


async def endpoint_task(
    cfg: "config.EndpointConfig", output: Callable[[EndpointStatus], Awaitable[None]]
) -> NoReturn:
    """Polls endpoint based on the passed configuration, calling output callback on each iteration."""

    async with aiohttp.ClientSession() as session:
        while True:
            start_real = time.time()
            start_monotonic = time.monotonic()

            result: EndpointStatus

            try:
                async with session.get(cfg.url, timeout=cfg.timeout) as response:
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
                        time_start=start_real,
                        time_end=start_real + (time.monotonic() - start_monotonic),
                    )
            except TimeoutError:
                result = EndpointStatus(
                    url=cfg.url,
                    reached=False,
                    error="timeout",
                    status=None,
                    regex_match=None,
                    time_start=start_real,
                    time_end=start_real + (time.monotonic() - start_monotonic),
                )
            except aiohttp.client_exceptions.ClientConnectorError as e:
                result = EndpointStatus(
                    url=cfg.url,
                    reached=False,
                    error="couldn't connect",
                    status=None,
                    regex_match=None,
                    time_start=start_real,
                    time_end=start_real + (time.monotonic() - start_monotonic),
                )
            except aiohttp.client_exceptions.ServerDisconnectedError as e:
                result = EndpointStatus(
                    url=cfg.url,
                    reached=False,
                    error="server disconnected",
                    status=None,
                    regex_match=None,
                    time_start=start_real,
                    time_end=start_real + (time.monotonic() - start_monotonic),
                )

            await output(result)

            duration = time.monotonic() - start_monotonic
            await asyncio.sleep(max(0, cfg.interval - duration))


async def main():
    cfg = config.load_or_die()

    producer = await kafka.producer()

    try:

        async def send(msg: EndpointStatus) -> None:
            logging.debug(f"Sending event {msg !r}")
            await producer.send("messages", msg.to_json().encode())

        logging.debug(f"Starting endpoint pollers")
        await asyncio.gather(*(endpoint_task(endpoint, send) for endpoint in cfg))
    finally:
        await producer.stop()


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
