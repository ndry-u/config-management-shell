"""Эмулятор командной оболочки UNIX с GUI на Tkinter.

Этап 4: реализованы команды ls, cd, uniq, tree, wc.
"""

from __future__ import annotations

import getpass
import socket
import sys
import tkinter as tk
from tkinter import ttk

from src.commands import (
    cmd_cd,
    cmd_ls,
    cmd_tree,
    cmd_uniq,
    cmd_wc,
)
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
NO_VFS_MESSAGE = "VFS не указан, работа без файловой системы"
VFS_REQUIRED = "Команда требует загруженной VFS"
ROOT_PATH = "/"
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
        self.cwd = ROOT_PATH
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

        self.prompt_label = ttk.Label(frame, text=self._prompt_text())
        self.prompt_label.pack(side="left")

        self.entry = ttk.Entry(frame)
        self.entry.pack(side="left", fill="x", expand=True, padx=ENTRY_PAD_X)
        self.entry.bind("<Return>", self._on_enter)
        self.entry.focus_set()

    def _prompt_text(self) -> str:
        """Возвращает приглашение с текущим путём."""
        return f"{self.config.prompt}{self.cwd}$ "

    def _refresh_prompt(self) -> None:
        """Обновляет приглашение после смены каталога."""
        self.prompt_label.configure(text=self._prompt_text())

    def _print(self, text: str) -> None:
        """Печатает текст в окно вывода."""
        self.output.configure(state="normal")
        self.output.insert("end", text + "\n")
        self.output.see("end")
        self.output.configure(state="disabled")

    def _print_lines(self, lines: list[str]) -> None:
        """Печатает список строк."""
        for line in lines:
            self._print(line)

    def _on_enter(self, _event: tk.Event) -> None:
        """Обрабатывает нажатие Enter в поле ввода."""
        line = self.entry.get()
        self.entry.delete(0, "end")
        self._print(f"{self._prompt_text()}{line}")
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

        if command == "exit":
            self.root.destroy()
            return

        self._dispatch(command, args)

    def _dispatch(self, command: str, args: list[str]) -> None:
        """Выполняет команду по имени."""
        handler = self._get_handler(command)
        if handler is None:
            self._print(f"{command}: команда не найдена")
            return

        if self.vfs is None and command != "exit":
            self._print(VFS_REQUIRED)
            return

        result = handler(self.vfs, self.cwd, args)
        if isinstance(result, tuple):
            new_cwd, lines = result
            self.cwd = new_cwd
            self._print_lines(lines)
            self._refresh_prompt()
        else:
            self._print_lines(result)

    def _get_handler(self, command: str):
        """Возвращает функцию-обработчик команды или None."""
        handlers = {
            "ls": cmd_ls,
            "cd": cmd_cd,
            "uniq": cmd_uniq,
            "wc": cmd_wc,
            "tree": cmd_tree,
        }
        return handlers.get(command)

    def load_vfs(self) -> None:
        """Загружает VFS из файла, указанного в конфигурации."""
        if not self.config.vfs_path:
            self._print(NO_VFS_MESSAGE)
            return

        try:
            self.vfs = load_vfs(self.config.vfs_path)
            self._print(f"VFS загружена: {self.vfs.name}")
            self.cwd = ROOT_PATH
            self._refresh_prompt()
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
