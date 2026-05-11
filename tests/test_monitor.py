import os

from health_check.checker import HealthCheckResult
from health_check.monitor import SiteTarget, monitor_once


class FakeChecker:
    def __init__(self, results):
        self.results = list(results)
        self.checked_urls = []

    def check(self, url, auth_token=None, accepted_status_codes=None):
        self.checked_urls.append((url, auth_token, accepted_status_codes))
        return self.results.pop(0)


class FakeNotifier:
    def __init__(self):
        self.messages = []

    def send(self, message):
        self.messages.append(message)


class FakeStatusLogger:
    def __init__(self):
        self.messages = []

    def log(self, message):
        self.messages.append(message)


def test_monitor_checks_all_targets():
    checker = FakeChecker(
        [
            HealthCheckResult(url="https://one.example", is_up=True, status_code=200),
            HealthCheckResult(url="https://two.example", is_up=True, status_code=200),
        ]
    )
    notifier = FakeNotifier()
    targets = [
        SiteTarget(name="Site One", url="https://one.example"),
        SiteTarget(name="Site Two", url="https://two.example"),
    ]

    down_sites = monitor_once(targets, checker, notifier, previous_down_urls=set())

    assert checker.checked_urls == [
        ("https://one.example", None, None),
        ("https://two.example", None, None),
    ]
    assert down_sites == set()
    assert notifier.messages == []


def test_monitor_logs_status_for_all_targets():
    checker = FakeChecker(
        [
            HealthCheckResult(url="https://one.example", is_up=True, status_code=200),
            HealthCheckResult(url="https://two.example", is_up=False, status_code=500),
        ]
    )
    notifier = FakeNotifier()
    status_logger = FakeStatusLogger()

    monitor_once(
        [
            SiteTarget(name="Site One", url="https://one.example"),
            SiteTarget(name="Site Two", url="https://two.example"),
        ],
        checker,
        notifier,
        previous_down_urls=set(),
        status_logger=status_logger,
    )

    assert status_logger.messages == [
        "STATUS: Site One esta no ar. URL: https://one.example. Status: 200.",
        "STATUS: Site Two esta fora do ar. URL: https://two.example. Status: 500.",
        "NOTIFICACAO: alerta enviado para Site Two.",
    ]


def test_monitor_logs_when_alert_notification_is_sent():
    checker = FakeChecker(
        [HealthCheckResult(url="https://one.example", is_up=False, status_code=500)]
    )
    notifier = FakeNotifier()
    status_logger = FakeStatusLogger()

    monitor_once(
        [SiteTarget(name="Site One", url="https://one.example")],
        checker,
        notifier,
        previous_down_urls=set(),
        status_logger=status_logger,
    )

    assert status_logger.messages == [
        "STATUS: Site One esta fora do ar. URL: https://one.example. Status: 500.",
        "NOTIFICACAO: alerta enviado para Site One.",
    ]


def test_monitor_passes_auth_token_from_environment(monkeypatch):
    monkeypatch.setenv("SITE_TOKEN", "synthetic-token")
    checker = FakeChecker(
        [HealthCheckResult(url="https://one.example", is_up=True, status_code=200)]
    )
    notifier = FakeNotifier()

    monitor_once(
        [
            SiteTarget(
                name="Site One",
                url="https://one.example",
                auth_token_env="SITE_TOKEN",
            )
        ],
        checker,
        notifier,
        previous_down_urls=set(),
    )

    assert checker.checked_urls == [("https://one.example", "synthetic-token", None)]
    assert os.environ["SITE_TOKEN"] == "synthetic-token"


def test_monitor_passes_accepted_status_codes_to_checker():
    checker = FakeChecker(
        [HealthCheckResult(url="https://one.example", is_up=True, status_code=403)]
    )
    notifier = FakeNotifier()

    monitor_once(
        [
            SiteTarget(
                name="Site One",
                url="https://one.example",
                accepted_status_codes={200, 403},
            )
        ],
        checker,
        notifier,
        previous_down_urls=set(),
    )

    assert checker.checked_urls == [("https://one.example", None, {200, 403})]
    assert notifier.messages == []


def test_monitor_sends_alert_when_site_goes_down():
    checker = FakeChecker(
        [
            HealthCheckResult(
                url="https://one.example",
                is_up=False,
                status_code=500,
                error=None,
            )
        ]
    )
    notifier = FakeNotifier()

    down_sites = monitor_once(
        [SiteTarget(name="Site One", url="https://one.example")],
        checker,
        notifier,
        previous_down_urls=set(),
    )

    assert down_sites == {"https://one.example"}
    assert notifier.messages == [
        "ALERTA: Site One esta fora do ar. URL: https://one.example. Status: 500."
    ]


def test_monitor_does_not_repeat_alert_while_site_remains_down():
    checker = FakeChecker(
        [
            HealthCheckResult(
                url="https://one.example",
                is_up=False,
                status_code=503,
                error=None,
            )
        ]
    )
    notifier = FakeNotifier()

    down_sites = monitor_once(
        [SiteTarget(name="Site One", url="https://one.example")],
        checker,
        notifier,
        previous_down_urls={"https://one.example"},
    )

    assert down_sites == {"https://one.example"}
    assert notifier.messages == []


def test_monitor_sends_recovery_message_when_site_returns():
    checker = FakeChecker(
        [HealthCheckResult(url="https://one.example", is_up=True, status_code=200)]
    )
    notifier = FakeNotifier()

    down_sites = monitor_once(
        [SiteTarget(name="Site One", url="https://one.example")],
        checker,
        notifier,
        previous_down_urls={"https://one.example"},
    )

    assert down_sites == set()
    assert notifier.messages == [
        "RECUPERADO: Site One voltou ao ar. URL: https://one.example. Status: 200."
    ]
