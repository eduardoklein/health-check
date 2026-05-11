import pytest
import requests

from health_check.notifiers import DiscordNotifier, EmailNotifier


class FakeSMTP:
    def __init__(self):
        self.started_tls = False
        self.login_call = None
        self.sent_message = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return None

    def starttls(self):
        self.started_tls = True

    def login(self, username, password):
        self.login_call = (username, password)

    def send_message(self, message):
        self.sent_message = message


def test_email_notifier_sends_message_with_tls_and_multiple_recipients():
    smtp = FakeSMTP()
    smtp_factory_calls = []

    def smtp_factory(host, port, timeout):
        smtp_factory_calls.append((host, port, timeout))
        return smtp

    notifier = EmailNotifier(
        host="smtp.example.com",
        port=587,
        username="alerts@example.com",
        password="secret",
        from_address="alerts@example.com",
        to_addresses=("ops@example.com", "dev@example.com"),
        smtp_factory=smtp_factory,
    )

    notifier.send("ALERTA: site caiu")

    assert smtp_factory_calls == [("smtp.example.com", 587, 10)]
    assert smtp.started_tls is True
    assert smtp.login_call == ("alerts@example.com", "secret")
    assert smtp.sent_message["Subject"] == "Health check alert"
    assert smtp.sent_message["From"] == "alerts@example.com"
    assert smtp.sent_message["To"] == "ops@example.com, dev@example.com"
    assert smtp.sent_message.get_content().strip() == "ALERTA: site caiu"


def test_email_notifier_can_be_built_from_environment(monkeypatch):
    monkeypatch.setenv("SMTP_HOST", "smtp.example.com")
    monkeypatch.setenv("SMTP_PORT", "2525")
    monkeypatch.setenv("SMTP_USERNAME", "alerts@example.com")
    monkeypatch.setenv("SMTP_PASSWORD", "secret")
    monkeypatch.setenv("ALERT_EMAIL_FROM", "alerts@example.com")
    monkeypatch.setenv("ALERT_EMAIL_TO", "ops@example.com, dev@example.com")

    notifier = EmailNotifier.from_env()

    assert notifier.host == "smtp.example.com"
    assert notifier.port == 2525
    assert notifier.username == "alerts@example.com"
    assert notifier.password == "secret"
    assert notifier.from_address == "alerts@example.com"
    assert notifier.to_addresses == ("ops@example.com", "dev@example.com")


def test_discord_notifier_posts_webhook_payload():
    calls = []

    def fake_post(url, json, timeout):
        calls.append((url, json, timeout))

        class Response:
            def raise_for_status(self):
                return None

        return Response()

    notifier = DiscordNotifier(
        webhook_url="https://discord.example/webhook",
        post=fake_post,
    )

    notifier.send("ALERTA: site caiu")

    assert calls == [
        (
            "https://discord.example/webhook",
            {"content": "ALERTA: site caiu"},
            10,
        )
    ]


def test_discord_notifier_raises_when_webhook_fails():
    def failing_post(url, json, timeout):
        raise requests.Timeout("timeout")

    notifier = DiscordNotifier(
        webhook_url="https://discord.example/webhook",
        post=failing_post,
    )

    with pytest.raises(requests.Timeout):
        notifier.send("ALERTA: site caiu")


def test_discord_notifier_can_be_built_from_environment(monkeypatch):
    monkeypatch.setenv("DISCORD_WEBHOOK_URL", "https://discord.example/webhook")

    notifier = DiscordNotifier.from_env()

    assert notifier.webhook_url == "https://discord.example/webhook"
