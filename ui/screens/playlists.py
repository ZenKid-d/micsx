"""Playlists screen for managing playlists."""

from pathlib import Path
from typing import Optional, List, Dict, Any, TYPE_CHECKING

from textual.screen import Screen
from textual.widgets import Header, Footer, Static, Button, Input, ListView, ListItem, Label
from textual.containers import Container, Vertical, Horizontal
from textual.binding import Binding
from textual.reactive import reactive
from textual.message import Message

from ui.widgets.track_list import TrackList
from core.playlist import PlaylistIO, PlaylistFormat

if TYPE_CHECKING:
    from ui.app import MicsxApp


class PlaylistsScreen(Screen):
    """Screen for managing playlists with import/export support."""
    
    BINDINGS = [
        Binding("escape", "back", "Back"),
        Binding("n", "new_playlist", "New"),
        Binding("d", "delete_playlist", "Delete"),
        Binding("i", "import_playlist", "Import"),
        Binding("e", "export_playlist", "Export"),
        Binding("enter", "select", "Select"),
        Binding("/", "focus_input", "Command"),
    ]
    
    CSS = """
    PlaylistsScreen {
        background: $surface;
    }
    
    PlaylistsScreen .main-container {
        height: 1fr;
    }
    
    PlaylistsScreen .playlists-sidebar {
        width: 30%;
        dock: left;
        padding: 1;
        border-right: solid $primary-darken-2;
    }
    
    PlaylistsScreen .playlist-content {
        width: 1fr;
        padding: 1;
    }
    
    PlaylistsScreen .section-title {
        text-style: bold;
        color: $primary;
        padding: 0 1;
        margin-bottom: 1;
    }
    
    PlaylistsScreen ListView {
        height: 1fr;
        background: $surface;
    }
    
    PlaylistsScreen ListItem {
        padding: 1;
        margin: 0;
    }
    
    PlaylistsScreen ListItem:hover {
        background: $surface-lighten-1;
    }
    
    PlaylistsScreen ListItem.-active {
        background: $primary-background-darken-1;
    }
    
    PlaylistsScreen .playlist-item-name {
        color: $text;
    }
    
    PlaylistsScreen .playlist-item-count {
        color: $text-muted;
        text-style: italic;
    }
    
    PlaylistsScreen .command-bar {
        dock: bottom;
        padding: 1;
        background: $surface-lighten-1;
        border-top: solid $primary-darken-2;
    }
    
    PlaylistsScreen Input {
        background: $surface;
        border: solid $primary;
        padding: 1;
    }
    
    PlaylistsScreen Input:focus {
        border: double $accent;
    }
    
    PlaylistsScreen .hint-text {
        color: $text-muted;
        text-style: italic;
        padding: 1;
    }
    
    PlaylistsScreen .empty-state {
        color: $text-muted;
        text-align: center;
        padding: 2;
    }
    
    PlaylistsScreen .status-message {
        color: $primary-lighten-1;
        padding: 1;
        background: $surface-lighten-1;
    }
    
    PlaylistsScreen .error-message {
        color: $error;
        padding: 1;
        background: $surface-lighten-1;
    }
    
    PlaylistsScreen TrackList {
        height: 1fr;
    }
    """
    
    # Reactive state
    selected_playlist_id: reactive[Optional[int]] = reactive(None)
    status_message: reactive[str] = reactive("")
    is_error: reactive[bool] = reactive(False)
    
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._playlist_io: Optional[PlaylistIO] = None
        self._playlists: List[Dict[str, Any]] = []
    
    def compose(self):
        """Compose the playlists screen."""
        yield Header()
        
        with Container(classes="main-container"):
            # Sidebar with playlists list
            with Vertical(classes="playlists-sidebar"):
                yield Static("📋 Playlists", classes="section-title")
                yield ListView(id="playlists-list")
                yield Static("", id="playlist-info", classes="hint-text")
            
            # Main content area
            with Vertical(classes="playlist-content"):
                yield Static("Select a playlist", id="playlist-title", classes="section-title")
                yield TrackList(id="playlist-tracks")
                yield Static("", id="content-hint", classes="hint-text")
        
        # Command bar at bottom
        with Vertical(classes="command-bar"):
            yield Input(
                placeholder="Commands: /import <file> | /export <file> [m3u|m3u8|pls] | /help",
                id="command-input"
            )
        
        yield Footer()
    
    def on_mount(self) -> None:
        """Handle screen mount."""
        app = self.app
        if hasattr(app, "db"):
            self._playlist_io = PlaylistIO(app.db)
        
        self._load_playlists()
        self._update_hints()
    
    def _load_playlists(self) -> None:
        """Load playlists from database."""
        app = self.app
        if not hasattr(app, "library_manager"):
            return
        
        self._playlists = app.library_manager.get_all_playlists()
        self._update_playlists_list()
    
    def _update_playlists_list(self) -> None:
        """Update the playlists list widget."""
        list_view = self.query_one("#playlists-list", ListView)
        list_view.clear()
        
        if not self._playlists:
            return
        
        for pl in self._playlists:
            name = pl.get('name', 'Unknown')
            count = pl.get('track_count', 0)
            
            item = ListItem(
                Label(f"{name} [dim]({count} tracks)[/]")
            )
            item.playlist_id = pl.get('id')
            item.playlist_name = name
            list_view.append(item)
    
    def _update_hints(self) -> None:
        """Update hint texts."""
        hint = self.query_one("#content-hint", Static)
        if self._playlists:
            hint.update("Press 'i' to import, 'e' to export, '/' for command input")
        else:
            hint.update("No playlists. Press 'i' to import or 'n' to create")
    
    def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Handle playlist selection."""
        item = event.item
        if hasattr(item, 'playlist_id'):
            self.selected_playlist_id = item.playlist_id
            self._load_playlist_content(item.playlist_id)
    
    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle command input."""
        if event.input.id == "command-input":
            self._process_command(event.value)
            event.input.value = ""
    
    def _process_command(self, command: str) -> None:
        """Process a command from the input bar.
        
        Commands:
        - /import <file> - Import playlist from file
        - /export <file> [format] - Export selected playlist to file
        - /export-queue <file> [format] - Export current queue to file
        - /help - Show help
        - /formats - Show supported formats
        """
        command = command.strip()
        
        if not command:
            return
        
        if command.startswith('/'):
            parts = command[1:].split(maxsplit=2)
            cmd = parts[0].lower() if parts else ""
            args = parts[1:] if len(parts) > 1 else []
            
            if cmd == "import":
                self._cmd_import(args)
            elif cmd == "export":
                self._cmd_export(args)
            elif cmd == "export-queue":
                self._cmd_export_queue(args)
            elif cmd == "help":
                self._cmd_help()
            elif cmd == "formats":
                self._cmd_formats()
            else:
                self._show_error(f"Unknown command: /{cmd}. Type /help for available commands.")
        else:
            # Treat as search/filter (future feature)
            self._show_status("Search not yet implemented")
    
    def _cmd_import(self, args: List[str]) -> None:
        """Import a playlist from file.
        
        Usage: /import <file_path>
        """
        if not args:
            self._show_error("Usage: /import <file_path>")
            return
        
        file_path = Path(args[0]).expanduser()
        
        if not file_path.exists():
            self._show_error(f"File not found: {file_path}")
            return
        
        if not self._playlist_io:
            self._show_error("Playlist I/O not initialized")
            return
        
        self._show_status(f"Importing playlist from {file_path.name}...")
        
        playlist_id, messages = self._playlist_io.import_to_database(file_path)
        
        if playlist_id:
            # Reload playlists
            self._load_playlists()
            
            # Show success message
            for msg in messages:
                if "Added" in msg:
                    self._show_status(msg)
                    self.notify(msg, title="Import Success")
                else:
                    # These are warnings about tracks not found
                    pass
            
            # Select the new playlist
            self.selected_playlist_id = playlist_id
            self._load_playlist_content(playlist_id)
        else:
            # Show errors
            for msg in messages:
                self._show_error(msg)
                break  # Show first error
    
    def _cmd_export(self, args: List[str]) -> None:
        """Export selected playlist to file.
        
        Usage: /export <file_path> [format]
        Formats: m3u, m3u8, pls (default: auto-detect from extension)
        """
        if not args:
            self._show_error("Usage: /export <file_path> [m3u|m3u8|pls]")
            return
        
        if self.selected_playlist_id is None:
            self._show_error("No playlist selected. Select a playlist first.")
            return
        
        file_path = Path(args[0]).expanduser()
        format_str = args[1].lower() if len(args) > 1 else None
        
        # Parse format
        format = None
        if format_str:
            format_map = {
                'm3u': PlaylistFormat.M3U,
                'm3u8': PlaylistFormat.M3U8,
                'pls': PlaylistFormat.PLS,
            }
            format = format_map.get(format_str)
            if format is None:
                self._show_error(f"Unknown format: {format_str}. Use: m3u, m3u8, or pls")
                return
        
        self._do_export(file_path, self.selected_playlist_id, format)
    
    def _cmd_export_queue(self, args: List[str]) -> None:
        """Export current playback queue to file.
        
        Usage: /export-queue <file_path> [format]
        """
        if not args:
            self._show_error("Usage: /export-queue <file_path> [m3u|m3u8|pls]")
            return
        
        app = self.app
        if not hasattr(app, "playlist_manager"):
            self._show_error("Playlist manager not available")
            return
        
        file_path = Path(args[0]).expanduser()
        format_str = args[1].lower() if len(args) > 1 else None
        
        # Parse format
        format = None
        if format_str:
            format_map = {
                'm3u': PlaylistFormat.M3U,
                'm3u8': PlaylistFormat.M3U8,
                'pls': PlaylistFormat.PLS,
            }
            format = format_map.get(format_str)
            if format is None:
                self._show_error(f"Unknown format: {format_str}. Use: m3u, m3u8, or pls")
                return
        
        tracks = app.playlist_manager.get_queue_tracks()
        
        if not tracks:
            self._show_error("Queue is empty")
            return
        
        if not self._playlist_io:
            self._show_error("Playlist I/O not initialized")
            return
        
        self._show_status(f"Exporting queue to {file_path.name}...")
        
        success, messages = self._playlist_io.export_queue(file_path, tracks, format)
        
        if success:
            self._show_status(f"Exported {len(tracks)} tracks to {file_path}")
            self.notify(f"Exported {len(tracks)} tracks", title="Export Success")
        else:
            for msg in messages:
                self._show_error(msg)
    
    def _do_export(self, file_path: Path, playlist_id: int, format: Optional[PlaylistFormat]) -> None:
        """Export a playlist to file."""
        if not self._playlist_io:
            self._show_error("Playlist I/O not initialized")
            return
        
        self._show_status(f"Exporting playlist to {file_path.name}...")
        
        success, messages = self._playlist_io.export_from_database(file_path, playlist_id, format)
        
        if success:
            self._show_status(f"Playlist exported to {file_path}")
            self.notify(f"Exported to {file_path.name}", title="Export Success")
        else:
            for msg in messages:
                self._show_error(msg)
    
    def _cmd_help(self) -> None:
        """Show help message."""
        help_text = """[bold]Available Commands:[/]

[cyan]/import <file>[/] - Import playlist (M3U, M3U8, PLS)
[cyan]/export <file> [format][/] - Export selected playlist
[cyan]/export-queue <file> [format][/] - Export current queue
[cyan]/formats[/] - Show supported formats
[cyan]/help[/] - Show this help

[dim]Formats: m3u (basic), m3u8 (extended with metadata), pls[/]"""
        
        self._show_status(help_text.replace('\n', ' | '))
        self.notify("Type /formats for supported formats", title="Help")
    
    def _cmd_formats(self) -> None:
        """Show supported formats."""
        formats_text = """[bold]Supported Playlist Formats:[/]

[yellow]M3U[/] - Basic format with file paths only
[yellow]M3U8[/] - Extended M3U with metadata (#EXTINF)
[yellow]PLS[/] - INI-style format with title/length

[dim]Auto-detected from file extension.[/]"""
        
        self._show_status("M3U | M3U8 | PLS - auto-detected from extension")
        self.notify("M3U (basic), M3U8 (extended), PLS (INI-style)", title="Formats")
    
    def _load_playlist_content(self, playlist_id: int) -> None:
        """Load and display playlist content."""
        app = self.app
        if not hasattr(app, "db"):
            return
        
        # Get playlist info
        playlist = app.db.get_playlist(playlist_id)
        if playlist:
            title_widget = self.query_one("#playlist-title", Static)
            title_widget.update(f"📋 {playlist.get('name', 'Unknown')}")
        
        # Get tracks
        tracks = app.db.get_playlist_tracks(playlist_id)
        
        track_list = self.query_one("#playlist-tracks", TrackList)
        track_list.update_tracks(tracks)
        
        # Update info
        info = self.query_one("#playlist-info", Static)
        info.update(f"{len(tracks)} tracks")
    
    def _show_status(self, message: str) -> None:
        """Show status message."""
        self.status_message = message
        self.is_error = False
        
        hint = self.query_one("#content-hint", Static)
        hint.update(f"[green]{message}[/]")
    
    def _show_error(self, message: str) -> None:
        """Show error message."""
        self.status_message = message
        self.is_error = True
        
        hint = self.query_one("#content-hint", Static)
        hint.update(f"[red]Error: {message}[/]")
        self.notify(message, title="Error", severity="error")
    
    # ==================== Actions ====================
    
    def action_back(self) -> None:
        """Go back to main screen."""
        self.app.pop_screen()
    
    def action_new_playlist(self) -> None:
        """Create new playlist."""
        # TODO: Implement playlist creation dialog
        self._show_status("Press '/' and type: /import <file> to import a playlist")
    
    def action_delete_playlist(self) -> None:
        """Delete selected playlist."""
        if self.selected_playlist_id is None:
            self._show_error("No playlist selected")
            return
        
        app = self.app
        if hasattr(app, "playlist_manager"):
            # Get playlist name for notification
            playlist_name = "Unknown"
            for pl in self._playlists:
                if pl.get('id') == self.selected_playlist_id:
                    playlist_name = pl.get('name', 'Unknown')
                    break
            
            app.playlist_manager.delete_playlist(self.selected_playlist_id)
            self.selected_playlist_id = None
            self._load_playlists()
            
            # Clear track list
            track_list = self.query_one("#playlist-tracks", TrackList)
            track_list.update_tracks([])
            
            # Update title
            title_widget = self.query_one("#playlist-title", Static)
            title_widget.update("Select a playlist")
            
            self._show_status(f"Deleted playlist: {playlist_name}")
            self.notify(f"Deleted: {playlist_name}", title="Playlist Deleted")
    
    def action_import_playlist(self) -> None:
        """Focus command input with /import prefix."""
        input_widget = self.query_one("#command-input", Input)
        input_widget.value = "/import "
        input_widget.focus()
    
    def action_export_playlist(self) -> None:
        """Focus command input with /export prefix."""
        if self.selected_playlist_id is None:
            self._show_error("No playlist selected. Select a playlist first.")
            return
        
        input_widget = self.query_one("#command-input", Input)
        input_widget.value = "/export "
        input_widget.focus()
    
    def action_select(self) -> None:
        """Select focused playlist."""
        list_view = self.query_one("#playlists-list", ListView)
        if list_view.highlighted_child and hasattr(list_view.highlighted_child, 'playlist_id'):
            self.selected_playlist_id = list_view.highlighted_child.playlist_id
            self._load_playlist_content(self.selected_playlist_id)
    
    def action_focus_input(self) -> None:
        """Focus the command input."""
        input_widget = self.query_one("#command-input", Input)
        input_widget.focus()
    
    # ==================== Track List Events ====================
    
    def on_track_list_track_selected(self, event: TrackList.TrackSelected) -> None:
        """Handle track selection from playlist."""
        app = self.app
        if hasattr(app, "play_track"):
            # Load the entire playlist into queue and play selected track
            if hasattr(app, "playlist_manager") and self.selected_playlist_id:
                tracks = app.db.get_playlist_tracks(self.selected_playlist_id)
                app.playlist_manager.clear()
                app.playlist_manager.add_tracks(tracks)
            
            app.play_track(event.track, event.index)
            self.app.pop_screen()