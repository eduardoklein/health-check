import requests

from health_check.checker import HttpChecker


class FakeResponse:
    def __init__(self, status_code):
        self.status_code = status_code


def test_http_checker_reports_site_up_for_success_status():
    calls = []

    def fake_get(url, timeout, headers):
        calls.append((url, timeout, headers))
        return FakeResponse(200)

    checker = HttpChecker(get=fake_get, timeout_seconds=3)

    result = checker.check("https://example.com")

    assert result.url == "https://example.com"
    assert result.is_up is True
    assert result.status_code == 200
    assert result.error is None
    assert calls == [
        (
            "https://example.com",
            3,
            {
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
            },
        )
    ]


def test_http_checker_sends_bearer_token_when_provided():
    calls = []

    def fake_get(url, timeout, headers):
        calls.append((url, timeout, headers))
        return FakeResponse(200)

    checker = HttpChecker(get=fake_get, timeout_seconds=3)

    result = checker.check("https://example.com", auth_token="test-token")

    assert result.is_up is True
    headers = calls[0][2]
    assert calls[0][0:2] == ("https://example.com", 3)
    assert headers["Authorization"] == "Bearer test-token"
    assert "User-Agent" in headers


def test_http_checker_accepts_configured_success_status_codes():
    checker = HttpChecker(get=lambda url, timeout, headers: FakeResponse(403))

    result = checker.check("https://example.com", accepted_status_codes={200, 403})

    assert result.is_up is True
    assert result.status_code == 403


def test_http_checker_reports_site_down_for_error_status():
    checker = HttpChecker(get=lambda url, timeout, headers: FakeResponse(503))

    result = checker.check("https://example.com")

    assert result.is_up is False
    assert result.status_code == 503
    assert result.error is None


def test_http_checker_reports_site_down_for_request_failure():
    def failing_get(url, timeout, headers):
        raise requests.Timeout("request timed out")

    checker = HttpChecker(get=failing_get)

    result = checker.check("https://example.com")

    assert result.is_up is False
    assert result.status_code is None
    assert result.error == "request timed out"
