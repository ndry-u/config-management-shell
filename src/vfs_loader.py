"""Загрузка VFS из CSV-файла."""

from __future__ import annotations

import base64
import binascii
import csv
from pathlib import Path

from src.vfs import (
    NODE_TYPE_DIR,
    NODE_TYPE_FILE,
    Vfs,
    VfsError,
    VfsNode,
)

BASE64_PREFIX = "base64:"
REQUIRED_COLUMNS = ("path", "type")
VALID_TYPES = (NODE_TYPE_FILE, NODE_TYPE_DIR)
DEFAULT_FILE_MODE = "644"
DEFAULT_OWNER = "user"


class VfsLoadError(Exception):
    """Ошибка загрузки VFS из файла."""


def _decode_base64(encoded: str, line_no: int) -> str:
    """Декодирует base64-строку в текст.

    Args:
        encoded: закодированная строка без префикса.
        line_no: номер строки CSV для сообщения об ошибке.

    Returns:
        Декодированный текст.

    Raises:
        VfsLoadError: если base64 повреждён.
    """
    try:
        decoded = base64.b64decode(encoded, validate=True)
    except (binascii.Error, ValueError) as error:
        raise VfsLoadError(
            f"Строка {line_no}: ошибка base64: {error}"
        ) from error
    return decoded.decode("utf-8", errors="replace")


def _decode_content(raw: str, line_no: int) -> str:
    """Декодирует содержимое с поддержкой base64.

    Args:
        raw: исходная строка содержимого из CSV.
        line_no: номер строки для сообщения об ошибке.

    Returns:
        Декодированная строка или исходная.
    """
    if not raw.startswith(BASE64_PREFIX):
        return raw
    encoded = raw[len(BASE64_PREFIX):]
    return _decode_base64(encoded, line_no)


def _parse_row(row: dict[str, str], line_no: int) -> tuple[str, VfsNode]:
    """Преобразует строку CSV в путь и узел VFS.

    Args:
        row: словарь с колонками path, type, content, mode, owner.
        line_no: номер строки для сообщения об ошибке.

    Returns:
        Кортеж (путь, узел).

    Raises:
        VfsLoadError: если строка некорректна.
    """
    path = row.get("path", "").strip()
    node_type = row.get("type", "").strip().lower()

    if not path:
        raise VfsLoadError(f"Строка {line_no}: пустая колонка path")
    if node_type not in VALID_TYPES:
        raise VfsLoadError(
            f"Строка {line_no}: неверный тип узла: {node_type!r}"
        )

    raw_content = row.get("content", "")
    content = ""
    if node_type == NODE_TYPE_FILE:
        content = _decode_content(raw_content, line_no)

    mode = row.get("mode", "").strip() or DEFAULT_FILE_MODE
    owner = row.get("owner", "").strip() or DEFAULT_OWNER
    name = path.rstrip("/").split("/")[-1] or "/"

    node = VfsNode(
        name=name,
        node_type=node_type,
        content=content,
        mode=mode,
        owner=owner,
    )
    return path, node


def _check_columns(fieldnames: list[str] | None) -> None:
    """Проверяет обязательные колонки CSV.

    Args:
        fieldnames: список колонок из CSV.

    Raises:
        VfsLoadError: если колонок нет или не хватает обязательных.
    """
    if fieldnames is None:
        raise VfsLoadError("Пустой CSV-файл")

    missing = [c for c in REQUIRED_COLUMNS if c not in fieldnames]
    if missing:
        raise VfsLoadError(f"Отсутствуют колонки: {missing}")


def _add_row(vfs: Vfs, row: dict[str, str], line_no: int) -> None:
    """Добавляет одну строку CSV в VFS.

    Args:
        vfs: целевая VFS.
        row: словарь с колонками CSV.
        line_no: номер строки для сообщения об ошибке.

    Raises:
        VfsLoadError: если строка некорректна.
    """
    node_path, node = _parse_row(row, line_no)

    if node_path == "/":
        return

    try:
        vfs.add_node(node_path, node)
    except VfsError as error:
        raise VfsLoadError(f"Строка {line_no}: {error}") from error


def load_vfs(path: str, name: str | None = None) -> Vfs:
    """Загружает VFS из CSV-файла.

    Args:
        path: путь к CSV-файлу.
        name: имя VFS; по умолчанию берётся имя файла без расширения.

    Returns:
        Загруженная VFS.

    Raises:
        VfsLoadError: если файл не найден, пуст или имеет неверный формат.
    """
    csv_path = Path(path)

    if not csv_path.exists():
        raise VfsLoadError(f"Файл VFS не найден: {path}")

    if name is None:
        name = csv_path.stem

    vfs = Vfs(name=name)

    with csv_path.open("r", encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream)
        _check_columns(reader.fieldnames)

        for line_no, row in enumerate(reader, start=2):
            _add_row(vfs, row, line_no)

    return vfs
