"""Модель виртуальной файловой системы (VFS).

VFS хранится в памяти в виде дерева узлов. Каждый узел — либо
каталог, либо файл. Каталоги содержат дочерние узлы, файлы — данные.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

DEFAULT_MODE = "644"
DEFAULT_DIR_MODE = "755"
DEFAULT_OWNER = "user"
PATH_SEPARATOR = "/"
ROOT_NAME = "/"


class VfsError(Exception):
    """Ошибка работы с VFS."""


class NodeType(Enum):
    """Тип узла VFS."""

    FILE = "file"
    DIR = "dir"


@dataclass
class VfsNode:
    """Узел виртуальной файловой системы.

    Attributes:
        name: имя узла (без слешей).
        node_type: FILE или DIR.
        content: текстовое содержимое (для файлов).
        mode: права доступа в виде строки, например '644'.
        owner: владелец файла или каталога.
        children: дочерние узлы (только для каталогов).
    """

    name: str
    node_type: NodeType
    content: str = ""
    mode: str = DEFAULT_MODE
    owner: str = DEFAULT_OWNER
    children: dict[str, "VfsNode"] = field(default_factory=dict)

    @property
    def is_dir(self) -> bool:
        """Является ли узел каталогом."""
        return self.node_type is NodeType.DIR

    @property
    def is_file(self) -> bool:
        """Является ли узел файлом."""
        return self.node_type is NodeType.FILE


class Vfs:
    """Виртуальная файловая система в памяти."""

    def __init__(self, name: str = "vfs") -> None:
        """Создаёт VFS с корневым каталогом.

        Args:
            name: имя VFS.
        """
        self.name = name
        self.root = VfsNode(ROOT_NAME, NodeType.DIR, mode=DEFAULT_DIR_MODE)

    def normalize(self, path: str) -> str:
        """Приводит путь к абсолютному виду.

        Args:
            path: путь, возможно относительный.

        Returns:
            Абсолютный путь без завершающего слеша (кроме корня).
        """
        if not path.startswith(PATH_SEPARATOR):
            path = PATH_SEPARATOR + path
        while "//" in path:
            path = path.replace("//", "/")
        if len(path) > 1 and path.endswith(PATH_SEPARATOR):
            path = path[:-1]
        return path

    def split(self, path: str) -> list[str]:
        """Разбивает путь на компоненты.

        Args:
            path: абсолютный или относительный путь.

        Returns:
            Список компонентов без пустых строк.
        """
        return [part for part in self.normalize(path).split("/") if part]

    def find(self, path: str) -> VfsNode | None:
        """Находит узел по пути.

        Args:
            path: путь к узлу.

        Returns:
            Узел или None, если путь не существует.
        """
        node = self.root
        for part in self.split(path):
            if not node.is_dir or part not in node.children:
                return None
            node = node.children[part]
        return node

    def add_node(self, path: str, node: VfsNode) -> None:
        """Добавляет узел по указанному пути.

        Промежуточные каталоги создаются автоматически.

        Args:
            path: абсолютный путь к узлу.
            node: добавляемый узел.

        Raises:
            VfsError: если путь занят узлом другого типа.
        """
        parts = self.split(path)
        if not parts:
            raise VfsError("Нельзя заменить корневой каталог")

        parent = self._ensure_parent(parts[:-1])
        name = parts[-1]

        if name in parent.children:
            raise VfsError(f"Путь уже существует: {path}")

        parent.children[name] = node

    def _ensure_parent(self, parts: list[str]) -> VfsNode:
        """Возвращает родительский узел, создавая промежуточные каталоги.

        Args:
            parts: компоненты пути родителя.

        Returns:
            Родительский узел.

        Raises:
            VfsError: если по пути встречается файл.
        """
        node = self.root
        for part in parts:
            existing = node.children.get(part)
            if existing is None:
                existing = VfsNode(part, NodeType.DIR, mode=DEFAULT_DIR_MODE)
                node.children[part] = existing
            elif not existing.is_dir:
                raise VfsError(f"Не каталог: {part}")
            node = existing
        return node

    def list_dir(self, path: str) -> list[VfsNode]:
        """Возвращает содержимое каталога.

        Args:
            path: путь к каталогу.

        Returns:
            Список дочерних узлов, отсортированный по имени.

        Raises:
            VfsError: если путь не найден или это не каталог.
        """
        node = self.find(path)
        if node is None:
            raise VfsError(f"Путь не найден: {path}")
        if not node.is_dir:
            raise VfsError(f"Не каталог: {path}")
        return sorted(node.children.values(), key=lambda n: n.name)