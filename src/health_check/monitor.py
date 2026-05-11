from dataclasses import dataclass
from typing import Protocol

from health_check.checker import HealthCheckResult


@dataclass(frozen=True)
class SiteTarget:
    name: str
    url: str


class Checker(Protocol):
    def check(self, url: str) -> HealthCheckResult:
        raise NotImplementedError


class Notifier(Protocol):
    def send(self, message: str) -> None:
        raise NotImplementedError


def monitor_once(
    targets: list[SiteTarget],
    checker: Checker,
    notifier: Notifier,
    previous_down_urls: set[str],
) -> set[str]:
    current_down_urls: set[str] = set()

    for target in targets:
        result = checker.check(target.url)

        if result.is_up:
            if target.url in previous_down_urls:
                notifier.send(_recovery_message(target, result))
            continue

        current_down_urls.add(target.url)
        if target.url not in previous_down_urls:
            notifier.send(_down_message(target, result))

    return current_down_urls


def _down_message(target: SiteTarget, result: HealthCheckResult) -> str:
    reason = _result_reason(result)
    return f"ALERTA: {target.name} esta fora do ar. URL: {target.url}. {reason}."


def _recovery_message(target: SiteTarget, result: HealthCheckResult) -> str:
    reason = _result_reason(result)
    return f"RECUPERADO: {target.name} voltou ao ar. URL: {target.url}. {reason}."


def _result_reason(result: HealthCheckResult) -> str:
    if result.status_code is not None:
        return f"Status: {result.status_code}"

    return f"Erro: {result.error or 'desconhecido'}"
