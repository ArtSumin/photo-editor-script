#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV="$SCRIPT_DIR/.venv"
DIST="$SCRIPT_DIR/dist"
PRODUCTION="$SCRIPT_DIR/production"

# Активируем venv если есть
if [ -d "$VENV" ]; then
    source "$VENV/bin/activate"
fi

# Проверяем pyinstaller
if ! command -v pyinstaller &>/dev/null; then
    echo "📦 Устанавливаю PyInstaller..."
    pip install pyinstaller
fi

# Создаём production/ если нет
mkdir -p "$PRODUCTION"

# ─── 1. Основной скрипт ──────────────────────────────────────────────────────

SRC="$SCRIPT_DIR/photo_editor.py"
OUT_NAME="photo_editor"

echo "🔧 [1/2] Сборка $OUT_NAME ..."
pyinstaller --onefile --name "$OUT_NAME" "$SRC" --noconfirm --clean --log-level WARN

cp "$DIST/$OUT_NAME" "$PRODUCTION/$OUT_NAME"
chmod +x "$PRODUCTION/$OUT_NAME"
rm -rf "$SCRIPT_DIR/build" "$DIST" "$SCRIPT_DIR/$OUT_NAME.spec"

echo "   ✅ $PRODUCTION/$OUT_NAME"

# ─── 2. Пресеты ──────────────────────────────────────────────────────────────

PRESETS_DIR="$SCRIPT_DIR/presets"

for preset in "$PRESETS_DIR"/make_*.py; do
    [ -f "$preset" ] || continue

    # make_370x370.py → make-370x370 (подчёркивания → дефисы для имени бинарника)
    base="$(basename "$preset" .py)"
    bin_name="${base//_/-}"

    echo "🔧 [2/2] Сборка пресета $bin_name ..."

    pyinstaller \
        --onefile \
        --name "$bin_name" \
        "$preset" \
        --noconfirm --clean --log-level WARN

    cp "$DIST/$bin_name" "$PRODUCTION/$bin_name"
    chmod +x "$PRODUCTION/$bin_name"
    rm -rf "$SCRIPT_DIR/build" "$DIST" "$SCRIPT_DIR/$bin_name.spec"

    echo "   ✅ $PRODUCTION/$bin_name"
done

echo ""
echo "═══════════════════════════════════════"
echo "  Все бинарники собраны в: production/"
echo "═══════════════════════════════════════"
echo ""
ls -lh "$PRODUCTION"/
echo ""
echo "Использование:"
echo "  ./production/photo_editor -i ./photos --max-side 1200 --format webp --quality 80"
echo "  # Пресеты: положите бинарник в папку с фото и запустите"
echo "  cp ./production/make-370x370 /путь/к/фоткам/ && cd /путь/к/фоткам/ && ./make-370x370"
