import asyncio

from . import collector, backend, frontend


async def main():
    await asyncio.gather(collector.main(), backend.main(), frontend.main())


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
