"""Playlists screen for managing playlists."""

from typing import List, Dict, Any

from textual.screen import Screen
from textual.widgets import Header, Footer, Static, Button
from textual.containers import Container, Vertical, Horizontal
from textual.binding import Binding

from ui.widgets.track_list import TrackList


class PlaylistsScreen(Screen):
    """Screen for managing playlists."""
    
    BINDINGS = [
        Binding("escape", "back", "Back"),
        Binding("n", "new_playlist", "New"),
        Binding("d", "delete_playlist", "Delete"),
        Binding("enter", "select", "Select"),
    ]
    
    CSS = """
    PlaylistsScreen {
        background: $surface;
    }
    
    PlaylistsScreen .playlists-list {
        width: 30%;
        dock: left;
        padding: 1;
    }
    
    PlaylistsScreen .playlist-content {
        width: 1fr;
        padding: 1;
    }
    
    PlaylistsScreen .playlist-item {
        padding: 1;
        margin: 1;
    }
    
    PlaylistsScreen .playlist-item:hover {
        background: $surface-lighten-1;
    }
    
    PlaylistsScreen .playlist-item.active {
        background: $primary-background-darken-1;
    }
    """
    
    def compose(self):
        """Compose the playlists screen."""
        yield Header()
        
        with Container():
            with Vertical(classes="playlists-list"):
                yield Static("[bold]Playlists[/]", classes="section-title")
                yield Static(self._get_playlists_list(), id="playlists-list")
            
            with Vertical(classes="playlist-content"):
                yield Static("Select a playlist", id="playlist-title")
                yield TrackList(id="playlist-tracks")
        
        yield Footer()
    
    def _get_playlists_list(self) -> str:
        """Get playlists list text."""
        app = self.app
        if not hasattr(app, "library_manager"):
            return "[dim]No playlists[/]"
        
        playlists = app.library_manager.get_all_playlists()
        if not playlists:
            return "[dim]No playlists[/] Press 'n' to create"
        
        lines = []
        for pl in playlists:
            lines.append(f"• {pl['name']} ({pl.get('track_count', 0)} tracks)")
        return "\n".join(lines)
    
    def on_mount(self) -> None:
        """Handle screen mount."""
        pass
    
    def action_back(self) -> None:
        """Go back to main screen."""
        self.app.pop_screen()
    
    def action_new_playlist(self) -> None:
        """Create new playlist."""
        # TODO: Implement playlist creation dialog
        pass
    
    def action_delete_playlist(self) -> None:
        """Delete selected playlist."""
        # TODO: Implement playlist deletion
        pass
    
    def action_select(self) -> None:
        """Select playlist."""
        pass