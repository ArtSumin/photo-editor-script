#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV="$SCRIPT_DIR/.venv"
SRC="$SCRIPT_DIR/photo_editor.py"
OUT_NAME="photo_editor"
DIST="$SCRIPT_DIR/dist"

echo "🔧 Сборка $OUT_NAME ..."

# Активируем venv если есть
if [ -d "$VENV" ]; then
    source "$VENV/bin/activate"
fi

# Проверяем pyinstaller
if ! command -v pyinstaller &>/dev/null; then
    echo "📦 Устанавливаю PyInstaller..."
    pip install pyinstaller
fi

# Собираем
pyinstaller --onefile --name "$OUT_NAME" "$SRC" --noconfirm --clean --log-level WARN

# Выносим бинарник на верхний уровень
cp "$DIST/$OUT_NAME" "$SCRIPT_DIR/$OUT_NAME"
chmod +x "$SCRIPT_DIR/$OUT_NAME"

# Чистим артефакты сборки
rm -rf "$SCRIPT_DIR/build" "$DIST" "$SCRIPT_DIR/$OUT_NAME.spec"

echo ""
echo "✅ Готово: $SCRIPT_DIR/$OUT_NAME"
echo ""
echo "Использование:"
echo "  ./$OUT_NAME -i ./photos --max-side 1200 --format webp --quality 80"
