@echo off
REM Скрипт реальной ОС для запуска эмулятора с разными параметрами.

cd /d "%~dp0\.."

echo === Запуск 1: все параметры ===
python -m src.main --vfs "data/vfs.csv" --prompt "my-shell> " --script "scripts/startup.txt"

echo.
echo === Запуск 2: только prompt ===
python -m src.main --prompt "test> "

echo.
echo === Запуск 3: без параметров ===
python -m src.main