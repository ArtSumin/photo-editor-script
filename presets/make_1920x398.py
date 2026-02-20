#!/usr/bin/env python3
"""
make-1920x398 — Автономный скрипт для создания изображений 1920×398 WebP.

Использование:
  1. Положите этот файл (или скомпилированный бинарник) в папку с фотографиями.
  2. Запустите — программа спросит базовое имя для файлов.
  3. Результат появится в папке на уровень выше:
       ../имя_1920x398/имя-1.webp, имя-2.webp, …

Пресет:
  Формат:   WebP
  Качество: 100
  Размер:   370 × 370 px (resize + crop по центру)
"""

from __future__ import annotations

import sys
import time
from pathlib import Path
from typing import Tuple

from PIL import Image

# ─── Пресет ───────────────────────────────────────────────────────────────────

WIDTH = 1920
HEIGHT = 398
FORMAT = "WEBP"
FORMAT_EXT = ".webp"
QUALITY = 100

SUPPORTED_EXTENSIONS: set[str] = {".jpg", ".jpeg", ".png", ".webp"}


# ─── Обработка изображений ───────────────────────────────────────────────────

def collect_images(input_dir: Path) -> list[Path]:
    """Собирает все поддерживаемые изображения из директории."""
    return sorted(
        p for p in input_dir.iterdir()
        if p.is_file() and p.suffix.lower() in SUPPORTED_EXTENSIONS
    )


def crop_center(img: Image.Image, target_w: int, target_h: int) -> Image.Image:
    """Обрезает изображение по центру до target_w × target_h."""
    img_w, img_h = img.size
    left = (img_w - target_w) // 2
    top = (img_h - target_h) // 2
    return img.crop((left, top, left + target_w, top + target_h))


def fit_and_crop(img: Image.Image, target_w: int, target_h: int) -> Image.Image:
    """
    Масштабирует изображение так, чтобы оно полностью покрывало target,
    затем обрезает по центру. Аналог CSS object-fit: cover.
    """
    orig_w, orig_h = img.size
    # Масштаб: берём больший, чтобы покрыть целевой размер
    scale = max(target_w / orig_w, target_h / orig_h)
    new_w = max(1, round(orig_w * scale))
    new_h = max(1, round(orig_h * scale))
    img = img.resize((new_w, new_h), Image.LANCZOS)
    return crop_center(img, target_w, target_h)


def ensure_rgb(img: Image.Image) -> Image.Image:
    """WebP поддерживает RGBA, но для совместимости конвертируем палитровые."""
    if img.mode in ("P", "LA"):
        return img.convert("RGBA")
    return img


def process_image(src: Path, dst_dir: Path, custom_name: str) -> Path:
    """Обрабатывает одно изображение с пресетными параметрами."""
    img = Image.open(src)
    img = fit_and_crop(img, WIDTH, HEIGHT)
    img = ensure_rgb(img)

    out_path = dst_dir / (custom_name + FORMAT_EXT)
    img.save(out_path, format=FORMAT, quality=QUALITY, method=6, lossless=True)
    return out_path


# ─── Определение рабочей папки ────────────────────────────────────────────────

def get_work_dir() -> Path:
    """
    PyInstaller-бинарник → папка, где лежит бинарник.
    Python-скрипт       → текущая рабочая директория.
    """
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path.cwd()


# ─── Main ─────────────────────────────────────────────────────────────────────

def main() -> None:
    work_dir = get_work_dir()

    print()
    print("╔══════════════════════════════════════════╗")
    print("║   make-1920x398  •  WebP  •  quality 100  ║")
    print("╚══════════════════════════════════════════╝")
    print()
    print(f"  📂 Папка с фото: {work_dir}")
    print()

    # --- Спрашиваем имя ---
    name = input("  Введите имя для файлов (например logo): ").strip()
    if not name:
        print("\n  ✖ Имя не может быть пустым.")
        input("  Нажмите Enter для выхода...")
        sys.exit(1)

    # --- Пути ---
    input_dir = work_dir
    output_dir = work_dir.parent / f"{name}_1920x398"
    output_dir.mkdir(parents=True, exist_ok=True)

    # --- Сбор изображений ---
    images = collect_images(input_dir)
    if not images:
        print("\n  ⚠  Изображения не найдены в текущей папке.")
        print("     Поддерживаемые форматы: jpg, jpeg, png, webp")
        input("\n  Нажмите Enter для выхода...")
        sys.exit(0)

    total = len(images)
    print()
    print(f"  📂 Найдено изображений: {total}")
    print(f"  📁 Результат: {output_dir.resolve()}")
    print(f"  📐 Размер: {WIDTH}×{HEIGHT} px")
    print(f"  🖼  Формат: WebP, качество {QUALITY}")
    print()

    # --- Обработка ---
    success = 0
    errors: list[str] = []
    t0 = time.perf_counter()

    for idx, src in enumerate(images, start=1):
        custom_name = f"{name}-{idx}"
        try:
            out = process_image(src, output_dir, custom_name)
            print(f"    [{idx}/{total}] ✔ {src.name} → {out.name}")
            success += 1
        except Exception as exc:
            errors.append(f"{src.name}: {exc}")
            print(f"    [{idx}/{total}] ✖ {src.name} — {exc}")

    elapsed = time.perf_counter() - t0
    print()
    print(f"  ✅ Готово: {success}/{total} за {elapsed:.2f}с")
    if errors:
        print(f"  ⚠  Ошибки ({len(errors)}):")
        for e in errors:
            print(f"     • {e}")

    print(f"\n  Результат в: {output_dir.resolve()}")
    input("\n  Нажмите Enter для выхода...")


if __name__ == "__main__":
    main()
