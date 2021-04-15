from typing import List, Optional, Pattern

import re
import toml
from urllib.parse import urlparse
from dataclasses import dataclass
from os import environ
from dotenv import load_dotenv

CFG_ENV_VAR = "AVMON_CFG"
DEFAULT_CFG_PATH = "./avmon.cfg.toml"


@dataclass
class EndpointConfig:
    """Configuration for a single monitored endpoint."""

    # Poll interval in seconds
    interval: int

    # Timeout in seconds
    timeout: float

    # Description of the endpoint
    description: str

    # URL to poll
    url: str

    # Regex that is matched against response body
    regex: Optional[Pattern]


class FieldValidationError(Exception):
    """Raised on missing or invalid field values."""

    def __init__(self, field, message):
        self.field = field
        self.message = message
        super().__init__(field + ": " + self.message)


def load(dotenv: bool = True) -> List[EndpointConfig]:
    """
    Loads configuration from file.
    Uses AVMON_CFG environment variable to locate config file,
    defaults to DEFAULT_CFG_PATH if not set.
    """

    if dotenv:
        load_dotenv()

    with open(environ.get(CFG_ENV_VAR, DEFAULT_CFG_PATH)) as f:
        cfg = toml.load(f)

    # Default interval
    default_interval = 60  # Once per minute
    if interval := cfg.get("interval"):
        if not isinstance(interval, int) or interval < 0:
            raise FieldValidationError("interval", "positive integer required")

    # Default timeout
    default_timeout = 10
    if timeout := cfg.get("timeout"):
        if not isinstance(timeout, (int, float)) or timeout < 0:
            raise FieldValidationError("timeout", "positive number required")

    # Per-endpoint configuration
    endpoints = []
    for i, endpoint in enumerate(cfg.get("endpoint", [])):
        description = endpoint.get("description")
        if description:
            description.strip()

        if "url" not in endpoint:
            raise FieldValidationError(
                "endpoint.url",
                "field missing ("
                + (
                    f"description: {description !r}"
                    if description is not None
                    else "No description"
                )
                + f", at index {i})",
            )

        url = urlparse(endpoint["url"])

        if url.scheme not in {"http", "https"}:
            raise FieldValidationError(
                "endpoint.url",
                f"invalid scheme (required https or http, got {url.scheme})",
            )

        regex = endpoint.get("regex")
        if regex is not None:
            try:
                regex = re.compile(regex)
            except re.error as e:
                raise FieldValidationError("endpoint.regex", f"invalid regex ({e})")

        if interval := endpoint.get("interval"):
            if not isinstance(interval, int) or interval < 0:
                raise FieldValidationError(
                    "endpoint.interval", "positive integer required"
                )
        else:
            interval = default_interval

        if timeout := endpoint.get("timeout"):
            if not isinstance(timeout, (float, int)) or timeout < 0:
                raise FieldValidationError(
                    "endpoint.timeout", "positive number required"
                )
        else:
            timeout = default_timeout

        endpoints.append(
            EndpointConfig(
                url=endpoint["url"],
                description=description,
                interval=interval,
                timeout=timeout,
                regex=regex,
            )
        )

    return endpoints


def load_or_die():
    """Loads configuration from file, or exits on error."""

    try:
        return load()
    except FieldValidationError as e:
        exit(f"Config file invalid: {e}")
    except toml.TomlDecodeError as e:
        exit(f"Could not read config file: {e}")
    except FileNotFoundError as e:
        exit(f"Could not read config file: {e}")
