import os
import smtplib
from dataclasses import dataclass
from email.message import EmailMessage
from typing import Callable

import requests


class ConsoleNotifier:
    def send(self, message: str) -> None:
        print(message, flush=True)


class ConsoleStatusLogger:
    def log(self, message: str) -> None:
        print(message, flush=True)


@dataclass(frozen=True)
class EmailNotifier:
    host: str
    port: int
    username: str
    password: str
    from_address: str
    to_addresses: tuple[str, ...]
    smtp_factory: Callable[..., smtplib.SMTP] = smtplib.SMTP
    timeout_seconds: float = 10

    @classmethod
    def from_env(cls) -> "EmailNotifier":
        return cls(
            host=_required_env("SMTP_HOST"),
            port=int(os.environ.get("SMTP_PORT", "587")),
            username=_required_env("SMTP_USERNAME"),
            password=_required_env("SMTP_PASSWORD"),
            from_address=_required_env("ALERT_EMAIL_FROM"),
            to_addresses=_email_recipients(_required_env("ALERT_EMAIL_TO")),
        )

    def send(self, message: str) -> None:
        email = EmailMessage()
        email["Subject"] = "Health check alert"
        email["From"] = self.from_address
        email["To"] = ", ".join(self.to_addresses)
        email.set_content(message)

        with self.smtp_factory(
            self.host,
            self.port,
            timeout=self.timeout_seconds,
        ) as smtp:
            smtp.starttls()
            smtp.login(self.username, self.password)
            smtp.send_message(email)


@dataclass(frozen=True)
class DiscordNotifier:
    webhook_url: str
    post: Callable[..., requests.Response] = requests.post
    timeout_seconds: float = 10

    @classmethod
    def from_env(cls) -> "DiscordNotifier":
        return cls(webhook_url=_required_env("DISCORD_WEBHOOK_URL"))

    def send(self, message: str) -> None:
        response = self.post(
            self.webhook_url,
            json={"content": message},
            timeout=self.timeout_seconds,
        )
        response.raise_for_status()


@dataclass(frozen=True)
class TwilioWhatsAppNotifier:
    account_sid: str
    auth_token: str
    from_number: str
    to_number: str

    @classmethod
    def from_env(cls) -> "TwilioWhatsAppNotifier":
        return cls(
            account_sid=_required_env("TWILIO_ACCOUNT_SID"),
            auth_token=_required_env("TWILIO_AUTH_TOKEN"),
            from_number=_required_env("TWILIO_WHATSAPP_FROM"),
            to_number=_required_env("TWILIO_WHATSAPP_TO"),
        )

    def send(self, message: str) -> None:
        try:
            from twilio.rest import Client
        except ImportError as exc:
            raise RuntimeError(
                "Twilio support requires installing the 'twilio' extra: "
                "pip install -e '.[twilio]'"
            ) from exc

        client = Client(self.account_sid, self.auth_token)
        client.messages.create(
            body=message,
            from_=f"whatsapp:{self.from_number}",
            to=f"whatsapp:{self.to_number}",
        )


def _required_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"missing required environment variable: {name}")
    return value


def _email_recipients(raw_value: str) -> tuple[str, ...]:
    recipients = tuple(
        recipient.strip()
        for recipient in raw_value.split(",")
        if recipient.strip()
    )
    if not recipients:
        raise RuntimeError("ALERT_EMAIL_TO must define at least one recipient")
    return recipients
