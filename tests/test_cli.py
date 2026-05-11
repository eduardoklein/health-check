import sys

import pytest

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
