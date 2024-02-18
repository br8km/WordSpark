"""HTTP Downloader Client."""

from io import BytesIO
from pathlib import Path
from typing import Optional, Union
from zipfile import ZipFile

from requests import Response
from tqdm import tqdm

from ..io import IO
from .basic import HTTPBasic, TesterBasic

__all__ = ("HTTPDownloader",)


class HTTPDownloader(HTTPBasic):
    """HTTP Downloader Client for Resumable request to Large/Medium Files."""

    def __init__(
        self,
        user_agent: str,
        proxy_url: str,
        timeout: int = 30,
    ) -> None:
        """Init HTTP Downloader."""
        super().__init__(
            user_agent=user_agent,
            proxy_url=proxy_url,
            timeout=timeout,
        )

    def _head(self, file_url: str) -> Optional[Response]:
        """Head Request"""
        return self.head(file_url, timeout=self._timeout)

    @staticmethod
    def _has_range(response: Response) -> bool:
        """Check if accept range from response headers"""
        key_range = "Accept-Ranges"
        return bool(key_range in response.headers.keys())

    @staticmethod
    def _file_size(response: Optional[Response]) -> int:
        """Parse file size from response headers"""
        try:
            if response:
                return int(response.headers["content-length"])
        except (KeyError, ValueError, AttributeError):
            pass
        return 0

    def download_direct(
        self,
        file_url: str,
        file_out: Path,
        chunk_size: int = 1024,
        debug: bool = False,
    ) -> bool:
        """Download In One Shot."""
        # Notice Strange that `stream=False`, otherwise will not work
        with self.get(file_url, stream=False) as response:
            response.raise_for_status()
            total_size = self._file_size(response)
            with open(file_out, "wb") as file:
                progress_bar = tqdm(total=total_size, unit="B", unit_scale=True)
                for chunk in response.iter_content(chunk_size=chunk_size):
                    file.write(chunk)
                    file.flush()
                    progress_bar.update(chunk_size)
                    progress_bar.refresh()
                progress_bar.close()

            file_size = file_out.stat().st_size
            if debug:
                print(f"file_size = {file_size}")
                print(f"total_size = {total_size}")
            return file_size >= total_size

    def _resume_download(
        self,
        file_url: str,
        pos_start: int,
        pos_end: int = 0,
    ) -> Response:
        """
        Resume download
        Parameters:
            :pos_start:int, start position of range
            :pos_end:int, end position of range, empty if zero
        """
        _range = f"bytes={pos_start}-"
        if pos_end:
            _range = f"{_range}{pos_end}"
        self._session.headers["Range"] = _range

        # Notice Strange that `stream=False`, otherwise will not work
        return self.get(file_url, stream=False)

    def download_ranges(
        self,
        file_url: str,
        file_out: Union[Path, str],
        chunk_size: int = 1024,
        block_size: int = 1024 * 1024,
        resume: bool = False,
        debug: bool = False,
    ) -> bool:
        """
        Downloading By Ranges.

        Steps:
            :check local file exists/size
            :get pos_start/pos_end
            :resume_download
            :append new chunk to file if present
        """

        # Cleanup downloaded file part.
        if not resume:
            IO.file_del(file_out)

        total_size = self._file_size(response=self._head(file_url))
        if not total_size:
            if debug:
                raise ValueError("File Size Error!")
            return False

        with open(file_out, "ab+") as file:
            progress_bar = tqdm(total=total_size, unit="B", unit_scale=True)

            index = 0
            while True:
                index += 1
                file_size = file_out.stat().st_size
                if file_size >= total_size:
                    break

                # fix error if pos_end > total_size [possible]?
                pos_end = min((file_size + block_size), total_size)

                if debug:
                    print()
                    print(f"<{index}>total_size = {total_size}")
                    print(f"<{index}>file_size = {file_size}")
                    print(f"<{index}>pos_end = {pos_end}")
                    print(
                        f"<{index}>header_range: {self._session.headers.get("Range")}"
                    )

                with self._resume_download(
                    file_url=file_url,
                    pos_start=file_size,
                    pos_end=pos_end,
                ) as response:
                    if debug:
                        print(response, len(response.text))
                    response.raise_for_status()
                    for chunk in response.iter_content(chunk_size=chunk_size):
                        file.write(chunk)
                        file.flush()

                        progress_bar.update(chunk_size)
                        progress_bar.refresh()

                if pos_end >= total_size:
                    break

            progress_bar.close()

        file_size = file_out.stat().st_size
        if debug:
            print(f"file_size = {file_size}")
            print(f"total_size = {total_size}")
        return file_size >= total_size

    def download(
        self,
        file_url: str,
        file_out: Union[Path, str],
        debug: bool = False,
    ) -> bool:
        """Smart Download."""

        IO.dir_create(Path(file_out).parent)

        response = self._head(file_url)
        if response is None:
            return False

        total_size = self._file_size(response)
        if not total_size:
            if debug:
                raise ValueError("File Size Error!")
            return False

        if self._has_range(response):
            return self.download_ranges(
                file_url=file_url,
                file_out=file_out,
                debug=debug,
            )

        return self.download_direct(
            file_url=file_url,
            file_out=file_out,
            debug=debug,
        )

    def download_bytes(
        self,
        file_url: str,
        chunk_size: int = 1024,
    ) -> BytesIO:
        """Download bytes data."""
        # Notice Strange that `stream=False`, otherwise will not work
        with self.get(file_url, stream=False) as response:
            print(response)
            response.raise_for_status()
            total_size = self._file_size(response)
            progress_bar = tqdm(total=total_size, unit="B", unit_scale=True)
            _data = BytesIO()
            for chunk in response.iter_content(chunk_size=chunk_size):
                _data.write(chunk)
                progress_bar.update(chunk_size)
                progress_bar.refresh()
            progress_bar.close()

            return _data

    @staticmethod
    def unzip(data: BytesIO, dir_to: Path) -> bool:
        """Unzip zipped bytes data into file path."""
        if not dir_to.exists():
            dir_to.mkdir(parents=True)
        with ZipFile(data) as file:
            file.extractall(str(dir_to.absolute()))

        return True


class TesterDownloader(TesterBasic):
    """Test HTTP Downloader Client."""

    def __init__(self) -> None:
        """Init Tester."""
        super().__init__()

    def setup(self) -> bool:
        """Setup."""
        assert self.config.dir_test.is_dir()
        assert self.config.dir_test.exists()

        self.http = HTTPDownloader(
            user_agent=self.list_ua[0],
            proxy_url=self.list_px[0],
            timeout=60,
        )

        self.url_direct = "https://raw.githubusercontent.com/br8km/pubData/main/test_files/ai_beauty.jpg"
        self.file_direct = self.config.dir_test / "file_direct.jpg"

        self.url_ranges = "https://raw.githubusercontent.com/br8km/pubData/main/test_files/ai_beauty.zip"
        self.file_ranges = self.config.dir_test / "file_ranges.zip"

        self.url_zip = "https://raw.githubusercontent.com/br8km/pubData/main/test_files/ai_beauty.zip"
        self.dir_zip = self.config.dir_test / "dir_zip"

        # Alternative Source: - "https://testfiledownload.com/"
        # Example: "http://ipv4.download.thinkbroadband.com/10MB.zip"

        return True

    def cleanup(self) -> bool:
        """Cleanup Test dirs/files."""
        self.file_direct.unlink(missing_ok=True)
        self.file_ranges.unlink(missing_ok=True)
        IO.dir_del(self.dir_zip, remain_root=False)

        return True

    def test_download_direct(self) -> None:
        """Test Download Direct File."""
        assert self.http.download_direct(
            file_url=self.url_direct,
            file_out=self.file_direct,
        )

    def test_download_ranges(self) -> None:
        """Test Download Ranges File."""
        assert self.http.download_ranges(
            file_url=self.url_ranges,
            file_out=self.file_ranges,
        )

    def test_download(self) -> None:
        """Test Download File automatic select direct/range methods."""
        assert self.http.download(
            file_url=self.url_direct,
            file_out=self.file_direct,
        )

        assert self.http.download(
            file_url=self.url_ranges,
            file_out=self.file_ranges,
        )

    def test_download_zip(self) -> None:
        """Test Download Zip Files."""
        print("start..")
        buffer = self.http.download_bytes(file_url=self.url_zip)
        buffer_size = buffer.getbuffer().nbytes
        print(f"buffer_size = {buffer_size}")
        assert buffer_size
        assert self.http.unzip(data=buffer, dir_to=self.dir_zip)

    def run_test(self) -> None:
        """Run Test."""
        assert self.setup()

        self.test_download_direct()
        print("Test: download_direct finished.\n")

        self.test_download_ranges()
        print("Test: download_ranges finished.\n")

        self.test_download()
        print("Test: download finished.\n")

        self.test_download_zip()
        print("Test: download_zip finished.\n")

        assert self.cleanup()


if __name__ == "__main__":
    TesterDownloader().run_test()
