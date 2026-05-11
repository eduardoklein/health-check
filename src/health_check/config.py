from dataclasses import dataclass
from pathlib import Path
import tomllib
from urllib.parse import urlparse

from health_check.monitor import SiteTarget


@dataclass(frozen=True)
class AppConfig:
    sites: list[SiteTarget]
    interval_seconds: int = 60
    timeout_seconds: int = 10


def load_config(path: Path) -> AppConfig:
    with path.open("rb") as config_file:
        raw_config = tomllib.load(config_file)

    sites = [_site_target(site) for site in raw_config.get("sites", [])]

    if not sites:
        raise ValueError("config must define at least one site")

    return AppConfig(
        sites=sites,
        interval_seconds=int(raw_config.get("interval_seconds", 60)),
        timeout_seconds=int(raw_config.get("timeout_seconds", 10)),
    )


def _accepted_status_codes(site: dict) -> set[int] | None:
    raw_codes = site.get("accepted_status_codes")
    if raw_codes is None:
        return None

    return {int(code) for code in raw_codes}


def _site_target(site: dict) -> SiteTarget:
    name = site["name"]
    url = site["url"]
    _validate_url(name, url)

    return SiteTarget(
        name=name,
        url=url,
        auth_token_env=site.get("auth_token_env"),
        accepted_status_codes=_accepted_status_codes(site),
    )


def _validate_url(name: str, url: str) -> None:
    parsed_url = urlparse(url)
    hostname = parsed_url.hostname or ""
    domain = hostname.removeprefix("www.")

    if parsed_url.scheme not in {"http", "https"} or "." not in domain:
        raise ValueError(f"invalid url for {name}: {url}")
