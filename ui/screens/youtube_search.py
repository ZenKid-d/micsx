"""YouTube search screen for Micsx music player."""

from typing import Optional, List, Dict, Any, TYPE_CHECKING

from textual.screen import Screen
from textual.widgets import Header, Footer, Static, Input
from textual.containers import Container, Vertical
from textual.binding import Binding
from textual.reactive import reactive

from ui.widgets.track_list import TrackList

if TYPE_CHECKING:
    from ui.app import MicsxApp


class YouTubeSearchScreen(Screen):
    """YouTube search screen."""

    BINDINGS = [
        Binding("escape", "go_back", "Back"),
        Binding("enter", "play_selected", "Play"),
        Binding("up", "cursor_up", "Up", show=False),
        Binding("down", "cursor_down", "Down", show=False),
        Binding("w", "cursor_up", "Up", show=False),
        Binding("s", "cursor_down", "Down", show=False),
    ]

    CSS = """
    YouTubeSearchScreen {
        background: $surface;
    }

    YouTubeSearchScreen .search-container {
        padding: 1;
        height: 1fr;
    }

    YouTubeSearchScreen .search-header {
        padding: 1;
        background: $primary-darken-3;
        margin-bottom: 1;
    }

    YouTubeSearchScreen .search-input {
        margin-bottom: 1;
    }

    YouTubeSearchScreen Input {
        background: $surface-lighten-1;
        border: solid $primary;
        padding: 1;
        color: $text;
    }

    YouTubeSearchScreen Input:focus {
        border: double $accent;
    }

    YouTubeSearchScreen Input.-placeholder {
        color: $text-muted;
    }

    YouTubeSearchScreen .results-title {
        text-style: bold;
        color: $primary;
        margin-bottom: 1;
    }

    YouTubeSearchScreen .no-results {
        color: $text-muted;
        text-align: center;
        padding: 2;
    }

    YouTubeSearchScreen .search-hint {
        color: $text-muted;
        text-style: italic;
        padding: 1;
    }

    YouTubeSearchScreen TrackList {
        height: 1fr;
    }

    YouTubeSearchScreen .loading {
        color: $accent;
        text-align: center;
        padding: 2;
    }

    YouTubeSearchScreen .error {
        color: $error;
        text-align: center;
        padding: 2;
    }
    """

    # Reactive query for search
    search_query: reactive[str] = reactive("")
    # Search results
    results: reactive[List[Dict[str, Any]]] = reactive([])

    def __init__(self, initial_query: str = "", **kwargs) -> None:
        super().__init__(**kwargs)
        self._initial_query = initial_query
        self._is_searching = False

    def compose(self):
        """Compose the YouTube search screen."""
        yield Header()

        with Container(classes="search-container"):
            with Vertical(classes="search-header"):
                yield Static("📺 Search YouTube", classes="results-title")
                yield Input(
                    placeholder="Type to search YouTube...",
                    id="youtube-search-input",
                    value=self._initial_query
                )
                yield Static("Press Enter to search, Escape to go back", classes="search-hint")

            yield TrackList(id="youtube-results")

        yield Footer()

    def on_mount(self) -> None:
        """Handle screen mount."""
        # Focus the input
        input_widget = self.query_one("#youtube-search-input", Input)
        input_widget.focus()
        print(f"[DEBUG] Input focused, has focus: {input_widget.has_focus}")

        # Perform initial search if query provided
        if self._initial_query:
            self.search_query = self._initial_query
            self._perform_search(self._initial_query)

    def on_input_changed(self, event: Input.Changed) -> None:
        """Handle input change."""
        if event.input.id == "youtube-search-input":
            self.search_query = event.value

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle input submit - perform search."""
        if event.input.id == "youtube-search-input":
            self._perform_search(event.value)

    def on_track_list_track_selected(self, event: TrackList.TrackSelected) -> None:
        """Handle track selection."""
        print(f"[DEBUG] Track selected: {event.track} at index {event.index}")
        self._play_youtube_track(event.track, event.index)

    def _perform_search(self, query: str) -> None:
        """Search YouTube and update results."""
        track_list = self.query_one("#youtube-results", TrackList)

        app = self.app
        if not hasattr(app, "youtube_client"):
            track_list.update_tracks([])
            return

        if not query or len(query.strip()) < 2:
            track_list.update_tracks([])
            return

        # Perform YouTube search
        try:
            results = app.youtube_client.search(query.strip())
            self.results = results

            # Convert YouTube results to track format
            tracks = []
            for video in results:
                track = {
                    'id': -1,  # Temporary ID, will be assigned when added to DB
                    'path': f"youtube:{video['video_id']}",
                    'title': video.get('title', 'Unknown Title'),
                    'artist': video.get('uploader', 'Unknown'),
                    'album': 'YouTube',
                    'duration': video.get('duration', 0),
                    'source_type': 'youtube',
                    'source_id': video.get('video_id', ''),
                    'source_url': video.get('url', ''),
                    'thumbnail_url': video.get('thumbnail', ''),
                }
                tracks.append(track)

            track_list.update_tracks(tracks)

        except Exception as e:
            # Show error
            track_list.update_tracks([])

    def _play_youtube_track(self, track: dict, index: int) -> None:
        """Play selected YouTube track."""
        app = self.app
        print(f"[DEBUG] _play_youtube_track called with track: {track}")

        if not hasattr(app, "play_youtube_track"):
            print("[DEBUG] App has no play_youtube_track method")
            return

        # Get full video info including stream URL
        video_id = track.get('source_id')
        print(f"[DEBUG] Video ID: {video_id}")

        if not video_id:
            print("[DEBUG] No video_id found")
            return

        try:
            print(f"[DEBUG] Getting video info for {video_id}")
            video_info = app.youtube_client.get_video_info(video_id)
            print(f"[DEBUG] Got video_info: {video_info}")

            if video_info:
                # Add to library and play
                print("[DEBUG] Calling play_youtube_track")
                app.play_youtube_track(video_info)
                self.app.pop_screen()
            else:
                print("[DEBUG] No video_info returned")
        except Exception as e:
            # Handle error (could show notification)
            print(f"[DEBUG] Error: {e}")
            import traceback
            traceback.print_exc()

    def action_cursor_up(self) -> None:
        """Move cursor up in results."""
        track_list = self.query_one("#youtube-results", TrackList)
        track_list.move_cursor_up()

    def action_cursor_down(self) -> None:
        """Move cursor down in results."""
        track_list = self.query_one("#youtube-results", TrackList)
        track_list.move_cursor_down()

    def action_play_selected(self) -> None:
        """Play currently selected track."""
        track_list = self.query_one("#youtube-results", TrackList)
        index = track_list._list_view.index if track_list._list_view else None
        if index is not None and 0 <= index < len(track_list._tracks):
            track = track_list._tracks[index]
            self._play_youtube_track(track, index)

    def action_go_back(self) -> None:
        """Go back to previous screen."""
        self.app.pop_screen()
