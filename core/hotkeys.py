"""Global hotkeys management using pynput."""

import threading
from typing import Optional, Callable, Dict
from pynput import keyboard
from pynput.keyboard import Key, KeyCode

from config.settings import Settings


class GlobalHotkeyManager:
    """Manage global keyboard shortcuts."""
    
    def __init__(self, settings: Settings):
        """Initialize hotkey manager.
        
        Args:
            settings: Application settings with hotkey config.
        """
        self.settings = settings
        
        # Callbacks
        self._callbacks: Dict[str, Callable] = {}
        
        # Hotkey definitions
        self._hotkeys: Dict[str, str] = {}
        self._update_hotkeys()
        
        # Listener
        self._listener: Optional[keyboard.Listener] = None
        self._running = False
        
        # Current pressed keys
        self._current_keys: set = set()
    
    def _update_hotkeys(self) -> None:
        """Update hotkey definitions from settings."""
        self._hotkeys = {
            self.settings.hotkey_play_pause: "play_pause",
            self.settings.hotkey_next: "next",
            self.settings.hotkey_prev: "prev",
        }
    
    def register_callback(self, action: str, callback: Callable) -> None:
        """Register a callback for an action.
        
        Args:
            action: Action name (play_pause, next, prev).
            callback: Function to call when hotkey is pressed.
        """
        self._callbacks[action] = callback
    
    def unregister_callback(self, action: str) -> None:
        """Unregister a callback."""
        if action in self._callbacks:
            del self._callbacks[action]
    
    def start(self) -> bool:
        """Start listening for hotkeys.
        
        Returns:
            True if started successfully, False otherwise.
        """
        if self._running:
            return True
        
        if not self.settings.global_hotkeys_enabled:
            return False
        
        try:
            self._running = True
            self._listener = keyboard.Listener(
                on_press=self._on_press,
                on_release=self._on_release
            )
            self._listener.daemon = True
            self._listener.start()
            return True
        except Exception as e:
            self._running = False
            return False
    
    def stop(self) -> None:
        """Stop listening for hotkeys."""
        self._running = False
        
        if self._listener:
            self._listener.stop()
            self._listener = None
        
        self._current_keys.clear()
    
    def _on_press(self, key) -> None:
        """Handle key press event."""
        if not self._running:
            return
        
        # Add key to current set
        self._current_keys.add(self._normalize_key(key))
        
        # Check for hotkey matches
        self._check_hotkeys()
    
    def _on_release(self, key) -> None:
        """Handle key release event."""
        if not self._running:
            return
        
        # Remove key from current set
        normalized = self._normalize_key(key)
        if normalized in self._current_keys:
            self._current_keys.discard(normalized)
    
    def _normalize_key(self, key) -> str:
        """Normalize a key for comparison.
        
        Args:
            key: Key from pynput.
            
        Returns:
            Normalized key string.
        """
        if isinstance(key, KeyCode):
            return f"<{key.char.lower()}>"
        elif isinstance(key, Key):
            return f"<{key.name}>"
        return str(key)
    
    def _check_hotkeys(self) -> None:
        """Check if current keys match any hotkey."""
        current_combo = "+".join(sorted(self._current_keys))
        
        for hotkey_str, action in self._hotkeys.items():
            if self._match_hotkey(hotkey_str):
                self._trigger_action(action)
                break
    
    def _match_hotkey(self, hotkey_str: str) -> bool:
        """Check if current keys match a hotkey string.
        
        Args:
            hotkey_str: Hotkey string like "<ctrl>+<alt>+p".
            
        Returns:
            True if matches, False otherwise.
        """
        # Parse hotkey string
        parts = [p.strip().lower() for p in hotkey_str.split("+")]
        required_keys = set()
        
        for part in parts:
            if part.startswith("<") and part.endswith(">"):
                key_name = part[1:-1]
                # Normalize key names
                if key_name == "ctrl":
                    key_name = "ctrl_l"  # or ctrl_r
                elif key_name == "alt":
                    key_name = "alt_l"  # or alt_r
                elif key_name == "shift":
                    key_name = "shift_l"  # or shift_r
                required_keys.add(f"<{key_name}>")
            else:
                required_keys.add(f"<{part}>")
        
        # Check for ctrl/alt variants
        expanded_required = set()
        for key in required_keys:
            expanded_required.add(key)
            if key == "<ctrl_l>":
                expanded_required.add("<ctrl_r>")
            elif key == "<alt_l>":
                expanded_required.add("<alt_r>")
            elif key == "<shift_l>":
                expanded_required.add("<shift_r>")
        
        # Check if all required keys are pressed
        for key in required_keys:
            if key in ["<ctrl_l>", "<ctrl_r>"]:
                if not ("<ctrl_l>" in self._current_keys or "<ctrl_r>" in self._current_keys):
                    return False
            elif key in ["<alt_l>", "<alt_r>"]:
                if not ("<alt_l>" in self._current_keys or "<alt_r>" in self._current_keys):
                    return False
            elif key in ["<shift_l>", "<shift_r>"]:
                if not ("<shift_l>" in self._current_keys or "<shift_r>" in self._current_keys):
                    return False
            elif key not in self._current_keys:
                return False
        
        return True
    
    def _trigger_action(self, action: str) -> None:
        """Trigger a callback action.
        
        Args:
            action: Action name to trigger.
        """
        if action in self._callbacks:
            try:
                self._callbacks[action]()
            except Exception:
                pass
    
    def update_settings(self, settings: Settings) -> None:
        """Update settings and hotkey definitions.
        
        Args:
            settings: New settings instance.
        """
        self.settings = settings
        self._update_hotkeys()
        
        # Restart if needed
        if self._running and not settings.global_hotkeys_enabled:
            self.stop()
        elif not self._running and settings.global_hotkeys_enabled:
            self.start()
    
    @property
    def is_running(self) -> bool:
        """Check if listener is running."""
        return self._running