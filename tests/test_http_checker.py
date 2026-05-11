import requests

from health_check.checker import HttpChecker


class FakeResponse:
    def __init__(self, status_code):
        self.status_code = status_code


def test_http_checker_reports_site_up_for_success_status():
    calls = []

    def fake_get(url, timeout):
        calls.append((url, timeout))
        return FakeResponse(200)

    checker = HttpChecker(get=fake_get, timeout_seconds=3)

    result = checker.check("https://example.com")

    assert result.url == "https://example.com"
    assert result.is_up is True
    assert result.status_code == 200
    assert result.error is None
    assert calls == [("https://example.com", 3)]


def test_http_checker_reports_site_down_for_error_status():
    checker = HttpChecker(get=lambda url, timeout: FakeResponse(503))

    result = checker.check("https://example.com")

    assert result.is_up is False
    assert result.status_code == 503
    assert result.error is None


def test_http_checker_reports_site_down_for_request_failure():
    def failing_get(url, timeout):
        raise requests.Timeout("request timed out")

    checker = HttpChecker(get=failing_get)

    result = checker.check("https://example.com")

    assert result.is_up is False
    assert result.status_code is None
    assert result.error == "request timed out"
