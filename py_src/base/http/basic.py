"""HTTP Basic Client."""

from abc import abstractmethod
from pathlib import Path
from typing import Any, Optional

import arrow
import responses
from requests import Response, Session
from requests.exceptions import (
    ConnectionError,
    ConnectTimeout,
    HTTPError,
    JSONDecodeError,
    ProxyError,
    ReadTimeout,
    SSLError,
)

from ...cfg import Config
from ..io import IO

__all__ = (
    "HTTPBasic",
    "TesterBasic",
)


class AbsHTTP:
    """Abstract cls for HTTP Client."""

    @abstractmethod
    def req(self) -> Optional[Response]:
        """HTTP Request Method."""
        raise NotImplementedError


class HTTPBasic(AbsHTTP):
    """HTTP Basic Client, for Fast Operation with Prototype.

    Features:
        - Custom Headers Operation
        - Cookies Operation
        - Flexible Request Parameters

    """

    _user_agent: str
    _proxy_url: str
    _timeout: int
    _session: Session

    def __init__(
        self,
        user_agent: str = "",
        proxy_url: str = "",
        timeout: int = 30,
    ) -> None:
        """Init HTTP Basic Client.

        :Parameters:
            :user_agent:str, HTTP Header for `User-Agent`;
            :proxy_url:str, constitute HTTP session proxies if present.
            :time_out:int, HTTP Request timeout, Default 30 seconds.

        """
        self._user_agent = user_agent
        self._proxy_url = proxy_url
        self._timeout = timeout

        self._session = Session()

        if user_agent:
            self._session.headers.update(
                {
                    "User-Agent": user_agent,
                }
            )

        if proxy_url:
            self._session.proxies = {
                "http": proxy_url,
                "https": proxy_url,
            }

    def header_set(self, key: str, value: Optional[str]) -> None:
        """Set session header value with key string."""
        if value is not None:
            self._session.headers[key] = value
        else:
            if key in self._session.headers.keys():
                del self._session.headers[key]

    def header_get(self, key: str) -> str:
        """Get session header value by key string."""
        if key and key in self._session.headers.keys():
            value = self._session.headers[key]
            if value:
                return value
        return ""

    def set_hd_accept(self, value: str = "*/*") -> None:
        """Shortcut for set heaer `Accept`."""
        self.header_set("Accept", value)

    def set_hd_accept_encoding(self, value: str = "gzip, defalte, br") -> None:
        """Shortcut for Set header `Accept-Encoding`."""
        self.header_set("Accept-Encoding", value)

    def set_hd_accept_lang(self, value: str = "en-US,en;q=0.5") -> None:
        """Shortcut for Set header `Accept-Language`."""
        self.header_set("Accept-Language", value)

    def set_hd_origin(self, value: Optional[str]) -> None:
        """Shortcut for Set header `Origin`."""
        self.header_set("Origin", value)

    def set_hd_referer(self, value: Optional[str]) -> None:
        """Shortcut for Set header `Referer`."""
        self.header_set("Referer", value)

    def set_hd_content_type(self, value: Optional[str]) -> None:
        """Shortcut for Set header `Content-Type`."""
        self.header_set("Content-Type", value)

    def set_hd_ajax(self, value: str = "XMLHttpRequest") -> None:
        """Shortcut for Set header `X-Requested-With`."""
        self.header_set("X-Requested-With", value)

    def set_hd_form_data(self, utf8: bool = True) -> None:
        """Shortcut for Set header `Content-Type` for form data submit."""
        value = "application/x-www-form-urlencoded"
        if utf8 is True:
            value = f"{value}; charset=UTF-8"
        self.header_set("Content-Type", value)

    def set_hd_json_payload(self, utf8: bool = True) -> None:
        """Shortcut for Set header `Content-Type` for json payload post."""
        value = "application/json"
        if utf8 is True:
            value = f"{value}; charset=UTF-8"
        self.header_set("Content-Type", value)

    def cookie_set(self, key: str, value: Optional[str]) -> None:
        """Set cookie for session."""
        return self._session.cookies.set(key, value)

    def cookie_get(self, key: str) -> Optional[str]:
        """Set cookie for session."""
        return self._session.cookies.get(name=key)

    def cookie_load(self, file_cookie: Path) -> None:
        """Load session cookie from local file."""
        if file_cookie.is_file():
            self._session.cookies.update(IO.load_dict(file_cookie))

    def cookie_save(self, file_cookie: Path) -> None:
        """Save session cookies into local file."""
        IO.save_dict(file_cookie, dict(self._session.cookies))

    def _prepare_headers(self, **kwargs: Any) -> None:
        """Preparing headers for following HTTP request."""
        if kwargs.get("json") is not None:
            self.h_json()
        elif kwargs.get("data") is not None:
            self.h_data()

        headers = kwargs.get("headers")
        if headers is not None:
            for key, value in headers.items():
                self.header_set(key, value)

    def req(
        self,
        method: str,
        url: str,
        debug: bool = False,
        **kwargs: Any,
    ) -> Optional[Response]:
        """Perform HTTP Request."""
        response = None

        try:
            self._prepare_headers(**kwargs)

            if not kwargs.get("timeout", None):
                kwargs["timeout"] = self._timeout

            with self._session.request(method, url, **kwargs) as response:
                if debug:
                    now = arrow.now().format()
                    code = response.status_code
                    length = len(response.text)
                    message = f"{now} - [{code}]<{length}>{response.url}"
                    print(message)

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
                raise error

        return response

    def get(self, url: str, debug: bool = False, **kwargs: Any) -> Optional[Response]:
        """HTTP GET Method."""
        return self.req("GET", url, debug=debug, **kwargs)

    def post(self, url: str, debug: bool = False, **kwargs: Any) -> Optional[Response]:
        """HTTP POST Method."""
        return self.req("POST", url, debug=debug, **kwargs)

    def head(self, url: str, debug: bool = False, **kwargs: Any) -> Optional[Response]:
        """HTTP HEAD Method."""
        return self.req("HEAD", url, debug=debug, **kwargs)

    def options(
        self, url: str, debug: bool = False, **kwargs: Any
    ) -> Optional[Response]:
        """HTTP OPTIONS Method."""
        return self.req("OPTIONS", url, debug=debug, **kwargs)

    def connect(
        self, url: str, debug: bool = False, **kwargs: Any
    ) -> Optional[Response]:
        """HTTP CONNECT Method."""
        return self.req("CONNECT", url, debug=debug, **kwargs)

    def put(self, url: str, debug: bool = False, **kwargs: Any) -> Optional[Response]:
        """HTTP PUT Method."""
        return self.req("PUT", url, debug=debug, **kwargs)

    def patch(self, url: str, debug: bool = False, **kwargs: Any) -> Optional[Response]:
        """HTTP PATCH Method."""
        return self.req("PATCH", url, debug=debug, **kwargs)

    def delete(
        self, url: str, debug: bool = False, **kwargs: Any
    ) -> Optional[Response]:
        """HTTP DELETE Method."""
        return self.req("DELETE", url, debug=debug, **kwargs)


class TesterBasic:
    """Test HTTP Basic Client."""

    config = Config()

    file_ua = config.dir_data / "ua.txt"
    file_proxy = config.dir_data / "proxy.txt"

    def __init__(self) -> None:
        """Init Tester."""
        self.list_ua = self.load_user_agent()
        self.list_px = self.load_proxy()

    def load_user_agent(self) -> list[str]:
        """Load list of User-Ageng string."""
        return IO.load_line(
            file_name=self.file_ua,
            keyword="Mozilla",
        )

    def load_proxy(self) -> list[str]:
        """Load list of proxy string."""
        return IO.load_line(
            file_name=self.file_proxy,
            keyword="://",
        )

    def setup(self) -> bool:
        """Setup."""
        self.http = HTTPBasic(
            user_agent=self.list_ua[0],
            proxy_url=self.list_px[0],
        )

    def test_header(self) -> None:
        """Test header operation."""
        key, value = "hello", "world"

        self.http.header_set(key=key, value=value)
        assert self.http.header_get(key=key) == value

        # check `User-Agent` header with remote response
        response = self.http.get(url="https://httpbin.org/headers")
        assert bool(
            response
            and response.json()["headers"]["User-Agent"] == self.http._user_agent
        )

        # test other common headers
        self.http.set_hd_accept(value=value)
        assert self.http.header_get("Accept") == value

        self.http.set_hd_accept_encoding(value=value)
        assert self.http.header_get("Accept-Encoding") == value

        self.http.set_hd_accept_lang(value=value)
        assert self.http.header_get("Accept-Language") == value

        self.http.set_hd_origin(value=value)
        assert self.http.header_get("Origin") == value

        self.http.set_hd_referer(value=value)
        assert self.http.header_get("Referer") == value

        self.http.set_hd_content_type(value=value)
        assert self.http.header_get("Content-Type") == value

        self.http.set_hd_ajax(value=value)
        assert self.http.header_get("X-Requested-With") == value

        self.http.set_hd_form_data()
        value_data = "application/x-www-form-urlencoded; charset=UTF-8"
        assert self.http.header_get("Content-Type") == value_data

        self.http.set_hd_json_payload()
        value_json = "application/json; charset=UTF-8"
        assert self.http.header_get("Content-Type") == value_json

    def test_cookie(self) -> None:
        """Test session cookies operation."""
        file_cookie = self.config.dir_test / "http.cookie.json"
        file_cookie.unlink(missing_ok=True)

        key, value = "hello", "world"
        self.http.cookie_set(key=key, value=value)
        self.http.cookie_save(file_cookie=file_cookie)

        self.http.cookie_set(key=key, value=None)
        assert self.http.cookie_get(key=key) is None

        assert file_cookie.is_file()

        self.http.cookie_load(file_cookie=file_cookie)
        assert self.http.cookie_get(key=key) == value

        file_cookie.unlink(missing_ok=True)

    @responses.activate
    def test_request(self) -> None:
        """Test request method."""

        url = "https://example.com/"

        # GET Method
        with responses.RequestsMock() as rsps:
            rsps.add(
                responses.GET,
                url=url,
            )
            response = self.http.get(url=url)
            assert response.status_code == 200

        # HEAD Method
        with responses.RequestsMock() as rsps:
            rsps.add(
                responses.HEAD,
                url=url,
            )
            response = self.http.head(url=url)
            assert response.status_code == 200

        # OPTIONS Method
        with responses.RequestsMock() as rsps:
            rsps.add(
                responses.OPTIONS,
                url=url,
            )
            response = self.http.options(url=url)
            assert response.status_code == 200

        # CONNECT Method : NOT Tested, as no `responses.CONNECT` provided.
        # with responses.RequestsMock() as rsps:
        #     rsps.add(
        #         responses.CONNECT,
        #         url=url,
        #     )
        # response = self.http.connect(url=url)
        # assert response.status_code == 200

        # POST Method
        with responses.RequestsMock() as rsps:
            payload: dict = {"hello": "world"}
            rsps.add(
                responses.POST,
                url=url,
                json=payload,
            )
            response = self.http.post(url=url)
            assert response.status_code == 200
            assert response.json() == payload

        # DELETE Method
        with responses.RequestsMock() as rsps:
            rsps.add(
                responses.DELETE,
                url=url,
            )
            response = self.http.delete(url=url)
            assert response.status_code == 200

        # PATCH Method
        with responses.RequestsMock() as rsps:
            rsps.add(
                responses.PATCH,
                url=url,
            )
            response = self.http.patch(url=url)
            assert response.status_code == 200

        # PUT Method
        with responses.RequestsMock() as rsps:
            rsps.add(
                responses.PUT,
                url=url,
            )
            response = self.http.put(url=url)
            assert response.status_code == 200

    def run_test(self) -> None:
        """Run Test."""
        self.setup()

        self.test_header()
        self.test_cookie()
        self.test_request()


if __name__ == "__main__":
    TesterBasic().run_test()
