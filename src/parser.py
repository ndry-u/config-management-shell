"""Парсер командной строки для эмулятора оболочки.

Разбирает строку ввода на имя команды и список аргументов,
корректно обрабатывая аргументы в одинарных и двойных кавычках.
"""

from __future__ import annotations


class ParseError(ValueError):
    """Ошибка разбора командной строки."""


def parse_command(line: str) -> tuple[str, list[str]]:
    """Разбирает строку на команду и аргументы.

    Поддерживает:
    - разделение по пробелам и табам;
    - аргументы в одинарных и двойных кавычках;
    - экранирование кавычек внутри строки с помощью обратного слэша.

    Args:
        line: строка ввода пользователя.

    Returns:
        Кортеж (имя_команды, список_аргументов).
        Если строка пустая — ("", []).

    Raises:
        ParseError: если кавычка не закрыта.
    """
    tokens: list[str] = []
    current: list[str] = []
    quote: str | None = None
    escaped = False

    for char in line:
        if escaped:
            current.append(char)
            escaped = False
            continue

        if char == "\\" and quote is not None:
            escaped = True
            continue

        if quote is not None:
            if char == quote:
                quote = None
            else:
                current.append(char)
            continue

        if char in ("'", '"'):
            quote = char
            continue

        if char in (" ", "\t"):
            if current:
                tokens.append("".join(current))
                current = []
            continue

        current.append(char)

    if quote is not None:
        raise ParseError(f"Незакрытая кавычка: {quote}")

    if current:
        tokens.append("".join(current))

    if not tokens:
        return "", []

    return tokens[0], tokens[1:]