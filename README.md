# 🎵 Micsx - CLI Music Player

Кросс-платформенный музыкальный плеер для терминала с красивым интерфейсом и поддержкой обложек альбомов.

## 🎯 Особенности

- 🎨 Красивый TUI интерфейс (Textual)
- 🖼️ Отображение обложек альбомов (Kitty terminal)
- 📁 Управление библиотекой музыки
- 🎵 Поддержка MP3, FLAC, OGG, WAV, M4A
- 📋 Плейлисты (создание/сохранение)
- 🔍 Поиск по названию и исполнителю
- ⌨️ Vim-like навигация и hotkeys
- 🔀 Shuffle и Repeat режимы
- 💾 SQLite база данных для метаданных
- 🐧 Linux + 🪟 Windows поддержка

## 📦 Установка

### Зависимости

```bash
# Linux (Arch)
sudo pacman -S python python-pip vlc

# Linux (Ubuntu/Debian)
sudo apt install python3 python3-pip vlc

# Windows
# Скачай и установи VLC: https://www.videolan.org/vlc/
# Установи Python: https://www.python.org/downloads/
```

### Установка плеера

```bash
# Клонируй репозиторий
git clone https://github.com/Zen-Kid-d/micsx.git
cd micsx

# Установи Python зависимости
pip install -r requirements.txt

# Запусти
python main.py
```

## 🎮 Управление

### Навигация
| Клавиша | Действие |
|---------|----------|
| W / ↑ | Вверх по списку |
| S / ↓ | Вниз по списку |
| A / ← | Перемотка назад (5 сек) |
| D / → | Перемотка вперёд (5 сек) |
| Enter | Выбрать трек |

### Воспроизведение
| Клавиша | Действие |
|---------|----------|
| Space | Play/Pause |
| N | Next track |
| P | Previous track |
| R | Toggle Repeat |
| Z | Toggle Shuffle |

### Громкость
| Клавиша | Действие |
|---------|----------|
| + / = | Увеличить громкость |
| - | Уменьшить громкость |
| M | Mute/Unmute |

### Другое
| Клавиша | Действие |
|---------|----------|
| L | Библиотека |
| / | Поиск |
| Q | Выход |

## 🏗️ Архитектура

```
┌─────────────────────────────────────────┐
│         UI Layer (Textual)              │  ← Пользовательский интерфейс
│  ┌──────────┐  ┌──────────┐  ┌────────┐│
│  │  Main    │  │ Library  │  │Playlist││
│  │  Screen  │  │ Screen   │  │ Screen ││
│  └──────────┘  └──────────┘  └────────┘│
└─────────────────────────────────────────┘
              ↕️ События / Команды
┌─────────────────────────────────────────┐
│      Business Logic Layer               │  ← Логика приложения
│  ┌──────────┐  ┌──────────┐  ┌────────┐│
│  │  Audio   │  │ Playlist │  │ Search ││
│  │  Player  │  │ Manager  │  │ Engine ││
│  └──────────┘  └──────────┘  └────────┘│
└─────────────────────────────────────────┘
              ↕️ Запросы / Данные
┌─────────────────────────────────────────┐
│        Data Layer                       │  ← Данные и хранилище
│  ┌──────────┐  ┌──────────┐  ┌────────┐│
│  │ Database │  │ Metadata │  │  File  ││
│  │   (SQL)  │  │ (mutagen)│  │ Scanner││
│  └──────────┘  └──────────┘  └────────┘│
└─────────────────────────────────────────┘
```

## 📁 Структура проекта

```
micsx/
├── config/           # Конфигурация и настройки
│   ├── settings.py   # Настройки приложения
│   └── theme.py      # Темы оформления
├── data/             # Работа с данными
│   ├── database.py   # SQLite база данных
│   ├── metadata.py   # Извлечение метаданных
│   └── scanner.py    # Сканирование файлов
├── core/             # Бизнес-логика
│   ├── player.py     # Аудиоплеер (VLC)
│   ├── playlist.py   # Управление плейлистами
│   ├── library.py    # Управление библиотекой
│   ├── search.py     # Поиск треков
│   └── hotkeys.py    # Глобальные хоткеи
├── ui/               # Пользовательский интерфейс
│   ├── app.py        # Главное приложение
│   ├── screens/      # Экраны
│   │   ├── main.py
│   │   ├── library.py
│   │   └── playlists.py
│   └── widgets/      # Виджеты
│       ├── track_list.py
│       ├── player_bar.py
│       └── cover_display.py
├── main.py           # Точка входа
└── requirements.txt  # Зависимости
```

## 🔧 Конфигурация

Файл конфигурации находится в `~/.config/micsx/settings.json`:

```json
{
  "music_path": "~/Music",
  "volume": 80,
  "shuffle": false,
  "repeat": "off",
  "theme": "catppuccin-mocha",
  "scan_on_startup": true,
  "global_hotkeys_enabled": true
}
```

## 🖼️ Обложки альбомов

Для отображения обложек используйте Kitty terminal:

```bash
# Установка Kitty (Linux)
sudo pacman -S kitty  # Arch
sudo apt install kitty  # Ubuntu/Debian
```

## 📝 Лицензия

MIT License
