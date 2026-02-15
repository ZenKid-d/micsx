"""SQLite database management for music library."""

import sqlite3
from pathlib import Path
from typing import Optional, List, Dict, Any
from contextlib import contextmanager
from datetime import datetime

from config.settings import get_data_dir


class Database:
    """SQLite database for music library metadata."""
    
    def __init__(self, db_path: Optional[Path] = None):
        """Initialize database connection.
        
        Args:
            db_path: Path to database file. Uses default if None.
        """
        self.db_path = db_path or (get_data_dir() / "library.db")
        self._init_database()
    
    @contextmanager
    def _get_connection(self):
        """Get database connection context manager."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def _init_database(self) -> None:
        """Initialize database schema."""
        with self._get_connection() as conn:
            # Tracks table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS tracks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    path TEXT UNIQUE NOT NULL,
                    title TEXT,
                    artist TEXT,
                    album TEXT,
                    album_artist TEXT,
                    duration INTEGER NOT NULL DEFAULT 0,
                    track_number INTEGER,
                    disc_number INTEGER,
                    genre TEXT,
                    year INTEGER,
                    cover_embedded INTEGER DEFAULT 0,
                    cover_external TEXT,
                    bitrate INTEGER,
                    sample_rate INTEGER,
                    channels INTEGER,
                    file_size INTEGER,
                    file_modified REAL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
            
            # Playlists table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS playlists (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    description TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
            
            # Playlist tracks junction table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS playlist_tracks (
                    playlist_id INTEGER NOT NULL,
                    track_id INTEGER NOT NULL,
                    position INTEGER NOT NULL,
                    added_at TEXT NOT NULL,
                    PRIMARY KEY (playlist_id, track_id),
                    FOREIGN KEY (playlist_id) REFERENCES playlists(id) ON DELETE CASCADE,
                    FOREIGN KEY (track_id) REFERENCES tracks(id) ON DELETE CASCADE
                )
            """)
            
            # Play history table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS play_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    track_id INTEGER NOT NULL,
                    played_at TEXT NOT NULL,
                    FOREIGN KEY (track_id) REFERENCES tracks(id) ON DELETE CASCADE
                )
            """)
            
            # Create indexes
            conn.execute("CREATE INDEX IF NOT EXISTS idx_tracks_artist ON tracks(artist)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_tracks_album ON tracks(album)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_tracks_title ON tracks(title)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_playlist_tracks_position ON playlist_tracks(playlist_id, position)")
    
    # ==================== Track Operations ====================
    
    def insert_track(self, track_data: Dict[str, Any]) -> Optional[int]:
        """Insert a new track into the database.
        
        Args:
            track_data: Dictionary with track metadata.
            
        Returns:
            Track ID if successful, None otherwise.
        """
        now = datetime.now().isoformat()
        track_data["created_at"] = now
        track_data["updated_at"] = now
        
        try:
            with self._get_connection() as conn:
                cursor = conn.execute("""
                    INSERT INTO tracks (
                        path, title, artist, album, album_artist, duration,
                        track_number, disc_number, genre, year,
                        cover_embedded, cover_external,
                        bitrate, sample_rate, channels,
                        file_size, file_modified,
                        created_at, updated_at
                    ) VALUES (
                        :path, :title, :artist, :album, :album_artist, :duration,
                        :track_number, :disc_number, :genre, :year,
                        :cover_embedded, :cover_external,
                        :bitrate, :sample_rate, :channels,
                        :file_size, :file_modified,
                        :created_at, :updated_at
                    )
                """, track_data)
                return cursor.lastrowid
        except sqlite3.IntegrityError:
            return None
    
    def update_track(self, path: str, track_data: Dict[str, Any]) -> bool:
        """Update an existing track.
        
        Args:
            path: Path to the track file.
            track_data: Dictionary with updated metadata.
            
        Returns:
            True if successful, False otherwise.
        """
        track_data["updated_at"] = datetime.now().isoformat()
        track_data["path"] = path
        
        with self._get_connection() as conn:
            cursor = conn.execute("""
                UPDATE tracks SET
                    title = :title,
                    artist = :artist,
                    album = :album,
                    album_artist = :album_artist,
                    duration = :duration,
                    track_number = :track_number,
                    disc_number = :disc_number,
                    genre = :genre,
                    year = :year,
                    cover_embedded = :cover_embedded,
                    cover_external = :cover_external,
                    bitrate = :bitrate,
                    sample_rate = :sample_rate,
                    channels = :channels,
                    file_size = :file_size,
                    file_modified = :file_modified,
                    updated_at = :updated_at
                WHERE path = :path
            """, track_data)
            return cursor.rowcount > 0
    
    def get_track(self, track_id: int) -> Optional[Dict[str, Any]]:
        """Get a track by ID."""
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT * FROM tracks WHERE id = ?", (track_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def get_track_by_path(self, path: str) -> Optional[Dict[str, Any]]:
        """Get a track by file path."""
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT * FROM tracks WHERE path = ?", (path,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def get_all_tracks(self, limit: int = 0, offset: int = 0) -> List[Dict[str, Any]]:
        """Get all tracks."""
        with self._get_connection() as conn:
            query = "SELECT * FROM tracks ORDER BY artist, album, track_number, title"
            if limit > 0:
                query += f" LIMIT {limit} OFFSET {offset}"
            cursor = conn.execute(query)
            return [dict(row) for row in cursor.fetchall()]
    
    def search_tracks(self, query: str) -> List[Dict[str, Any]]:
        """Search tracks by title or artist."""
        search_term = f"%{query}%"
        with self._get_connection() as conn:
            cursor = conn.execute("""
                SELECT * FROM tracks 
                WHERE title LIKE ? OR artist LIKE ?
                ORDER BY artist, album, track_number, title
            """, (search_term, search_term))
            return [dict(row) for row in cursor.fetchall()]
    
    def delete_track(self, track_id: int) -> bool:
        """Delete a track by ID."""
        with self._get_connection() as conn:
            cursor = conn.execute("DELETE FROM tracks WHERE id = ?", (track_id,))
            return cursor.rowcount > 0
    
    def delete_track_by_path(self, path: str) -> bool:
        """Delete a track by file path."""
        with self._get_connection() as conn:
            cursor = conn.execute("DELETE FROM tracks WHERE path = ?", (path,))
            return cursor.rowcount > 0
    
    def get_track_count(self) -> int:
        """Get total number of tracks."""
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM tracks")
            return cursor.fetchone()[0]
    
    # ==================== Playlist Operations ====================
    
    def create_playlist(self, name: str, description: str = "") -> Optional[int]:
        """Create a new playlist."""
        now = datetime.now().isoformat()
        try:
            with self._get_connection() as conn:
                cursor = conn.execute("""
                    INSERT INTO playlists (name, description, created_at, updated_at)
                    VALUES (?, ?, ?, ?)
                """, (name, description, now, now))
                return cursor.lastrowid
        except sqlite3.IntegrityError:
            return None
    
    def get_playlist(self, playlist_id: int) -> Optional[Dict[str, Any]]:
        """Get a playlist by ID."""
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT * FROM playlists WHERE id = ?", (playlist_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def get_playlist_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Get a playlist by name."""
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT * FROM playlists WHERE name = ?", (name,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def get_all_playlists(self) -> List[Dict[str, Any]]:
        """Get all playlists."""
        with self._get_connection() as conn:
            cursor = conn.execute("""
                SELECT p.*, COUNT(pt.track_id) as track_count
                FROM playlists p
                LEFT JOIN playlist_tracks pt ON p.id = pt.playlist_id
                GROUP BY p.id
                ORDER BY p.name
            """)
            return [dict(row) for row in cursor.fetchall()]
    
    def rename_playlist(self, playlist_id: int, new_name: str) -> bool:
        """Rename a playlist."""
        now = datetime.now().isoformat()
        try:
            with self._get_connection() as conn:
                cursor = conn.execute("""
                    UPDATE playlists SET name = ?, updated_at = ?
                    WHERE id = ?
                """, (new_name, now, playlist_id))
                return cursor.rowcount > 0
        except sqlite3.IntegrityError:
            return False
    
    def delete_playlist(self, playlist_id: int) -> bool:
        """Delete a playlist."""
        with self._get_connection() as conn:
            cursor = conn.execute("DELETE FROM playlists WHERE id = ?", (playlist_id,))
            return cursor.rowcount > 0
    
    # ==================== Playlist Track Operations ====================
    
    def add_track_to_playlist(self, playlist_id: int, track_id: int) -> bool:
        """Add a track to a playlist."""
        now = datetime.now().isoformat()
        
        with self._get_connection() as conn:
            # Get next position
            cursor = conn.execute("""
                SELECT COALESCE(MAX(position), -1) + 1
                FROM playlist_tracks
                WHERE playlist_id = ?
            """, (playlist_id,))
            position = cursor.fetchone()[0]
            
            try:
                conn.execute("""
                    INSERT INTO playlist_tracks (playlist_id, track_id, position, added_at)
                    VALUES (?, ?, ?, ?)
                """, (playlist_id, track_id, position, now))
                
                # Update playlist timestamp
                conn.execute("""
                    UPDATE playlists SET updated_at = ? WHERE id = ?
                """, (now, playlist_id))
                
                return True
            except sqlite3.IntegrityError:
                return False
    
    def remove_track_from_playlist(self, playlist_id: int, track_id: int) -> bool:
        """Remove a track from a playlist."""
        now = datetime.now().isoformat()
        
        with self._get_connection() as conn:
            # Get position of track being removed
            cursor = conn.execute("""
                SELECT position FROM playlist_tracks
                WHERE playlist_id = ? AND track_id = ?
            """, (playlist_id, track_id))
            row = cursor.fetchone()
            if not row:
                return False
            
            removed_position = row[0]
            
            # Delete the track
            conn.execute("""
                DELETE FROM playlist_tracks
                WHERE playlist_id = ? AND track_id = ?
            """, (playlist_id, track_id))
            
            # Reorder remaining tracks
            conn.execute("""
                UPDATE playlist_tracks
                SET position = position - 1
                WHERE playlist_id = ? AND position > ?
            """, (playlist_id, removed_position))
            
            # Update playlist timestamp
            conn.execute("""
                UPDATE playlists SET updated_at = ? WHERE id = ?
            """, (now, playlist_id))
            
            return True
    
    def get_playlist_tracks(self, playlist_id: int) -> List[Dict[str, Any]]:
        """Get all tracks in a playlist."""
        with self._get_connection() as conn:
            cursor = conn.execute("""
                SELECT t.*, pt.position, pt.added_at
                FROM tracks t
                JOIN playlist_tracks pt ON t.id = pt.track_id
                WHERE pt.playlist_id = ?
                ORDER BY pt.position
            """, (playlist_id,))
            return [dict(row) for row in cursor.fetchall()]
    
    def reorder_playlist_track(self, playlist_id: int, track_id: int, new_position: int) -> bool:
        """Move a track to a new position in the playlist."""
        with self._get_connection() as conn:
            # Get current position
            cursor = conn.execute("""
                SELECT position FROM playlist_tracks
                WHERE playlist_id = ? AND track_id = ?
            """, (playlist_id, track_id))
            row = cursor.fetchone()
            if not row:
                return False
            
            old_position = row[0]
            if old_position == new_position:
                return True
            
            # Shift other tracks
            if new_position < old_position:
                conn.execute("""
                    UPDATE playlist_tracks
                    SET position = position + 1
                    WHERE playlist_id = ? AND position >= ? AND position < ?
                """, (playlist_id, new_position, old_position))
            else:
                conn.execute("""
                    UPDATE playlist_tracks
                    SET position = position - 1
                    WHERE playlist_id = ? AND position > ? AND position <= ?
                """, (playlist_id, old_position, new_position))
            
            # Move the track
            conn.execute("""
                UPDATE playlist_tracks
                SET position = ?
                WHERE playlist_id = ? AND track_id = ?
            """, (new_position, playlist_id, track_id))
            
            return True
    
    # ==================== Play History ====================
    
    def record_play(self, track_id: int) -> None:
        """Record a track play in history."""
        now = datetime.now().isoformat()
        with self._get_connection() as conn:
            conn.execute("""
                INSERT INTO play_history (track_id, played_at)
                VALUES (?, ?)
            """, (track_id, now))
    
    def get_recently_played(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recently played tracks."""
        with self._get_connection() as conn:
            cursor = conn.execute("""
                SELECT t.*, ph.played_at
                FROM tracks t
                JOIN play_history ph ON t.id = ph.track_id
                ORDER BY ph.played_at DESC
                LIMIT ?
            """, (limit,))
            return [dict(row) for row in cursor.fetchall()]
    
    def get_play_count(self, track_id: int) -> int:
        """Get the play count for a track."""
        with self._get_connection() as conn:
            cursor = conn.execute("""
                SELECT COUNT(*) FROM play_history WHERE track_id = ?
            """, (track_id,))
            return cursor.fetchone()[0]
    
    def close(self) -> None:
        """Close database connection (no-op for context manager pattern)."""
        # Using context manager pattern, no persistent connection to close
        pass
