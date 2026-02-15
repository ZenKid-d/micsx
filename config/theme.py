"""Theme and color scheme management."""

from dataclasses import dataclass
from typing import Dict


@dataclass
class Theme:
    """Color theme for the application."""
    
    name: str
    # Backgrounds
    background: str
    surface: str
    surface_alt: str
    
    # Text
    text: str
    text_muted: str
    text_dim: str
    
    # Accents
    primary: str
    secondary: str
    accent: str
    
    # Status
    success: str
    warning: str
    error: str
    
    # Player specific
    progress_bg: str
    progress_fg: str
    
    def to_textual_colors(self) -> Dict[str, str]:
        """Convert theme to Textual color dictionary."""
        return {
            "background": self.background,
            "surface": self.surface,
            "surface_alt": self.surface_alt,
            "text": self.text,
            "text_muted": self.text_muted,
            "text_dim": self.text_dim,
            "primary": self.primary,
            "secondary": self.secondary,
            "accent": self.accent,
            "success": self.success,
            "warning": self.warning,
            "error": self.error,
            "progress_bg": self.progress_bg,
            "progress_fg": self.progress_fg,
            "panel": self.surface,
            "border": self.text_dim,
            "border_focus": self.primary,
            "selection": self.primary,
            "selection_bg": f"{self.primary}33",
        }


def get_default_theme() -> Theme:
    """Get the default Tokyo Night theme."""
    return Theme(
        name="tokyo_night",
        # Backgrounds
        background="#1a1b26",
        surface="#24283b",
        surface_alt="#292e42",
        
        # Text
        text="#c0caf5",
        text_muted="#565f89",
        text_dim="#3b4261",
        
        # Accents
        primary="#7aa2f7",
        secondary="#bb9af7",
        accent="#7dcfff",
        
        # Status
        success="#9ece6a",
        warning="#e0af68",
        error="#f7768e",
        
        # Player
        progress_bg="#3b4261",
        progress_fg="#7aa2f7",
    )


# Available themes
THEMES: Dict[str, Theme] = {
    "tokyo_night": get_default_theme(),
    "tokyo_night_storm": Theme(
        name="tokyo_night_storm",
        background="#24283b",
        surface="#1f2335",
        surface_alt="#292e42",
        text="#a9b1d6",
        text_muted="#565f89",
        text_dim="#3b4261",
        primary="#7aa2f7",
        secondary="#bb9af7",
        accent="#7dcfff",
        success="#9ece6a",
        warning="#e0af68",
        error="#f7768e",
        progress_bg="#3b4261",
        progress_fg="#7aa2f7",
    ),
    "nord": Theme(
        name="nord",
        background="#2e3440",
        surface="#3b4252",
        surface_alt="#434c5e",
        text="#eceff4",
        text_muted="#d8dee9",
        text_dim="#4c566a",
        primary="#88c0d0",
        secondary="#81a1c1",
        accent="#8fbcbb",
        success="#a3be8c",
        warning="#ebcb8b",
        error="#bf616a",
        progress_bg="#4c566a",
        progress_fg="#88c0d0",
    ),
    "gruvbox": Theme(
        name="gruvbox",
        background="#282828",
        surface="#3c3836",
        surface_alt="#504945",
        text="#ebdbb2",
        text_muted="#a89984",
        text_dim="#665c54",
        primary="#83a598",
        secondary="#d3869b",
        accent="#8ec07c",
        success="#b8bb26",
        warning="#fabd2f",
        error="#fb4934",
        progress_bg="#665c54",
        progress_fg="#83a598",
    ),
}


def get_theme(name: str) -> Theme:
    """Get a theme by name, returns default if not found."""
    return THEMES.get(name, get_default_theme())