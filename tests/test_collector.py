from typing import List, Optional

import pytest

from dataclasses import dataclass
from contextlib import asynccontextmanager
import portpicker
import socket
import asyncio
from aiohttp import web

from avmon.collector import endpoint_task, check_endpoint
from avmon.config import EndpointConfig


@pytest.mark.asyncio
async def test_endpoint_task():
    port = portpicker.pick_unused_port()

    cfg = EndpointConfig(
        interval=0.000001,
        timeout=1.0,
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


@dataclass
class MockSession:
    """Mock session that returns given responses in order."""

    responses: List["MockResponse"]

    @asynccontextmanager
    async def get(self, url: str, **_ignored_kwargs):
        yield self.responses.pop(0)


@dataclass
class MockResponse:
    status: int
    content: str

    async def text(self):
        return self.content


@pytest.mark.asyncio
async def test_check_endpoint():
    cfg = EndpointConfig(
        interval=0.000001,
        timeout=1.0,
        description="test",
        url=f"THIS IS IGNORED",
        regex=r"\ba{4}\b",  # One "word" with exactly four lowercase "a" letters
    )

    mock_session = MockSession([])

    for status, word in [(200, "aaaaa"), (200, "aaaa"), (404, "nothing")]:
        mock_session.responses.append(
            MockResponse(status=status, content=f"Test {word} content")
        )
        result = await check_endpoint(mock_session, cfg)
        assert result.status == status
        assert result.regex_match == (word == "aaaa")
