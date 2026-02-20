#!/usr/bin/env python3
"""
photo_editor.py — Production-ready CLI для массовой обработки изображений.

Возможности:
  • Resize (width / height / max-side) с сохранением пропорций
  • Crop по центру
  • Конвертация формата (JPEG, PNG, WebP)
  • Настройка качества сжатия
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path
from typing import Optional, Tuple

from PIL import Image

# ─── Константы ────────────────────────────────────────────────────────────────

SUPPORTED_EXTENSIONS: set[str] = {".jpg", ".jpeg", ".png", ".webp"}

FORMAT_MAP: dict[str, str] = {
    "jpeg": "JPEG",
    "jpg": "JPEG",
    "png": "PNG",
    "webp": "WEBP",
}

DEFAULT_QUALITY: int = 85


# ─── Утилиты ─────────────────────────────────────────────────────────────────

def collect_images(input_dir: Path) -> list[Path]:
    """Собирает все поддерживаемые изображения из директории (не рекурсивно)."""
    return sorted(
        p for p in input_dir.iterdir()
        if p.is_file() and p.suffix.lower() in SUPPORTED_EXTENSIONS
    )


def calculate_new_size(
    original_size: Tuple[int, int],
    *,
    width: Optional[int] = None,
    height: Optional[int] = None,
    max_side: Optional[int] = None,
) -> Tuple[int, int]:
    """
    Вычисляет новый размер с сохранением пропорций.

    Приоритет: max_side > (width + height) > width > height.
    """
    orig_w, orig_h = original_size

    if max_side is not None:
        ratio = max_side / max(orig_w, orig_h)
        return _apply_ratio(orig_w, orig_h, ratio)

    if width is not None and height is not None:
        return (width, height)

    if width is not None:
        ratio = width / orig_w
        return _apply_ratio(orig_w, orig_h, ratio)

    if height is not None:
        ratio = height / orig_h
        return _apply_ratio(orig_w, orig_h, ratio)

    return original_size


def _apply_ratio(w: int, h: int, ratio: float) -> Tuple[int, int]:
    return (max(1, round(w * ratio)), max(1, round(h * ratio)))


def crop_center(img: Image.Image, target_w: int, target_h: int) -> Image.Image:
    """Обрезает изображение по центру до target_w × target_h."""
    img_w, img_h = img.size
    left = (img_w - target_w) // 2
    top = (img_h - target_h) // 2
    right = left + target_w
    bottom = top + target_h
    return img.crop((left, top, right, bottom))


def ensure_rgb(img: Image.Image, target_format: str) -> Image.Image:
    """Конвертирует в RGB, если целевой формат — JPEG (не поддерживает альфа)."""
    if target_format == "JPEG" and img.mode in ("RGBA", "P", "LA"):
        return img.convert("RGB")
    return img


# ─── Основная обработка ──────────────────────────────────────────────────────

def process_image(
    src: Path,
    dst_dir: Path,
    *,
    width: Optional[int] = None,
    height: Optional[int] = None,
    max_side: Optional[int] = None,
    out_format: Optional[str] = None,
    quality: int = DEFAULT_QUALITY,
    do_crop_center: bool = False,
) -> Path:
    """
    Обрабатывает одно изображение и сохраняет результат в dst_dir.

    Возвращает путь к сохранённому файлу.
    """
    img = Image.open(src)

    # --- Resize ---
    needs_resize = any(v is not None for v in (width, height, max_side))
    if needs_resize:
        new_size = calculate_new_size(
            img.size, width=width, height=height, max_side=max_side,
        )
        img = img.resize(new_size, Image.LANCZOS)

    # --- Crop center ---
    if do_crop_center and width and height:
        img = crop_center(img, width, height)

    # --- Формат ---
    if out_format:
        pil_format = FORMAT_MAP[out_format.lower()]
        ext = f".{out_format.lower()}"
        if ext == ".jpg":
            ext = ".jpeg"
    else:
        pil_format = FORMAT_MAP.get(src.suffix.lower().lstrip("."), "JPEG")
        ext = src.suffix.lower()

    img = ensure_rgb(img, pil_format)

    # --- Сохранение ---
    out_name = src.stem + ext
    out_path = dst_dir / out_name
    save_kwargs: dict = {"quality": quality}
    if pil_format == "WEBP":
        save_kwargs["method"] = 4  # баланс скорость/качество
    img.save(out_path, format=pil_format, **save_kwargs)
    return out_path


# ─── CLI ──────────────────────────────────────────────────────────────────────

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="photo_editor",
        description="Массовая обработка изображений: resize, crop, convert.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
Примеры:
  photo_editor -i ./photos --max-side 1200 --format webp --quality 80
  photo_editor -i ./raw -o ./processed --width 800 --height 600 --crop-center --format jpeg

Если --output не указан, результат сохраняется в папку {input}_processed.
""",
    )

    p.add_argument("-i", "--input", required=True, type=Path,
                   help="Входная папка с изображениями")
    p.add_argument("-o", "--output", required=False, type=Path, default=None,
                   help="Выходная папка (по умолчанию: {input}_processed)")

    size_group = p.add_argument_group("Размер")
    size_group.add_argument("--width", type=int, default=None,
                            help="Целевая ширина (px)")
    size_group.add_argument("--height", type=int, default=None,
                            help="Целевая высота (px)")
    size_group.add_argument("--max-side", type=int, default=None,
                            help="Максимальная сторона (px), сохраняет пропорции")

    p.add_argument("-f", "--format", dest="out_format", default=None,
                   choices=["jpeg", "png", "webp"],
                   help="Выходной формат (jpeg | png | webp)")
    p.add_argument("-q", "--quality", type=int, default=DEFAULT_QUALITY,
                   help=f"Качество сжатия 0-100 (по умолчанию {DEFAULT_QUALITY})")
    p.add_argument("--crop-center", action="store_true",
                   help="Обрезать по центру до --width × --height после resize")

    return p


def validate_args(args: argparse.Namespace) -> None:
    if not args.input.is_dir():
        sys.exit(f"✖ Входная папка не найдена: {args.input}")
    if not 0 <= args.quality <= 100:
        sys.exit("✖ --quality должно быть в диапазоне 0-100")
    if args.crop_center and (args.width is None or args.height is None):
        sys.exit("✖ --crop-center требует указания --width и --height")


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    validate_args(args)

    # Авто-генерация output если не указан
    if args.output is None:
        args.output = args.input.parent / f"{args.input.name}_processed"

    # Подготовка
    args.output.mkdir(parents=True, exist_ok=True)
    images = collect_images(args.input)

    if not images:
        print("⚠  Изображения не найдены во входной папке.")
        sys.exit(0)

    total = len(images)
    print(f"📂 Найдено изображений: {total}")
    print(f"   Вход:  {args.input.resolve()}")
    print(f"   Выход: {args.output.resolve()}")
    print()

    success = 0
    errors: list[str] = []
    t0 = time.perf_counter()

    for idx, src in enumerate(images, start=1):
        try:
            out = process_image(
                src,
                args.output,
                width=args.width,
                height=args.height,
                max_side=args.max_side,
                out_format=args.out_format,
                quality=args.quality,
                do_crop_center=args.crop_center,
            )
            print(f"  [{idx}/{total}] ✔ {src.name} → {out.name}")
            success += 1
        except Exception as exc:
            errors.append(f"{src.name}: {exc}")
            print(f"  [{idx}/{total}] ✖ {src.name} — {exc}")

    elapsed = time.perf_counter() - t0
    print()
    print(f"✅ Готово: {success}/{total} за {elapsed:.2f}с")
    if errors:
        print(f"⚠  Ошибки ({len(errors)}):")
        for e in errors:
            print(f"   • {e}")


if __name__ == "__main__":
    main()
