import os
from dataclasses import dataclass


class ConsoleNotifier:
    def send(self, message: str) -> None:
        print(message, flush=True)


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
