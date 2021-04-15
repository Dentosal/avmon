import pytest
from contextlib import contextmanager
import subprocess
import re
import asyncio
import aiohttp

from avmon.collector import endpoint_task
from avmon.config import EndpointConfig


@contextmanager
def infra():
    """Test with full infrastructure."""

    output = subprocess.check_output(["docker-compose", "ps", "-q"])
    if output.strip():
        raise RuntimeError("Please stop running containers before E2E tests")

    subprocess.run(
        [
            "docker-compose",
            "-f",
            "docker-compose.yml",
            "-f",
            "tests/docker-compose.yml",
            "up",
            "--build",
            "-d",
        ],
        check=True,
    )

    try:
        yield
    finally:
        subprocess.run(["docker-compose", "down", "-v"], check=False)


@pytest.mark.asyncio
async def test_e2e():
    """
    End-to-end test using the full pipeline.
    Uses test configuration and checks that http visualization includes correct values.
    """

    with infra():
        for _ in range(5):
            await asyncio.sleep(2.0)
            async with aiohttp.ClientSession() as session:
                try:
                    async with session.get(
                        "http://localhost:8080/", timeout=2
                    ) as response:
                        text = await response.text()
                        rows = re.findall(r"<tr.*?>(.+?)</tr>", text)
                        assert len(rows) == 3
                        for r in rows:
                            fields = re.findall(r"<td.*?>(.*?)</td>", r)

                            if "delay" in fields[0]:
                                assert fields

                            elif "/status/200" in fields[0]:
                                assert fields[2] == "200"

                            elif "/status/400" in fields[0]:
                                assert fields[2] == "400"

                except Exception as e:
                    print("Failed with", e)
                    print("Trying again...")
                else:
                    break
        else:  # No break
            raise RuntimeError("Failed too many times")
