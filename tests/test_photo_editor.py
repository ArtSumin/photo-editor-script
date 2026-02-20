"""
test_photo_editor.py — юнит- и интеграционные тесты для photo_editor.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest
from PIL import Image

# Подключаем модуль из корня проекта
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from photo_editor import (
    calculate_new_size,
    collect_images,
    crop_center,
    ensure_rgb,
    process_image,
)


# ═══════════════════════════════════════════════════════════════════════════════
#  Unit-тесты: calculate_new_size
# ═══════════════════════════════════════════════════════════════════════════════

class TestCalculateNewSize:
    """Тесты для функции calculate_new_size."""

    def test_no_params_returns_original(self):
        assert calculate_new_size((1920, 1080)) == (1920, 1080)

    def test_width_only_keeps_aspect(self):
        w, h = calculate_new_size((1920, 1080), width=960)
        assert w == 960
        assert h == 540

    def test_height_only_keeps_aspect(self):
        w, h = calculate_new_size((1920, 1080), height=540)
        assert w == 960
        assert h == 540

    def test_width_and_height_exact(self):
        w, h = calculate_new_size((1920, 1080), width=800, height=600)
        assert (w, h) == (800, 600)

    def test_max_side_landscape(self):
        w, h = calculate_new_size((1920, 1080), max_side=960)
        assert w == 960
        assert h == 540

    def test_max_side_portrait(self):
        w, h = calculate_new_size((800, 1200), max_side=600)
        assert w == 400
        assert h == 600

    def test_max_side_square(self):
        w, h = calculate_new_size((1000, 1000), max_side=500)
        assert (w, h) == (500, 500)

    def test_max_side_overrides_width_height(self):
        """max_side имеет приоритет над width/height."""
        w, h = calculate_new_size((1920, 1080), width=100, height=100, max_side=960)
        assert w == 960
        assert h == 540

    def test_tiny_result_at_least_1px(self):
        w, h = calculate_new_size((10000, 1), max_side=1)
        assert w >= 1
        assert h >= 1


# ═══════════════════════════════════════════════════════════════════════════════
#  Unit-тесты: crop_center
# ═══════════════════════════════════════════════════════════════════════════════

class TestCropCenter:
    """Тесты для функции crop_center."""

    def test_crop_center_basic(self):
        img = Image.new("RGB", (1000, 800), (255, 0, 0))
        result = crop_center(img, 500, 400)
        assert result.size == (500, 400)

    def test_crop_center_no_change(self):
        img = Image.new("RGB", (500, 500), (0, 0, 0))
        result = crop_center(img, 500, 500)
        assert result.size == (500, 500)

    def test_crop_center_small_target(self):
        img = Image.new("RGB", (1920, 1080), (0, 0, 0))
        result = crop_center(img, 100, 100)
        assert result.size == (100, 100)


# ═══════════════════════════════════════════════════════════════════════════════
#  Unit-тесты: ensure_rgb
# ═══════════════════════════════════════════════════════════════════════════════

class TestEnsureRgb:
    """Тесты конвертации в RGB для JPEG."""

    def test_rgba_to_rgb_for_jpeg(self):
        img = Image.new("RGBA", (100, 100), (255, 0, 0, 128))
        result = ensure_rgb(img, "JPEG")
        assert result.mode == "RGB"

    def test_palette_to_rgb_for_jpeg(self):
        img = Image.new("P", (100, 100))
        result = ensure_rgb(img, "JPEG")
        assert result.mode == "RGB"

    def test_rgb_stays_rgb_for_jpeg(self):
        img = Image.new("RGB", (100, 100), (255, 0, 0))
        result = ensure_rgb(img, "JPEG")
        assert result.mode == "RGB"

    def test_rgba_stays_rgba_for_png(self):
        img = Image.new("RGBA", (100, 100), (255, 0, 0, 128))
        result = ensure_rgb(img, "PNG")
        assert result.mode == "RGBA"

    def test_rgba_stays_rgba_for_webp(self):
        img = Image.new("RGBA", (100, 100), (255, 0, 0, 128))
        result = ensure_rgb(img, "WEBP")
        assert result.mode == "RGBA"


# ═══════════════════════════════════════════════════════════════════════════════
#  Unit-тесты: collect_images
# ═══════════════════════════════════════════════════════════════════════════════

class TestCollectImages:
    """Тесты для сбора изображений из директории."""

    def test_collects_only_images(self, test_images_dir):
        images = collect_images(test_images_dir)
        names = {p.name for p in images}
        # Не должно содержать txt-файл
        assert "readme.txt" not in names
        # Должно содержать все изображения
        assert "landscape.jpg" in names
        assert "portrait.png" in names
        assert "square.webp" in names
        assert "with_alpha.png" in names
        assert "tiny.jpeg" in names

    def test_empty_dir(self, tmp_path):
        images = collect_images(tmp_path)
        assert images == []

    def test_returns_sorted(self, test_images_dir):
        images = collect_images(test_images_dir)
        names = [p.name for p in images]
        assert names == sorted(names)


# ═══════════════════════════════════════════════════════════════════════════════
#  Интеграционные тесты: process_image
# ═══════════════════════════════════════════════════════════════════════════════

class TestProcessImage:
    """Интеграционные тесты для обработки одного изображения."""

    def test_resize_max_side(self, test_images_dir, output_dir):
        src = test_images_dir / "landscape.jpg"
        out = process_image(src, output_dir, max_side=960)
        img = Image.open(out)
        assert max(img.size) == 960
        assert img.size == (960, 540)

    def test_resize_width_only(self, test_images_dir, output_dir):
        src = test_images_dir / "landscape.jpg"
        out = process_image(src, output_dir, width=480)
        img = Image.open(out)
        assert img.size[0] == 480
        # Пропорционально 1920:1080 → 480:270
        assert img.size[1] == 270

    def test_resize_height_only(self, test_images_dir, output_dir):
        src = test_images_dir / "portrait.png"
        out = process_image(src, output_dir, height=600)
        img = Image.open(out)
        assert img.size[1] == 600
        # 800:1200 → 400:600
        assert img.size[0] == 400

    def test_convert_to_webp(self, test_images_dir, output_dir):
        src = test_images_dir / "landscape.jpg"
        out = process_image(src, output_dir, out_format="webp")
        assert out.suffix == ".webp"
        img = Image.open(out)
        assert img.format == "WEBP"

    def test_convert_to_jpeg(self, test_images_dir, output_dir):
        src = test_images_dir / "portrait.png"
        out = process_image(src, output_dir, out_format="jpeg")
        assert out.suffix == ".jpeg"
        img = Image.open(out)
        assert img.format == "JPEG"

    def test_convert_to_png(self, test_images_dir, output_dir):
        src = test_images_dir / "landscape.jpg"
        out = process_image(src, output_dir, out_format="png")
        assert out.suffix == ".png"
        img = Image.open(out)
        assert img.format == "PNG"

    def test_rgba_to_jpeg_conversion(self, test_images_dir, output_dir):
        """RGBA PNG → JPEG должен пройти без ошибок (конвертация в RGB)."""
        src = test_images_dir / "with_alpha.png"
        out = process_image(src, output_dir, out_format="jpeg")
        img = Image.open(out)
        assert img.mode == "RGB"
        assert img.format == "JPEG"

    def test_palette_to_jpeg_conversion(self, test_images_dir, output_dir):
        """Palette PNG → JPEG без ошибок."""
        src = test_images_dir / "palette.png"
        out = process_image(src, output_dir, out_format="jpeg")
        img = Image.open(out)
        assert img.mode == "RGB"

    def test_crop_center_integration(self, test_images_dir, output_dir):
        src = test_images_dir / "landscape.jpg"
        out = process_image(
            src, output_dir, width=800, height=600, do_crop_center=True,
        )
        img = Image.open(out)
        assert img.size == (800, 600)

    def test_quality_affects_file_size(self, test_images_dir, output_dir):
        """Низкое качество → меньший файл."""
        src = test_images_dir / "landscape.jpg"
        out_low = process_image(src, output_dir, quality=10, out_format="jpeg")
        size_low = out_low.stat().st_size

        out_dir_high = output_dir / "high"
        out_dir_high.mkdir()
        out_high = process_image(src, out_dir_high, quality=95, out_format="jpeg")
        size_high = out_high.stat().st_size

        assert size_low < size_high

    def test_no_resize_keeps_original_dimensions(self, test_images_dir, output_dir):
        src = test_images_dir / "square.webp"
        out = process_image(src, output_dir)
        img = Image.open(out)
        assert img.size == (1000, 1000)

    def test_wide_image_max_side(self, test_images_dir, output_dir):
        src = test_images_dir / "wide.png"
        out = process_image(src, output_dir, max_side=800)
        img = Image.open(out)
        assert max(img.size) == 800
        # 4000×500 → 800×100
        assert img.size == (800, 100)

    def test_tiny_image_resize_up(self, test_images_dir, output_dir):
        """Маленькое изображение можно увеличить."""
        src = test_images_dir / "tiny.jpeg"
        out = process_image(src, output_dir, width=100, height=100)
        img = Image.open(out)
        assert img.size == (100, 100)

    def test_output_file_name_preserved(self, test_images_dir, output_dir):
        src = test_images_dir / "landscape.jpg"
        out = process_image(src, output_dir)
        assert out.stem == "landscape"


# ═══════════════════════════════════════════════════════════════════════════════
#  E2E тест: полный CLI
# ═══════════════════════════════════════════════════════════════════════════════

class TestCLI:
    """End-to-end тесты через вызов скрипта как subprocess."""

    SCRIPT = str(Path(__file__).resolve().parent.parent / "photo_editor.py")

    def test_cli_basic_run(self, test_images_dir, output_dir):
        result = subprocess.run(
            [
                sys.executable, self.SCRIPT,
                "--input", str(test_images_dir),
                "--output", str(output_dir),
                "--max-side", "500",
                "--format", "webp",
                "--quality", "75",
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "✅ Готово" in result.stdout
        # Должны быть webp-файлы в output
        webp_files = list(output_dir.glob("*.webp"))
        assert len(webp_files) > 0

    def test_cli_missing_input(self, tmp_path):
        result = subprocess.run(
            [
                sys.executable, self.SCRIPT,
                "--input", str(tmp_path / "nonexistent"),
                "--output", str(tmp_path / "out"),
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode != 0

    def test_cli_crop_without_dimensions(self, test_images_dir, tmp_path):
        result = subprocess.run(
            [
                sys.executable, self.SCRIPT,
                "--input", str(test_images_dir),
                "--output", str(tmp_path / "out"),
                "--crop-center",
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode != 0

    def test_cli_empty_input(self, tmp_path):
        empty_in = tmp_path / "empty_in"
        empty_in.mkdir()
        result = subprocess.run(
            [
                sys.executable, self.SCRIPT,
                "--input", str(empty_in),
                "--output", str(tmp_path / "out"),
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "не найдены" in result.stdout

    def test_cli_creates_output_dir(self, test_images_dir, tmp_path):
        out = tmp_path / "deep" / "nested" / "output"
        result = subprocess.run(
            [
                sys.executable, self.SCRIPT,
                "--input", str(test_images_dir),
                "--output", str(out),
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert out.is_dir()


# ═══════════════════════════════════════════════════════════════════════════════
#  Тесты на реальных изображениях (опционально)
# ═══════════════════════════════════════════════════════════════════════════════

class TestRealImages:
    """
    Тесты запускаются только если в tests/real_images/ лежат файлы.
    Положите туда пару реальных фото для проверки.
    """

    def test_real_images_max_side(self, real_images_dir, output_dir):
        if real_images_dir is None:
            pytest.skip("Нет реальных изображений в tests/real_images/")
        images = collect_images(real_images_dir)
        if not images:
            pytest.skip("Папка real_images существует, но изображений нет")
        for src in images:
            out = process_image(src, output_dir, max_side=800, out_format="webp", quality=80)
            img = Image.open(out)
            assert max(img.size) <= 800
            assert img.format == "WEBP"

    def test_real_images_crop_center(self, real_images_dir, output_dir):
        if real_images_dir is None:
            pytest.skip("Нет реальных изображений в tests/real_images/")
        images = collect_images(real_images_dir)
        for src in images:
            out = process_image(
                src, output_dir, width=400, height=400, do_crop_center=True,
            )
            img = Image.open(out)
            assert img.size == (400, 400)
