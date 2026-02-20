"""
conftest.py — фикстуры и генерация синтетических тестовых изображений.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest
from PIL import Image


FIXTURES_DIR = Path(__file__).parent / "test_images"
# Папка для реальных изображений, которые пользователь может подложить вручную
REAL_IMAGES_DIR = Path(__file__).parent / "real_images"


# ─── Генерация синтетических изображений ──────────────────────────────────────

def _make_rgb(w: int, h: int, color: tuple) -> Image.Image:
    return Image.new("RGB", (w, h), color)


def _make_rgba(w: int, h: int, color: tuple) -> Image.Image:
    return Image.new("RGBA", (w, h), color)


def _make_palette(w: int, h: int) -> Image.Image:
    img = Image.new("P", (w, h))
    return img


def generate_test_images(target_dir: Path) -> dict[str, Path]:
    """Создаёт набор синтетических изображений для тестов. Возвращает dict имя → путь."""
    target_dir.mkdir(parents=True, exist_ok=True)
    generated: dict[str, Path] = {}

    # 1. Обычный JPEG 1920×1080
    p = target_dir / "landscape.jpg"
    _make_rgb(1920, 1080, (30, 120, 200)).save(p, "JPEG", quality=90)
    generated["landscape_jpg"] = p

    # 2. Портрет PNG 800×1200
    p = target_dir / "portrait.png"
    _make_rgb(800, 1200, (200, 50, 80)).save(p, "PNG")
    generated["portrait_png"] = p

    # 3. Квадрат WebP 1000×1000
    p = target_dir / "square.webp"
    _make_rgb(1000, 1000, (50, 200, 100)).save(p, "WEBP", quality=85)
    generated["square_webp"] = p

    # 4. RGBA PNG (с альфа-каналом) 640×480
    p = target_dir / "with_alpha.png"
    _make_rgba(640, 480, (255, 255, 0, 128)).save(p, "PNG")
    generated["rgba_png"] = p

    # 5. Palette-mode PNG 320×240
    p = target_dir / "palette.png"
    _make_palette(320, 240).save(p, "PNG")
    generated["palette_png"] = p

    # 6. Маленькое изображение 10×10 (граничный случай)
    p = target_dir / "tiny.jpeg"
    _make_rgb(10, 10, (0, 0, 0)).save(p, "JPEG")
    generated["tiny_jpeg"] = p

    # 7. Широкое изображение 4000×500
    p = target_dir / "wide.png"
    _make_rgb(4000, 500, (100, 100, 100)).save(p, "PNG")
    generated["wide_png"] = p

    # 8. Не-изображение (должно быть пропущено collect_images)
    p = target_dir / "readme.txt"
    p.write_text("This is not an image.")
    generated["not_image"] = p

    return generated


# ─── Pytest fixtures ──────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def test_images_dir(tmp_path_factory) -> Path:
    """Директория с синтетическими тестовыми изображениями (на всю сессию)."""
    d = tmp_path_factory.mktemp("input_images")
    generate_test_images(d)
    return d


@pytest.fixture()
def output_dir(tmp_path) -> Path:
    """Чистая выходная директория для каждого теста."""
    d = tmp_path / "output"
    d.mkdir()
    return d


@pytest.fixture(scope="session")
def real_images_dir() -> Path | None:
    """
    Возвращает путь к папке tests/real_images, если она существует и содержит файлы.
    Сюда можно вручную положить настоящие фотографии.
    """
    if REAL_IMAGES_DIR.is_dir() and any(REAL_IMAGES_DIR.iterdir()):
        return REAL_IMAGES_DIR
    return None
