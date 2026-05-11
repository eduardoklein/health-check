from pathlib import Path

import pytest

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
auth_token_env = "API_TOKEN"
accepted_status_codes = [200, 204, 403]
""".strip(),
        encoding="utf-8",
    )

    config = load_config(Path(config_file))

    assert config.interval_seconds == 15
    assert config.timeout_seconds == 4
    assert config.sites == [
        SiteTarget(name="Portal", url="https://portal.example"),
        SiteTarget(
            name="API",
            url="https://api.example/health",
            auth_token_env="API_TOKEN",
            accepted_status_codes={200, 204, 403},
        ),
    ]


def test_load_config_rejects_url_without_valid_domain_suffix(tmp_path):
    config_file = tmp_path / "config.toml"
    config_file.write_text(
        """
[[sites]]
name = "Evenyx"
url = "https://www.evenyx"
""".strip(),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="invalid url for Evenyx"):
        load_config(Path(config_file))
