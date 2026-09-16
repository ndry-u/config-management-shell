"""Парсер командной строки для эмулятора оболочки.

Разбирает строку ввода на имя команды и список аргументов,
корректно обрабатывая аргументы в одинарных и двойных кавычках.
"""

from __future__ import annotations

QUOTE_CHARS = ("'", '"')
SEPARATOR_CHARS = (" ", "\t")
ESCAPE_CHAR = "\\"


class ParseError(ValueError):
    """Ошибка разбора командной строки."""


def _is_quote(char: str) -> bool:
    """Проверяет, является ли символ кавычкой."""
    return char in QUOTE_CHARS


def _is_separator(char: str) -> bool:
    """Проверяет, является ли символ разделителем аргументов."""
    return char in SEPARATOR_CHARS


def _consume_inside_quote(
    char: str, quote: str, escaped: bool
) -> tuple[str | None, bool, str | None]:
    """Обрабатывает символ внутри кавычек.

    Returns:
        Кортеж (новый_quote, escaped, символ_для_добавления).
        Если символ не нужно добавлять — третьим элементом None.
    """
    if escaped:
        return quote, False, char

    if char == ESCAPE_CHAR:
        return quote, True, None

    if char == quote:
        return None, False, None

    return quote, False, char


def _consume_outside_quote(char: str) -> tuple[bool, str | None]:
    """Обрабатывает символ вне кавычек.

    Returns:
        Кортеж (начинается_ли_кавычка, символ_для_добавления).
    """
    if _is_quote(char):
        return True, None

    if _is_separator(char):
        return False, None

    return False, char


def _flush(tokens: list[str], current: list[str]) -> None:
    """Добавляет накопленный токен в список, если он не пуст."""
    if current:
        tokens.append("".join(current))
        current.clear()


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
        if quote is not None:
            quote, escaped, addition = _consume_inside_quote(
                char, quote, escaped
            )
        else:
            starts_quote, addition = _consume_outside_quote(char)
            if starts_quote:
                quote = char
            elif addition is None:
                _flush(tokens, current)

        if addition is not None:
            current.append(addition)

    if quote is not None:
        raise ParseError(f"Незакрытая кавычка: {quote}")

    _flush(tokens, current)
    return tokens


def parse_command(line: str) -> tuple[str, list[str]]:
    """Разбирает строку на команду и аргументы.

    Поддерживает:
    - разделение по пробелам и табам;
    - аргументы в одинарных и двойных кавычках;
    - экранирование кавычек обратным слэшем внутри кавычек.

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