"""Music library management."""

from typing import Optional, List, Dict, Any, Callable
from pathlib import Path

from config.settings import Settings
from data.database import Database
from data.scanner import LibraryUpdater, ScanResult


class LibraryManager:
    """Manage the music library."""
    
    def __init__(self, database: Database, settings: Settings):
        """Initialize library manager.
        
        Args:
            database: Database instance.
            settings: Application settings.
        """
        self.database = database
        self.settings = settings
        self.updater = LibraryUpdater(database, settings)
        
        # Callbacks
        self._on_scan_progress: Optional[Callable[[str, int, int], None]] = None
        self._on_scan_complete: Optional[Callable[[ScanResult], None]] = None
    
    # ==================== Scanning ====================
    
    def scan_library(self) -> ScanResult:
        """Scan all music directories and update library.
        
        Returns:
            ScanResult with statistics.
        """
        return self.updater.update_library(callback=self._on_scan_progress)
    
    def scan_new_files(self) -> int:
        """Scan for new files only (no updates/removals).
        
        Returns:
            Number of new tracks added.
        """
        return self.updater.scan_new_files(callback=self._on_scan_progress)
    
    def rescan_library(self) -> ScanResult:
        """Full rescan of the library."""
        # Clear and rescan
        return self.scan_library()
    
    # ==================== Track Operations ====================
    
    def get_all_tracks(self) -> List[Dict[str, Any]]:
        """Get all tracks in the library."""
        return self.database.get_all_tracks()
    
    def get_track(self, track_id: int) -> Optional[Dict[str, Any]]:
        """Get a track by ID."""
        return self.database.get_track(track_id)
    
    def get_track_count(self) -> int:
        """Get total number of tracks."""
        return self.database.get_track_count()
    
    def delete_track(self, track_id: int) -> bool:
        """Delete a track from the library."""
        return self.database.delete_track(track_id)
    
    # ==================== Organizing ====================
    
    def get_artists(self) -> List[str]:
        """Get list of all artists."""
        tracks = self.database.get_all_tracks()
        artists = set()
        for track in tracks:
            if track.get("artist"):
                artists.add(track["artist"])
        return sorted(artists)
    
    def get_albums(self) -> List[Dict[str, Any]]:
        """Get list of all albums with metadata."""
        tracks = self.database.get_all_tracks()
        albums = {}
        
        for track in tracks:
            album = track.get("album")
            artist = track.get("album_artist") or track.get("artist")
            
            if album:
                key = (album, artist)
                if key not in albums:
                    albums[key] = {
                        "name": album,
                        "artist": artist,
                        "track_count": 0,
                        "duration": 0,
                        "year": track.get("year"),
                    }
                albums[key]["track_count"] += 1
                albums[key]["duration"] += track.get("duration", 0)
        
        return list(albums.values())
    
    def get_tracks_by_artist(self, artist: str) -> List[Dict[str, Any]]:
        """Get all tracks by an artist."""
        all_tracks = self.database.get_all_tracks()
        return [t for t in all_tracks if t.get("artist") == artist]
    
    def get_tracks_by_album(self, album: str, artist: str = None) -> List[Dict[str, Any]]:
        """Get all tracks in an album."""
        all_tracks = self.database.get_all_tracks()
        
        tracks = []
        for track in all_tracks:
            if track.get("album") == album:
                if artist is None or track.get("artist") == artist or track.get("album_artist") == artist:
                    tracks.append(track)
        
        # Sort by track number
        tracks.sort(key=lambda t: (t.get("disc_number", 0), t.get("track_number", 0)))
        return tracks
    
    # ==================== Recently Played ====================
    
    def get_recently_played(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recently played tracks."""
        return self.database.get_recently_played(limit)
    
    def record_play(self, track_id: int) -> None:
        """Record a track play."""
        self.database.record_play(track_id)
    
    # ==================== Directories ====================
    
    def add_music_directory(self, path: str) -> bool:
        """Add a music directory to settings."""
        if not Path(path).exists():
            return False
        
        self.settings.add_music_dir(path)
        return True
    
    def remove_music_directory(self, path: str) -> bool:
        """Remove a music directory from settings."""
        return self.settings.remove_music_dir(path)
    
    def get_music_directories(self) -> List[str]:
        """Get configured music directories."""
        return self.settings.music_dirs.copy()
    
    # ==================== Callbacks ====================
    
    def set_on_scan_progress(self, callback: Callable[[str, int, int], None]) -> None:
        """Set scan progress callback."""
        self._on_scan_progress = callback
    
    def set_on_scan_complete(self, callback: Callable[[ScanResult], None]) -> None:
        """Set scan complete callback."""
        self._on_scan_complete = callback