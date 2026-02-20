"""Centralized signal definitions for PyQt6 UI.

This module provides a centralized signal bus for cross-component communication.
"""

from PyQt6.QtCore import QObject, pyqtSignal


class SignalBus(QObject):
    """Central signal bus for application-wide events.

    This provides a single point for cross-component communication
    without requiring direct references between components.
    """

    # Player signals
    player_state_changed = pyqtSignal(object)  # PlayerState
    player_position_changed = pyqtSignal(float, int)  # position (0.0-1.0), current_seconds
    player_track_loaded = pyqtSignal(dict)  # Track dictionary

    # Playlist signals
    playlist_track_changed = pyqtSignal(dict)  # Current track dict
    playlist_queue_changed = pyqtSignal()  # Queue modified
    playlist_shuffle_changed = pyqtSignal(bool)  # Shuffle state
    playlist_repeat_changed = pyqtSignal(object)  # RepeatMode

    # Library signals
    library_scan_progress = pyqtSignal(str, int, int)  # path, current, total
    library_scan_complete = pyqtSignal(object)  # ScanResult
    library_updated = pyqtSignal()  # Library contents changed

    # YouTube signals
    youtube_search_complete = pyqtSignal(list)  # List of video dicts
    youtube_stream_ready = pyqtSignal(str, dict)  # stream_url, track_dict
    youtube_error = pyqtSignal(str)  # Error message

    # UI navigation signals
    panel_changed = pyqtSignal(str)  # Panel name


# Global signal bus instance
signal_bus = SignalBus()
