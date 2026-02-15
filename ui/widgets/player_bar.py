"""Player bar widget for playback controls and info."""

from typing import Optional, TYPE_CHECKING

from textual.widget import Widget
from textual.widgets import Static, ProgressBar
from textual.containers import Horizontal, Vertical
from textual.reactive import reactive
from textual.message import Message

from core.player import PlayerState
from core.playlist import RepeatMode

if TYPE_CHECKING:
    from core.player import TrackInfo


class PlayerBar(Widget):
    """Bottom player bar with controls and track info."""
    
    DEFAULT_CSS = """
    PlayerBar {
        dock: bottom;
        height: 5;
        width: 1fr;
        background: $surface-lighten-1;
        border-top: thick $primary;
        padding: 1 2;
    }
    
    PlayerBar .progress-row {
        height: 1;
        width: 1fr;
        align: center middle;
        margin-bottom: 1;
    }
    
    PlayerBar .time-label {
        width: 6;
        text-align: center;
        color: $text-muted;
    }
    
    PlayerBar .progress-bar-container {
        width: 1fr;
        height: 1;
        padding: 0 1;
    }
    
    PlayerBar ProgressBar {
        height: 1;
        width: 100%;
        background: $surface;
    }
    
    PlayerBar Bar > .bar--bar {
        background: $surface;
        color: $primary;
    }
    
    PlayerBar .info-row {
        height: 2;
        width: 1fr;
        align: center middle;
    }
    
    PlayerBar .track-info {
        width: 1fr;
        height: 2;
        content-align: left middle;
    }
    
    PlayerBar .controls {
        width: auto;
        height: 2;
        content-align: center middle;
        padding: 0 2;
    }
    
    PlayerBar .status-icons {
        width: auto;
        height: 2;
        text-align: right;
        content-align: center middle;
        padding: 0 1;
    }
    """
    
    # Reactive properties
    track_title: reactive[str] = reactive("", layout=True)
    track_artist: reactive[str] = reactive("", layout=True)
    state: reactive[PlayerState] = reactive(PlayerState.STOPPED, layout=True)
    position: reactive[float] = reactive(0.0, layout=True)
    current_time: reactive[int] = reactive(0, layout=True)
    total_time: reactive[int] = reactive(0, layout=True)
    volume: reactive[int] = reactive(80, layout=True)
    shuffle: reactive[bool] = reactive(False, layout=True)
    repeat: reactive[RepeatMode] = reactive(RepeatMode.OFF, layout=True)
    
    class PlayPause(Message):
        """Play/pause toggle message."""
        pass
    
    class NextTrack(Message):
        """Next track message."""
        pass
    
    class PrevTrack(Message):
        """Previous track message."""
        pass
    
    class Seek(Message):
        """Seek message."""
        def __init__(self, position: float) -> None:
            super().__init__()
            self.position = position
    
    class VolumeChange(Message):
        """Volume change message."""
        def __init__(self, volume: int) -> None:
            super().__init__()
            self.volume = volume
    
    class ToggleShuffle(Message):
        """Toggle shuffle message."""
        pass
    
    class ToggleRepeat(Message):
        """Toggle repeat message."""
        pass
    
    def compose(self):
        """Compose the player bar."""
        # Progress bar row
        with Horizontal(classes="progress-row"):
            yield Static(self._format_time(self.current_time), classes="time-label", id="time-current")
            with Vertical(classes="progress-bar-container"):
                yield ProgressBar(total=100, show_percentage=False, id="progress")
            yield Static(self._format_time(self.total_time), classes="time-label", id="time-total")
        
        # Controls row
        with Horizontal():
            with Vertical(classes="track-info"):
                yield Static(self._get_track_display(), id="track-display")
            
            with Horizontal(classes="controls"):
                yield Static(self._get_controls_display(), id="controls-display")
            
            with Horizontal(classes="status-icons"):
                yield Static(self._get_status_display(), id="status-display")
    
    def _get_track_display(self) -> str:
        """Get track display string."""
        if not self.track_title:
            return "[dim]No track playing[/]"
        
        if self.track_artist:
            return f"[bold]{self.track_title}[/] [dim]- {self.track_artist}[/]"
        return f"[bold]{self.track_title}[/]"
    
    def _get_controls_display(self) -> str:
        """Get controls display string."""
        play_icon = "⏸" if self.state == PlayerState.PLAYING else "▶"
        return f"◀ {play_icon} ▶  Vol: {self.volume}%"
    
    def _get_status_display(self) -> str:
        """Get status icons display."""
        icons = []
        
        if self.shuffle:
            icons.append("🔀")
        
        if self.repeat == RepeatMode.ONE:
            icons.append("🔂")
        
        return " ".join(icons) if icons else ""
    
    def _format_time(self, seconds: int) -> str:
        """Format time as M:SS."""
        if seconds <= 0:
            return "0:00"
        minutes = seconds // 60
        secs = seconds % 60
        return f"{minutes}:{secs:02d}"
    
    def watch_track_title(self, old_value: str, new_value: str) -> None:
        """Update track display when title changes."""
        try:
            display = self.query_one("#track-display", Static)
            display.update(self._get_track_display())
        except Exception:
            pass
    
    def watch_track_artist(self, old_value: str, new_value: str) -> None:
        """Update track display when artist changes."""
        try:
            display = self.query_one("#track-display", Static)
            display.update(self._get_track_display())
        except Exception:
            pass
    
    def watch_state(self, old_value: PlayerState, new_value: PlayerState) -> None:
        """Update controls when state changes."""
        try:
            display = self.query_one("#controls-display", Static)
            display.update(self._get_controls_display())
        except Exception:
            pass
    
    def watch_volume(self, old_value: int, new_value: int) -> None:
        """Update controls when volume changes."""
        try:
            display = self.query_one("#controls-display", Static)
            display.update(self._get_controls_display())
        except Exception:
            pass
    
    def watch_shuffle(self, old_value: bool, new_value: bool) -> None:
        """Update status when shuffle changes."""
        try:
            display = self.query_one("#status-display", Static)
            display.update(self._get_status_display())
        except Exception:
            pass
    
    def watch_repeat(self, old_value: RepeatMode, new_value: RepeatMode) -> None:
        """Update status when repeat changes."""
        try:
            display = self.query_one("#status-display", Static)
            display.update(self._get_status_display())
        except Exception:
            pass
    
    def watch_position(self, old_value: float, new_value: float) -> None:
        """Update progress bar when position changes."""
        try:
            progress = self.query_one("#progress", ProgressBar)
            progress.update(progress=int(new_value * 100))
        except Exception:
            pass
    
    def watch_current_time(self, old_value: int, new_value: int) -> None:
        """Update time display when current time changes."""
        try:
            display = self.query_one("#time-current", Static)
            display.update(self._format_time(new_value))
        except Exception:
            pass
    
    def watch_total_time(self, old_value: int, new_value: int) -> None:
        """Update time display when total time changes."""
        try:
            display = self.query_one("#time-total", Static)
            display.update(self._format_time(new_value))
        except Exception:
            pass
    
    def set_track(self, track_info: Optional["TrackInfo"]) -> None:
        """Set current track info."""
        if track_info:
            self.track_title = track_info.title
            self.track_artist = track_info.artist or ""
            self.total_time = track_info.duration
        else:
            self.track_title = ""
            self.track_artist = ""
            self.total_time = 0
            self.current_time = 0
            self.position = 0.0