# 🎵 Micsx - CLI Music Player

A cross-platform terminal music player with a beautiful TUI interface and album cover support.

![License](https://img.shields.io/badge/license-MIT-blue)
![Python](https://img.shields.io/badge/python-3.10+-green)
![Platform](https://img.shields.io/badge/platform-Linux%20%7C%20Windows-lightgrey)

## 🎯 Features

- 🎨 Beautiful TUI interface (Textual)
- 🖼️ Album cover display (Kitty terminal)
- 📁 Music library management
- 🎵 Support for MP3, FLAC, OGG, WAV, M4A
- 📋 Playlists (create/save/load)
- 🔍 Search by title and artist
- ⌨️ Vim-like navigation and hotkeys
- 🔀 Shuffle and Repeat modes
- 🔔 Toast notifications for actions
- 🎯 Playing track highlight
- 🗑️ Remove tracks from queue
- 💾 SQLite database for metadata
- 🐧 Linux + 🪟 Windows support

## 📦 Installation

### Requirements

```
# Linux (Arch)
sudo pacman -S python python-pip vlc

# Linux (Ubuntu/Debian)
sudo apt install python3 python3-pip vlc

# Windows
# Download and install VLC: https://www.videolan.org/vlc/
# Install Python: https://www.python.org/downloads/
```

### Install the Plan


# Clone the repository
```
git clone https://github.com/yourusername/micsx.git
cd micsx
```
# Create virtual environment
```
python -m venv venv
```

# Activate venv
```
source venv/bin/activate  # Linux
# or
.\venv\Scripts\activate  # Windows
```
```
# Install dependencies
pip install -r requirements.txt

# Run
python main.py
```

## 🎮 Controls

### Navigation
| Key | Action |
|-----|--------|
| W / ↑ | Move up in list |
| S / ↓ | Move down in list |
| A / ← | Seek backward (5 sec) |
| D / → | Seek forward (5 sec) |
| Enter | Select track |

### Playback
| Key | Action |
|-----|--------|
| Space | Play/Pause |
| N | Next track |
| P | Previous track |
| R | Toggle Repeat (OFF/ONE) |
| S | Toggle Shuffle |

### Volume
| Key | Action |
|-----|--------|
| + / = | Increase volume |
| - | Decrease volume |
| M | Mute/Unmute |

### Queue
| Key | Action |
|-----|--------|
| X / Delete | Remove track from queue |

### Other
| Key | Action |
|-----|--------|
| L | Open library |
| / | Search |
| Q | Quit |

## 🏗️ Architecture

```
┌─────────────────────────────────────────┐
│         UI Layer (Textual)              │  ← User Interface
│  ┌──────────┐  ┌──────────┐  ┌────────┐│
│  │  Main    │  │ Library  │  │Playlist││
│  │  Screen  │  │ Screen   │  │ Screen ││
│  └──────────┘  └──────────┘  └────────┘│
└─────────────────────────────────────────┘
              ↕️ Events / Commands
┌─────────────────────────────────────────┐
│      Business Logic Layer               │  ← Application Logic
│  ┌──────────┐  ┌──────────┐  ┌────────┐│
│  │  Audio   │  │ Playlist │  │ Search ││
│  │  Player  │  │ Manager  │  │ Engine ││
│  └──────────┘  └──────────┘  └────────┘│
└─────────────────────────────────────────┘
              ↕️ Queries / Data
┌─────────────────────────────────────────┐
│        Data Layer                       │  ← Data Storage
│  ┌──────────┐  ┌──────────┐  ┌────────┐│
│  │ Database │  │ Metadata │  │  File  ││
│  │   (SQL)  │  │ (mutagen)│  │ Scanner││
│  └──────────┘  └──────────┘  └────────┘│
└─────────────────────────────────────────┘
```

## 📁 Project Structure

```
micsx/
├── config/           # Configuration and settings
│   ├── settings.py   # Application settings
│   └── theme.py      # Theme definitions
├── data/             # Data handling
│   ├── database.py   # SQLite database
│   ├── metadata.py   # Metadata extraction
│   └── scanner.py    # File scanning
├── core/             # Business logic
│   ├── player.py     # Audio player (VLC)
│   ├── playlist.py   # Playlist management
│   ├── library.py    # Library management
│   ├── search.py     # Track search
│   └── hotkeys.py    # Global hotkeys
├── ui/               # User interface
│   ├── app.py        # Main application
│   ├── screens/      # Screens
│   │   ├── main.py
│   │   ├── library.py
│   │   └── playlists.py
│   └── widgets/      # Widgets
│       ├── track_list.py
│       ├── player_bar.py
│       └── cover_display.py
├── main.py           # Entry point
└── requirements.txt  # Dependencies
```

## 🔧 Configuration

Configuration file is located at `~/.config/micsx/settings.json`:

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

## 🖼️ Album Covers

For album cover display, use Kitty terminal:

```bash
# Install Kitty (Linux)
sudo pacman -S kitty  # Arch
sudo apt install kitty  # Ubuntu/Debian
```

## 📝 License

MIT License
<<<<<<< HEAD
=======

## 🙏 Credits

- [Textual](https://github.com/Textualize/textual) - TUI framework
- [python-vlc](https://github.com/oaubert/python-vlc) - VLC bindings
- [mutagen](https://github.com/quodlibet/mutagen) - Audio metadata
>>>>>>> 167b338 (0.2)
