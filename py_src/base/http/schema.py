"""HTTP Client Schema."""

from dataclasses import dataclass

import arrow


@dataclass
class AbsDebugItem:
    """Abstract cls for DebugItem."""

    time_stamp: float

    url: str

    headers: dict
    cookies: dict

    @property
    def time_str(self) -> str:
        """Convert time_stamp from float to string."""
        return arrow.get(self.time_stamp).format()


@dataclass
class DebugRequest(AbsDebugItem):
    """Request Data for Debugger."""

    method: str

    params: dict


@dataclass
class DebugResponse(AbsDebugItem):
    """Response Data for Debugger."""

    success: bool
    code: int

    text: str
    json: dict


@dataclass
class DebugData:
    """Data for Debugger."""

    req: DebugRequest
    res: DebugResponse


@dataclass
class RateLimit:
    """RateLimit Headers."""

    limit: int
    ramining: int
    reset: int
