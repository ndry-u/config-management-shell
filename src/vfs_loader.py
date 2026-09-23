"""Загрузка VFS из CSV-файла."""

from __future__ import annotations

import base64
import binascii
import csv
from pathlib import Path

from src.vfs import Vfs, VfsError, VfsNode, NodeType

BASE64_PREFIX = "base64:"
REQUIRED_COLUMNS = ("path", "type")
VALID_TYPES = ("file", "dir")
MIN_COLUMNS = 2


class VfsLoadError(Exception):
    """Ошибка загрузки VFS из файла."""


def _decode_content(raw: str) -> str:
    """Декодирует содержимое файла из base64, если есть префикс.

    Args:
        raw: исходная строка содержимого из CSV.

    Returns:
        Декодированная строка или исходная, если префикса нет.

    Raises:
        VfsLoadError: если base64-строка повреждена.
    """
    if not raw.startswith(BASE64_PREFIX):
        return raw

    encoded = raw[len(BASE64_PREFIX):]
    try:
        decoded_bytes = base64.b64decode(encoded, validate=True)
        return decoded_bytes.decode("utf-8", errors="replace")
    except (binascii.Error, ValueError) as error:
        raise VfsLoadError(f"Ошибка декодирования base64: {error}") from error


def _parse_row(row: dict[str, str]) -> tuple[str, VfsNode]:
    """Преобразует строку CSV в путь и узел VFS.

    Args:
        row: словарь с колонками path, type, content, mode, owner.

    Returns:
        Кортеж (путь, узел).

    Raises:
        VfsLoadError: если строка некорректна.
    """
    path = row.get("path", "").strip()
    node_type_str = row.get("type", "").strip().lower()

    if not path:
        raise VfsLoadError("Пустая колонка path")
    if node_type_str not in VALID_TYPES:
        raise VfsLoadError(f"Неверный тип узла: {node_type_str!r}")

    node_type = NodeType(node_type_str)
    content = _decode_content(row.get("content", "")) if node_type is NodeType.FILE else ""
    mode = row.get("mode", "").strip() or "644"
    owner = row.get("owner", "").strip() or "user"
    name = path.rstrip("/").split("/")[-1] or "/"

    node = VfsNode(
        name=name,
        node_type=node_type,
        content=content,
        mode=mode,
        owner=owner,
    )
    return path, node


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

        if reader.fieldnames is None:
            raise VfsLoadError("Пустой CSV-файл")

        missing = [c for c in REQUIRED_COLUMNS if c not in reader.fieldnames]
        if missing:
            raise VfsLoadError(f"Отсутствуют колонки: {missing}")

        for row_number, row in enumerate(reader, start=2):
            try:
                node_path, node = _parse_row(row)
            except VfsLoadError as error:
                raise VfsLoadError(
                    f"Строка {row_number}: {error}"
                ) from error

            if node_path == "/":
                continue

            try:
                vfs.add_node(node_path, node)
            except VfsError as error:
                raise VfsLoadError(
                    f"Строка {row_number}: {error}"
                ) from error

    return vfs