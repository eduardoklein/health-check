from dataclasses import dataclass
import os
from typing import Protocol

from health_check.checker import HealthCheckResult


@dataclass(frozen=True)
class SiteTarget:
    name: str
    url: str
    auth_token_env: str | None = None
    accepted_status_codes: set[int] | None = None


class Checker(Protocol):
    def check(
        self,
        url: str,
        auth_token: str | None = None,
        accepted_status_codes: set[int] | None = None,
    ) -> HealthCheckResult:
        raise NotImplementedError


class Notifier(Protocol):
    def send(self, message: str) -> None:
        raise NotImplementedError


class StatusLogger(Protocol):
    def log(self, message: str) -> None:
        raise NotImplementedError


def monitor_once(
    targets: list[SiteTarget],
    checker: Checker,
    notifier: Notifier,
    previous_down_urls: set[str],
    status_logger: StatusLogger | None = None,
) -> set[str]:
    current_down_urls: set[str] = set()

    for target in targets:
        result = checker.check(
            target.url,
            auth_token=_auth_token_for(target),
            accepted_status_codes=target.accepted_status_codes,
        )
        if status_logger:
            status_logger.log(_status_message(target, result))

        if result.is_up:
            if target.url in previous_down_urls:
                notifier.send(_recovery_message(target, result))
            continue

        current_down_urls.add(target.url)
        if target.url not in previous_down_urls:
            notifier.send(_down_message(target, result))
            if status_logger:
                status_logger.log(f"NOTIFICACAO: alerta enviado para {target.name}.")

    return current_down_urls


def _down_message(target: SiteTarget, result: HealthCheckResult) -> str:
    reason = _result_reason(result)
    return f"ALERTA: {target.name} esta fora do ar. URL: {target.url}. {reason}."


def _recovery_message(target: SiteTarget, result: HealthCheckResult) -> str:
    reason = _result_reason(result)
    return f"RECUPERADO: {target.name} voltou ao ar. URL: {target.url}. {reason}."


def _status_message(target: SiteTarget, result: HealthCheckResult) -> str:
    state = "esta no ar" if result.is_up else "esta fora do ar"
    reason = _result_reason(result)
    return f"STATUS: {target.name} {state}. URL: {target.url}. {reason}."


def _result_reason(result: HealthCheckResult) -> str:
    if result.status_code is not None:
        return f"Status: {result.status_code}"

    return f"Erro: {result.error or 'desconhecido'}"


def _auth_token_for(target: SiteTarget) -> str | None:
    if not target.auth_token_env:
        return None

    return os.environ.get(target.auth_token_env)
