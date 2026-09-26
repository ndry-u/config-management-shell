"""Выполнение стартового скрипта эмулятора."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

COMMENT_PREFIXES = ("#",)
DEFAULT_PROMPT = "> "


class StartupScriptError(Exception):
    """Ошибка выполнения стартового скрипта."""


def _is_comment(line: str) -> bool:
    """Проверяет, является ли строка комментарием."""
    stripped = line.lstrip()
    return stripped.startswith(COMMENT_PREFIXES)


def _clean(line: str) -> str:
    """Убирает пробелы и комментарии из строки."""
    without_comment = line.split("#", 1)[0]
    return without_comment.rstrip()


def run_startup_script(
    path: str,
    execute: Callable[[str], None],
    echo: Callable[[str], None],
    prompt: str = DEFAULT_PROMPT,
) -> None:
    """Выполняет стартовый скрипт строка за строкой.

    Команды выполняются последовательно. Ошибочные строки пропускаются:
    эмулятор выводит сообщение, но не прерывает выполнение.

    Args:
        path: путь к файлу скрипта.
        execute: функция выполнения одной строки как команды.
        echo: функция вывода строки в окно вывода.
        prompt: приглашение к вводу, отображаемое перед каждой командой.

    Raises:
        StartupScriptError: если файл не найден.
    """
    script_path = Path(path)

    if not script_path.exists():
        raise StartupScriptError(f"Файл скрипта не найден: {path}")

    text = script_path.read_text(encoding="utf-8")
    for raw_line in text.splitlines():
        if not raw_line.strip() or _is_comment(raw_line):
            continue

        command = _clean(raw_line)
        if not command:
            continue

        echo(f"{prompt}{command}")
        execute(command)
