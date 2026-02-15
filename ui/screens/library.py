"""Library screen for browsing music collection."""

from textual.screen import Screen
from textual.widgets import Header, Footer, Static, Input
from textual.containers import Container, Vertical
from textual.binding import Binding
from textual.message import Message

from ui.widgets.track_list import TrackList


class LibraryScreen(Screen):
    """Screen for browsing the music library."""
    
    BINDINGS = [
        Binding("escape", "back", "Back"),
        Binding("enter", "select", "Select"),
        Binding("/", "focus_search", "Search"),
        Binding("r", "refresh", "Refresh"),
        Binding("w", "cursor_up", "Up", show=False),
        Binding("up", "cursor_up", "Up", show=False),
        Binding("s", "cursor_down", "Down", show=False),
        Binding("down", "cursor_down", "Down", show=False),
    ]
    
    CSS = """
    LibraryScreen {
        background: $surface;
    }
    
    LibraryScreen .search-container {
        height: 3;
        padding: 1;
    }
    
    LibraryScreen Input {
        width: 1fr;
    }
    
    LibraryScreen .library-content {
        height: 1fr;
        padding: 0 1;
    }
    
    LibraryScreen .section-title {
        text-style: bold;
        margin-bottom: 1;
    }
    
    LibraryScreen .stats {
        color: $text-muted;
        margin-bottom: 1;
    }
    """
    
    def compose(self):
        """Compose the library screen."""
        yield Header()
        
        with Container():
            with Vertical(classes="search-container"):
                yield Input(placeholder="Search tracks...", id="search-input")
            
            with Vertical(classes="library-content"):
                yield Static(self._get_stats_text(), classes="stats", id="library-stats")
                yield TrackList(id="library-list")
        
        yield Footer()
    
    def _get_stats_text(self) -> str:
        """Get library statistics text."""
        app = self.app
        if hasattr(app, "library_manager"):
            count = app.library_manager.get_track_count()
            return f"[dim]Library: {count} tracks[/]"
        return "[dim]Library: 0 tracks[/]"
    
    def on_mount(self) -> None:
        """Handle screen mount."""
        self._load_library()
    
    def _load_library(self) -> None:
        """Load library tracks."""
        app = self.app
        if hasattr(app, "library_manager"):
            tracks = app.library_manager.get_all_tracks()
            track_list = self.query_one("#library-list", TrackList)
            track_list.update_tracks(tracks)
            
            # Update stats
            stats = self.query_one("#library-stats", Static)
            stats.update(f"[dim]Library: {len(tracks)} tracks[/]")
    
    def on_track_list_track_selected(self, event: TrackList.TrackSelected) -> None:
        """Handle track selection."""
        app = self.app
        if hasattr(app, "play_from_library"):
            app.play_from_library(event.track)
    
    def on_input_changed(self, event: Input.Changed) -> None:
        """Handle search input change."""
        if event.input.id == "search-input":
            self._search(event.value)
    
    def _search(self, query: str) -> None:
        """Search tracks."""
        app = self.app
        if not hasattr(app, "search_engine"):
            return
        
        track_list = self.query_one("#library-list", TrackList)
        
        if query.strip():
            result = app.search_engine.search(query)
            track_list.update_tracks(result.tracks)
        else:
            tracks = app.library_manager.get_all_tracks()
            track_list.update_tracks(tracks)
    
    def action_back(self) -> None:
        """Go back to main screen."""
        self.app.pop_screen()
    
    def action_select(self) -> None:
        """Select current track."""
        pass
    
    def action_focus_search(self) -> None:
        """Focus search input."""
        search_input = self.query_one("#search-input", Input)
        search_input.focus()
    
    def action_refresh(self) -> None:
        """Refresh library."""
        self._load_library()
    
    def action_cursor_up(self) -> None:
        """Move cursor up."""
        track_list = self.query_one("#library-list", TrackList)
        track_list.move_cursor_up()
    
    def action_cursor_down(self) -> None:
        """Move cursor down."""
        track_list = self.query_one("#library-list", TrackList)
        track_list.move_cursor_down()