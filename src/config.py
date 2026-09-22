"""Разбор параметров командной строки эмулятора."""

from __future__ import annotations

import argparse
from dataclasses import dataclass

DEFAULT_PROMPT = "$ "
DEFAULT_STARTUP_SCRIPT = ""


@dataclass(frozen=True)
class Config:
    """Параметры запуска эмулятора.

    Attributes:
        vfs_path: путь к физическому расположению VFS.
        prompt: пользовательское приглашение к вводу.
        startup_script: путь к стартовому скрипту.
    """

    vfs_path: str
    prompt: str
    startup_script: str


def build_parser() -> argparse.ArgumentParser:
    """Создаёт argparse-парсер с описанием параметров.

    Returns:
        Настроенный парсер аргументов командной строки.
    """
    parser = argparse.ArgumentParser(
        prog="shell-emulator",
        description="Эмулятор команд оболочки UNIX",
    )
    parser.add_argument(
        "--vfs",
        dest="vfs_path",
        default="",
        help="Путь к физическому расположению VFS",
    )
    parser.add_argument(
        "--prompt",
        dest="prompt",
        default=DEFAULT_PROMPT,
        help="Пользовательское приглашение к вводу",
    )
    parser.add_argument(
        "--script",
        dest="startup_script",
        default=DEFAULT_STARTUP_SCRIPT,
        help="Путь к стартовому скрипту",
    )
    return parser


def parse_config(argv: list[str] | None = None) -> Config:
    """Разбирает аргументы командной строки в Config.

    Args:
        argv: список аргументов; None означает sys.argv[1:].

    Returns:
        Заполненная структура Config.
    """
    parser = build_parser()
    namespace = parser.parse_args(argv)
    return Config(
        vfs_path=namespace.vfs_path,
        prompt=namespace.prompt,
        startup_script=namespace.startup_script,
    )


def format_config(config: Config) -> str:
    """Формирует отладочный вывод параметров.

    Args:
        config: разобранные параметры.

    Returns:
        Многострочная строка вида "ключ = значение".
    """
    lines = [
        "Параметры запуска:",
        f"  vfs_path       = {config.vfs_path!r}",
        f"  prompt         = {config.prompt!r}",
        f"  startup_script = {config.startup_script!r}",
    ]
    return "\n".join(lines)
