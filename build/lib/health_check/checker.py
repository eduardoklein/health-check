from dataclasses import dataclass
from typing import Callable

import requests


DEFAULT_HEADERS = {
    "Accept": (
        "text/html,application/xhtml+xml,application/xml;q=0.9,"
        "image/avif,image/webp,*/*;q=0.8"
    ),
    "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
    "Upgrade-Insecure-Requests": "1",
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
}


@dataclass(frozen=True)
class HealthCheckResult:
    url: str
    is_up: bool
    status_code: int | None = None
    error: str | None = None


class HttpChecker:
    def __init__(
        self,
        get: Callable[..., requests.Response] | None = None,
        timeout_seconds: float = 10,
    ):
        self._get = get or requests.get
        self._timeout_seconds = timeout_seconds

    def check(
        self,
        url: str,
        auth_token: str | None = None,
        accepted_status_codes: set[int] | None = None,
    ) -> HealthCheckResult:
        headers = dict(DEFAULT_HEADERS)
        if auth_token:
            headers["Authorization"] = f"Bearer {auth_token}"

        try:
            response = self._get(
                url,
                timeout=self._timeout_seconds,
                headers=headers,
            )
        except requests.RequestException as exc:
            return HealthCheckResult(url=url, is_up=False, error=str(exc))

        accepted_codes = accepted_status_codes or set(range(200, 400))

        return HealthCheckResult(
            url=url,
            is_up=response.status_code in accepted_codes,
            status_code=response.status_code,
        )
