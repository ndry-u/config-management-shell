"""Эмулятор командной оболочки UNIX с GUI на Tkinter.

Этап 1: REPL — минимальный прототип.
"""

from __future__ import annotations

import getpass
import socket
import tkinter as tk
from tkinter import ttk

from parser import ParseError, parse_command

WINDOW_TITLE_TEMPLATE = "Эмулятор - [{user}@{host}]"
WINDOW_GEOMETRY = "800x500"
TEXT_FONT = ("Consolas", 11)
TEXT_BG = "black"
TEXT_FG = "#00ff00"
PROMPT_SYMBOL = ">"
EXIT_MESSAGE = "Эмулятор запущен. Введите 'exit' для выхода."


class ShellEmulator:
    """Графический эмулятор командной оболочки."""

    def __init__(self) -> None:
        """Создаёт окно и виджеты эмулятора."""
        self.root = tk.Tk()
        self.root.title(self._build_title())
        self.root.geometry(WINDOW_GEOMETRY)
        self._build_ui()

    def _build_title(self) -> str:
        """Формирует заголовок окна из данных ОС."""
        user = getpass.getuser()
        host = socket.gethostname()
        return WINDOW_TITLE_TEMPLATE.format(user=user, host=host)

    def _build_ui(self) -> None:
        """Создаёт виджеты окна."""
        self.output = tk.Text(
            self.root,
            wrap="word",
            state="disabled",
            bg=TEXT_BG,
            fg=TEXT_FG,
            font=TEXT_FONT,
        )
        self.output.pack(fill="both", expand=True, padx=4, pady=(4, 0))

        frame = ttk.Frame(self.root)
        frame.pack(fill="x", padx=4, pady=4)

        ttk.Label(frame, text=PROMPT_SYMBOL).pack(side="left")
        self.entry = ttk.Entry(frame)
        self.entry.pack(side="left", fill="x", expand=True, padx=(4, 0))
        self.entry.bind("<Return>", self._on_enter)
        self.entry.focus_set()

    def _print(self, text: str) -> None:
        """Печатает текст в окно вывода."""
        self.output.configure(state="normal")
        self.output.insert("end", text + "\n")
        self.output.see("end")
        self.output.configure(state="disabled")

    def _on_enter(self, _event: tk.Event) -> None:
        """Обрабатывает нажатие Enter в поле ввода."""
        line = self.entry.get()
        self.entry.delete(0, "end")
        self._print(f"{PROMPT_SYMBOL} {line}")
        self._execute(line)

    def _execute(self, line: str) -> None:
        """Разбирает строку и выполняет команду."""
        if not line.strip():
            return

        try:
            command, args = parse_command(line)
        except ParseError as error:
            self._print(f"Ошибка разбора: {error}")
            return

        handler = self._get_handler(command)
        if handler is None:
            self._print(f"{command}: команда не найдена")
            return

        handler(args)

    def _get_handler(self, command: str):
        """Возвращает метод-обработчик команды или None."""
        handlers = {
            "ls": self._cmd_ls,
            "cd": self._cmd_cd,
            "exit": self._cmd_exit,
        }
        return handlers.get(command)

    def _cmd_ls(self, args: list[str]) -> None:
        """Заглушка команды ls."""
        self._print(f"ls: аргументы = {args}")

    def _cmd_cd(self, args: list[str]) -> None:
        """Заглушка команды cd."""
        self._print(f"cd: аргументы = {args}")

    def _cmd_exit(self, args: list[str]) -> None:
        """Закрывает приложение."""
        self.root.destroy()

    def run(self) -> None:
        """Запускает главный цикл Tkinter."""
        self._print(EXIT_MESSAGE)
        self.root.mainloop()


def main() -> None:
    """Точка входа."""
    ShellEmulator().run()


if __name__ == "__main__":
    main()