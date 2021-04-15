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


async def check_endpoint(
    session: aiohttp.ClientSession, cfg: config.EndpointConfig
) -> EndpointStatus:
    start_real = time.time()
    start_monotonic = time.monotonic()

    try:
        async with session.get(cfg.url, timeout=cfg.timeout) as response:
            time_end = start_real + (time.monotonic() - start_monotonic)

            # Check if regex can be found in the body
            is_match = None
            if r := cfg.regex:
                text = await response.text()
                is_match = bool(re.search(r, text))

            return EndpointStatus(
                url=cfg.url,
                reached=True,
                error=None,
                status=response.status,
                regex_match=is_match,
                time_start=start_real,
                time_end=time_end,
            )

    except Exception as e:
        time_end = start_real + (time.monotonic() - start_monotonic)

        message: str

        if isinstance(e, TimeoutError):
            message = "timeout"
        elif isinstance(e, aiohttp.client_exceptions.ClientConnectorError):
            message = "couldn't connect"
        elif isinstance(e, aiohttp.client_exceptions.ServerDisconnectedError):
            message = "server disconnected"
        else:  # Unknown error, don't catch
            raise

        return EndpointStatus(
            url=cfg.url,
            reached=False,
            error=message,
            status=None,
            regex_match=None,
            time_start=start_real,
            time_end=start_real + (time.monotonic() - start_monotonic),
        )


async def endpoint_task(
    cfg: "config.EndpointConfig", output: Callable[[EndpointStatus], Awaitable[None]]
) -> NoReturn:
    """Polls endpoint based on the passed configuration, calling output callback on each iteration."""

    async with aiohttp.ClientSession() as session:
        while True:
            start = time.monotonic()
            result = await check_endpoint(session, cfg)
            await output(result)
            duration = time.monotonic() - start
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
