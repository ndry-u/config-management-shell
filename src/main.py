"""Эмулятор командной оболочки UNIX с GUI на Tkinter.

Этап 3: добавлена загрузка виртуальной файловой системы (VFS)
из CSV-файла в память.
"""

from __future__ import annotations

import getpass
import socket
import sys
import tkinter as tk
from tkinter import ttk

from src.config import Config, format_config, parse_config
from src.parser import ParseError, parse_command
from src.startup import StartupScriptError, run_startup_script
from src.vfs import Vfs
from src.vfs_loader import VfsLoadError, load_vfs

WINDOW_TITLE_TEMPLATE = "Эмулятор - [{user}@{host}]"
WINDOW_GEOMETRY = "800x500"
TEXT_FONT = ("Consolas", 11)
TEXT_BG = "black"
TEXT_FG = "#00ff00"
EXIT_MESSAGE = "Эмулятор запущен. Введите 'exit' для выхода."
PAD_X = 4
PAD_Y = 4
ENTRY_PAD_X = (4, 0)


class ShellEmulator:
    """Графический эмулятор командной оболочки."""

    def __init__(self, config: Config) -> None:
        """Создаёт окно, виджеты и применяет конфигурацию.

        Args:
            config: параметры запуска эмулятора.
        """
        self.config = config
        self.vfs: Vfs | None = None
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
        self.output.pack(fill="both", expand=True, padx=PAD_X, pady=(PAD_Y, 0))

        frame = ttk.Frame(self.root)
        frame.pack(fill="x", padx=PAD_X, pady=PAD_Y)

        ttk.Label(frame, text=self.config.prompt).pack(side="left")
        self.entry = ttk.Entry(frame)
        self.entry.pack(side="left", fill="x", expand=True, padx=ENTRY_PAD_X)
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
        self._print(f"{self.config.prompt}{line}")
        self.execute(line)

    def execute(self, line: str) -> None:
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

    def load_vfs(self) -> None:
        """Загружает VFS из файла, указанного в конфигурации."""
        if not self.config.vfs_path:
            self._print("VFS не указан, работа без файловой системы")
            return

        try:
            self.vfs = load_vfs(self.config.vfs_path)
            self._print(f"VFS загружена: {self.vfs.name}")
        except VfsLoadError as error:
            self._print(f"Ошибка загрузки VFS: {error}")

    def run_startup(self) -> None:
        """Выполняет стартовый скрипт, если он задан."""
        if not self.config.startup_script:
            return

        try:
            run_startup_script(
                self.config.startup_script,
                execute=self.execute,
                echo=self._print,
                prompt=self.config.prompt,
            )
        except StartupScriptError as error:
            self._print(f"Ошибка стартового скрипта: {error}")

    def run(self) -> None:
        """Запускает главный цикл Tkinter."""
        self._print(format_config(self.config))
        self.load_vfs()
        self._print(EXIT_MESSAGE)
        self.run_startup()
        self.root.mainloop()


def main(argv: list[str] | None = None) -> None:
    """Точка входа.

    Args:
        argv: аргументы командной строки; None означает sys.argv[1:].
    """
    config = parse_config(argv)
    ShellEmulator(config).run()


if __name__ == "__main__":
    main(sys.argv[1:])