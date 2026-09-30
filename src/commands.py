"""Реализации команд эмулятора, работающих с VFS."""

from __future__ import annotations

from collections.abc import Callable

from src.vfs import Vfs, VfsError, VfsNode

PATH_SEPARATOR = "/"
ROOT_PATH = "/"
PARENT_DIR = ".."
CURRENT_DIR = "."
SIZE_UNIT_DIVIDER = 1024


def _format_size(size: int) -> str:
    """Форматирует размер файла в человекочитаемый вид.

    Args:
        size: размер в байтах.

    Returns:
        Строка вида '12 B', '1.5 KB', '2.3 MB'.
    """
    if size < SIZE_UNIT_DIVIDER:
        return f"{size} B"
    kb = size / SIZE_UNIT_DIVIDER
    if kb < SIZE_UNIT_DIVIDER:
        return f"{kb:.1f} KB"
    mb = kb / SIZE_UNIT_DIVIDER
    return f"{mb:.1f} MB"


def _node_label(node: VfsNode) -> str:
    """Формирует строку для вывода узла в ls.

    Args:
        node: узел VFS.

    Returns:
        Строка с именем, правами и владельцем.
    """
    suffix = PATH_SEPARATOR if node.is_dir else ""
    return f"{node.mode} {node.owner:>8} {node.name}{suffix}"


def resolve_path(current: str, target: str) -> str:
    """Преобразует путь с учётом текущего каталога.

    Args:
        current: текущий абсолютный путь.
        target: путь из аргумента команды.

    Returns:
        Абсолютный нормализованный путь.
    """
    if not target:
        return current
    if target.startswith(PATH_SEPARATOR):
        combined = target
    else:
        combined = current.rstrip(PATH_SEPARATOR) + PATH_SEPARATOR + target

    parts: list[str] = []
    for part in combined.split(PATH_SEPARATOR):
        if part in ("", CURRENT_DIR):
            continue
        if part == PARENT_DIR:
            if parts:
                parts.pop()
            continue
        parts.append(part)
    return PATH_SEPARATOR + PATH_SEPARATOR.join(parts)


def cmd_ls(vfs: Vfs, cwd: str, args: list[str]) -> list[str]:
    """Выводит содержимое каталога.

    Args:
        vfs: виртуальная файловая система.
        cwd: текущий каталог.
        args: аргументы команды.

    Returns:
        Список строк для вывода.
    """
    target = args[0] if args else cwd
    path = resolve_path(cwd, target)
    try:
        node = vfs.find(path)
        if node is None:
            return [f"ls: путь не найден: {target}"]
        if node.is_file:
            return [_node_label(node)]
        children = vfs.list_dir(path)
        if not children:
            return []
        return [_node_label(child) for child in children]
    except VfsError as error:
        return [f"ls: {error}"]


def cmd_cd(vfs: Vfs, cwd: str, args: list[str]) -> tuple[str, list[str]]:
    """Меняет текущий каталог.

    Args:
        vfs: виртуальная файловая система.
        cwd: текущий каталог.
        args: аргументы команды.

    Returns:
        Кортеж (новый_текущий_каталог, строки_для_вывода).
    """
    if not args:
        return ROOT_PATH, []

    target = args[0]
    path = resolve_path(cwd, target)
    node = vfs.find(path)
    if node is None:
        return cwd, [f"cd: путь не найден: {target}"]
    if not node.is_dir:
        return cwd, [f"cd: не каталог: {target}"]
    return path, []


def cmd_uniq(vfs: Vfs, cwd: str, args: list[str]) -> list[str]:
    """Убирает повторяющиеся строки из файла.

    Args:
        vfs: виртуальная файловая система.
        cwd: текущий каталог.
        args: аргументы команды.

    Returns:
        Список уникальных строк или сообщение об ошибке.
    """
    if not args:
        return ["uniq: укажите файл"]

    path = resolve_path(cwd, args[0])
    node = vfs.find(path)
    if node is None:
        return [f"uniq: файл не найден: {args[0]}"]
    if not node.is_file:
        return [f"uniq: не файл: {args[0]}"]

    seen: set[str] = set()
    result: list[str] = []
    for line in node.content.splitlines():
        if line not in seen:
            seen.add(line)
            result.append(line)
    return result


def cmd_wc(vfs: Vfs, cwd: str, args: list[str]) -> list[str]:
    """Считает строки, слова и символы в файле.

    Args:
        vfs: виртуальная файловая система.
        cwd: текущий каталог.
        args: аргументы команды.

    Returns:
        Одна строка с количеством строк, слов и символов.
    """
    if not args:
        return ["wc: укажите файл"]

    path = resolve_path(cwd, args[0])
    node = vfs.find(path)
    if node is None:
        return [f"wc: файл не найден: {args[0]}"]
    if not node.is_file:
        return [f"wc: не файл: {args[0]}"]

    lines = len(node.content.splitlines())
    words = len(node.content.split())
    chars = len(node.content)
    return [f"{lines:>4} {words:>4} {chars:>6} {args[0]}"]


def _walk(node: VfsNode, prefix: str) -> list[str]:
    """Рекурсивно обходит дерево для команды tree.

    Args:
        node: текущий узел.
        prefix: префикс отступов.

    Returns:
        Список строк дерева.
    """
    result: list[str] = []
    items = sorted(node.children.values(), key=lambda n: n.name)
    for index, child in enumerate(items):
        is_last = index == len(items) - 1
        branch = "└── " if is_last else "├── "
        result.append(f"{prefix}{branch}{child.name}")
        if child.is_dir:
            extension = "    " if is_last else "│   "
            result.extend(_walk(child, prefix + extension))
    return result


def cmd_tree(vfs: Vfs, cwd: str, args: list[str]) -> list[str]:
    """Выводит дерево каталогов.

    Args:
        vfs: виртуальная файловая система.
        cwd: текущий каталог.
        args: аргументы команды.

    Returns:
        Список строк дерева.
    """
    target = args[0] if args else cwd
    path = resolve_path(cwd, target)
    node = vfs.find(path)
    if node is None:
        return [f"tree: путь не найден: {target}"]
    if not node.is_dir:
        return [f"tree: не каталог: {target}"]

    display = path if path != ROOT_PATH else ROOT_PATH
    result = [display]
    result.extend(_walk(node, ""))
    return result


CommandResult = list[str] | tuple[str, list[str]]
CommandFn = Callable[[Vfs, str, list[str]], CommandResult]
