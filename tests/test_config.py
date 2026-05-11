from pathlib import Path

from health_check.config import load_config
from health_check.monitor import SiteTarget


def test_load_config_reads_targets_and_runtime_settings(tmp_path):
    config_file = tmp_path / "config.toml"
    config_file.write_text(
        """
interval_seconds = 15
timeout_seconds = 4

[[sites]]
name = "Portal"
url = "https://portal.example"

[[sites]]
name = "API"
url = "https://api.example/health"
""".strip(),
        encoding="utf-8",
    )

    config = load_config(Path(config_file))

    assert config.interval_seconds == 15
    assert config.timeout_seconds == 4
    assert config.sites == [
        SiteTarget(name="Portal", url="https://portal.example"),
        SiteTarget(name="API", url="https://api.example/health"),
    ]
