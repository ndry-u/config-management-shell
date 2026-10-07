"""Реализации команд эмулятора, работающих с VFS."""

from __future__ import annotations

from collections.abc import Callable

from src.vfs import (
    NODE_TYPE_DIR,
    Vfs,
    VfsError,
    VfsNode,
)

PATH_SEPARATOR = "/"
ROOT_PATH = "/"
PARENT_DIR = ".."
CURRENT_DIR = "."
HIDDEN_PREFIX = "."
SIZE_UNIT_DIVIDER = 1024
LS_FLAG_ALL = "a"
LS_FLAG_LONG = "l"
LS_FLAG_HUMAN = "h"
LS_FLAGS_ALLOWED = (LS_FLAG_ALL, LS_FLAG_LONG, LS_FLAG_HUMAN)
CHMOD_MIN_LEN = 3
CHMOD_MAX_LEN = 4


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


def _node_name(node: VfsNode) -> str:
    """Возвращает имя узла с суффиксом-слешем для каталогов."""
    suffix = PATH_SEPARATOR if node.is_dir else ""
    return f"{node.name}{suffix}"


def _node_label(node: VfsNode) -> str:
    """Формирует длинную строку для вывода узла.

    Args:
        node: узел VFS.

    Returns:
        Строка с правами, владельцем, размером и именем.
    """
    size = len(node.content) if node.is_file else 0
    return (
        f"{node.mode} {node.owner:>8} {size:>6} {_node_name(node)}"
    )


def _node_label_human(node: VfsNode) -> str:
    """Длинная строка с человекочитаемым размером."""
    raw_size = len(node.content) if node.is_file else 0
    size = _format_size(raw_size)
    return (
        f"{node.mode} {node.owner:>8} {size:>7} {_node_name(node)}"
    )


def _parse_ls_args(args: list[str]) -> tuple[set[str], list[str]]:
    """Разделяет аргументы ls на флаги и пути.

    Args:
        args: аргументы команды.

    Returns:
        Кортеж (множество_флагов, список_путей).
    """
    flags: set[str] = set()
    paths: list[str] = []
    for arg in args:
        if arg.startswith("-") and arg != "-":
            for char in arg[1:]:
                if char in LS_FLAGS_ALLOWED:
                    flags.add(char)
        else:
            paths.append(arg)
    return flags, paths


def _format_ls_line(node: VfsNode, flags: set[str]) -> str:
    """Формирует строку вывода ls по флагам.

    Args:
        node: узел VFS.
        flags: множество активных флагов.

    Returns:
        Строка для вывода.
    """
    if LS_FLAG_LONG not in flags:
        return _node_name(node)
    if LS_FLAG_HUMAN in flags:
        return _node_label_human(node)
    return _node_label(node)


def _filter_children(
    children: list[VfsNode],
    flags: set[str],
) -> list[VfsNode]:
    """Убирает скрытые узлы, если флаг -a не задан.

    Args:
        children: список дочерних узлов.
        flags: множество активных флагов.

    Returns:
        Отфильтрованный список.
    """
    if LS_FLAG_ALL in flags:
        return children
    return [n for n in children if not n.name.startswith(HIDDEN_PREFIX)]


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


def _parent_path(path: str) -> str:
    """Возвращает путь к родительскому каталогу.

    Args:
        path: абсолютный путь.

    Returns:
        Путь родителя или корень, если path уже корень.
    """
    if path == ROOT_PATH:
        return ROOT_PATH
    parts = path.rstrip(PATH_SEPARATOR).split(PATH_SEPARATOR)
    parent = PATH_SEPARATOR.join(parts[:-1])
    return parent or ROOT_PATH


def _basename(path: str) -> str:
    """Возвращает последний компонент пути.

    Args:
        path: абсолютный путь.

    Returns:
        Имя узла или пустая строка для корня.
    """
    parts = [p for p in path.split(PATH_SEPARATOR) if p]
    return parts[-1] if parts else ""


def cmd_ls(vfs: Vfs, cwd: str, args: list[str]) -> list[str]:
    """Выводит содержимое каталога.

    Поддерживает флаги:
    - `-a` — показать скрытые файлы;
    - `-l` — длинный формат (права, владелец, размер);
    - `-h` — человекочитаемый размер (с `-l`).

    Args:
        vfs: виртуальная файловая система.
        cwd: текущий каталог.
        args: аргументы команды.

    Returns:
        Список строк для вывода.
    """
    flags, paths = _parse_ls_args(args)
    target = paths[0] if paths else cwd
    path = resolve_path(cwd, target)

    try:
        node = vfs.find(path)
        if node is None:
            return [f"ls: путь не найден: {target}"]
        if node.is_file:
            return [_format_ls_line(node, flags)]
        children = _filter_children(vfs.list_dir(path), flags)
        if not children:
            return []
        return [_format_ls_line(child, flags) for child in children]
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


def cmd_mkdir(vfs: Vfs, cwd: str, args: list[str]) -> list[str]:
    """Создаёт каталог в VFS.

    Args:
        vfs: виртуальная файловая система.
        cwd: текущий каталог.
        args: аргументы команды.

    Returns:
        Пустой список при успехе или сообщение об ошибке.
    """
    if not args:
        return ["mkdir: укажите имя каталога"]

    path = resolve_path(cwd, args[0])
    if path == ROOT_PATH:
        return ["mkdir: корневой каталог уже существует"]
    if vfs.find(path) is not None:
        return [f"mkdir: уже существует: {args[0]}"]

    parent = _parent_path(path)
    parent_node = vfs.find(parent)
    if parent_node is None or not parent_node.is_dir:
        return [f"mkdir: нет такого каталога: {parent}"]

    name = _basename(path)
    node = VfsNode(name, NODE_TYPE_DIR, mode="755")
    try:
        parent_node.children[name] = node
    except VfsError as error:
        return [f"mkdir: {error}"]
    return []


def _is_valid_mode(mode: str) -> bool:
    """Проверяет, что строка прав корректна.

    Args:
        mode: строка прав, например '644', '755', '1777'.

    Returns:
        True, если строка состоит только из цифр и длины 3 или 4.
    """
    if not mode.isdigit():
        return False
    return CHMOD_MIN_LEN <= len(mode) <= CHMOD_MAX_LEN


def cmd_chmod(vfs: Vfs, cwd: str, args: list[str]) -> list[str]:
    """Меняет права доступа узла VFS.

    Args:
        vfs: виртуальная файловая система.
        cwd: текущий каталог.
        args: аргументы команды.

    Returns:
        Пустой список при успехе или сообщение об ошибке.
    """
    if len(args) < 2:
        return ["chmod: укажите права и путь"]

    mode, target = args[0], args[1]
    if not _is_valid_mode(mode):
        return [f"chmod: неверный формат прав: {mode}"]

    path = resolve_path(cwd, target)
    node = vfs.find(path)
    if node is None:
        return [f"chmod: путь не найден: {target}"]

    node.mode = mode
    return []


CommandResult = list[str] | tuple[str, list[str]]
CommandFn = Callable[[Vfs, str, list[str]], CommandResult]
