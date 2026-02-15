"""Track list widget for displaying and selecting tracks."""

from typing import Optional, List, Dict, Any, TYPE_CHECKING

from textual.widget import Widget
from textual.widgets import ListView, ListItem, Label
from textual.message import Message
from textual.scroll_view import ScrollView

if TYPE_CHECKING:
    from textual.app import App


class TrackItem(ListItem):
    """A single track item in the list."""
    
    def __init__(self, track: Dict[str, Any], index: int = 0, is_playing: bool = False, **kwargs) -> None:
        super().__init__(**kwargs)
        self.track = track
        self.track_index = index
        self.is_playing = is_playing
    
    def compose(self):
        """Compose the track item."""
        track = self.track
        title = track.get("title") or "Unknown Title"
        artist = track.get("artist") or "Unknown Artist"
        duration = self._format_duration(track.get("duration", 0))
        
        # Show index number
        idx = self.track_index + 1
        
        if self.is_playing:
            # Playing track - highlight with primary color
            label_text = f"[bold cyan]▶[/] [bold cyan]{idx:2d}.[/] [bold cyan]{title}[/] [dim cyan]-[/] [italic cyan]{artist}[/] [dim cyan]{duration}[/]"
        else:
            label_text = f"[dim]{idx:2d}.[/] {title} [dim]-[/] [italic]{artist}[/] [dim]{duration}[/]"
        
        yield Label(label_text)
    
    def _format_duration(self, seconds: int) -> str:
        """Format duration as M:SS."""
        if seconds <= 0:
            return "0:00"
        minutes = seconds // 60
        secs = seconds % 60
        return f"{minutes}:{secs:02d}"


class TrackList(Widget):
    """Widget for displaying a list of tracks."""
    
    BINDINGS = [
        ("enter", "select", "Select"),
        ("up", "cursor_up", "Up"),
        ("down", "cursor_down", "Down"),
        ("x", "remove", "Remove"),
        ("delete", "remove", "Remove"),
    ]
    
    DEFAULT_CSS = """
    TrackList {
        height: 1fr;
        width: 1fr;
    }
    
    TrackList ListView {
        height: auto;
    }
    
    TrackList TrackItem {
        padding: 0 1;
        height: 1;
    }
    
    TrackList TrackItem:hover {
        background: $surface-lighten-1;
    }
    
    TrackList TrackItem:focus {
        background: $primary-background-darken-1;
        color: $text;
    }
    
    TrackList TrackItem.playing {
        background: $primary-background;
        color: $text;
    }
    
    TrackList TrackItem.-active {
        background: $primary-background-darken-1;
        color: $text;
    }
    """
    
    class TrackSelected(Message):
        """Message sent when a track is selected."""
        
        def __init__(self, track: Dict[str, Any], index: int) -> None:
            super().__init__()
            self.track = track
            self.index = index
    
    class TrackRemoved(Message):
        """Message sent when a track is removed from queue."""
        
        def __init__(self, track: Dict[str, Any], index: int) -> None:
            super().__init__()
            self.track = track
            self.index = index
    
    def __init__(self, tracks: Optional[List[Dict[str, Any]]] = None, **kwargs) -> None:
        super().__init__(**kwargs)
        self._tracks: List[Dict[str, Any]] = tracks or []
        self._list_view: Optional[ListView] = None
        self._playing_id: Optional[int] = None
    
    def compose(self):
        """Compose the track list."""
        items = [TrackItem(track) for track in self._tracks]
        self._list_view = ListView(*items)
        yield self._list_view
    
    def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Handle track selection."""
        item = event.item
        if isinstance(item, TrackItem):
            try:
                index = self._tracks.index(item.track)
                self.post_message(self.TrackSelected(item.track, index))
            except ValueError:
                pass
    
    def update_tracks(self, tracks: List[Dict[str, Any]]) -> None:
        """Update the track list."""
        self._tracks = tracks
        
        # Remove old list view and create new one
        if self._list_view:
            self._list_view.remove()
        
        items = [
            TrackItem(track, index=i, is_playing=(track.get("id") == self._playing_id))
            for i, track in enumerate(tracks)
        ]
        self._list_view = ListView(*items)
        self.mount(self._list_view)
        
        # Focus the list view
        if self._list_view:
            self._list_view.focus()
    
    def set_playing(self, track_id: Optional[int]) -> None:
        """Highlight the currently playing track."""
        self._playing_id = track_id
        
        # Rebuild list with new playing state
        if self._tracks:
            self.update_tracks(self._tracks)
    
    def get_track(self, index: int) -> Optional[Dict[str, Any]]:
        """Get track by index."""
        if 0 <= index < len(self._tracks):
            return self._tracks[index]
        return None
    
    def get_track_count(self) -> int:
        """Get number of tracks."""
        return len(self._tracks)
    
    def move_cursor_up(self) -> None:
        """Move cursor up."""
        if self._list_view:
            self._list_view.action_cursor_up()
    
    def move_cursor_down(self) -> None:
        """Move cursor down."""
        if self._list_view:
            self._list_view.action_cursor_down()
    
    def select_first(self) -> None:
        """Select first track."""
        if self._list_view and self._tracks:
            self._list_view.index = 0
    
    def select_last(self) -> None:
        """Select last track."""
        if self._list_view and self._tracks:
            self._list_view.index = len(self._tracks) - 1
    
    def action_select(self) -> None:
        """Select current track."""
        if self._list_view and self._tracks:
            index = self._list_view.index
            if index is not None and 0 <= index < len(self._tracks):
                track = self._tracks[index]
                self.post_message(self.TrackSelected(track, index))
    
    def action_cursor_up(self) -> None:
        """Move cursor up."""
        self.move_cursor_up()
    
    def action_cursor_down(self) -> None:
        """Move cursor down."""
        self.move_cursor_down()
    
    def action_remove(self) -> None:
        """Remove current track from queue."""
        if self._list_view and self._tracks:
            index = self._list_view.index
            if index is not None and 0 <= index < len(self._tracks):
                track = self._tracks[index]
                self.post_message(self.TrackRemoved(track, index))
    
    def remove_track(self, index: int) -> None:
        """Remove track at index and refresh list."""
        if 0 <= index < len(self._tracks):
            self._tracks.pop(index)
            self.update_tracks(self._tracks)
