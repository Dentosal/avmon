import asyncio

from . import collector
from . import backend


async def main():
    await asyncio.gather(collector.main(), backend.main())


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
