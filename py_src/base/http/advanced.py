"""HTTP Client."""

from dataclasses import asdict
from time import time
from typing import Any, Optional

import loguru
import orjson
import responses
from loguru._logger import Logger
from requests import Response
from requests.exceptions import (
    ConnectionError,
    ConnectTimeout,
    HTTPError,
    JSONDecodeError,
    ProxyError,
    ReadTimeout,
    SSLError,
)

from ..cache import MemoryCache
from ..debug import Debugger
from ..io import IO
from ..timer import Delayer
from .basic import HTTPBasic, TesterBasic
from .schema import DebugData, DebugRequest, DebugResponse

__all__ = ("HTTPClient",)


class HTTPClient(HTTPBasic):
    """HTTP Client.

    Features:
        - HTTPBasic Features, and
        - Logging
        - Debugging
        - Backoff Delaying if Captcha/Limited

    """

    _logger: Logger

    _debugger: Optional[Debugger]
    _data: Optional[DebugData]  # for save HTTP resquest/response data

    _delayer: Optional[Delayer]  # timestamp convert and backoff delaying
    _errors: Optional[MemoryCache]  # count errors for backoff delaying

    def __init__(
        self,
        user_agent: str,
        proxy_url: str,
        logger: Logger,
        debugger: Optional[Debugger] = None,
        use_delay: bool = False,
        timeout: int = 30,
    ) -> None:
        """Init HTTP Client.

        :Parameters:
            :user_agent:str, `User-Agent` Header;
            :proxy_url:str, proxies for session;
            :logger:Logger from `loguru` library;
            :timeout:int, Deafult 30 seconds;
            :debugger: Optional `Debugger` if debugging;

        """
        super().__init__(
            user_agent=user_agent,
            proxy_url=proxy_url,
            timeout=timeout,
        )

        self._debugger = debugger
        self._logger = logger
        self._use_delay = use_delay

        self._data = None

        self._delayer = Delayer() if use_delay else None
        self._errors = MemoryCache(seconds=3600) if use_delay else None

    def _save_request(self, method: str, url: str, **kwargs: Any) -> None:
        """Save HTTP request information for debugger."""
        params: dict[str, Any] = {}
        for key, value in kwargs.items():
            try:
                orjson.dumps({"v": value})
            except TypeError:
                value = str(value)
            params[key] = value

        cookies = dict(self._session.cookies.items())
        headers = dict(self._session.headers.items())

        # Get Request timestamp int/str
        time_stamp = int(time())

        self._data = DebugData(
            req=DebugRequest(
                time_stamp=time_stamp,
                method=method,
                url=url,
                params=params,
                headers=headers,
                cookies=cookies,
            ),
            res=DebugResponse(
                time_stamp=time_stamp,
                url="",
                headers={},
                cookies={},
                success=False,
                code=0,
                text="",
                json={},
            ),
        )

    def _save_response(self, response: Response) -> None:
        """Save HTTP response info for debugger."""
        # Get Response timestamp int/str
        time_stamp = int(time())

        try:
            res_json = orjson.loads(response.text)
        except orjson.JSONDecodeError:
            res_json = {}

        cookies = dict(response.cookies.items())
        headers = dict(response.headers.items())

        self._data.res.time_stamp = time_stamp
        self._data.res.code = response.status_code
        self._data.res.success = response.ok
        self._data.res.url = response.url
        self._data.res.headers = headers
        self._data.res.cookies = cookies
        self._data.res.text = response.text
        self._data.res.json = res_json

    def req(
        self,
        method: str,
        url: str,
        debug: bool = False,
        **kwargs: Any,
    ) -> Optional[Response]:
        """Preform HTTP Request."""
        if debug:
            assert self._debugger is not None

        response = None
        self._data = None

        try:
            if not kwargs.get("timeout", None):
                kwargs["timeout"] = self._timeout

            self._prepare_headers(**kwargs)

            if debug:
                self._save_request(method, url, **kwargs)

            with self._session.request(method, url, **kwargs) as response:
                code = response.status_code
                length = len(response.text)
                message = f"[{code}]<{length}>{response.url}"
                self._logger.debug(message)

                if debug:
                    self._save_response(response)
                    self._debugger.save(asdict(self._data))

                if self._errors is not None:
                    self._errors.add(
                        key="error",
                        value={
                            "key": "error",
                        },
                    )

                return response

        except (
            ConnectionError,
            ConnectTimeout,
            HTTPError,
            JSONDecodeError,
            ProxyError,
            ReadTimeout,
            SSLError,
        ) as error:
            if debug:
                self._debugger.save(asdict(self._data))
                raise error
            self._logger.exception(error)

        return response

    # Custom Coding Part

    @staticmethod
    def _is_captcha(response: Optional[Response]) -> bool:
        """Check if got Captcha page. Rewrite Logic to make it work."""
        raise NotImplementedError

    @staticmethod
    def _is_limited(response: Optional[Response]) -> bool:
        """Check if got Rate-limited. Rewrite if Required."""
        if isinstance(response, Response):
            return response.status_code == 429
        return False

    @staticmethod
    def _retry_after(response: Optional[Response]) -> int:
        """Get delta-seconds to retry after requests.

        Notes:
            Based on Header Value of `RateLimit-Reset` or `Retry-After`.
            Check if Reasonabe before use it in production.

        """
        raise NotImplementedError

    def _delay(self, retry_after: int = 2, debug: bool = False) -> float:
        """Smart Delaying. Rewrite if Required.

        Notes:
            You may select different delay method/parameters here, Eg:

            `self._delayer.near(1, 0.05)`
            `self._delayer.more_than(1, 0.05)`
            `self._delayer.less_than(1, 0.05)`

            OR use backoff delaying by using method `_backoff` below.

        """
        # Lazy Load Delayer
        if self._delayer is None:
            self._delayer = Delayer()

        return self._delayer.more_than(
            base=retry_after,
            percentage=0.05,
            debug=debug,
        )

    def _backoff(
        self,
        response: Optional[Response],
        debug: bool = False,
    ) -> float:
        """Backoff Delaying.

        Note:
            Rewrite method `_is_limited` before use this method.
            Rewrite below code to suit your use case. You may want to select more appropriate backoff parameters.

        """
        # Lazy Load Delayer
        if self._delayer is None:
            self._delayer = Delayer()

        # Lazy Load MemoryCache for rate limit errors
        if self._errors is None:
            self._errors = MemoryCache(seconds=3600)

        if self._is_limited(response=response):
            return self._delayer.backoff(
                errors=self._errors.size(),
                debug=debug,
            )
        return 0.0


class TesterAdvanced(TesterBasic):
    """Test HTTP Client."""

    def __init__(self) -> None:
        """Init Tester."""
        super().__init__()

    def setup(self) -> None:
        """Setup."""
        self.debugger_name = "HTTPClient"
        self.dir_debug = self.config.dir_debug
        self.debugger = Debugger(
            name=self.debugger_name,
            dir=self.dir_debug,
        )

        self.file_log = self.config.dir_test / "HTTPClient.log"
        self.file_log.unlink(missing_ok=True)

        self.logger = loguru.logger
        self.logger.add(sink=self.file_log)

        IO.dir_del(dir_name=self.dir_debug, remain_root=True)

    def cleanup(self) -> None:
        """Cleanup."""
        # self.file_log.unlink(missing_ok=True)
        IO.dir_del(dir_name=self.dir_debug, remain_root=True)

    def test_logging(self) -> None:
        """Test Logging."""
        self.http = HTTPClient(
            user_agent=self.list_ua[0],
            proxy_url=self.list_px[0],
            logger=self.logger,
            debugger=None,
        )
        message = "Hello From Test"
        self.http._logger.info(message)
        assert self.file_log.is_file()
        assert IO.load_line(self.file_log, keyword=message)

    def test_debugging(self) -> None:
        """Test Debugging."""
        self.http = HTTPClient(
            user_agent=self.list_ua[0],
            proxy_url=self.list_px[0],
            logger=self.logger,
            debugger=self.debugger,
        )

        url = "https://example.com/"
        with responses.RequestsMock() as rsps:
            rsps.add(
                responses.GET,
                url=url,
            )
            response = self.http.get(url=url, debug=True)
            assert response and response.status_code == 200
            assert bool(
                file.name.startswith(self.debugger_name)
                for file in self.config.dir_debug.glob("*.*")
            )

    def test_delaying(self) -> None:
        """Test Delaying."""
        self.http = HTTPClient(
            user_agent=self.list_ua[0],
            proxy_url=self.list_px[0],
            logger=self.logger,
            debugger=self.debugger,
            use_delay=True,
        )

        # normal delaying
        assert self.http._delay(retry_after=2, debug=True) > 0

        # mock 429 errors and backoff delaying
        url = "https://example.com/"
        with responses.RequestsMock() as rsps:
            rsps.add(
                responses.GET,
                url=url,
                status=429,
            )
            response = self.http.get(url=url, debug=True)
            assert response.status_code == 429
            assert self.http._errors.size()
            assert self.http._backoff(response=response, debug=True)

    def run_test(self) -> None:
        """Run Test."""
        self.setup()

        self.test_logging()
        self.test_debugging()
        self.test_delaying()

        self.cleanup()


if __name__ == "__main__":
    TesterAdvanced().run_test()
