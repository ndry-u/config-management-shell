"""Эмулятор командной оболочки UNIX с GUI на Tkinter.

Этап 1: REPL — минимальный прототип.
"""

from __future__ import annotations

import getpass
import socket
import tkinter as tk
from tkinter import ttk

from parser import ParseError, parse_command

class ShellEmulator:
    """Графический эмулятор командной оболочки."""

    WINDOW_TITLE_TEMPLATE = "Эмулятор - [{user}@{host}]"

    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title(self._build_title())
        self.root.geometry("800x500")
        self._build_ui()

    def _build_title(self) -> str:
        """Формирует заголовок окна из данных ОС."""
        user = getpass.getuser()
        host = socket.gethostname()
        return self.WINDOW_TITLE_TEMPLATE.format(user=user, host=host)

    def _build_ui(self) -> None:
        """Создаёт виджеты окна."""
        self.output = tk.Text(
            self.root,
            wrap="word",
            state="disabled",
            bg="black",
            fg="#00ff00",
            font=("Consolas", 11),
        )
        self.output.pack(fill="both", expand=True, padx=4, pady=(4, 0))

        frame = ttk.Frame(self.root)
        frame.pack(fill="x", padx=4, pady=4)

        ttk.Label(frame, text=">").pack(side="left")
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
        """Обработчик нажатия Enter в поле ввода."""
        line = self.entry.get()
        self.entry.delete(0, "end")
        self._print(f"> {line}")
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

        handler = self.COMMANDS.get(command)
        if handler is None:
            self._print(f"{command}: команда не найдена")
            return

        handler(self, args)

    def _cmd_ls(self, args: list[str]) -> None:
        """Заглушка команды ls."""
        self._print(f"ls: аргументы = {args}")

    def _cmd_cd(self, args: list[str]) -> None:
        """Заглушка команды cd."""
        self._print(f"cd: аргументы = {args}")

    def _cmd_exit(self, args: list[str]) -> None:
        """Закрывает приложение."""
        self.root.destroy()

    COMMANDS = {
        "ls": _cmd_ls,
        "cd": _cmd_cd,
        "exit": _cmd_exit,
    }


    def run(self) -> None:
        """Запускает главный цикл Tkinter."""
        self._print("Эмулятор запущен. Введите 'exit' для выхода.")
        self.root.mainloop()


def main() -> None:
    """Точка входа."""
    ShellEmulator().run()


if __name__ == "__main__":
    main()