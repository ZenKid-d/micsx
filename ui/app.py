"""Main Textual application for Micsx music player."""

import asyncio
from typing import Optional, Dict, Any
from pathlib import Path

from textual.app import App
from textual.reactive import reactive

from config.settings import Settings
from config.theme import Theme
from data.database import Database
from data.scanner import FileScanner
from core.player import AudioPlayer, PlayerState
from core.playlist import PlaylistManager, RepeatMode
from core.library import LibraryManager
from core.search import SearchEngine
from core.hotkeys import GlobalHotkeyManager
from ui.screens.main import MainScreen


class MicsxApp(App):
    """Main application class for Micsx music player."""
    
    CSS = """
    /* Global styles */
    * {
        transition: background 0.2s;
    }
    
    /* Colors */
    $primary: #7c3aed;
    $primary-background: #5b21b6;
    $surface: #1e1e2e;
    $surface-lighten-1: #2a2a3e;
    $text: #cdd6f4;
    $text-muted: #6c7086;
    """
    
    SCREENS = {
        "main": MainScreen,
    }
    
    BINDINGS = [
        ("ctrl+q", "quit", "Quit"),
        ("ctrl+l", "library", "Library"),
    ]
    
    # Reactive state
    current_track: reactive[Optional[Dict[str, Any]]] = reactive(None)
    
    def __init__(self, music_path: Optional[str] = None, **kwargs) -> None:
        super().__init__(**kwargs)
        
        # Initialize settings
        self.settings = Settings()
        self.settings.load()
        
        # Override music path if provided
        if music_path:
            self.settings.music_path = music_path
        
        # Initialize database (schema is created automatically in __init__)
        self.db = Database()
        
        # Initialize managers
        self.scanner = FileScanner(self.settings)
        self.library_manager = LibraryManager(self.db, self.settings)
        self.playlist_manager = PlaylistManager(self.db)
        self.search_engine = SearchEngine(self.db)
        
        # Initialize player
        self.player = AudioPlayer()
        self._setup_player_callbacks()
        
        # Initialize hotkey manager
        self.hotkey_manager: Optional[GlobalHotkeyManager] = None
        
        # Update interval for progress bar
        self._update_task: Optional[asyncio.Task] = None
    
    def _setup_player_callbacks(self) -> None:
        """Set up player event callbacks."""
        self.player.set_on_state_change(self._on_player_state_change)
        self.player.set_on_track_end(self._on_track_end)
        self.player.set_on_position_change(self._on_position_change)
    
    def on_mount(self) -> None:
        """Handle app mount."""
        # Use built-in dark theme
        self.theme = "textual-dark"
        
        # Push main screen
        self.push_screen("main")
        
        # Scan library if needed
        if self.settings.scan_on_startup:
            self._scan_library()
        
        # Start global hotkeys if enabled
        if self.settings.global_hotkeys_enabled:
            self._start_hotkey_manager()
        
        # Start progress update task
        self._update_task = asyncio.create_task(self._update_progress_loop())
    
    def on_unmount(self) -> None:
        """Handle app unmount."""
        # Stop player
        self.player.stop()
        self.player.cleanup()
        
        # Stop hotkey manager
        if self.hotkey_manager:
            self.hotkey_manager.stop()
        
        # Cancel update task
        if self._update_task:
            self._update_task.cancel()
        
        # Save settings
        self.settings.save()
        
        # Close database
        self.db.close()
    
    def _scan_library(self) -> None:
        """Scan music library."""
        music_path = self.settings.music_path
        if not music_path or not Path(music_path).exists():
            return
        
        # Run scan using LibraryUpdater (saves to DB)
        result = self.library_manager.scan_library()
        
        # Update search engine
        self.search_engine.rebuild_index()
    
    def _start_hotkey_manager(self) -> None:
        """Start global hotkey manager."""
        try:
            self.hotkey_manager = GlobalHotkeyManager(self.settings)
            self.hotkey_manager.register_callback("play_pause", self.toggle_play)
            self.hotkey_manager.register_callback("next", self.next_track)
            self.hotkey_manager.register_callback("prev", self.prev_track)
            self.hotkey_manager.start()
        except Exception:
            self.hotkey_manager = None
    
    async def _update_progress_loop(self) -> None:
        """Update progress bar periodically."""
        while True:
            try:
                await asyncio.sleep(0.5)
                
                if self.player.state == PlayerState.PLAYING:
                    position = self.player.position
                    current_time = self.player.position_seconds
                    
                    # Update main screen
                    screen = self.screen
                    if hasattr(screen, "update_player_position"):
                        screen.update_player_position(position, current_time)
            except asyncio.CancelledError:
                break
            except Exception:
                pass
    
    def _on_player_state_change(self, state: PlayerState) -> None:
        """Handle player state change."""
        screen = self.screen
        if hasattr(screen, "update_player_state"):
            screen.update_player_state(state)
    
    def _on_track_end(self) -> None:
        """Handle track end - play next track automatically.
        
        Called from VLC thread, so we need to use call_from_thread.
        """
        # Use call_from_thread to safely execute in main thread
        try:
            self.call_from_thread(self._handle_track_end)
        except Exception:
            pass
    
    def _handle_track_end(self) -> None:
        """Handle track end in main thread."""
        if self.playlist_manager.repeat_mode == RepeatMode.ONE:
            # Replay current track from beginning
            self.player.seek(0)
            self.player.play()
        elif self.playlist_manager.has_next():
            # Play next track automatically
            self.playlist_manager.next()
            track = self.playlist_manager.get_current_track()
            if track:
                self.current_track = track
                self.player.load_track(track)
                self.player.play()
                # Update UI
                screen = self.screen
                if hasattr(screen, "update_current_track"):
                    screen.update_current_track(track)
        else:
            # Stop at end of queue
            self.player.stop()
            self.current_track = None
    
    def _on_position_change(self, position: float, current_time: int) -> None:
        """Handle position change."""
        screen = self.screen
        if hasattr(screen, "update_player_position"):
            screen.update_player_position(position, current_time)
    
    def play_track(self, track: Dict[str, Any], index: int = 0) -> None:
        """Play a specific track.
        
        Args:
            track: Track dictionary.
            index: Index in playlist.
        """
        self.current_track = track
        
        # Load and play
        self.player.load_track(track)
        self.player.play()
        
        # Update current index
        self.playlist_manager.current_index = index
        
        # Update UI
        screen = self.screen
        if hasattr(screen, "update_current_track"):
            screen.update_current_track(track)
    
    def _play_current_track(self) -> None:
        """Play the current track from playlist."""
        track = self.playlist_manager.get_current_track()
        if track:
            self.play_track(track, self.playlist_manager.current_index)
    
    def toggle_play(self) -> None:
        """Toggle play/pause."""
        if self.player.state == PlayerState.PLAYING:
            self.player.pause()
        else:
            if self.player.current_track:
                self.player.play()
            elif self.current_track:
                self.play_track(self.current_track)
    
    def next_track(self) -> None:
        """Play next track."""
        if self.playlist_manager.next():
            self._play_current_track()
    
    def prev_track(self) -> None:
        """Play previous track."""
        if self.playlist_manager.previous():
            self._play_current_track()
    
    def toggle_shuffle(self) -> None:
        """Toggle shuffle mode."""
        self.playlist_manager.toggle_shuffle()
        screen = self.screen
        if hasattr(screen, "update_shuffle_repeat"):
            screen.update_shuffle_repeat(
                self.playlist_manager.shuffle,
                self.playlist_manager.repeat_mode
            )
    
    def toggle_repeat(self) -> None:
        """Toggle repeat mode."""
        self.playlist_manager.toggle_repeat()
        screen = self.screen
        if hasattr(screen, "update_shuffle_repeat"):
            screen.update_shuffle_repeat(
                self.playlist_manager.shuffle,
                self.playlist_manager.repeat_mode
            )
    
    def toggle_mute(self) -> None:
        """Toggle mute."""
        self.player.mute()
        screen = self.screen
        if hasattr(screen, "update_volume"):
            screen.update_volume(0 if self.player.is_muted else self.player.volume)
    
    def volume_up(self) -> None:
        """Increase volume."""
        self.player.volume_up(5)
        screen = self.screen
        if hasattr(screen, "update_volume"):
            screen.update_volume(self.player.volume)
    
    def volume_down(self) -> None:
        """Decrease volume."""
        self.player.volume_down(5)
        screen = self.screen
        if hasattr(screen, "update_volume"):
            screen.update_volume(self.player.volume)
    
    def seek(self, seconds: int) -> None:
        """Seek relative to current position."""
        self.player.seek_seconds(seconds)
    
    def play_from_library(self, track: Dict[str, Any]) -> None:
        """Play a track from library, replacing queue."""
        self.playlist_manager.clear()
        self.playlist_manager.add_tracks([track])
        self.play_track(track, 0)
    
    def action_library(self) -> None:
        """Open library screen."""
        from ui.screens.library import LibraryScreen
        self.push_screen(LibraryScreen())