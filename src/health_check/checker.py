from dataclasses import dataclass
from typing import Callable

import requests


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

    def check(self, url: str) -> HealthCheckResult:
        try:
            response = self._get(url, timeout=self._timeout_seconds)
        except requests.RequestException as exc:
            return HealthCheckResult(url=url, is_up=False, error=str(exc))

        return HealthCheckResult(
            url=url,
            is_up=200 <= response.status_code < 400,
            status_code=response.status_code,
        )
