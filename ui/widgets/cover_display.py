"""Cover art display widget using Kitty terminal graphics."""

import base64
import os
import sys
from pathlib import Path
from typing import Optional, Tuple

from textual.widget import Widget
from textual.widgets import Static
from textual.reactive import reactive

from data.metadata import MetadataExtractor


class CoverDisplay(Widget):
    """Display album cover art in Kitty-compatible terminals."""
    
    DEFAULT_CSS = """
    CoverDisplay {
        width: 20;
        height: 10;
        text-align: center;
        content-align: center middle;
    }
    
    CoverDisplay Static {
        text-align: center;
    }
    """
    
    # Reactive properties
    cover_path: reactive[str] = reactive("", layout=True)
    has_cover: reactive[bool] = reactive(False, layout=True)
    
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._cover_data: Optional[bytes] = None
        self._cover_mime: Optional[str] = None
        self._kitty_supported = self._check_kitty_support()
    
    def _check_kitty_support(self) -> bool:
        """Check if terminal supports Kitty graphics protocol."""
        # Check if we're in Kitty terminal
        term = os.environ.get("TERM", "")
        term_program = os.environ.get("TERM_PROGRAM", "")
        
        return "kitty" in term.lower() or "kitty" in term_program.lower()
    
    def compose(self):
        """Compose the cover display."""
        yield Static(self._get_display_text(), id="cover-text")
    
    def _get_display_text(self) -> str:
        """Get display text for the cover area."""
        if not self._kitty_supported:
            return "[dim]Cover art requires Kitty terminal[/]"
        
        if not self.has_cover:
            return "[dim]No cover[/]"
        
        return ""  # Cover will be drawn by Kitty
    
    def set_cover_from_track(self, track_path: str) -> None:
        """Set cover from a track file.
        
        Args:
            track_path: Path to the audio file.
        """
        result = MetadataExtractor.extract_cover(Path(track_path))
        
        if result:
            self._cover_data, self._cover_mime = result
            self.has_cover = True
            
            if self._kitty_supported:
                self._display_kitty_image()
        else:
            self._cover_data = None
            self._cover_mime = None
            self.has_cover = False
            self._clear_kitty_image()
    
    def set_cover_from_file(self, image_path: str) -> None:
        """Set cover from an image file.
        
        Args:
            image_path: Path to the image file.
        """
        try:
            path = Path(image_path)
            if not path.exists():
                self.has_cover = False
                return
            
            self._cover_data = path.read_bytes()
            self._cover_mime = self._get_mime_from_extension(path.suffix)
            self.has_cover = True
            
            if self._kitty_supported:
                self._display_kitty_image()
        except Exception:
            self.has_cover = False
    
    def clear_cover(self) -> None:
        """Clear the cover display."""
        self._cover_data = None
        self._cover_mime = None
        self.has_cover = False
        
        if self._kitty_supported:
            self._clear_kitty_image()
    
    def _get_mime_from_extension(self, ext: str) -> str:
        """Get MIME type from file extension."""
        ext = ext.lower()
        mime_map = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".gif": "image/gif",
            ".webp": "image/webp",
        }
        return mime_map.get(ext, "image/jpeg")
    
    def _display_kitty_image(self) -> None:
        """Display image using Kitty graphics protocol."""
        if not self._cover_data or not self._kitty_supported:
            return
        
        try:
            # Encode image data
            encoded = base64.b64encode(self._cover_data).decode("ascii")
            
            # Get widget dimensions (approximate character size)
            width = self.size.width
            height = self.size.height
            
            # Send Kitty graphics escape sequence
            # a=T: transmit and display
            # f: format (24 for RGB, 32 for RGBA, 100 for PNG/JPEG auto-detect)
            # s, v: width and height in pixels (auto-detected)
            # c, r: columns and rows to display in
            
            # Use PNG/JPEG format (100) for automatic detection
            escape = f"\033_Ga=T,f=100,c={width},r={height};{encoded}\033\\"
            
            # Write to stderr (Kitty expects it there)
            sys.stderr.write(escape)
            sys.stderr.flush()
        except Exception:
            pass
    
    def _clear_kitty_image(self) -> None:
        """Clear Kitty graphics."""
        if not self._kitty_supported:
            return
        
        try:
            # Delete all images
            escape = "\033_Ga=d\033\\"
            sys.stderr.write(escape)
            sys.stderr.flush()
        except Exception:
            pass
    
    def on_hide(self) -> None:
        """Handle widget hide - clear image."""
        self._clear_kitty_image()
    
    def on_leave(self) -> None:
        """Handle widget leave - clear image when screen changes."""
        self._clear_kitty_image()