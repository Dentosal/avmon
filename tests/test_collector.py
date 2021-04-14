import pytest

import portpicker
import socket
import asyncio
from aiohttp import web

from avmon.collector import endpoint_task
from avmon.config import EndpointConfig


@pytest.mark.asyncio
async def test_endpoint_task():
    port = portpicker.pick_unused_port()

    cfg = EndpointConfig(
        interval=0.000001,
        description="test",
        url=f"http://localhost:{port}",
        regex=None,
    )

    routes = web.RouteTableDef()

    request_count = 0

    @routes.get("/")
    async def all(request: web.Request) -> web.Response:
        nonlocal request_count
        request_count += 1
        return web.Response(text="OK")

    app = web.Application()
    app.add_routes(routes)
    runner = web.AppRunner(app)
    await runner.setup()

    tcp_site = web.TCPSite(runner, "localhost", port)

    call_count = 0

    async def callback(msg):
        nonlocal call_count
        if call_count == 0:
            assert msg.reached == True
            call_count = False
            await runner.cleanup()  # Stop the web server
        elif call_count == 1:
            assert msg.reached == False
        else:
            raise RuntimeError("Stop")

        call_count += 1

    await tcp_site.start()
    try:
        await endpoint_task(cfg, callback)
    except RuntimeError as e:
        assert str(e) == "Stop"

    assert request_count == 1
