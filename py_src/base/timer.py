"""Time Operation."""

import random
import time
from datetime import datetime
from functools import wraps
from typing import Any, Callable, Optional

import arrow
import pytz
from arrow import Arrow

__all__ = (
    "timing",
    "Timer",
    "Delayer",
)


def timing(func: Callable) -> Any:
    """Measure Timing of functions.

    :Usage Example:

    @timing
    def hello(name: str, age: int) -> None:
        return f'Hello {name}, You are {age} years old now!'

    """

    @wraps(func)
    def wrap(*args: Any, **kwargs: Any) -> Any:
        """Wrap function."""
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        print(
            "func:%r args:%r, kwargs:%r took: %2.8f sec"
            % (func.__name__, args, kwargs, end - start)
        )

        return result

    return wrap


class Timer:
    """Base cls for time transformation and smart Delaying."""

    def __init__(self, tz_info: str = "Asia/Hong_Kong") -> None:
        """Init Timer."""
        self._tz_info: str = tz_info
        self._tz_offset: float = self.utc_offset(tz_info)

        self._now: Arrow = self.to_now()
        self._fmt: str = "YYYY-MM-DD HH:mm:ssZZ"

    def to_now(self) -> Arrow:
        """Get now `Arrow` object."""
        # return arrow.utcnow().shift(seconds=self._tz_offset)
        return arrow.utcnow().to(tz=self._tz_info)

    def to_str(self, now: Optional[Arrow] = None, fmt: str = "") -> str:
        """string format for now"""
        fmt = fmt if fmt else self._fmt
        now = now if now else self._now
        return now.format(fmt)

    def to_int(self, now: Optional[Arrow] = None) -> int:
        """int timestamp for now"""
        now = now if now else self._now
        return int(now.utcnow().timestamp())

    def int2str(
        self,
        now_ts: int,
        tzinfo: str = "",
        fmt: str = "",
    ) -> str:
        """int to string for timestamp of now"""
        fmt = fmt if fmt else self._fmt
        tzinfo = tzinfo if tzinfo else self._tz_info
        return arrow.get(now_ts, tzinfo=tzinfo).format(fmt)

    def str2int(self, now_str: str, fmt: str = "", tzinfo: str = "") -> int:
        """string to int for timestamp of now"""
        fmt = fmt if fmt else self._fmt
        tzinfo = tzinfo if tzinfo else self._tz_info
        return int(arrow.get(now_str, fmt, tzinfo=tzinfo).timestamp())

    def iso_week(self, offset: int = 0) -> str:
        """return ISO week format like: `2020W36`"""
        iso = self._now.shift(weeks=offset).isocalendar()
        return "{}W{}".format(iso[0], iso[1])

    @classmethod
    def utc_offset(cls, time_zone: str) -> float:
        """Convert time zone string to utc offset."""
        now = datetime.now(pytz.timezone(time_zone))
        offset = now.utcoffset()
        if offset:
            return offset.total_seconds()
        return 0.0


class Delayer:
    """Delayer."""

    @classmethod
    def between(cls, min: float, max: float, debug: bool = False) -> float:
        """Delay Between (min, max) seconds. skip REAL sleep if debug is True."""
        pause = random.uniform(min, max)
        if not debug:
            time.sleep(pause)
        return pause

    @classmethod
    def near(cls, base: float, percentage: float, debug: bool = False) -> float:
        """Delay Near (base - percentage, base + percentage) seconds."""
        assert 0 < percentage < 1
        return cls.between(
            min=base - base * percentage,
            max=base + base * percentage,
            debug=debug,
        )

    @classmethod
    def more_than(
        cls, base: float, percentage: float, debug: bool = False
    ) -> float:
        """Delay More than (base, base + percentage) seconds."""
        assert 0 < percentage < 1
        return cls.between(
            min=base,
            max=base + base * percentage,
            debug=debug,
        )

    @classmethod
    def less_than(
        cls, base: float, percentage: float, debug: bool = False
    ) -> float:
        """Delay Less than (base - percentage, base) seconds."""
        assert 0 < percentage < 1
        return cls.between(
            min=base - base * percentage,
            max=base,
            debug=debug,
        )

    @classmethod
    def backoff(
        cls,
        base: float = 1.0,
        factor: int = 2,
        errors: int = 0,
        percentage: float = 0.1,
        debug: bool = False,
    ) -> float:
        """Delay with Exponential backoff.

        Reference:
            - https://github.com/litl/backoff

        Parameters:
            :base:float, base seconds for calculate pause time;
            :factor:int, backoff factor;
            :errors:int, number of errors occured in a period of time;
            :percentage:float, ratio to base float for calculate pause seconds;
            :debug:bool, Default `False`, skip REAL sleep if True;

        Returns:
            :float, seconds of time pause;

        """
        factor = max(factor, 2)
        exponent = factor * (2**errors) if errors else factor
        return cls.more_than(
            base=base * exponent,
            percentage=percentage,
            debug=debug,
        )


class Tester:
    """TestCase for Timer/Delayer."""

    tz_info = "Asia/Hong_Kong"
    tz_offset = float(8 * 3600)

    timer = Timer(tz_info=tz_info)

    @timing
    def _method_with_delay(self, name: str, pause: float) -> float:
        """Delay for pause, return pause."""
        print(f"name = {name}")
        time.sleep(pause)
        return pause

    def test_timing(self) -> bool:
        """Test timing decorator."""
        name = "Andy"
        pause = 0.5
        assert pause == self._method_with_delay(name, pause=pause)

        return True

    def test_utc_offset(self) -> bool:
        """Test UTC offset"""
        offset = self.timer.utc_offset(self.tz_info)
        print(f"offset = {offset}")
        assert offset == self.tz_offset

        return True

    def test_transforming(self) -> bool:
        """Test timer cls."""
        # Must Be New Timer Object, otherwise timer._now not correct
        self.timer = Timer(tz_info=self.tz_info)

        now_ts = self.timer.to_int()
        print(f"now_ts = {now_ts}")
        now_str = self.timer.to_str()
        print(f"now_str = {now_str}")

        for index in range(3):
            time.sleep(0.5)
            new_ts = self.timer.str2int(now_str=now_str)
            print(f"[{index}]new_ts = {new_ts}")
            assert now_ts == new_ts

        for index in range(3):
            time.sleep(0.5)
            new_str = self.timer.int2str(now_ts=now_ts)
            print(f"[{index}]new_str = {new_str}")
            assert now_str == new_str

        week = self.timer.iso_week()
        assert "W" in week
        assert week.startswith("W") is False
        assert week.endswith("W") is False

        return True

    def test_delay(self) -> bool:
        """Test delay methods."""
        delayer = Delayer()
        # Delay Between
        left, right = 1.0, 3.0
        pause = delayer.between(min=left, max=right, debug=True)
        assert left < pause < right

        # Delay Near
        base = 10.0
        percentage = 0.05
        pause = delayer.near(base=base, percentage=percentage, debug=True)
        assert abs(pause - base) < base * percentage

        # Delay More Than
        base = 10.0
        percentage = 0.05
        pause = delayer.more_than(base=base, percentage=percentage, debug=True)
        assert bool(abs(pause - base) < base * percentage and pause > base)

        # Delay Less Than
        base = 10.0
        percentage = 0.05
        pause = delayer.less_than(base=base, percentage=percentage, debug=True)
        assert bool(abs(pause - base) < base * percentage and pause < base)

        # Delay Backoff
        base = 10.0
        percentage = 0.05
        pause = 0
        for errors in range(10):
            next = delayer.backoff(
                base=base,
                factor=2,
                errors=errors,
                percentage=percentage,
                debug=True,
            )
            assert next > pause
            pause = next

        # Delay debug = False
        start = time.time()
        pause = delayer.between(1, 2, debug=False)
        print(f"real.pause = {pause}")
        assert time.time() >= start + pause

        return True

    def run_test(self) -> None:
        """Run Test."""
        assert self.test_timing()
        assert self.test_utc_offset()
        assert self.test_transforming()
        assert self.test_delay()


if __name__ == "__main__":
    Tester().run_test()
