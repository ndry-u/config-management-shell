#!/usr/bin/env bash
# Скрипт реальной ОС для запуска эмулятора с разными параметрами.

set -e

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_ROOT"

echo "=== Запуск 1: все параметры ==="
python -m src.main \
  --vfs "data/vfs.csv" \
  --prompt "my-shell> " \
  --script "scripts/startup.txt"

echo
echo "=== Запуск 2: только prompt ==="
python -m src.main --prompt "test> "

echo
echo "=== Запуск 3: без параметров (значения по умолчанию) ==="
python -m src.main