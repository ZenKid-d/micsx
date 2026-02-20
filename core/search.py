"""Search engine for music library with fuzzy matching."""

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from functools import lru_cache

from thefuzz import fuzz

from data.database import Database


@dataclass
class SearchResult:
    """Container for search results."""
    tracks: List[Dict[str, Any]]
    query: str
    total: int


@dataclass
class ScoredTrack:
    """Track with fuzzy match score."""
    track: Dict[str, Any]
    score: int
    matched_field: str


class SearchEngine:
    """Search tracks in the music library with fuzzy matching."""
    
    # Minimum score threshold for fuzzy matching
    MIN_SCORE = 60
    
    # Fields to search in with weights
    SEARCH_FIELDS = [
        ("title", 1.0),
        ("artist", 0.9),
        ("album", 0.8),
        ("album_artist", 0.7),
    ]
    
    def __init__(self, database: Database):
        """Initialize search engine.
        
        Args:
            database: Database instance for queries.
        """
        self.database = database
        self._search_history: List[str] = []
        self._max_history = 50
        self._cache: Dict[str, List[Dict[str, Any]]] = {}
    
    def search(self, query: str, limit: int = 100) -> SearchResult:
        """Search tracks using fuzzy matching.
        
        Searches in title, artist, album with score > 60.
        Results are sorted by relevance.
        
        Args:
            query: Search query string.
            limit: Maximum number of results.
            
        Returns:
            SearchResult with matching tracks sorted by score.
        """
        if not query or not query.strip():
            return SearchResult(tracks=[], query=query, total=0)
        
        query = query.strip()
        
        # Add to history
        self._add_to_history(query)
        
        # Perform fuzzy search
        tracks = self.fuzzy_search(query, limit)
        
        return SearchResult(
            tracks=tracks,
            query=query,
            total=len(tracks)
        )
    
    def fuzzy_search(self, query: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Perform fuzzy search across all relevant fields.
        
        Args:
            query: Search query string.
            limit: Maximum number of results.
            
        Returns:
            List of tracks sorted by relevance score.
        """
        all_tracks = self.database.get_all_tracks()
        
        if not all_tracks:
            return []
        
        # Score each track
        scored_tracks: List[ScoredTrack] = []
        query_lower = query.lower()
        
        for track in all_tracks:
            best_score = 0
            best_field = ""
            
            for field, weight in self.SEARCH_FIELDS:
                value = track.get(field, "")
                if not value:
                    continue
                
                # Calculate multiple fuzzy scores
                # partial_ratio - best for substring matching
                partial_score = fuzz.partial_ratio(query_lower, value.lower())
                # token_sort_ratio - handles word order
                token_score = fuzz.token_sort_ratio(query_lower, value.lower())
                # ratio - overall similarity
                ratio_score = fuzz.ratio(query_lower, value.lower())
                
                # Take best score and apply weight
                field_score = max(partial_score, token_score, ratio_score) * weight
                
                if field_score > best_score:
                    best_score = field_score
                    best_field = field
            
            # Only include if above threshold
            if best_score >= self.MIN_SCORE:
                scored_tracks.append(ScoredTrack(
                    track=track,
                    score=int(best_score),
                    matched_field=best_field
                ))
        
        # Sort by score (descending)
        scored_tracks.sort(key=lambda x: x.score, reverse=True)
        
        # Return limited results
        return [st.track for st in scored_tracks[:limit]]
    
    def search_by_title(self, query: str) -> List[Dict[str, Any]]:
        """Search tracks by title only using fuzzy matching."""
        return self._search_field(query, "title")
    
    def search_by_artist(self, query: str) -> List[Dict[str, Any]]:
        """Search tracks by artist only using fuzzy matching."""
        return self._search_field(query, "artist")
    
    def search_by_album(self, query: str) -> List[Dict[str, Any]]:
        """Search tracks by album only using fuzzy matching."""
        return self._search_field(query, "album")
    
    def _search_field(self, query: str, field: str) -> List[Dict[str, Any]]:
        """Search in a specific field with fuzzy matching."""
        all_tracks = self.database.get_all_tracks()
        query_lower = query.lower()
        
        scored = []
        for track in all_tracks:
            value = track.get(field, "")
            if not value:
                continue
            
            score = fuzz.partial_ratio(query_lower, value.lower())
            if score >= self.MIN_SCORE:
                scored.append((score, track))
        
        scored.sort(key=lambda x: x[0], reverse=True)
        return [t for s, t in scored]
    
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
    
    def clear_cache(self) -> None:
        """Clear search cache."""
        self._cache.clear()
    
    def rebuild_index(self) -> None:
        """Rebuild search index and clear cache."""
        self.clear_cache()
    
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