"""Playlist management."""

import random
import re
import configparser
from pathlib import Path
from typing import Optional, List, Dict, Any, Callable, Tuple
from dataclasses import dataclass, field
from enum import Enum

from PyQt6.QtCore import QObject, pyqtSignal

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


class PlaylistManager(QObject):
    """Manage playback queue and playlists with Qt signals."""

    # Qt signals for UI updates
    track_changed = pyqtSignal(dict)  # Current track dict
    queue_changed = pyqtSignal()  # Queue modified
    shuffle_changed = pyqtSignal(bool)  # Shuffle state
    repeat_changed = pyqtSignal(object)  # RepeatMode

    def __init__(self, database: Database):
        """Initialize playlist manager.

        Args:
            database: Database instance for track operations.
        """
        super().__init__()  # Initialize QObject

        self.database = database

        # Playback queue
        self._queue = PlaylistState()

        # Saved playlists
        self._current_playlist_id: Optional[int] = None
    
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

        self.queue_changed.emit()
        track = self.get_current_track()
        if track:
            self.track_changed.emit(track)
    
    def add_to_queue(self, track: Dict[str, Any]) -> None:
        """Add a track to the end of the queue."""
        track_id = track["id"]
        self._queue.track_ids.append(track_id)
        self._queue.original_order.append(track_id)

        if self._queue.shuffle_enabled:
            self._shuffle_queue()

        self.queue_changed.emit()
    
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

        self.queue_changed.emit()
    
    def add_next(self, track: Dict[str, Any]) -> None:
        """Add a track to play next."""
        track_id = track["id"]
        insert_index = self._queue.current_index + 1

        self._queue.track_ids.insert(insert_index, track_id)
        self._queue.original_order.insert(insert_index, track_id)

        self.queue_changed.emit()
    
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

            self.queue_changed.emit()
            return True
        return False
    
    def clear_queue(self) -> None:
        """Clear the playback queue."""
        self._queue.track_ids.clear()
        self._queue.original_order.clear()
        self._queue.shuffle_order.clear()
        self._queue.current_index = -1

        self.queue_changed.emit()
    
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
        track = self.get_current_track()
        if track:
            self.track_changed.emit(track)
        return track
    
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
        track = self.get_current_track()
        if track:
            self.track_changed.emit(track)
        return track
    
    def go_to_index(self, index: int) -> Optional[Dict[str, Any]]:
        """Go to a specific index in the queue."""
        if 0 <= index < len(self._queue.track_ids):
            self._queue.current_index = index
            track = self.get_current_track()
            if track:
                self.track_changed.emit(track)
            return track
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

        self.queue_changed.emit()
        self.shuffle_changed.emit(self._queue.shuffle_enabled)
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
        self.repeat_changed.emit(self._queue.repeat_mode)
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
            track = self.get_current_track()
            if track:
                self.track_changed.emit(track)
    
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
            track = self.get_current_track()
            if track:
                self.track_changed.emit(track)
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
    
    # ==================== Callbacks (removed - using Qt signals now) ====================


class PlaylistFormat(Enum):
    """Supported playlist formats."""
    M3U = "m3u"
    M3U8 = "m3u8"
    PLS = "pls"


@dataclass
class PlaylistEntry:
    """Represents a single entry in a playlist file."""
    path: str
    title: Optional[str] = None
    artist: Optional[str] = None
    duration: int = -1  # -1 means unknown
    
    def get_display_title(self) -> str:
        """Get display title for the entry."""
        if self.artist and self.title:
            return f"{self.artist} - {self.title}"
        elif self.title:
            return self.title
        else:
            return Path(self.path).stem


class PlaylistIO:
    """Import and export playlists in various formats.
    
    Supported formats:
    - M3U: Basic playlist with file paths
    - M3U8: Extended M3U with metadata (#EXTINF)
    - PLS: INI-style playlist format
    """
    
    # Audio file extensions to look for
    AUDIO_EXTENSIONS = {'.mp3', '.flac', '.wav', '.ogg', '.m4a', '.aac', '.wma', '.ape', '.opus'}
    
    def __init__(self, database: Database):
        """Initialize playlist I/O.
        
        Args:
            database: Database instance for track lookups.
        """
        self.database = database
    
    # ==================== Import Methods ====================
    
    def import_playlist(
        self, 
        file_path: Path, 
        format: Optional[PlaylistFormat] = None
    ) -> Tuple[List[PlaylistEntry], List[str]]:
        """Import a playlist file.
        
        Args:
            file_path: Path to the playlist file.
            format: Playlist format. Auto-detected if None.
            
        Returns:
            Tuple of (imported entries, list of errors/warnings)
        """
        if not file_path.exists():
            return [], [f"File not found: {file_path}"]
        
        # Auto-detect format from extension
        if format is None:
            format = self._detect_format(file_path)
        
        if format is None:
            return [], [f"Unknown playlist format: {file_path.suffix}"]
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            # Try with latin-1 encoding
            try:
                with open(file_path, 'r', encoding='latin-1') as f:
                    content = f.read()
            except Exception as e:
                return [], [f"Failed to read file: {e}"]
        except Exception as e:
            return [], [f"Failed to read file: {e}"]
        
        if format == PlaylistFormat.PLS:
            return self._parse_pls(content, file_path)
        else:
            # M3U and M3U8 use the same parser
            return self._parse_m3u(content, file_path)
    
    def _detect_format(self, file_path: Path) -> Optional[PlaylistFormat]:
        """Detect playlist format from file extension."""
        ext = file_path.suffix.lower()
        if ext == '.m3u8':
            return PlaylistFormat.M3U8
        elif ext == '.m3u':
            return PlaylistFormat.M3U
        elif ext == '.pls':
            return PlaylistFormat.PLS
        return None
    
    def _parse_m3u(self, content: str, file_path: Path) -> Tuple[List[PlaylistEntry], List[str]]:
        """Parse M3U/M3U8 playlist content.
        
        M3U8 format:
        #EXTM3U
        #EXTINF:duration,title
        file_path
        """
        entries: List[PlaylistEntry] = []
        errors: List[str] = []
        
        lines = content.split('\n')
        current_duration = -1
        current_title = None
        current_artist = None
        
        playlist_dir = file_path.parent
        
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            
            if not line:
                continue
            
            if line.startswith('#EXTM3U'):
                # Header for extended M3U
                continue
            
            if line.startswith('#EXTINF:'):
                # Extended info line: #EXTINF:duration,title
                # Or: #EXTINF:duration,artist - title
                try:
                    info_part = line[8:]  # Remove '#EXTINF:'
                    
                    # Parse duration and title
                    if ',' in info_part:
                        duration_str, title_part = info_part.split(',', 1)
                        try:
                            current_duration = int(float(duration_str.strip()))
                        except ValueError:
                            current_duration = -1
                        
                        # Parse "Artist - Title" format
                        if ' - ' in title_part:
                            parts = title_part.split(' - ', 1)
                            current_artist = parts[0].strip()
                            current_title = parts[1].strip()
                        else:
                            current_title = title_part.strip()
                            current_artist = None
                    else:
                        current_duration = -1
                        current_title = None
                        current_artist = None
                except Exception as e:
                    errors.append(f"Line {line_num}: Failed to parse EXTINF: {e}")
                continue
            
            if line.startswith('#'):
                # Skip other directives
                continue
            
            # This is a file path
            path = self._resolve_path(line, playlist_dir)
            
            if path:
                entry = PlaylistEntry(
                    path=str(path),
                    title=current_title,
                    artist=current_artist,
                    duration=current_duration
                )
                entries.append(entry)
            else:
                errors.append(f"Line {line_num}: File not found: {line}")
            
            # Reset for next entry
            current_duration = -1
            current_title = None
            current_artist = None
        
        return entries, errors
    
    def _parse_pls(self, content: str, file_path: Path) -> Tuple[List[PlaylistEntry], List[str]]:
        """Parse PLS playlist content.
        
        PLS format:
        [playlist]
        File1=path
        Title1=title
        Length1=duration
        NumberOfEntries=N
        """
        entries: List[PlaylistEntry] = []
        errors: List[str] = []
        
        playlist_dir = file_path.parent
        
        # Parse as INI file
        config = configparser.ConfigParser()
        try:
            config.read_string(content)
        except configparser.Error as e:
            return [], [f"Failed to parse PLS: {e}"]
        
        if 'playlist' not in config:
            return [], ["Invalid PLS file: missing [playlist] section"]
        
        playlist_section = config['playlist']
        
        # Get number of entries
        try:
            num_entries = playlist_section.getint('NumberOfEntries', fallback=0)
        except ValueError:
            num_entries = 0
        
        if num_entries == 0:
            # Try to auto-detect entries
            num_entries = 0
            for key in playlist_section:
                if key.lower().startswith('file'):
                    try:
                        idx = int(key[4:])
                        num_entries = max(num_entries, idx)
                    except ValueError:
                        pass
        
        for i in range(1, num_entries + 1):
            file_key = f'File{i}'
            title_key = f'Title{i}'
            length_key = f'Length{i}'
            
            if file_key not in playlist_section:
                continue
            
            file_path_str = playlist_section[file_key]
            path = self._resolve_path(file_path_str, playlist_dir)
            
            if path:
                title = playlist_section.get(title_key, None)
                duration = -1
                try:
                    duration = playlist_section.getint(length_key, fallback=-1)
                except ValueError:
                    pass
                
                # Parse artist from title if present
                artist = None
                if title and ' - ' in title:
                    parts = title.split(' - ', 1)
                    artist = parts[0].strip()
                    title = parts[1].strip()
                
                entry = PlaylistEntry(
                    path=str(path),
                    title=title,
                    artist=artist,
                    duration=duration
                )
                entries.append(entry)
            else:
                errors.append(f"Entry {i}: File not found: {file_path_str}")
        
        return entries, errors
    
    def _resolve_path(self, path_str: str, playlist_dir: Path) -> Optional[Path]:
        """Resolve a path from playlist to absolute path.
        
        Handles:
        - Absolute paths
        - Relative paths (relative to playlist directory)
        - URIs (file://)
        """
        path_str = path_str.strip()
        
        # Handle file:// URIs
        if path_str.lower().startswith('file://'):
            path_str = path_str[7:]
            # URL decode
            import urllib.parse
            path_str = urllib.parse.unquote(path_str)
        
        path = Path(path_str)
        
        # Already absolute
        if path.is_absolute() and path.exists():
            return path
        
        # Try relative to playlist directory
        if not path.is_absolute():
            relative_path = playlist_dir / path
            if relative_path.exists():
                return relative_path.resolve()
        
        # Try as absolute path (might not exist but return anyway)
        if path.is_absolute():
            return path
        
        return None
    
    # ==================== Export Methods ====================
    
    def export_playlist(
        self,
        file_path: Path,
        tracks: List[Dict[str, Any]],
        format: Optional[PlaylistFormat] = None,
        relative_paths: bool = True
    ) -> Tuple[bool, List[str]]:
        """Export tracks to a playlist file.
        
        Args:
            file_path: Output file path.
            tracks: List of track dictionaries from database.
            format: Playlist format. Auto-detected if None.
            relative_paths: Use relative paths when possible.
            
        Returns:
            Tuple of (success, list of errors/warnings)
        """
        # Auto-detect format from extension
        if format is None:
            format = self._detect_format(file_path)
        
        if format is None:
            return False, [f"Unknown playlist format: {file_path.suffix}"]
        
        output_dir = file_path.parent
        
        try:
            # Ensure parent directory exists
            output_dir.mkdir(parents=True, exist_ok=True)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                if format == PlaylistFormat.PLS:
                    self._write_pls(f, tracks, output_dir, relative_paths)
                elif format == PlaylistFormat.M3U8:
                    self._write_m3u8(f, tracks, output_dir, relative_paths)
                else:
                    self._write_m3u(f, tracks, output_dir, relative_paths)
            
            return True, []
        except Exception as e:
            return False, [f"Failed to write playlist: {e}"]
    
    def _write_m3u(
        self, 
        f, 
        tracks: List[Dict[str, Any]], 
        output_dir: Path, 
        relative_paths: bool
    ) -> None:
        """Write basic M3U playlist."""
        for track in tracks:
            path = self._get_track_path(track, output_dir, relative_paths)
            f.write(f"{path}\n")
    
    def _write_m3u8(
        self, 
        f, 
        tracks: List[Dict[str, Any]], 
        output_dir: Path, 
        relative_paths: bool
    ) -> None:
        """Write extended M3U8 playlist with metadata."""
        f.write("#EXTM3U\n")
        
        for track in tracks:
            duration = track.get('duration', -1)
            if duration is None:
                duration = -1
            
            # Build title string
            artist = track.get('artist', '')
            title = track.get('title', '')
            
            if artist and title:
                display_title = f"{artist} - {title}"
            elif title:
                display_title = title
            else:
                display_title = Path(track.get('path', '')).stem
            
            path = self._get_track_path(track, output_dir, relative_paths)
            f.write(f"#EXTINF:{duration},{display_title}\n")
            f.write(f"{path}\n")
    
    def _write_pls(
        self, 
        f, 
        tracks: List[Dict[str, Any]], 
        output_dir: Path, 
        relative_paths: bool
    ) -> None:
        """Write PLS playlist format."""
        f.write("[playlist]\n\n")
        
        for i, track in enumerate(tracks, 1):
            path = self._get_track_path(track, output_dir, relative_paths)
            
            duration = track.get('duration', -1)
            if duration is None:
                duration = -1
            
            # Build title
            artist = track.get('artist', '')
            title = track.get('title', '')
            
            if artist and title:
                display_title = f"{artist} - {title}"
            elif title:
                display_title = title
            else:
                display_title = Path(track.get('path', '')).stem
            
            f.write(f"File{i}={path}\n")
            f.write(f"Title{i}={display_title}\n")
            f.write(f"Length{i}={duration}\n\n")
        
        f.write(f"NumberOfEntries={len(tracks)}\n")
        f.write("Version=2\n")
    
    def _get_track_path(
        self, 
        track: Dict[str, Any], 
        output_dir: Path, 
        relative_paths: bool
    ) -> str:
        """Get the path to write for a track."""
        track_path = Path(track.get('path', ''))
        
        if relative_paths and track_path.is_absolute():
            try:
                relative = track_path.relative_to(output_dir)
                return str(relative)
            except ValueError:
                # Paths are not relative
                pass
        
        return str(track_path)
    
    # ==================== Integration Methods ====================
    
    def import_to_database(
        self,
        file_path: Path,
        playlist_name: Optional[str] = None,
        format: Optional[PlaylistFormat] = None
    ) -> Tuple[Optional[int], List[str]]:
        """Import a playlist file and create a database playlist.
        
        Args:
            file_path: Path to the playlist file.
            playlist_name: Name for the new playlist. Uses filename if None.
            format: Playlist format. Auto-detected if None.
            
        Returns:
            Tuple of (playlist_id or None, list of errors/warnings)
        """
        entries, errors = self.import_playlist(file_path, format)
        
        if not entries:
            return None, errors if errors else ["No valid entries found in playlist"]
        
        # Determine playlist name
        if playlist_name is None:
            playlist_name = file_path.stem
        
        # Create playlist
        playlist_id = self.database.create_playlist(playlist_name)
        if playlist_id is None:
            return None, errors + [f"Failed to create playlist '{playlist_name}'"]
        
        # Add tracks to playlist
        added_count = 0
        for entry in entries:
            # Try to find track in database by path
            track = self.database.get_track_by_path(entry.path)
            
            if track:
                self.database.add_track_to_playlist(playlist_id, track['id'])
                added_count += 1
            else:
                errors.append(f"Track not in library: {entry.path}")
        
        if added_count == 0:
            self.database.delete_playlist(playlist_id)
            return None, errors + ["No tracks from playlist found in library"]
        
        errors.append(f"Added {added_count} tracks to playlist '{playlist_name}'")
        return playlist_id, errors
    
    def export_from_database(
        self,
        file_path: Path,
        playlist_id: int,
        format: Optional[PlaylistFormat] = None,
        relative_paths: bool = True
    ) -> Tuple[bool, List[str]]:
        """Export a database playlist to a file.
        
        Args:
            file_path: Output file path.
            playlist_id: Database playlist ID.
            format: Playlist format. Auto-detected if None.
            relative_paths: Use relative paths when possible.
            
        Returns:
            Tuple of (success, list of errors/warnings)
        """
        tracks = self.database.get_playlist_tracks(playlist_id)
        
        if not tracks:
            return False, ["Playlist is empty or not found"]
        
        return self.export_playlist(file_path, tracks, format, relative_paths)
    
    def export_queue(
        self,
        file_path: Path,
        tracks: List[Dict[str, Any]],
        format: Optional[PlaylistFormat] = None,
        relative_paths: bool = True
    ) -> Tuple[bool, List[str]]:
        """Export current queue to a playlist file.
        
        Args:
            file_path: Output file path.
            tracks: List of track dictionaries.
            format: Playlist format. Auto-detected if None.
            relative_paths: Use relative paths when possible.
            
        Returns:
            Tuple of (success, list of errors/warnings)
        """
        if not tracks:
            return False, ["Queue is empty"]
        
        return self.export_playlist(file_path, tracks, format, relative_paths)
