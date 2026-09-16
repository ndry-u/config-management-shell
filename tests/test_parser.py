"""Юнит-тесты для парсера командной строки."""

import pytest

from src.parser import ParseError, parse_command


class TestParseCommand:
    """Тесты функции parse_command."""

    def test_simple_command_without_args(self) -> None:
        assert parse_command("ls") == ("ls", [])

    def test_command_with_args(self) -> None:
        assert parse_command("ls -la /home") == ("ls", ["-la", "/home"])

    def test_double_quotes(self) -> None:
        assert parse_command('echo "hello world"') == (
            "echo",
            ["hello world"],
        )

    def test_single_quotes(self) -> None:
        assert parse_command("echo 'hello world'") == (
            "echo",
            ["hello world"],
        )

    def test_mixed_quotes(self) -> None:
        assert parse_command('cmd "a b" c \'d e\'') == (
            "cmd",
            ["a b", "c", "d e"],
        )

    def test_empty_string(self) -> None:
        assert parse_command("") == ("", [])

    def test_only_spaces(self) -> None:
        assert parse_command("   \t  ") == ("", [])

    def test_multiple_spaces_between_args(self) -> None:
        assert parse_command("ls    -la") == ("ls", ["-la"])

    def test_unclosed_quote_raises(self) -> None:
        with pytest.raises(ParseError):
            parse_command('echo "unterminated')

    def test_escaped_quote_inside_double_quotes(self) -> None:
        assert parse_command('echo "a \\"b\\" c"') == (
            "echo",
            ['a "b" c'],
        )