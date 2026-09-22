"""Юнит-тесты для модуля конфигурации."""

from src.config import Config, format_config, parse_config


class TestParseConfig:
    """Тесты функции parse_config."""

    def test_defaults(self) -> None:
        config = parse_config([])
        assert config.vfs_path == ""
        assert config.prompt == "$ "
        assert config.startup_script == ""

    def test_all_arguments(self) -> None:
        config = parse_config([
            "--vfs", "data/vfs.csv",
            "--prompt", "myshell> ",
            "--script", "scripts/startup.txt",
        ])
        assert config.vfs_path == "data/vfs.csv"
        assert config.prompt == "myshell> "
        assert config.startup_script == "scripts/startup.txt"

    def test_only_prompt(self) -> None:
        config = parse_config(["--prompt", "x> "])
        assert config.vfs_path == ""
        assert config.prompt == "x> "
        assert config.startup_script == ""


class TestFormatConfig:
    """Тесты функции format_config."""

    def test_format_contains_all_keys(self) -> None:
        config = Config(
            vfs_path="a",
            prompt="b",
            startup_script="c",
        )
        text = format_config(config)
        assert "vfs_path" in text
        assert "prompt" in text
        assert "startup_script" in text

    def test_format_contains_values(self) -> None:
        config = Config(
            vfs_path="data/vfs.csv",
            prompt="my> ",
            startup_script="scripts/startup.txt",
        )
        text = format_config(config)
        assert "data/vfs.csv" in text
        assert "my> " in text
        assert "scripts/startup.txt" in text
