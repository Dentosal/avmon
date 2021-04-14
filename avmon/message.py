from typing import Optional

import json
from dataclasses import dataclass, asdict


@dataclass
class EndpointStatus:
    # The endpoint
    url: str

    # Was the endpoint reached?
    reached: bool

    # If the endpoint was unreachable, this describes why
    error: Optional[str]

    # The http status code (if the endpoint was reached)
    status: Optional[int]

    # Did the specified regex match anywhere in the body (if specified)
    regex_match: Optional[bool]

    # Interval during which the request was beign made, in float seconds (time.monotonic)
    time_start: float
    time_end: float

    def to_json(self) -> str:
        return json.dumps(asdict(self))

    @classmethod
    def from_json(cls, data: bytes) -> "EndpointStatus":
        return cls(**json.loads(data))
