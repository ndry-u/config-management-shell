"""Юнит-тесты для команд эмулятора."""
from src.commands import (
    cmd_cd,
    cmd_ls,
    cmd_tree,
    cmd_uniq,
    cmd_wc,
    resolve_path,
)
from src.vfs import NODE_TYPE_FILE, Vfs, VfsNode


def _make_vfs() -> Vfs:
    """Создаёт простую VFS для тестов."""
    vfs = Vfs(name="test")
    vfs.add_node("/home", VfsNode("home", "dir"))
    vfs.add_node("/home/user", VfsNode("user", "dir"))
    vfs.add_node(
        "/home/user/readme.txt",
        VfsNode("readme.txt", NODE_TYPE_FILE, content="a\nb\na\nc\n"),
    )
    vfs.add_node(
        "/home/user/empty.txt",
        VfsNode("empty.txt", NODE_TYPE_FILE, content=""),
    )
    return vfs


class TestResolvePath:
    """Тесты функции resolve_path."""

    def test_absolute(self) -> None:
        assert resolve_path("/home", "/tmp") == "/tmp"

    def test_relative(self) -> None:
        assert resolve_path("/home", "user") == "/home/user"

    def test_parent(self) -> None:
        assert resolve_path("/home/user", "..") == "/home"

    def test_current(self) -> None:
        assert resolve_path("/home", ".") == "/home"

    def test_double_dots_at_root(self) -> None:
        assert resolve_path("/", "..") == "/"


class TestLs:
    """Тесты команды ls."""

    def test_ls_root(self) -> None:
        vfs = _make_vfs()
        lines = cmd_ls(vfs, "/", [])
        assert any("home" in line for line in lines)

    def test_ls_missing(self) -> None:
        vfs = _make_vfs()
        lines = cmd_ls(vfs, "/", ["missing"])
        assert "не найден" in lines[0]

    def test_ls_file(self) -> None:
        vfs = _make_vfs()
        lines = cmd_ls(vfs, "/", ["/home/user/readme.txt"])
        assert len(lines) == 1
        assert "readme.txt" in lines[0]


class TestCd:
    """Тесты команды cd."""

    def test_cd_absolute(self) -> None:
        vfs = _make_vfs()
        new_cwd, lines = cmd_cd(vfs, "/", ["/home"])
        assert new_cwd == "/home"
        assert lines == []

    def test_cd_relative(self) -> None:
        vfs = _make_vfs()
        new_cwd, _ = cmd_cd(vfs, "/home", ["user"])
        assert new_cwd == "/home/user"

    def test_cd_missing(self) -> None:
        vfs = _make_vfs()
        new_cwd, lines = cmd_cd(vfs, "/", ["missing"])
        assert new_cwd == "/"
        assert "не найден" in lines[0]

    def test_cd_to_file_fails(self) -> None:
        vfs = _make_vfs()
        _, lines = cmd_cd(vfs, "/", ["/home/user/readme.txt"])
        assert "не каталог" in lines[0]

    def test_cd_without_args(self) -> None:
        vfs = _make_vfs()
        new_cwd, _ = cmd_cd(vfs, "/home", [])
        assert new_cwd == "/"


class TestUniq:
    """Тесты команды uniq."""

    def test_uniq_removes_duplicates(self) -> None:
        vfs = _make_vfs()
        lines = cmd_uniq(vfs, "/", ["/home/user/readme.txt"])
        assert lines == ["a", "b", "c"]

    def test_uniq_missing(self) -> None:
        vfs = _make_vfs()
        lines = cmd_uniq(vfs, "/", ["missing.txt"])
        assert "не найден" in lines[0]

    def test_uniq_without_args(self) -> None:
        vfs = _make_vfs()
        lines = cmd_uniq(vfs, "/", [])
        assert "укажите" in lines[0]


class TestWc:
    """Тесты команды wc."""

    def test_wc_counts(self) -> None:
        vfs = _make_vfs()
        lines = cmd_wc(vfs, "/", ["/home/user/readme.txt"])
        parts = lines[0].split()
        assert parts[0] == "4"

    def test_wc_empty(self) -> None:
        vfs = _make_vfs()
        lines = cmd_wc(vfs, "/", ["/home/user/empty.txt"])
        parts = lines[0].split()
        assert parts[0] == "0"

    def test_wc_missing(self) -> None:
        vfs = _make_vfs()
        lines = cmd_wc(vfs, "/", ["missing"])
        assert "не найден" in lines[0]


class TestTree:
    """Тесты команды tree."""

    def test_tree_has_root(self) -> None:
        vfs = _make_vfs()
        lines = cmd_tree(vfs, "/", [])
        assert lines[0] == "/"

    def test_tree_contains_children(self) -> None:
        vfs = _make_vfs()
        lines = cmd_tree(vfs, "/", [])
        text = "\n".join(lines)
        assert "home" in text
        assert "user" in text
        assert "readme.txt" in text

    def test_tree_missing(self) -> None:
        vfs = _make_vfs()
        lines = cmd_tree(vfs, "/", ["missing"])
        assert "не найден" in lines[0]
