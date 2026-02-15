"""Search engine for music library."""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from data.database import Database


@dataclass
class SearchResult:
    """Container for search results."""
    tracks: List[Dict[str, Any]]
    query: str
    total: int


class SearchEngine:
    """Search tracks in the music library."""
    
    def __init__(self, database: Database):
        """Initialize search engine.
        
        Args:
            database: Database instance for queries.
        """
        self.database = database
        self._search_history: List[str] = []
        self._max_history = 50
    
    def search(self, query: str, limit: int = 100) -> SearchResult:
        """Search tracks by title or artist.
        
        Args:
            query: Search query string.
            limit: Maximum number of results.
            
        Returns:
            SearchResult with matching tracks.
        """
        if not query or not query.strip():
            return SearchResult(tracks=[], query=query, total=0)
        
        query = query.strip()
        
        # Add to history
        self._add_to_history(query)
        
        # Perform search
        tracks = self.database.search_tracks(query)
        
        # Limit results
        limited_tracks = tracks[:limit]
        
        return SearchResult(
            tracks=limited_tracks,
            query=query,
            total=len(tracks)
        )
    
    def search_by_title(self, query: str) -> List[Dict[str, Any]]:
        """Search tracks by title only."""
        all_tracks = self.database.get_all_tracks()
        query_lower = query.lower()
        
        return [
            track for track in all_tracks
            if track.get("title") and query_lower in track["title"].lower()
        ]
    
    def search_by_artist(self, query: str) -> List[Dict[str, Any]]:
        """Search tracks by artist only."""
        all_tracks = self.database.get_all_tracks()
        query_lower = query.lower()
        
        return [
            track for track in all_tracks
            if track.get("artist") and query_lower in track["artist"].lower()
        ]
    
    def search_by_album(self, query: str) -> List[Dict[str, Any]]:
        """Search tracks by album only."""
        all_tracks = self.database.get_all_tracks()
        query_lower = query.lower()
        
        return [
            track for track in all_tracks
            if track.get("album") and query_lower in track["album"].lower()
        ]
    
    def get_history(self, limit: int = 10) -> List[str]:
        """Get recent search history.
        
        Args:
            limit: Maximum number of history items.
            
        Returns:
            List of recent search queries.
        """
        return self._search_history[:limit]
    
    def clear_history(self) -> None:
        """Clear search history."""
        self._search_history.clear()
    
    def rebuild_index(self) -> None:
        """Rebuild search index (no-op for database-based search)."""
        # This is a no-op since we search directly from the database
        # Could be extended to build an in-memory index for faster search
        pass
    
    def _add_to_history(self, query: str) -> None:
        """Add query to search history."""
        # Remove if already exists
        if query in self._search_history:
            self._search_history.remove(query)
        
        # Add to front
        self._search_history.insert(0, query)
        
        # Limit size
        if len(self._search_history) > self._max_history:
            self._search_history = self._search_history[:self._max_history]