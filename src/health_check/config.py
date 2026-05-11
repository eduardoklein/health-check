from dataclasses import dataclass
from pathlib import Path
import tomllib

from health_check.monitor import SiteTarget


@dataclass(frozen=True)
class AppConfig:
    sites: list[SiteTarget]
    interval_seconds: int = 60
    timeout_seconds: int = 10


def load_config(path: Path) -> AppConfig:
    with path.open("rb") as config_file:
        raw_config = tomllib.load(config_file)

    sites = [
        SiteTarget(name=site["name"], url=site["url"])
        for site in raw_config.get("sites", [])
    ]

    if not sites:
        raise ValueError("config must define at least one site")

    return AppConfig(
        sites=sites,
        interval_seconds=int(raw_config.get("interval_seconds", 60)),
        timeout_seconds=int(raw_config.get("timeout_seconds", 10)),
    )
