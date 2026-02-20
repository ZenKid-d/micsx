"""Audio visualizer widget with real-time spectrum display."""

import random
import math
from typing import List, Optional

from textual.widget import Widget
from textual.reactive import reactive
from textual.message import Message


class AudioVisualizer(Widget):
    """Animated audio visualizer widget using Unicode blocks.
    
    Simulates audio frequency bars using sinusoidal waves
    with random seeds for natural-looking animation.
    """
    
    DEFAULT_CSS = """
    AudioVisualizer {
        height: 3;
        width: 100%;
        content-align: center middle;
        background: $surface;
        padding: 0 2;
    }
    """
    
    # Reactive properties
    is_playing: reactive[bool] = reactive(False)
    
    # Visualizer settings
    NUM_BARS = 24
    MAX_HEIGHT = 8  # Max height in Unicode block levels
    
    # Unicode block characters for different heights (bottom to top)
    BLOCK_CHARS = [' ', '▁', '▂', '▃', '▄', '▅', '▆', '▇', '█']
    
    def __init__(self, **kwargs) -> None:
        """Initialize visualizer."""
        super().__init__(**kwargs)
        
        # Animation state
        self._frame = 0
        self._seed = random.randint(0, 10000)
        self._bar_heights: List[int] = [0] * self.NUM_BARS
        self._target_heights: List[int] = [0] * self.NUM_BARS
        
        # Animation timer
        self._animation_timer = None
    
    def on_mount(self) -> None:
        """Start animation when mounted."""
        self._start_animation()
    
    def on_unmount(self) -> None:
        """Stop animation when unmounted."""
        self._stop_animation()
    
    def _start_animation(self) -> None:
        """Start the animation timer."""
        if self._animation_timer is None:
            self._animation_timer = self.set_interval(0.05, self._update_frame)
    
    def _stop_animation(self) -> None:
        """Stop the animation timer."""
        if self._animation_timer:
            self._animation_timer.stop()
            self._animation_timer = None
    
    def _update_frame(self) -> None:
        """Update animation frame."""
        if not self.is_playing:
            # Smoothly decrease bars when not playing
            for i in range(self.NUM_BARS):
                if self._bar_heights[i] > 0:
                    self._bar_heights[i] = max(0, self._bar_heights[i] - 1)
            self.refresh()
            return
        
        self._frame += 1
        
        # Generate new target heights using multiple sine waves
        for i in range(self.NUM_BARS):
            # Multiple sine waves for more natural movement
            phase = self._frame * 0.15
            
            # Base wave
            base = math.sin(phase + i * 0.5) * 0.5 + 0.5
            
            # Secondary faster wave
            secondary = math.sin(phase * 1.7 + i * 0.3 + self._seed) * 0.3
            
            # Tertiary slow wave for overall movement
            tertiary = math.sin(phase * 0.3 + self._seed * 0.1) * 0.2
            
            # Random variation
            noise = (random.random() - 0.5) * 0.2
            
            # Combine all waves
            combined = base + secondary + tertiary + noise
            
            # Clamp and scale to height
            combined = max(0, min(1, combined))
            self._target_heights[i] = int(combined * self.MAX_HEIGHT)
            
            # Smooth interpolation
            diff = self._target_heights[i] - self._bar_heights[i]
            self._bar_heights[i] += int(diff * 0.4)
        
        self.refresh()
    
    def set_playing(self, playing: bool) -> None:
        """Set playing state.
        
        Args:
            playing: Whether audio is playing.
        """
        self.is_playing = playing
        if playing:
            # Reset seed for new track
            self._seed = random.randint(0, 10000)
    
    def render(self) -> str:
        """Render the visualizer.
        
        Returns:
            Rendered string with animated bars.
        """
        # Build 3 lines of visualization
        lines = []
        
        for line_num in range(3):
            line_parts = []
            bar_height = self.MAX_HEIGHT // 3
            
            for i, height in enumerate(self._bar_heights):
                # Calculate which part of the bar to show
                line_threshold = (3 - line_num) * bar_height
                
                if height >= line_threshold:
                    # Full block
                    line_parts.append('█')
                elif height > line_threshold - bar_height:
                    # Partial block
                    char_index = height - (line_threshold - bar_height) + 1
                    char_index = max(0, min(len(self.BLOCK_CHARS) - 1, char_index))
                    line_parts.append(self.BLOCK_CHARS[char_index])
                else:
                    # Empty
                    line_parts.append(' ')
            
            lines.append(''.join(line_parts))
        
        # Return as multi-line string with primary color
        return '\n'.join(lines)


class MiniVisualizer(Widget):
    """Compact single-line visualizer for player bar.
    
    Supports real-time spectrum data from AudioAnalyzer
    with smooth interpolation between frames.
    """
    
    DEFAULT_CSS = """
    MiniVisualizer {
        height: 1;
        width: 1fr;
        color: $primary;
        content-align: center middle;
    }
    """
    
    is_playing: reactive[bool] = reactive(False)
    
    NUM_BARS = 20
    BLOCK_CHARS = [' ', '▁', '▂', '▃', '▄', '▅', '▆', '▇', '█']
    
    def __init__(self, **kwargs) -> None:
        """Initialize mini visualizer."""
        super().__init__(**kwargs)
        self._frame = 0
        self._seed = random.randint(0, 10000)
        self._animation_timer = None
        
        # Current interpolated heights
        self._bar_heights: List[float] = [0.0] * self.NUM_BARS
        
        # Target heights from spectrum data
        self._target_heights: List[float] = [0.0] * self.NUM_BARS
        
        # Current time position in ms (for spectrum lookup)
        self._current_time_ms: int = 0
    
    def on_mount(self) -> None:
        """Start animation."""
        self._animation_timer = self.set_interval(0.05, self._update_frame)
    
    def on_unmount(self) -> None:
        """Stop animation."""
        if self._animation_timer:
            self._animation_timer.stop()
    
    def _update_frame(self) -> None:
        """Update frame with smooth interpolation."""
        self._frame += 1
        
        # Smooth interpolation towards target heights
        for i in range(self.NUM_BARS):
            diff = self._target_heights[i] - self._bar_heights[i]
            # Faster interpolation when playing, slower when idle
            speed = 0.5 if self.is_playing else 0.15
            self._bar_heights[i] += diff * speed
        
        self.refresh()
    
    def set_playing(self, playing: bool) -> None:
        """Set playing state.
        
        Args:
            playing: Whether audio is playing.
        """
        self.is_playing = playing
        if playing:
            self._seed = random.randint(0, 10000)
    
    def update_spectrum(self, spectrum: Optional[List[float]], time_ms: int = 0) -> None:
        """Update visualizer with spectrum data.
        
        Args:
            spectrum: List of 20 normalized band values (0.0 - 1.0).
            time_ms: Current playback position in milliseconds.
        """
        self._current_time_ms = time_ms
        
        if spectrum and len(spectrum) == self.NUM_BARS:
            # Use real spectrum data - map to character indices
            for i, value in enumerate(spectrum):
                # Scale to block character range
                target = value * (len(self.BLOCK_CHARS) - 1)
                self._target_heights[i] = target
        elif self.is_playing:
            # Fallback to simulated animation when no spectrum data
            self._generate_simulated_frame()
        else:
            # Idle animation
            self._generate_idle_frame()
    
    def _generate_simulated_frame(self) -> None:
        """Generate simulated spectrum when playing but no data."""
        for i in range(self.NUM_BARS):
            phase = self._frame * 0.15
            value = math.sin(phase + i * 0.4 + self._seed) * 0.5 + 0.5
            value += math.sin(phase * 1.3 + i * 0.2) * 0.25
            value += (random.random() - 0.5) * 0.3
            value = max(0, min(1, value))
            self._target_heights[i] = value * (len(self.BLOCK_CHARS) - 1)
    
    def _generate_idle_frame(self) -> None:
        """Generate subtle idle animation."""
        for i in range(self.NUM_BARS):
            phase = self._frame * 0.05
            value = math.sin(phase + i * 0.3) * 0.15 + 0.15
            self._target_heights[i] = value * (len(self.BLOCK_CHARS) - 1)
    
    def render(self) -> str:
        """Render mini visualizer."""
        parts = []
        for height in self._bar_heights:
            char_idx = int(max(0, min(len(self.BLOCK_CHARS) - 1, height)))
            parts.append(self.BLOCK_CHARS[char_idx])
        return ''.join(parts)