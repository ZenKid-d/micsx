"""File scanner for music library."""

import os
from pathlib import Path
from typing import List, Dict, Any, Callable, Optional, Set
from dataclasses import dataclass
import threading

from config.settings import Settings
from .metadata import MetadataExtractor


@dataclass
class ScanResult:
    """Result of a library scan."""
    added: int = 0
    updated: int = 0
    removed: int = 0
    errors: List[str] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []
    
    @property
    def total_changes(self) -> int:
        return self.added + self.updated + self.removed


class FileScanner:
    """Scan directories for music files."""
    
    def __init__(self, settings: Settings):
        """Initialize scanner with settings.
        
        Args:
            settings: Application settings instance.
        """
        self.settings = settings
        self._supported_extensions: Set[str] = set(
            ext.lower() for ext in settings.supported_formats
        )
        self._cancel_flag = False
    
    def cancel(self) -> None:
        """Cancel ongoing scan."""
        self._cancel_flag = True
    
    def is_music_file(self, file_path: Path) -> bool:
        """Check if file is a supported music file."""
        return file_path.suffix.lower() in self._supported_extensions
    
    def scan_directory(
        self,
        directory,
        recursive: bool = True,
        callback: Optional[Callable[[int, int], None]] = None
    ) -> List[Dict[str, Any]]:
        """Scan a directory for music files.
        
        Args:
            directory: Directory path to scan (Path or str).
            recursive: Whether to scan subdirectories.
            callback: Optional callback(progress, total) for progress updates.
            
        Returns:
            List of track data dictionaries.
        """
        self._cancel_flag = False
        tracks = []
        
        # Convert to Path if string
        if isinstance(directory, str):
            directory = Path(directory)
        
        # Find all music files
        music_files = self._find_music_files(directory, recursive)
        total = len(music_files)
        
        for i, file_path in enumerate(music_files):
            if self._cancel_flag:
                break
            
            if callback:
                callback(i + 1, total)
            
            track_data = self._process_file(file_path)
            if track_data:
                tracks.append(track_data)
        
        return tracks
    
    def _find_music_files(self, directory: Path, recursive: bool) -> List[Path]:
        """Find all music files in directory."""
        music_files = []
        
        if not directory.exists():
            return music_files
        
        if recursive:
            for root, dirs, files in os.walk(directory):
                if self._cancel_flag:
                    break
                
                # Skip hidden directories
                dirs[:] = [d for d in dirs if not d.startswith('.')]
                
                for file in files:
                    file_path = Path(root) / file
                    if self.is_music_file(file_path):
                        music_files.append(file_path)
        else:
            for file in directory.iterdir():
                if file.is_file() and self.is_music_file(file):
                    music_files.append(file)
        
        return music_files
    
    def _process_file(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """Process a single music file and extract metadata."""
        try:
            metadata = MetadataExtractor.extract(file_path)
            
            stat = file_path.stat()
            
            return {
                "path": str(file_path.resolve()),
                "title": metadata.title,
                "artist": metadata.artist,
                "album": metadata.album,
                "album_artist": metadata.album_artist,
                "duration": int(metadata.duration),
                "track_number": metadata.track_number,
                "disc_number": metadata.disc_number,
                "genre": metadata.genre,
                "year": metadata.year,
                "cover_embedded": 1 if metadata.cover_data else 0,
                "cover_external": None,
                "bitrate": metadata.bitrate,
                "sample_rate": metadata.sample_rate,
                "channels": metadata.channels,
                "file_size": stat.st_size,
                "file_modified": stat.st_mtime,
            }
        except Exception as e:
            return None
    
    def scan_all_directories(
        self,
        callback: Optional[Callable[[str, int, int], None]] = None
    ) -> List[Dict[str, Any]]:
        """Scan all configured music directories.
        
        Args:
            callback: Optional callback(directory, progress, total) for updates.
            
        Returns:
            List of track data dictionaries.
        """
        all_tracks = []
        
        for directory_str in self.settings.music_dirs:
            if self._cancel_flag:
                break
            
            directory = Path(directory_str).expanduser()
            if not directory.exists():
                continue
            
            def dir_callback(progress: int, total: int):
                if callback:
                    callback(directory_str, progress, total)
            
            tracks = self.scan_directory(directory, callback=dir_callback)
            all_tracks.extend(tracks)
        
        return all_tracks


class LibraryUpdater:
    """Update the library database with scanned tracks."""
    
    def __init__(self, database, settings: Settings):
        """Initialize updater.
        
        Args:
            database: Database instance.
            settings: Application settings.
        """
        self.database = database
        self.scanner = FileScanner(settings)
    
    def update_library(
        self,
        callback: Optional[Callable[[str, int, int], None]] = None
    ) -> ScanResult:
        """Update the library by scanning directories.
        
        Args:
            callback: Optional progress callback.
            
        Returns:
            ScanResult with statistics.
        """
        result = ScanResult()
        
        # Get all existing tracks
        existing_tracks = self.database.get_all_tracks()
        existing_paths = {track["path"] for track in existing_tracks}
        path_to_id = {track["path"]: track["id"] for track in existing_tracks}
        
        # Scan directories
        def scan_callback(directory: str, progress: int, total: int):
            if callback:
                callback(directory, progress, total)
        
        scanned_tracks = self.scanner.scan_all_directories(callback=scan_callback)
        scanned_paths = set()
        
        # Process scanned tracks
        for track_data in scanned_tracks:
            path = track_data["path"]
            scanned_paths.add(path)
            
            if path in existing_paths:
                # Check if file was modified
                existing_id = path_to_id[path]
                existing = next(t for t in existing_tracks if t["path"] == path)
                
                if existing.get("file_modified") != track_data.get("file_modified"):
                    # Update track
                    self.database.update_track(path, track_data)
                    result.updated += 1
            else:
                # New track
                self.database.insert_track(track_data)
                result.added += 1
        
        # Remove tracks that no longer exist
        for path in existing_paths - scanned_paths:
            if self.database.delete_track_by_path(path):
                result.removed += 1
        
        return result
    
    def scan_new_files(
        self,
        callback: Optional[Callable[[str, int, int], None]] = None
    ) -> int:
        """Scan only for new files (no updates or removals).
        
        Returns:
            Number of new tracks added.
        """
        existing_paths = {
            track["path"] for track in self.database.get_all_tracks()
        }
        
        scanned = self.scanner.scan_all_directories(callback=callback)
        added = 0
        
        for track_data in scanned:
            if track_data["path"] not in existing_paths:
                if self.database.insert_track(track_data):
                    added += 1
        
        return added