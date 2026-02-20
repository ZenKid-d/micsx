"""Search screen for Micsx music player."""

from typing import Optional, TYPE_CHECKING

from textual.screen import Screen
from textual.widgets import Header, Footer, Static, Input
from textual.containers import Container, Vertical
from textual.binding import Binding
from textual.reactive import reactive

from ui.widgets.track_list import TrackList

if TYPE_CHECKING:
    from ui.app import MicsxApp


class SearchScreen(Screen):
    """Search screen with fuzzy matching."""
    
    BINDINGS = [
        Binding("escape", "go_back", "Back"),
        Binding("enter", "play_selected", "Play"),
        Binding("up", "cursor_up", "Up", show=False),
        Binding("down", "cursor_down", "Down", show=False),
        Binding("w", "cursor_up", "Up", show=False),
        Binding("s", "cursor_down", "Down", show=False),
    ]
    
    CSS = """
    SearchScreen {
        background: $surface;
    }
    
    SearchScreen .search-container {
        padding: 1;
        height: 1fr;
    }
    
    SearchScreen .search-header {
        padding: 1;
        background: $primary-darken-3;
        margin-bottom: 1;
    }
    
    SearchScreen .search-input {
        margin-bottom: 1;
    }
    
    SearchScreen Input {
        background: $surface-lighten-1;
        border: solid $primary;
        padding: 1;
    }
    
    SearchScreen Input:focus {
        border: double $accent;
    }
    
    SearchScreen .results-title {
        text-style: bold;
        color: $primary;
        margin-bottom: 1;
    }
    
    SearchScreen .no-results {
        color: $text-muted;
        text-align: center;
        padding: 2;
    }
    
    SearchScreen .search-hint {
        color: $text-muted;
        text-style: italic;
        padding: 1;
    }
    
    SearchScreen TrackList {
        height: 1fr;
    }
    """
    
    # Reactive query for real-time search (renamed to avoid conflict with Textual.query())
    search_query: reactive[str] = reactive("")
    
    def __init__(self, initial_query: str = "", **kwargs) -> None:
        super().__init__(**kwargs)
        self._initial_query = initial_query
    
    def compose(self):
        """Compose the search screen."""
        yield Header()
        
        with Container(classes="search-container"):
            with Vertical(classes="search-header"):
                yield Static("🔍 Search Library", classes="results-title")
                yield Input(
                    placeholder="Type to search (title, artist, album)...",
                    id="search-input",
                    value=self._initial_query
                )
                yield Static("Press Enter to play, Escape to go back", classes="search-hint")
            
            yield TrackList(id="search-results")
        
        yield Footer()
    
    def on_mount(self) -> None:
        """Handle screen mount."""
        # Focus the input
        input_widget = self.query_one("#search-input", Input)
        input_widget.focus()
        
        # Perform initial search if query provided
        if self._initial_query:
            self.search_query = self._initial_query
            self._perform_search(self._initial_query)
    
    def on_input_changed(self, event: Input.Changed) -> None:
        """Handle input change for real-time search."""
        if event.input.id == "search-input":
            self.search_query = event.value
            self._perform_search(event.value)
    
    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle input submit - play first result."""
        if event.input.id == "search-input":
            track_list = self.query_one("#search-results", TrackList)
            tracks = track_list._tracks
            if tracks:
                # Play first track
                self._play_track(tracks[0], 0)
    
    def on_track_list_track_selected(self, event: TrackList.TrackSelected) -> None:
        """Handle track selection."""
        self._play_track(event.track, event.index)
    
    def _perform_search(self, query: str) -> None:
        """Perform fuzzy search and update results."""
        track_list = self.query_one("#search-results", TrackList)
        
        app = self.app
        if not hasattr(app, "search_engine"):
            track_list.update_tracks([])
            return
        
        if not query or len(query.strip()) < 2:
            track_list.update_tracks([])
            return
        
        # Perform fuzzy search
        result = app.search_engine.search(query.strip())
        track_list.update_tracks(result.tracks)
    
    def _play_track(self, track: dict, index: int) -> None:
        """Play selected track."""
        app = self.app
        if hasattr(app, "play_track"):
            # Add to queue and play
            if hasattr(app, "playlist_manager"):
                app.playlist_manager.clear()
                app.playlist_manager.add_track(track)
            app.play_track(track, 0)
            self.app.pop_screen()
    
    def action_cursor_up(self) -> None:
        """Move cursor up in results."""
        track_list = self.query_one("#search-results", TrackList)
        track_list.move_cursor_up()
    
    def action_cursor_down(self) -> None:
        """Move cursor down in results."""
        track_list = self.query_one("#search-results", TrackList)
        track_list.move_cursor_down()
    
    def action_play_selected(self) -> None:
        """Play currently selected track."""
        track_list = self.query_one("#search-results", TrackList)
        # Get currently highlighted track
        # This would need to be implemented in TrackList
        pass
    
    def action_go_back(self) -> None:
        """Go back to previous screen."""
        self.app.pop_screen()