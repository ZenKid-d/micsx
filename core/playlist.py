"""Playlist management."""

import random
from typing import Optional, List, Dict, Any, Callable
from dataclasses import dataclass, field
from enum import Enum

from data.database import Database


class RepeatMode(Enum):
    """Repeat mode for playlist playback."""
    OFF = "off"
    ALL = "all"
    ONE = "one"


@dataclass
class PlaylistState:
    """State of the playlist playback."""
    track_ids: List[int] = field(default_factory=list)
    current_index: int = -1
    shuffle_enabled: bool = False
    repeat_mode: RepeatMode = RepeatMode.OFF
    original_order: List[int] = field(default_factory=list)
    shuffle_order: List[int] = field(default_factory=list)


class PlaylistManager:
    """Manage playback queue and playlists."""
    
    def __init__(self, database: Database):
        """Initialize playlist manager.
        
        Args:
            database: Database instance for track operations.
        """
        self.database = database
        
        # Playback queue
        self._queue = PlaylistState()
        
        # Saved playlists
        self._current_playlist_id: Optional[int] = None
        
        # Callbacks
        self._on_track_change: Optional[Callable[[Dict[str, Any]], None]] = None
        self._on_queue_change: Optional[Callable[[], None]] = None
    
    # ==================== Queue Management ====================
    
    def set_queue(self, tracks: List[Dict[str, Any]], start_index: int = 0) -> None:
        """Set the playback queue.
        
        Args:
            tracks: List of track dictionaries.
            start_index: Index of track to start with.
        """
        self._queue.track_ids = [t["id"] for t in tracks]
        self._queue.original_order = self._queue.track_ids.copy()
        self._queue.current_index = start_index
        
        if self._queue.shuffle_enabled:
            self._shuffle_queue()
        
        self._notify_queue_change()
        self._notify_track_change()
    
    def add_to_queue(self, track: Dict[str, Any]) -> None:
        """Add a track to the end of the queue."""
        track_id = track["id"]
        self._queue.track_ids.append(track_id)
        self._queue.original_order.append(track_id)
        
        if self._queue.shuffle_enabled:
            self._shuffle_queue()
        
        self._notify_queue_change()
    
    def add_tracks(self, tracks: List[Dict[str, Any]]) -> None:
        """Add multiple tracks to the queue.
        
        Args:
            tracks: List of track dictionaries.
        """
        for track in tracks:
            track_id = track["id"]
            self._queue.track_ids.append(track_id)
            self._queue.original_order.append(track_id)
        
        if self._queue.shuffle_enabled:
            self._shuffle_queue()
        
        self._notify_queue_change()
    
    def add_next(self, track: Dict[str, Any]) -> None:
        """Add a track to play next."""
        track_id = track["id"]
        insert_index = self._queue.current_index + 1
        
        self._queue.track_ids.insert(insert_index, track_id)
        self._queue.original_order.insert(insert_index, track_id)
        
        self._notify_queue_change()
    
    def remove_from_queue(self, index: int) -> bool:
        """Remove a track from the queue by index."""
        if 0 <= index < len(self._queue.track_ids):
            removed_id = self._queue.track_ids.pop(index)
            
            if removed_id in self._queue.original_order:
                self._queue.original_order.remove(removed_id)
            
            if index < self._queue.current_index:
                self._queue.current_index -= 1
            elif index == self._queue.current_index:
                # Current track was removed
                if self._queue.current_index >= len(self._queue.track_ids):
                    self._queue.current_index = len(self._queue.track_ids) - 1
            
            self._notify_queue_change()
            return True
        return False
    
    def clear_queue(self) -> None:
        """Clear the playback queue."""
        self._queue.track_ids.clear()
        self._queue.original_order.clear()
        self._queue.shuffle_order.clear()
        self._queue.current_index = -1
        
        self._notify_queue_change()
    
    # ==================== Playback Navigation ====================
    
    def get_current_track(self) -> Optional[Dict[str, Any]]:
        """Get the current track in the queue."""
        if not self._has_current_track():
            return None
        
        track_id = self._queue.track_ids[self._queue.current_index]
        return self.database.get_track(track_id)
    
    def get_next_track(self) -> Optional[Dict[str, Any]]:
        """Get the next track (without advancing)."""
        if not self._queue.track_ids:
            return None
        
        next_index = self._queue.current_index + 1
        
        if next_index >= len(self._queue.track_ids):
            if self._queue.repeat_mode == RepeatMode.ALL:
                next_index = 0
            else:
                return None
        
        track_id = self._queue.track_ids[next_index]
        return self.database.get_track(track_id)
    
    def get_previous_track(self) -> Optional[Dict[str, Any]]:
        """Get the previous track (without moving)."""
        if not self._queue.track_ids:
            return None
        
        prev_index = self._queue.current_index - 1
        
        if prev_index < 0:
            if self._queue.repeat_mode == RepeatMode.ALL:
                prev_index = len(self._queue.track_ids) - 1
            else:
                return None
        
        track_id = self._queue.track_ids[prev_index]
        return self.database.get_track(track_id)
    
    def advance(self) -> Optional[Dict[str, Any]]:
        """Advance to the next track and return it."""
        if not self._queue.track_ids:
            return None
        
        next_index = self._queue.current_index + 1
        
        if next_index >= len(self._queue.track_ids):
            if self._queue.repeat_mode == RepeatMode.ALL:
                next_index = 0
            else:
                return None
        
        self._queue.current_index = next_index
        self._notify_track_change()
        return self.get_current_track()
    
    def go_back(self) -> Optional[Dict[str, Any]]:
        """Go back to the previous track and return it."""
        if not self._queue.track_ids:
            return None
        
        prev_index = self._queue.current_index - 1
        
        if prev_index < 0:
            if self._queue.repeat_mode == RepeatMode.ALL:
                prev_index = len(self._queue.track_ids) - 1
            else:
                return None
        
        self._queue.current_index = prev_index
        self._notify_track_change()
        return self.get_current_track()
    
    def go_to_index(self, index: int) -> Optional[Dict[str, Any]]:
        """Go to a specific index in the queue."""
        if 0 <= index < len(self._queue.track_ids):
            self._queue.current_index = index
            self._notify_track_change()
            return self.get_current_track()
        return None
    
    def go_to_track(self, track_id: int) -> Optional[Dict[str, Any]]:
        """Go to a specific track by ID."""
        if track_id in self._queue.track_ids:
            index = self._queue.track_ids.index(track_id)
            return self.go_to_index(index)
        return None
    
    # ==================== Shuffle & Repeat ====================
    
    def toggle_shuffle(self) -> bool:
        """Toggle shuffle mode.
        
        Returns:
            New shuffle state.
        """
        self._queue.shuffle_enabled = not self._queue.shuffle_enabled
        
        if self._queue.shuffle_enabled:
            self._shuffle_queue()
        else:
            self._restore_order()
        
        self._notify_queue_change()
        return self._queue.shuffle_enabled
    
    def toggle_repeat(self) -> RepeatMode:
        """Cycle through repeat modes (OFF <-> ONE).
        
        Returns:
            New repeat mode.
        """
        if self._queue.repeat_mode == RepeatMode.OFF:
            self._queue.repeat_mode = RepeatMode.ONE
        else:
            self._queue.repeat_mode = RepeatMode.OFF
        return self._queue.repeat_mode
    
    @property
    def shuffle_enabled(self) -> bool:
        return self._queue.shuffle_enabled
    
    @property
    def shuffle(self) -> bool:
        """Alias for shuffle_enabled for compatibility."""
        return self._queue.shuffle_enabled
    
    @property
    def repeat_mode(self) -> RepeatMode:
        return self._queue.repeat_mode
    
    def _shuffle_queue(self) -> None:
        """Shuffle the queue while keeping current track."""
        if not self._queue.track_ids:
            return
        
        current_id = None
        if self._has_current_track():
            current_id = self._queue.track_ids[self._queue.current_index]
        
        # Create shuffled order
        shuffled = self._queue.track_ids.copy()
        random.shuffle(shuffled)
        
        # Move current track to front if there was one
        if current_id is not None and current_id in shuffled:
            shuffled.remove(current_id)
            shuffled.insert(0, current_id)
            self._queue.current_index = 0
        else:
            self._queue.current_index = 0
        
        self._queue.track_ids = shuffled
    
    def _restore_order(self) -> None:
        """Restore original queue order."""
        current_id = None
        if self._has_current_track():
            current_id = self._queue.track_ids[self._queue.current_index]
        
        self._queue.track_ids = self._queue.original_order.copy()
        
        if current_id is not None and current_id in self._queue.track_ids:
            self._queue.current_index = self._queue.track_ids.index(current_id)
        else:
            self._queue.current_index = 0
    
    def next(self) -> bool:
        """Advance to next track.
        
        Returns:
            True if successful, False otherwise.
        """
        return self.advance() is not None
    
    def previous(self) -> bool:
        """Go to previous track.
        
        Returns:
            True if successful, False otherwise.
        """
        return self.go_back() is not None
    
    def has_next(self) -> bool:
        """Check if there's a next track."""
        if not self._queue.track_ids:
            return False
        
        next_index = self._queue.current_index + 1
        return next_index < len(self._queue.track_ids)
    
    def has_previous(self) -> bool:
        """Check if there's a previous track."""
        if not self._queue.track_ids:
            return False
        
        prev_index = self._queue.current_index - 1
        return prev_index >= 0
    
    def go_to_first(self) -> None:
        """Go to first track in queue."""
        if self._queue.track_ids:
            self._queue.current_index = 0
            self._notify_track_change()
    
    def clear(self) -> None:
        """Clear the queue (alias for clear_queue)."""
        self.clear_queue()
    
    # ==================== Queue Info ====================
    
    @property
    def queue_length(self) -> int:
        """Get queue length."""
        return len(self._queue.track_ids)
    
    @property
    def current_index(self) -> int:
        """Get current track index."""
        return self._queue.current_index
    
    @current_index.setter
    def current_index(self, value: int) -> None:
        """Set current track index."""
        if 0 <= value < len(self._queue.track_ids):
            self._queue.current_index = value
            self._notify_track_change()
        elif value < 0:
            self._queue.current_index = -1
    
    def get_queue_tracks(self) -> List[Dict[str, Any]]:
        """Get all tracks in the queue."""
        tracks = []
        for track_id in self._queue.track_ids:
            track = self.database.get_track(track_id)
            if track:
                tracks.append(track)
        return tracks
    
    def _has_current_track(self) -> bool:
        """Check if there's a valid current track."""
        return (
            self._queue.track_ids and
            0 <= self._queue.current_index < len(self._queue.track_ids)
        )
    
    # ==================== Saved Playlists ====================
    
    def create_playlist(self, name: str, description: str = "") -> Optional[int]:
        """Create a new saved playlist."""
        return self.database.create_playlist(name, description)
    
    def save_queue_as_playlist(self, name: str, description: str = "") -> Optional[int]:
        """Save current queue as a new playlist."""
        playlist_id = self.database.create_playlist(name, description)
        if playlist_id is None:
            return None
        
        for track_id in self._queue.track_ids:
            self.database.add_track_to_playlist(playlist_id, track_id)
        
        return playlist_id
    
    def load_playlist(self, playlist_id: int) -> bool:
        """Load a saved playlist into the queue."""
        tracks = self.database.get_playlist_tracks(playlist_id)
        if not tracks:
            return False
        
        self.set_queue(tracks)
        self._current_playlist_id = playlist_id
        return True
    
    def get_all_playlists(self) -> List[Dict[str, Any]]:
        """Get all saved playlists."""
        return self.database.get_all_playlists()
    
    def delete_playlist(self, playlist_id: int) -> bool:
        """Delete a saved playlist."""
        if self._current_playlist_id == playlist_id:
            self._current_playlist_id = None
        return self.database.delete_playlist(playlist_id)
    
    # ==================== Callbacks ====================
    
    def set_on_track_change(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """Set track change callback."""
        self._on_track_change = callback
    
    def set_on_queue_change(self, callback: Callable[[], None]) -> None:
        """Set queue change callback."""
        self._on_queue_change = callback
    
    def _notify_track_change(self) -> None:
        """Notify track change callback."""
        if self._on_track_change:
            track = self.get_current_track()
            try:
                self._on_track_change(track)
            except Exception:
                pass
    
    def _notify_queue_change(self) -> None:
        """Notify queue change callback."""
        if self._on_queue_change:
            try:
                self._on_queue_change()
            except Exception:
                pass