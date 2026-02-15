"""Audio player using VLC backend."""

import time
import threading
from pathlib import Path
from typing import Optional, Callable, Dict, Any
from enum import Enum
from dataclasses import dataclass

import vlc


class PlayerState(Enum):
    """Player playback state."""
    STOPPED = "stopped"
    PLAYING = "playing"
    PAUSED = "paused"
    LOADING = "loading"
    ERROR = "error"


@dataclass
class TrackInfo:
    """Information about currently playing track."""
    id: int
    path: str
    title: str
    artist: Optional[str]
    album: Optional[str]
    duration: int  # seconds


class AudioPlayer:
    """VLC-based audio player."""
    
    def __init__(self, settings=None):
        """Initialize the audio player.
        
        Args:
            settings: Application settings instance.
        """
        self.settings = settings
        self._volume = settings.volume if settings else 80
        
        # VLC instances
        self._instance: Optional[vlc.Instance] = None
        self._player: Optional[vlc.MediaPlayer] = None
        self._media: Optional[vlc.Media] = None
        
        # State
        self._state = PlayerState.STOPPED
        self._current_track: Optional[TrackInfo] = None
        self._position: float = 0.0  # 0.0 to 1.0
        self._muted: bool = False
        
        # Callbacks
        self._on_state_change: Optional[Callable[[PlayerState], None]] = None
        self._on_position_change: Optional[Callable[[float, int], None]] = None
        self._on_track_end: Optional[Callable[[], None]] = None
        
        # Threading
        self._position_thread: Optional[threading.Thread] = None
        self._running = False
        
        # Initialize VLC
        self._init_vlc()
    
    def _init_vlc(self) -> None:
        """Initialize VLC instance and player."""
        try:
            # Create VLC instance with minimal options
            self._instance = vlc.Instance([
                "--no-video",
                "--no-xlib",
                "--quiet",
                "--no-ignore-config",
            ])
            self._player = self._instance.media_player_new()
            self._player.audio_set_volume(self._volume)
        except Exception as e:
            self._state = PlayerState.ERROR
            raise RuntimeError(f"Failed to initialize VLC: {e}")
    
    def load_track(self, track: Dict[str, Any]) -> bool:
        """Load a track for playback.
        
        Args:
            track: Track dictionary from database.
            
        Returns:
            True if successful, False otherwise.
        """
        if not self._instance or not self._player:
            return False
        
        path = track.get("path")
        if not path or not Path(path).exists():
            return False
        
        try:
            # Stop current playback
            self.stop()
            
            # Create new media
            self._media = self._instance.media_new(path)
            self._player.set_media(self._media)
            
            # Store track info
            self._current_track = TrackInfo(
                id=track["id"],
                path=path,
                title=track.get("title") or Path(path).stem,
                artist=track.get("artist"),
                album=track.get("album"),
                duration=track.get("duration", 0),
            )
            
            self._state = PlayerState.STOPPED
            return True
        except Exception as e:
            self._state = PlayerState.ERROR
            return False
    
    def play(self) -> bool:
        """Start or resume playback.
        
        Returns:
            True if successful, False otherwise.
        """
        if not self._player:
            return False
        
        if self._state == PlayerState.PLAYING:
            return True
        
        try:
            if self._player.play() == 0:
                self._state = PlayerState.PLAYING
                self._start_position_thread()
                self._notify_state_change()
                return True
        except Exception:
            pass
        
        return False
    
    def pause(self) -> bool:
        """Pause playback.
        
        Returns:
            True if successful, False otherwise.
        """
        if not self._player or self._state != PlayerState.PLAYING:
            return False
        
        try:
            self._player.pause()
            self._state = PlayerState.PAUSED
            self._notify_state_change()
            return True
        except Exception:
            pass
        
        return False
    
    def toggle_pause(self) -> bool:
        """Toggle between play and pause.
        
        Returns:
            True if successful, False otherwise.
        """
        if self._state == PlayerState.PLAYING:
            return self.pause()
        elif self._state == PlayerState.PAUSED:
            return self.play()
        return False
    
    def stop(self) -> None:
        """Stop playback."""
        if self._player:
            self._player.stop()
        
        self._stop_position_thread()
        self._state = PlayerState.STOPPED
        self._position = 0.0
        self._notify_state_change()
    
    def seek(self, position: float) -> bool:
        """Seek to position.
        
        Args:
            position: Position as float between 0.0 and 1.0.
            
        Returns:
            True if successful, False otherwise.
        """
        if not self._player or not self._current_track:
            return False
        
        try:
            duration_ms = self._current_track.duration * 1000
            seek_ms = int(position * duration_ms)
            self._player.set_time(seek_ms)
            return True
        except Exception:
            pass
        
        return False
    
    def seek_seconds(self, seconds: int) -> bool:
        """Seek by seconds relative to current position.
        
        Args:
            seconds: Seconds to seek (negative for backward).
            
        Returns:
            True if successful, False otherwise.
        """
        if not self._player or not self._current_track:
            return False
        
        try:
            current_time = self._player.get_time()
            new_time = max(0, current_time + seconds * 1000)
            self._player.set_time(new_time)
            return True
        except Exception:
            pass
        
        return False
    
    @property
    def volume(self) -> int:
        """Get current volume (0-100)."""
        return self._volume
    
    @volume.setter
    def volume(self, value: int) -> None:
        """Set volume (0-100)."""
        self._volume = max(0, min(100, value))
        if self._player:
            self._player.audio_set_volume(self._volume)
    
    def volume_up(self, amount: int = 5) -> int:
        """Increase volume.
        
        Args:
            amount: Amount to increase.
            
        Returns:
            New volume level.
        """
        self.volume = self._volume + amount
        return self._volume
    
    def volume_down(self, amount: int = 5) -> int:
        """Decrease volume.
        
        Args:
            amount: Amount to decrease.
            
        Returns:
            New volume level.
        """
        self.volume = self._volume - amount
        return self._volume
    
    def mute(self) -> bool:
        """Toggle mute.
        
        Returns:
            True if now muted, False if unmuted.
        """
        if self._player:
            self._player.audio_toggle_mute()
            self._muted = self._player.audio_get_mute()
            return self._muted
        return False
    
    @property
    def is_muted(self) -> bool:
        """Check if audio is muted."""
        if self._player:
            return self._player.audio_get_mute()
        return self._muted
    
    @property
    def state(self) -> PlayerState:
        """Get current player state."""
        return self._state
    
    @property
    def current_track(self) -> Optional[TrackInfo]:
        """Get currently loaded track."""
        return self._current_track
    
    @property
    def position(self) -> float:
        """Get current position (0.0 to 1.0)."""
        return self._position
    
    @property
    def position_seconds(self) -> int:
        """Get current position in seconds."""
        if self._current_track:
            return int(self._position * self._current_track.duration)
        return 0
    
    def get_position_info(self) -> tuple:
        """Get position info as (current_seconds, total_seconds).
        
        Returns:
            Tuple of (current, total) in seconds.
        """
        if self._current_track:
            current = int(self._position * self._current_track.duration)
            total = self._current_track.duration
            return (current, total)
        return (0, 0)
    
    # ==================== Callbacks ====================
    
    def set_on_state_change(self, callback: Callable[[PlayerState], None]) -> None:
        """Set state change callback."""
        self._on_state_change = callback
    
    def set_on_position_change(self, callback: Callable[[float, int], None]) -> None:
        """Set position change callback."""
        self._on_position_change = callback
    
    def set_on_track_end(self, callback: Callable[[], None]) -> None:
        """Set track end callback."""
        self._on_track_end = callback
    
    def _notify_state_change(self) -> None:
        """Notify state change callback."""
        if self._on_state_change:
            try:
                self._on_state_change(self._state)
            except Exception:
                pass
    
    def _notify_position_change(self) -> None:
        """Notify position change callback."""
        if self._on_position_change:
            try:
                current, total = self.get_position_info()
                self._on_position_change(self._position, current)
            except Exception:
                pass
    
    # ==================== Position Thread ====================
    
    def _start_position_thread(self) -> None:
        """Start the position update thread."""
        if self._position_thread and self._position_thread.is_alive():
            return
        
        self._running = True
        self._position_thread = threading.Thread(target=self._position_loop, daemon=True)
        self._position_thread.start()
    
    def _stop_position_thread(self) -> None:
        """Stop the position update thread."""
        self._running = False
        if self._position_thread:
            self._position_thread.join(timeout=0.5)
            self._position_thread = None
    
    def _position_loop(self) -> None:
        """Position update loop."""
        while self._running and self._state == PlayerState.PLAYING:
            try:
                if self._player and self._current_track:
                    time_ms = self._player.get_time()
                    duration_ms = self._current_track.duration * 1000
                    
                    if duration_ms > 0:
                        self._position = min(1.0, time_ms / duration_ms)
                    
                    self._notify_position_change()
                    
                    # Check if track ended
                    if time_ms >= duration_ms and duration_ms > 0:
                        if self._on_track_end:
                            self._on_track_end()
                        break
            except Exception:
                pass
            
            time.sleep(0.1)
    
    # ==================== Cleanup ====================
    
    def cleanup(self) -> None:
        """Clean up resources."""
        self._stop_position_thread()
        self.stop()
        
        if self._media:
            self._media = None
        
        if self._player:
            self._player.release()
            self._player = None
        
        if self._instance:
            self._instance.release()
            self._instance = None