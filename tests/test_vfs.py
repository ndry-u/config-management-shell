"""Юнит-тесты для VFS и загрузчика CSV."""

import pytest

from src.vfs import (
    NODE_TYPE_DIR,
    NODE_TYPE_FILE,
    Vfs,
    VfsError,
    VfsNode,
)
from src.vfs_loader import VfsLoadError, load_vfs


class TestVfsModel:
    """Тесты модели VFS."""

    def test_empty_vfs_has_root(self) -> None:
        """Пустая VFS содержит только корневой каталог."""
        vfs = Vfs()
        assert vfs.root.name == "/"
        assert vfs.root.is_dir
        assert vfs.root.children == {}

    def test_add_file(self) -> None:
        """Добавление файла в корень VFS."""
        vfs = Vfs()
        vfs.add_node("/file.txt", VfsNode("file.txt", NODE_TYPE_FILE))
        node = vfs.find("/file.txt")
        assert node is not None
        assert node.is_file

    def test_add_creates_intermediate_dirs(self) -> None:
        """Промежуточные каталоги создаются автоматически."""
        vfs = Vfs()
        vfs.add_node("/a/b/c.txt", VfsNode("c.txt", NODE_TYPE_FILE))
        assert vfs.find("/a") is not None
        assert vfs.find("/a/b") is not None
        assert vfs.find("/a/b/c.txt") is not None

    def test_find_missing_returns_none(self) -> None:
        """Поиск отсутствующего пути возвращает None."""
        vfs = Vfs()
        assert vfs.find("/missing") is None

    def test_add_duplicate_raises(self) -> None:
        """Повторное добавление того же пути вызывает ошибку."""
        vfs = Vfs()
        vfs.add_node("/f.txt", VfsNode("f.txt", NODE_TYPE_FILE))
        with pytest.raises(VfsError):
            vfs.add_node("/f.txt", VfsNode("f.txt", NODE_TYPE_FILE))

    def test_list_dir_sorted(self) -> None:
        """Содержимое каталога отсортировано по имени."""
        vfs = Vfs()
        vfs.add_node("/b", VfsNode("b", NODE_TYPE_DIR))
        vfs.add_node("/a", VfsNode("a", NODE_TYPE_DIR))
        names = [n.name for n in vfs.list_dir("/")]
        assert names == ["a", "b"]

    def test_list_dir_on_file_raises(self) -> None:
        """Попытка прочитать каталог у файла вызывает ошибку."""
        vfs = Vfs()
        vfs.add_node("/f.txt", VfsNode("f.txt", NODE_TYPE_FILE))
        with pytest.raises(VfsError):
            vfs.list_dir("/f.txt")


class TestVfsLoader:
    """Тесты загрузчика VFS из CSV."""

    def test_load_sample(self, tmp_path) -> None:
        """Загрузка простого CSV с текстовым файлом."""
        csv_file = tmp_path / "v.csv"
        csv_file.write_text(
            "path,type,content,mode,owner\n"
            "/,dir,,755,root\n"
            "/home,dir,,755,root\n"
            "/home/readme.txt,file,hello,644,user\n",
            encoding="utf-8",
        )
        vfs = load_vfs(str(csv_file))
        node = vfs.find("/home/readme.txt")
        assert node is not None
        assert node.content == "hello"

    def test_base64_content(self, tmp_path) -> None:
        """Загрузка файла с содержимым в base64."""
        csv_file = tmp_path / "v.csv"
        csv_file.write_text(
            "path,type,content,mode,owner\n"
            "/,dir,,755,root\n"
            "/bin.txt,file,base64:SGVsbG8=,644,user\n",
            encoding="utf-8",
        )
        vfs = load_vfs(str(csv_file))
        node = vfs.find("/bin.txt")
        assert node is not None
        assert node.content == "Hello"

    def test_missing_file_raises(self) -> None:
        """Несуществующий файл вызывает ошибку."""
        with pytest.raises(VfsLoadError):
            load_vfs("nonexistent.csv")

    def test_invalid_type_raises(self, tmp_path) -> None:
        """Неверный тип узла вызывает ошибку."""
        csv_file = tmp_path / "v.csv"
        csv_file.write_text(
            "path,type,content,mode,owner\n"
            "/,dir,,755,root\n"
            "/bad,unknown,,644,user\n",
            encoding="utf-8",
        )
        with pytest.raises(VfsLoadError):
            load_vfs(str(csv_file))

    def test_missing_columns_raises(self, tmp_path) -> None:
        """Отсутствие обязательных колонок вызывает ошибку."""
        csv_file = tmp_path / "v.csv"
        csv_file.write_text("foo,bar\n1,2\n", encoding="utf-8")
        with pytest.raises(VfsLoadError):
            load_vfs(str(csv_file))

    def test_empty_file_raises(self, tmp_path) -> None:
        """Пустой файл вызывает ошибку."""
        csv_file = tmp_path / "v.csv"
        csv_file.write_text("", encoding="utf-8")
        with pytest.raises(VfsLoadError):
            load_vfs(str(csv_file))
