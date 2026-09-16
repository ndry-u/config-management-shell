"""Парсер командной строки для эмулятора оболочки.

Разбирает строку ввода на имя команды и список аргументов,
корректно обрабатывая аргументы в одинарных и двойных кавычках.
"""

from __future__ import annotations


class ParseError(ValueError):
    """Ошибка разбора командной строки."""


def _is_quote(char: str) -> bool:
    """Проверяет, является ли символ кавычкой."""
    return char in ("'", '"')


def _is_separator(char: str) -> bool:
    """Проверяет, является ли символ разделителем аргументов."""
    return char in (" ", "\t")


def _tokenize(line: str) -> list[str]:
    """Разбивает строку на токены с учётом кавычек.

    Args:
        line: строка ввода пользователя.

    Returns:
        Список токенов без кавычек-обёрток.

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
        elif char == "\\" and quote is not None:
            escaped = True
        elif quote is not None:
            if char == quote:
                quote = None
            else:
                current.append(char)
        elif _is_quote(char):
            quote = char
        elif _is_separator(char):
            if current:
                tokens.append("".join(current))
                current = []
        else:
            current.append(char)

    if quote is not None:
        raise ParseError(f"Незакрытая кавычка: {quote}")

    if current:
        tokens.append("".join(current))

    return tokens


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
    tokens = _tokenize(line)

    if not tokens:
        return "", []

    return tokens[0], tokens[1:]