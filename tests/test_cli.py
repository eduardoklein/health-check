import sys

import pytest

import health_check.cli as cli
from health_check.checker import HealthCheckResult
from health_check.cli import main


def test_cli_exits_with_clear_message_when_config_file_is_missing(
    monkeypatch, capsys, tmp_path
):
    missing_config = tmp_path / "missing.toml"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "health-check",
            "--config",
            str(missing_config),
            "--notifier",
            "console",
            "--once",
        ],
    )

    with pytest.raises(SystemExit) as exc_info:
        main()

    assert exc_info.value.code == 2
    assert (
        f"config file not found: {missing_config}" in capsys.readouterr().err
    )


def test_cli_loads_dotenv_before_monitoring(monkeypatch, tmp_path):
    config_file = tmp_path / "config.toml"
    config_file.write_text(
        """
interval_seconds = 60
timeout_seconds = 10

[[sites]]
name = "Protected"
url = "https://protected.example"
auth_token_env = "PROTECTED_TOKEN"
""".strip(),
        encoding="utf-8",
    )
    dotenv_file = tmp_path / ".env"
    dotenv_file.write_text("PROTECTED_TOKEN=synthetic-token\n", encoding="utf-8")
    observed = {}

    class FakeChecker:
        def __init__(self, timeout_seconds):
            observed["timeout_seconds"] = timeout_seconds

        def check(self, url, auth_token=None, accepted_status_codes=None):
            observed["auth_token"] = auth_token
            return HealthCheckResult(url=url, is_up=True, status_code=200)

    monkeypatch.delenv("PROTECTED_TOKEN", raising=False)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "health-check",
            "--config",
            str(config_file),
            "--notifier",
            "console",
            "--once",
        ],
    )
    monkeypatch.setattr(cli, "HttpChecker", FakeChecker)

    main()

    assert observed["auth_token"] == "synthetic-token"


def test_cli_supports_email_and_discord_notifiers(monkeypatch):
    monkeypatch.setenv("SMTP_HOST", "smtp.example.com")
    monkeypatch.setenv("SMTP_USERNAME", "alerts@example.com")
    monkeypatch.setenv("SMTP_PASSWORD", "secret")
    monkeypatch.setenv("ALERT_EMAIL_FROM", "alerts@example.com")
    monkeypatch.setenv("ALERT_EMAIL_TO", "ops@example.com")
    monkeypatch.setenv("DISCORD_WEBHOOK_URL", "https://discord.example/webhook")

    assert cli._build_notifier("email").__class__.__name__ == "EmailNotifier"
    assert cli._build_notifier("discord").__class__.__name__ == "DiscordNotifier"
