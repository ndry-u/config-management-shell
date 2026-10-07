# Эмулятор командной оболочки UNIX

Практическая работа №1 по дисциплине «Конфигурационное управление».
Вариант №20.

## Общее описание

Эмулятор командной оболочки UNIX с графическим интерфейсом (GUI) на
Python + Tkinter. Работает с виртуальной файловой системой (VFS),
загружаемой из CSV-файла в память.

## Этапы разработки

- [x] Этап 1. REPL — минимальный прототип
- [x] Этап 2. Конфигурация
- [x] Этап 3. VFS
- [x] Этап 4. Основные команды (`uniq`, `tree`, `wc`)
- [x] Этап 5. Дополнительные команды (`mkdir`, `chmod`)

## Функции и настройки

### Этап 1 (реализовано)

- GUI на Tkinter.
- Заголовок окна: `Эмулятор - [username@hostname]`.
- Парсер с поддержкой одинарных и двойных кавычек.
- Команда `exit`.
- Обработка ошибок: неизвестная команда, незакрытая кавычка.

### Этап 2 (реализовано)

- Параметры командной строки:
  - `--vfs` — путь к физическому расположению VFS;
  - `--prompt` — пользовательское приглашение к вводу;
  - `--script` — путь к стартовому скрипту.
- Отладочный вывод параметров при запуске.
- Стартовый скрипт: команды выполняются последовательно,
  ошибочные строки пропускаются, ввод и вывод отображаются в окне.
- Скрипты реальной ОС для тестирования:
  `scripts/demo.sh`, `scripts/demo.bat`.

### Этап 3 (реализовано)

- Виртуальная файловая система (VFS) хранится в памяти.
- VFS загружается из CSV-файла, путь указывается параметром `--vfs`.
- Формат CSV: колонки `path`, `type`, `content`, `mode`, `owner`.
- Вложенность выражается через `path` (`/home/user/file.txt`).
- Двоичные данные кодируются в base64 с префиксом `base64:`.
- Обработка ошибок загрузки: файл не найден, пустой файл,
  отсутствуют колонки, неверный тип узла, повреждённый base64.
- Промежуточные каталоги создаются автоматически.
- Тестовые наборы VFS:
  `data/vfs_minimal.csv`, `data/vfs_sample.csv`, `data/vfs_deep.csv`,
  `data/vfs_dupes.csv`.

### Этап 4 (реализовано)

- Команда `ls` — список файлов и каталогов с поддержкой флагов:
  - `-a` — показывать скрытые файлы (начинающиеся с `.`);
  - `-l` — длинный формат (права, владелец, размер, имя);
  - `-h` — человекочитаемый размер (вместе с `-l`);
  - флаги комбинируются: `ls -la`, `ls -lh`, `ls -lah`.
- Команда `cd` — смена текущего каталога, поддерживает `..`, `.`,
  абсолютные и относительные пути.
- Команда `uniq` — удаление повторяющихся строк из файла.
- Команда `wc` — подсчёт строк, слов и символов.
- Команда `tree` — рекурсивное дерево каталогов.
- Приглашение показывает текущий путь: `my> /home/user$ `.

### Этап 5 (реализовано)

- Команда `mkdir` — создание каталога в VFS (в памяти).
- Команда `chmod` — смена прав доступа файла или каталога в VFS.
- Поддержка относительных и абсолютных путей.
- Проверка формата прав (3 или 4 цифры).
- Обработка ошибок:
  - каталог уже существует;
  - нет родительского каталога;
  - неверный формат прав;
  - путь не найден;
  - недостаточно аргументов.

## Сборка и запуск

Требуется Python 3.10+.

На Windows:
```
run.bat
```

На Linux/macOS:
```bash
./run.sh
```

Либо напрямую из корня проекта:
```bash
python -m src.main
```

## Запуск тестов

```bash
python -m pytest tests/ -v
```

## Проверка стиля

```bash
python -m flake8 --max-line-length=80 src/ tests/
python -m pylint --rcfile=.pylintrc src/ tests/ --disable=all --enable=C0114,C0115,R0913,R0914,R0915,C0103,C0301,R0912
```

## Примеры использования

### Запуск с VFS

```bash
python -m src.main --vfs data/vfs_sample.csv --prompt "my> "
```

Вывод при запуске:
```
Параметры запуска:
  vfs_path       = 'data/vfs_sample.csv'
  prompt         = 'my> '
  startup_script = ''
VFS загружена: vfs_sample
Эмулятор запущен. Введите 'exit' для выхода.
```

### ls с флагами

```
my> /$ ls
home/
tmp/

my> /$ ls -l
755     root      0 home/
1777     root      0 tmp/

my> /$ ls -lah /home/user
644     user    11 B data.bin
644     user    38 B dupes.txt
644     user    17 B notes.txt
644     user    11 B readme.txt
```

### cd и работа с путями

```
my> /$ cd /home/user
my> /home/user$ cd ..
my> /home$ cd
my> /$
```

### wc и uniq

```
my> /$ wc /home/user/readme.txt
   1    2   11 /home/user/readme.txt

my> /$ uniq /home/user/dupes.txt
apple
banana
cherry
date
```

### tree

```
my> /$ tree
/
├── home/
│   └── user/
│       ├── data.bin
│       ├── dupes.txt
│       ├── notes.txt
│       └── readme.txt
└── tmp/
    └── log.txt
```

### mkdir

```
my> /$ mkdir /home/user/test
my> /$ ls /home/user
644     user data.bin
644     user dupes.txt
644     user notes.txt
644     user readme.txt
755     user test/

my> /$ mkdir /home/user/test
mkdir: уже существует: /home/user/test

my> /$ mkdir /missing/sub
mkdir: нет такого каталога: /
```

### chmod

```
my> /$ chmod 600 /home/user/readme.txt
my> /$ ls -l /home/user
600     user    11 readme.txt
644     user    38 dupes.txt
...

my> /$ chmod 1777 /home/user/newdir
my> /$ ls -l /home/user
1777     user    0 newdir/

my> /$ chmod abc /home/user/readme.txt
chmod: неверный формат прав: abc

my> /$ chmod 644 /missing.txt
chmod: путь не найден: /missing.txt
```

### Обработка ошибок

```
my> /$ cd /missing
cd: путь не найден: /missing

my> /$ cd /home/user/readme.txt
cd: не каталог: /home/user/readme.txt

my> /$ wc /missing.txt
wc: файл не найден: /missing.txt

my> /$ ls "/home
Ошибка разбора: Незакрытая кавычка: "

my> /$ abcd
abcd: команда не найдена
```

### Стартовый скрипт

Файл `scripts/startup.txt` содержит команды, которые эмулятор
выполняет при старте:

```
ls
ls -l
cd /home/user
wc readme.txt
uniq /tmp/log.txt
mkdir /home/user/test
chmod 600 /home/user/readme.txt
tree
```

Строки, начинающиеся с `#`, — комментарии; они пропускаются.
Ошибочные строки также пропускаются, выполнение не прерывается.

## Важное замечание

VFS модифицируется **только в памяти**. После выхода из эмулятора
все изменения (`mkdir`, `chmod`) теряются. Физический CSV-файл
не изменяется.