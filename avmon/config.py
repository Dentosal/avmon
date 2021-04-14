from typing import Optional, Pattern

import re
import toml
from urllib.parse import urlparse
from dataclasses import dataclass
from os import environ

CFG_ENV_VAR = "AVMON_CFG"
DEFAULT_CFG_PATH = "./avmon.cfg.toml"


@dataclass
class EndpointConfig:
    """Configuration for a single monitored endpoint."""

    # Poll interval in seconds
    interval: int

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


def load():
    """
    Loads configuration from file.
    Uses AVMON_CFG environment variable to locate config file,
    defaults to DEFAULT_CFG_PATH if not set.
    """

    with open(environ.get(CFG_ENV_VAR, DEFAULT_CFG_PATH)) as f:
        cfg = toml.load(f)

    default_interval = 60  # Once per minute
    if interval := cfg.get("interval"):
        if not isinstance(interval, int) or interval < 0:
            raise FieldValidationError("interval", "positive integer required")

    endpoints = []
    for i, endpoint in enumerate(cfg["endpoint"]):
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

        endpoints.append(
            EndpointConfig(
                url=endpoint["url"],
                description=description,
                interval=interval,
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
