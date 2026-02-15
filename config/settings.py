"""Application settings management."""

import json
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, asdict, field


def get_config_dir() -> Path:
    """Get the configuration directory path."""
    config_dir = Path.home() / ".config" / "micsx"
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir


def get_data_dir() -> Path:
    """Get the data directory path for database and cache."""
    data_dir = Path.home() / ".local" / "share" / "micsx"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


@dataclass
class Settings:
    """Application settings."""
    
    # Music library
    music_path: str = field(default_factory=lambda: str(Path.home() / "Music"))
    music_dirs: list[str] = field(default_factory=lambda: [str(Path.home() / "Music")])
    supported_formats: list[str] = field(default_factory=lambda: [
        ".mp3", ".flac", ".ogg", ".wav", ".m4a", ".aac", ".wma"
    ])
    scan_on_startup: bool = True
    
    # Playback
    volume: int = 80
    shuffle: bool = False
    repeat: bool = False  # False = off, True = all (can add "one" later)
    
    # UI
    theme: str = "tokyo_night"
    show_cover_art: bool = True
    
    # Global hotkeys
    global_hotkeys_enabled: bool = True
    hotkey_play_pause: str = "<ctrl>+<alt>+p"
    hotkey_next: str = "<ctrl>+<alt>+n"
    hotkey_prev: str = "<ctrl>+<alt>+b"
    
    # Window
    min_width: int = 80
    min_height: int = 24
    
    @classmethod
    def get_config_path(cls) -> Path:
        """Get path to config file."""
        return get_config_dir() / "config.json"
    
    @classmethod
    def load(cls) -> "Settings":
        """Load settings from config file."""
        config_path = cls.get_config_path()
        
        if config_path.exists():
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})
            except (json.JSONDecodeError, TypeError):
                pass
        
        return cls()
    
    def save(self) -> None:
        """Save settings to config file."""
        config_path = self.get_config_path()
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(asdict(self), f, indent=2, ensure_ascii=False)
    
    def add_music_dir(self, path: str) -> None:
        """Add a music directory."""
        if path not in self.music_dirs:
            self.music_dirs.append(path)
            self.save()
    
    def remove_music_dir(self, path: str) -> None:
        """Remove a music directory."""
        if path in self.music_dirs:
            self.music_dirs.remove(path)
            self.save()