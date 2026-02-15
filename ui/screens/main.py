"""Main screen for Micsx music player."""

from typing import Optional, TYPE_CHECKING

from textual.screen import Screen
from textual.widgets import Header, Footer, Static
from textual.containers import Container, Horizontal, Vertical
from textual.binding import Binding

from ui.widgets.track_list import TrackList
from ui.widgets.player_bar import PlayerBar
from ui.widgets.cover_display import CoverDisplay
from core.player import PlayerState

if TYPE_CHECKING:
    from ui.app import MicsxApp


class MainScreen(Screen):
    """Main playback screen."""
    
    BINDINGS = [
        Binding("space", "toggle_play", "Play/Pause"),
        Binding("n", "next_track", "Next"),
        Binding("p", "prev_track", "Prev"),
        Binding("s", "toggle_shuffle", "Shuffle"),
        Binding("r", "toggle_repeat", "Repeat"),
        Binding("m", "toggle_mute", "Mute"),
        Binding("+", "volume_up", "Vol+"),
        Binding("-", "volume_down", "Vol-"),
        Binding("a", "seek_back", "← 5s"),
        Binding("d", "seek_forward", "→ 5s"),
        Binding("/", "search", "Search"),
        Binding("l", "go_library", "Library"),
        Binding("q", "quit", "Quit"),
        # Vim-style navigation
        Binding("w", "cursor_up", "Up", show=False),
        Binding("up", "cursor_up", "Up", show=False),
        Binding("s", "cursor_down", "Down", show=False),
        Binding("down", "cursor_down", "Down", show=False),
    ]
    
    CSS = """
    MainScreen {
        background: $surface;
    }
    
    MainScreen Container {
        height: 1fr;
    }
    
    MainScreen .main-content {
        padding: 1;
    }
    
    MainScreen .sidebar {
        width: 22;
        dock: left;
        padding: 1;
    }
    
    MainScreen .track-list-container {
        width: 1fr;
    }
    
    MainScreen CoverDisplay {
        margin-bottom: 1;
    }
    
    MainScreen .now-playing-info {
        height: auto;
        margin-top: 1;
    }
    """
    
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._current_track_id: Optional[int] = None
    
    def compose(self):
        """Compose the main screen."""
        yield Header()
        
        with Container():
            with Horizontal(classes="main-content"):
                # Sidebar with cover art
                with Vertical(classes="sidebar"):
                    yield CoverDisplay(id="cover")
                    with Vertical(classes="now-playing-info"):
                        yield Static("", id="now-playing-title")
                        yield Static("", id="now-playing-artist")
                        yield Static("", id="now-playing-album")
                
                # Main track list
                with Vertical(classes="track-list-container"):
                    yield Static("Queue", classes="section-title")
                    yield TrackList(id="queue-list")
        
        yield PlayerBar(id="player-bar")
        yield Footer()
    
    def on_mount(self) -> None:
        """Handle screen mount."""
        app = self.app
        if hasattr(app, "playlist_manager") and hasattr(app, "library_manager"):
            # Load all tracks from library into queue
            all_tracks = app.library_manager.get_all_tracks()
            if all_tracks:
                app.playlist_manager.clear()
                app.playlist_manager.add_tracks(all_tracks)
            tracks = app.playlist_manager.get_queue_tracks()
            self._update_track_list(tracks)
    
    def on_track_list_track_selected(self, event: TrackList.TrackSelected) -> None:
        """Handle track selection."""
        app = self.app
        if hasattr(app, "play_track"):
            app.play_track(event.track, event.index)
    
    def action_toggle_play(self) -> None:
        """Toggle play/pause."""
        app = self.app
        if hasattr(app, "toggle_play"):
            app.toggle_play()
    
    def action_next_track(self) -> None:
        """Play next track."""
        app = self.app
        if hasattr(app, "next_track"):
            app.next_track()
    
    def action_prev_track(self) -> None:
        """Play previous track."""
        app = self.app
        if hasattr(app, "prev_track"):
            app.prev_track()
    
    def action_toggle_shuffle(self) -> None:
        """Toggle shuffle mode."""
        app = self.app
        if hasattr(app, "toggle_shuffle"):
            app.toggle_shuffle()
    
    def action_toggle_repeat(self) -> None:
        """Toggle repeat mode."""
        app = self.app
        if hasattr(app, "toggle_repeat"):
            app.toggle_repeat()
    
    def action_toggle_mute(self) -> None:
        """Toggle mute."""
        app = self.app
        if hasattr(app, "toggle_mute"):
            app.toggle_mute()
    
    def action_volume_up(self) -> None:
        """Increase volume."""
        app = self.app
        if hasattr(app, "volume_up"):
            app.volume_up()
    
    def action_volume_down(self) -> None:
        """Decrease volume."""
        app = self.app
        if hasattr(app, "volume_down"):
            app.volume_down()
    
    def action_seek_back(self) -> None:
        """Seek backwards."""
        app = self.app
        if hasattr(app, "seek"):
            app.seek(-5)
    
    def action_seek_forward(self) -> None:
        """Seek forwards."""
        app = self.app
        if hasattr(app, "seek"):
            app.seek(5)
    
    def action_cursor_up(self) -> None:
        """Move cursor up."""
        track_list = self.query_one("#queue-list", TrackList)
        track_list.move_cursor_up()
    
    def action_cursor_down(self) -> None:
        """Move cursor down."""
        track_list = self.query_one("#queue-list", TrackList)
        track_list.move_cursor_down()
    
    def action_search(self) -> None:
        """Open search."""
        # TODO: Implement search
        pass
    
    def action_go_library(self) -> None:
        """Go to library screen."""
        from .library import LibraryScreen
        self.app.push_screen(LibraryScreen())
    
    def action_quit(self) -> None:
        """Quit the application."""
        self.app.exit()
    
    def update_player_state(self, state: PlayerState) -> None:
        """Update player bar with new state."""
        player_bar = self.query_one("#player-bar", PlayerBar)
        player_bar.state = state
    
    def update_player_position(self, position: float, current_time: int) -> None:
        """Update player bar position."""
        player_bar = self.query_one("#player-bar", PlayerBar)
        player_bar.position = position
        player_bar.current_time = current_time
    
    def update_shuffle_repeat(self, shuffle: bool, repeat) -> None:
        """Update shuffle and repeat indicators."""
        player_bar = self.query_one("#player-bar", PlayerBar)
        player_bar.shuffle = shuffle
        player_bar.repeat = repeat
    
    def update_volume(self, volume: int) -> None:
        """Update volume display."""
        player_bar = self.query_one("#player-bar", PlayerBar)
        player_bar.volume = volume
    
    def update_current_track(self, track: dict) -> None:
        """Update current track display."""
        player_bar = self.query_one("#player-bar", PlayerBar)
        
        # Update player bar
        from core.player import TrackInfo
        if track:
            track_info = TrackInfo(
                id=track["id"],
                path=track["path"],
                title=track.get("title", "Unknown"),
                artist=track.get("artist"),
                album=track.get("album"),
                duration=track.get("duration", 0)
            )
            player_bar.set_track(track_info)
            
            # Update now playing info
            title_widget = self.query_one("#now-playing-title", Static)
            artist_widget = self.query_one("#now-playing-artist", Static)
            album_widget = self.query_one("#now-playing-album", Static)
            
            title_widget.update(f"[bold]{track.get('title', 'Unknown')}[/]")
            artist_widget.update(f"[dim]{track.get('artist', 'Unknown Artist')}[/]")
            album_widget.update(f"[dim]{track.get('album', '')}[/]" if track.get('album') else "")
            
            # Update cover art
            cover = self.query_one("#cover", CoverDisplay)
            cover.set_cover_from_track(track["path"])
            
            # Highlight in track list
            track_list = self.query_one("#queue-list", TrackList)
            track_list.set_playing(track["id"])
        else:
            player_bar.set_track(None)
    
    def _update_track_list(self, tracks: list) -> None:
        """Update the track list."""
        track_list = self.query_one("#queue-list", TrackList)
        track_list.update_tracks(tracks)