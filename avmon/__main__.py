from os import environ
import asyncio


if __name__ == "__main__":
    role = environ["AVMON_ROLE"]

    if role == "collector":
        from .collector import main
    elif role == "backend":
        from .backend import main
    elif role == "frontend":
        from .frontend import main
    else:
        exit(f"AVMON_ROLE {role !r} unknown")

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
