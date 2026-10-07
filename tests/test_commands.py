"""Юнит-тесты для команд эмулятора."""

from src.commands import (
    cmd_cd,
    cmd_chmod,
    cmd_ls,
    cmd_mkdir,
    cmd_tree,
    cmd_uniq,
    cmd_wc,
    resolve_path,
)
from src.vfs import NODE_TYPE_DIR, NODE_TYPE_FILE, Vfs, VfsNode


def _make_vfs() -> Vfs:
    """Создаёт тестовую VFS с несколькими уровнями вложенности."""
    vfs = Vfs(name="test")
    vfs.add_node("/home", VfsNode("home", NODE_TYPE_DIR, mode="755"))
    vfs.add_node("/home/user", VfsNode("user", NODE_TYPE_DIR, mode="755"))
    vfs.add_node(
        "/home/user/readme.txt",
        VfsNode("readme.txt", NODE_TYPE_FILE, content="a\nb\na\nc\n"),
    )
    vfs.add_node(
        "/home/user/empty.txt",
        VfsNode("empty.txt", NODE_TYPE_FILE, content=""),
    )
    vfs.add_node(
        "/home/user/multi.txt",
        VfsNode(
            "multi.txt",
            NODE_TYPE_FILE,
            content="one two three\nfour five\n",
        ),
    )
    vfs.add_node("/tmp", VfsNode("tmp", NODE_TYPE_DIR, mode="1777"))
    vfs.add_node(
        "/tmp/log.txt",
        VfsNode("log.txt", NODE_TYPE_FILE, content="x\nx\ny\n"),
    )
    return vfs


class TestResolvePath:
    """Тесты функции resolve_path."""

    def test_absolute(self) -> None:
        """Абсолютный путь возвращается как есть."""
        assert resolve_path("/home", "/tmp") == "/tmp"

    def test_relative(self) -> None:
        """Относительный путь присоединяется к текущему."""
        assert resolve_path("/home", "user") == "/home/user"

    def test_parent(self) -> None:
        """'..' поднимает на уровень выше."""
        assert resolve_path("/home/user", "..") == "/home"

    def test_parent_from_relative(self) -> None:
        """'../tmp' из /home/user даёт /home/tmp."""
        assert resolve_path("/home/user", "../tmp") == "/home/tmp"

    def test_current(self) -> None:
        """'.' оставляет путь неизменным."""
        assert resolve_path("/home", ".") == "/home"

    def test_double_dots_at_root(self) -> None:
        """'..' в корне остаётся корнем."""
        assert resolve_path("/", "..") == "/"

    def test_empty_target(self) -> None:
        """Пустой путь возвращает текущий каталог."""
        assert resolve_path("/home", "") == "/home"

    def test_multiple_slashes_absolute(self) -> None:
        """Двойные слеши в абсолютном пути схлопываются."""
        assert resolve_path("/home", "/user//docs") == "/user/docs"

    def test_multiple_slashes_relative(self) -> None:
        """Двойные слеши в относительном пути схлопываются."""
        assert resolve_path("/home", "user//docs") == "/home/user/docs"


class TestLs:
    """Тесты команды ls."""

    def test_ls_root_shows_children(self) -> None:
        """В корне видны home и tmp."""
        vfs = _make_vfs()
        lines = cmd_ls(vfs, "/", [])
        names = " ".join(lines)
        assert "home" in names
        assert "tmp" in names

    def test_ls_empty_dir(self) -> None:
        """Пустой каталог даёт пустой вывод."""
        vfs = _make_vfs()
        vfs.add_node("/empty", VfsNode("empty", NODE_TYPE_DIR))
        lines = cmd_ls(vfs, "/", ["empty"])
        assert lines == []

    def test_ls_specific_dir(self) -> None:
        """ls /home/user показывает файлы."""
        vfs = _make_vfs()
        lines = cmd_ls(vfs, "/", ["/home/user"])
        names = " ".join(lines)
        assert "readme.txt" in names
        assert "empty.txt" in names

    def test_ls_relative_path(self) -> None:
        """ls user из /home работает."""
        vfs = _make_vfs()
        lines = cmd_ls(vfs, "/home", ["user"])
        assert any("readme.txt" in line for line in lines)

    def test_ls_missing_path(self) -> None:
        """Отсутствующий путь даёт сообщение об ошибке."""
        vfs = _make_vfs()
        lines = cmd_ls(vfs, "/", ["missing"])
        assert "не найден" in lines[0]

    def test_ls_file_shows_single_line(self) -> None:
        """ls файла выводит одну строку."""
        vfs = _make_vfs()
        lines = cmd_ls(vfs, "/", ["/home/user/readme.txt"])
        assert len(lines) == 1
        assert "readme.txt" in lines[0]


class TestLsFlags:
    """Тесты флагов команды ls."""

    def test_ls_default_short_format(self) -> None:
        """Без -l выводятся только имена."""
        vfs = _make_vfs()
        lines = cmd_ls(vfs, "/", [])
        for line in lines:
            assert " " not in line.strip()

    def test_ls_long_format(self) -> None:
        """С -l выводятся права, владелец и размер."""
        vfs = _make_vfs()
        lines = cmd_ls(vfs, "/", ["-l"])
        assert any("755" in line for line in lines)

    def test_ls_hidden_visible_with_flag(self) -> None:
        """Флаг -a показывает скрытые файлы."""
        vfs = _make_vfs()
        vfs.add_node(
            "/.hidden",
            VfsNode(".hidden", NODE_TYPE_FILE, content="x"),
        )
        without = cmd_ls(vfs, "/", [])
        with_flag = cmd_ls(vfs, "/", ["-a"])
        assert not any(".hidden" in line for line in without)
        assert any(".hidden" in line for line in with_flag)

    def test_ls_combined_flags(self) -> None:
        """Комбинированные флаги -la работают."""
        vfs = _make_vfs()
        lines = cmd_ls(vfs, "/", ["-la"])
        assert any("755" in line for line in lines)

    def test_ls_flags_and_path(self) -> None:
        """Флаги и путь можно комбинировать."""
        vfs = _make_vfs()
        lines = cmd_ls(vfs, "/", ["-l", "/home"])
        assert any("user" in line for line in lines)

    def test_ls_human_readable(self) -> None:
        """Флаг -h даёт человекочитаемый размер."""
        vfs = _make_vfs()
        vfs.add_node(
            "/big.txt",
            VfsNode("big.txt", NODE_TYPE_FILE, content="x" * 2048),
        )
        lines = cmd_ls(vfs, "/", ["-lh"])
        assert any("2.0 KB" in line for line in lines)


class TestCd:
    """Тесты команды cd."""

    def test_cd_absolute(self) -> None:
        """cd /home переходит в /home."""
        vfs = _make_vfs()
        new_cwd, lines = cmd_cd(vfs, "/", ["/home"])
        assert new_cwd == "/home"
        assert lines == []

    def test_cd_relative(self) -> None:
        """cd user из /home переходит в /home/user."""
        vfs = _make_vfs()
        new_cwd, _ = cmd_cd(vfs, "/home", ["user"])
        assert new_cwd == "/home/user"

    def test_cd_parent(self) -> None:
        """cd .. из /home/user переходит в /home."""
        vfs = _make_vfs()
        new_cwd, _ = cmd_cd(vfs, "/home/user", [".."])
        assert new_cwd == "/home"

    def test_cd_without_args_goes_to_root(self) -> None:
        """cd без аргументов переходит в корень."""
        vfs = _make_vfs()
        new_cwd, _ = cmd_cd(vfs, "/home/user", [])
        assert new_cwd == "/"

    def test_cd_missing_path(self) -> None:
        """cd в отсутствующий путь не меняет cwd."""
        vfs = _make_vfs()
        new_cwd, lines = cmd_cd(vfs, "/", ["missing"])
        assert new_cwd == "/"
        assert "не найден" in lines[0]

    def test_cd_to_file_fails(self) -> None:
        """cd в файл не меняет cwd."""
        vfs = _make_vfs()
        new_cwd, lines = cmd_cd(vfs, "/", ["/home/user/readme.txt"])
        assert new_cwd == "/"
        assert "не каталог" in lines[0]


class TestUniq:
    """Тесты команды uniq."""

    def test_uniq_removes_duplicates(self) -> None:
        """Повторяющиеся строки удаляются."""
        vfs = _make_vfs()
        lines = cmd_uniq(vfs, "/", ["/home/user/readme.txt"])
        assert lines == ["a", "b", "c"]

    def test_uniq_preserves_order(self) -> None:
        """Порядок первого вхождения сохраняется."""
        vfs = _make_vfs()
        lines = cmd_uniq(vfs, "/", ["/tmp/log.txt"])
        assert lines == ["x", "y"]

    def test_uniq_empty_file(self) -> None:
        """Пустой файл → пустой вывод."""
        vfs = _make_vfs()
        lines = cmd_uniq(vfs, "/", ["/home/user/empty.txt"])
        assert lines == []

    def test_uniq_missing_file(self) -> None:
        """Отсутствующий файл даёт ошибку."""
        vfs = _make_vfs()
        lines = cmd_uniq(vfs, "/", ["missing.txt"])
        assert "не найден" in lines[0]

    def test_uniq_dir_fails(self) -> None:
        """uniq на каталоге даёт ошибку."""
        vfs = _make_vfs()
        lines = cmd_uniq(vfs, "/", ["/home"])
        assert "не файл" in lines[0]

    def test_uniq_without_args(self) -> None:
        """uniq без аргументов — сообщение."""
        vfs = _make_vfs()
        lines = cmd_uniq(vfs, "/", [])
        assert "укажите" in lines[0]


class TestWc:
    """Тесты команды wc."""

    def test_wc_counts_lines(self) -> None:
        """Считает количество строк."""
        vfs = _make_vfs()
        lines = cmd_wc(vfs, "/", ["/home/user/readme.txt"])
        parts = lines[0].split()
        assert parts[0] == "4"

    def test_wc_counts_words(self) -> None:
        """Считает количество слов."""
        vfs = _make_vfs()
        lines = cmd_wc(vfs, "/", ["/home/user/multi.txt"])
        parts = lines[0].split()
        assert parts[1] == "5"

    def test_wc_empty_file(self) -> None:
        """Пустой файл — нули."""
        vfs = _make_vfs()
        lines = cmd_wc(vfs, "/", ["/home/user/empty.txt"])
        parts = lines[0].split()
        assert parts[0] == "0"
        assert parts[1] == "0"
        assert parts[2] == "0"

    def test_wc_missing(self) -> None:
        """Отсутствующий файл."""
        vfs = _make_vfs()
        lines = cmd_wc(vfs, "/", ["missing"])
        assert "не найден" in lines[0]

    def test_wc_dir_fails(self) -> None:
        """wc на каталоге."""
        vfs = _make_vfs()
        lines = cmd_wc(vfs, "/", ["/home"])
        assert "не файл" in lines[0]

    def test_wc_without_args(self) -> None:
        """wc без аргументов."""
        vfs = _make_vfs()
        lines = cmd_wc(vfs, "/", [])
        assert "укажите" in lines[0]

    def test_wc_relative_path(self) -> None:
        """wc с относительным путём."""
        vfs = _make_vfs()
        lines = cmd_wc(vfs, "/home/user", ["readme.txt"])
        parts = lines[0].split()
        assert parts[0] == "4"


class TestTree:
    """Тесты команды tree."""

    def test_tree_starts_with_root(self) -> None:
        """Первая строка — корень."""
        vfs = _make_vfs()
        lines = cmd_tree(vfs, "/", [])
        assert lines[0] == "/"

    def test_tree_contains_all_levels(self) -> None:
        """Все уровни вложенности присутствуют."""
        vfs = _make_vfs()
        text = "\n".join(cmd_tree(vfs, "/", []))
        assert "home" in text
        assert "user" in text
        assert "readme.txt" in text

    def test_tree_specific_dir(self) -> None:
        """tree /home/user показывает файлы."""
        vfs = _make_vfs()
        lines = cmd_tree(vfs, "/", ["/home/user"])
        assert lines[0] == "/home/user"
        text = "\n".join(lines)
        assert "readme.txt" in text
        assert "empty.txt" in text

    def test_tree_missing(self) -> None:
        """tree несуществующего пути."""
        vfs = _make_vfs()
        lines = cmd_tree(vfs, "/", ["missing"])
        assert "не найден" in lines[0]

    def test_tree_file_fails(self) -> None:
        """tree файла — ошибка."""
        vfs = _make_vfs()
        lines = cmd_tree(vfs, "/", ["/home/user/readme.txt"])
        assert "не каталог" in lines[0]

    def test_tree_empty_dir(self) -> None:
        """tree пустого каталога — только заголовок."""
        vfs = _make_vfs()
        vfs.add_node("/empty", VfsNode("empty", NODE_TYPE_DIR))
        lines = cmd_tree(vfs, "/", ["/empty"])
        assert lines == ["/empty"]

    def test_tree_relative(self) -> None:
        """tree с относительным путём."""
        vfs = _make_vfs()
        lines = cmd_tree(vfs, "/home", ["user"])
        assert lines[0] == "/home/user"


class TestMkdir:
    """Тесты команды mkdir."""

    def test_mkdir_in_root(self) -> None:
        """mkdir /newdir создаёт каталог в корне."""
        vfs = _make_vfs()
        lines = cmd_mkdir(vfs, "/", ["/newdir"])
        assert lines == []
        node = vfs.find("/newdir")
        assert node is not None
        assert node.is_dir

    def test_mkdir_relative(self) -> None:
        """mkdir newdir в /home создаёт /home/newdir."""
        vfs = _make_vfs()
        lines = cmd_mkdir(vfs, "/home", ["newdir"])
        assert lines == []
        assert vfs.find("/home/newdir") is not None

    def test_mkdir_existing(self) -> None:
        """mkdir существующего каталога даёт ошибку."""
        vfs = _make_vfs()
        lines = cmd_mkdir(vfs, "/", ["/home"])
        assert "уже существует" in lines[0]

    def test_mkdir_missing_parent(self) -> None:
        """mkdir в несуществующем родителе даёт ошибку."""
        vfs = _make_vfs()
        lines = cmd_mkdir(vfs, "/", ["/missing/sub"])
        assert "нет такого каталога" in lines[0]

    def test_mkdir_without_args(self) -> None:
        """mkdir без аргументов — сообщение."""
        vfs = _make_vfs()
        lines = cmd_mkdir(vfs, "/", [])
        assert "укажите" in lines[0]

    def test_mkdir_root_fails(self) -> None:
        """mkdir / не создаёт корень."""
        vfs = _make_vfs()
        lines = cmd_mkdir(vfs, "/", ["/"])
        assert "корневой" in lines[0]

    def test_mkdir_deep(self) -> None:
        """mkdir по глубокому пути."""
        vfs = _make_vfs()
        lines = cmd_mkdir(vfs, "/", ["/home/user/projects"])
        assert lines == []
        assert vfs.find("/home/user/projects") is not None


class TestChmod:
    """Тесты команды chmod."""

    def test_chmod_file(self) -> None:
        """chmod 600 файла меняет mode."""
        vfs = _make_vfs()
        lines = cmd_chmod(vfs, "/", ["600", "/home/user/readme.txt"])
        assert lines == []
        node = vfs.find("/home/user/readme.txt")
        assert node is not None
        assert node.mode == "600"

    def test_chmod_dir(self) -> None:
        """chmod 700 каталога меняет mode."""
        vfs = _make_vfs()
        lines = cmd_chmod(vfs, "/", ["700", "/home"])
        assert lines == []
        node = vfs.find("/home")
        assert node is not None
        assert node.mode == "700"

    def test_chmod_relative(self) -> None:
        """chmod с относительным путём."""
        vfs = _make_vfs()
        lines = cmd_chmod(vfs, "/home/user", ["640", "readme.txt"])
        assert lines == []
        node = vfs.find("/home/user/readme.txt")
        assert node is not None
        assert node.mode == "640"

    def test_chmod_four_digits(self) -> None:
        """chmod принимает 4-значные права."""
        vfs = _make_vfs()
        lines = cmd_chmod(vfs, "/", ["1777", "/tmp"])
        assert lines == []
        node = vfs.find("/tmp")
        assert node is not None
        assert node.mode == "1777"

    def test_chmod_missing_path(self) -> None:
        """chmod несуществующего пути."""
        vfs = _make_vfs()
        lines = cmd_chmod(vfs, "/", ["644", "/missing"])
        assert "не найден" in lines[0]

    def test_chmod_invalid_mode(self) -> None:
        """chmod с неправильными правами."""
        vfs = _make_vfs()
        lines = cmd_chmod(vfs, "/", ["abc", "/home"])
        assert "неверный формат" in lines[0]

    def test_chmod_too_short(self) -> None:
        """chmod со слишком короткими правами."""
        vfs = _make_vfs()
        lines = cmd_chmod(vfs, "/", ["64", "/home"])
        assert "неверный формат" in lines[0]

    def test_chmod_too_long(self) -> None:
        """chmod со слишком длинными правами."""
        vfs = _make_vfs()
        lines = cmd_chmod(vfs, "/", ["17777", "/home"])
        assert "неверный формат" in lines[0]

    def test_chmod_without_args(self) -> None:
        """chmod без аргументов — сообщение."""
        vfs = _make_vfs()
        lines = cmd_chmod(vfs, "/", [])
        assert "укажите" in lines[0]

    def test_chmod_only_mode(self) -> None:
        """chmod только с правами — сообщение."""
        vfs = _make_vfs()
        lines = cmd_chmod(vfs, "/", ["644"])
        assert "укажите" in lines[0]
