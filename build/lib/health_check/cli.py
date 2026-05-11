from argparse import ArgumentParser
from pathlib import Path
import sys
import time

from dotenv import load_dotenv

from health_check.checker import HttpChecker
from health_check.config import load_config
from health_check.monitor import monitor_once
from health_check.notifiers import (
    ConsoleNotifier,
    ConsoleStatusLogger,
    DiscordNotifier,
    EmailNotifier,
    TwilioWhatsAppNotifier,
)


def main() -> None:
    parser = ArgumentParser(description="Monitora sites e envia alerta se cairem.")
    parser.add_argument(
        "--config",
        default="config.toml",
        help="Caminho do arquivo TOML de configuracao.",
    )
    parser.add_argument(
        "--notifier",
        choices=["console", "email", "discord", "twilio-whatsapp"],
        default="console",
        help="Canal usado para enviar alertas.",
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Executa uma rodada de verificacao e encerra.",
    )
    args = parser.parse_args()

    config_path = Path(args.config)
    load_dotenv(config_path.parent / ".env")

    try:
        config = load_config(config_path)
    except FileNotFoundError as exc:
        print(f"config file not found: {exc.filename}", file=sys.stderr)
        raise SystemExit(2) from exc
    except ValueError as exc:
        print(f"invalid config: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc
    checker = HttpChecker(timeout_seconds=config.timeout_seconds)
    notifier = _build_notifier(args.notifier)
    status_logger = ConsoleStatusLogger()
    previous_down_urls: set[str] = set()

    while True:
        previous_down_urls = monitor_once(
            config.sites,
            checker,
            notifier,
            previous_down_urls=previous_down_urls,
            status_logger=status_logger,
        )

        if args.once:
            break

        time.sleep(config.interval_seconds)


def _build_notifier(name: str):
    if name == "email":
        return EmailNotifier.from_env()
    if name == "discord":
        return DiscordNotifier.from_env()
    if name == "twilio-whatsapp":
        return TwilioWhatsAppNotifier.from_env()

    return ConsoleNotifier()
