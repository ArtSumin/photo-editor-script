# Photo Editor — CLI для массовой обработки изображений

## Установка зависимостей

```bash
pip install -r requirements.txt
```

---

## Примеры использования

### Уменьшить все фото до max-side 1200px и конвертировать в WebP

```bash
python photo_editor.py --input ./photos --output ./out --max-side 1200 --format webp --quality 80
```

### Ресайз до 800×600 с обрезкой по центру, формат JPEG

```bash
python photo_editor.py -i ./raw -o ./processed --width 800 --height 600 --crop-center --format jpeg
```

### Только изменить ширину (высота пропорционально)

```bash
python photo_editor.py -i ./input -o ./output --width 1024
```

### Конвертировать всё в PNG без ресайза

```bash
python photo_editor.py -i ./input -o ./output --format png
```

---

## Сборка в standalone бинарник (PyInstaller)

### 1. Установить PyInstaller

```bash
pip install pyinstaller
```

### 2. Сборка для macOS

```bash
pyinstaller --onefile --name photo_editor photo_editor.py
```

Бинарник → `dist/photo_editor`

Запуск:

```bash
./dist/photo_editor -i ./photos -o ./out --max-side 1200 --format webp
```

### 3. Сборка для Windows

```cmd
pyinstaller --onefile --name photo_editor photo_editor.py
```

Бинарник → `dist\photo_editor.exe`

Запуск:

```cmd
dist\photo_editor.exe -i .\photos -o .\out --max-side 1200 --format webp
```

---

## Поддерживаемые форматы

| Вход             | Выход              |
| ---------------- | ------------------ |
| `.jpg` `.jpeg`   | `jpeg`             |
| `.png`           | `png`              |
| `.webp`          | `webp`             |
