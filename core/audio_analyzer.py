"""Audio spectrum analyzer for visualization using FFT."""

import numpy as np
from pathlib import Path
from typing import Optional, List, Tuple
from dataclasses import dataclass
import threading
import tempfile
import os

# Try to import audio libraries
try:
    import librosa
    HAS_LIBROSA = True
except ImportError:
    HAS_LIBROSA = False

try:
    from scipy.io import wavfile
    from scipy import signal
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False


@dataclass
class SpectrumFrame:
    """A single frame of spectrum data."""
    bands: List[float]  # Normalized band values (0.0 - 1.0)
    time_ms: int  # Position in track (milliseconds)


class AudioAnalyzer:
    """Analyze audio files for spectrum visualization."""
    
    # Frequency bands for visualization (20 bands)
    # Low frequencies (bass) to high frequencies (treble)
    NUM_BANDS = 20
    
    # Samples per frame (determines time resolution)
    HOP_LENGTH = 512  # ~23ms at 22050Hz sample rate
    
    def __init__(self):
        """Initialize analyzer."""
        self._spectrum_data: List[SpectrumFrame] = []
        self._duration_ms: int = 0
        self._is_analyzed: bool = False
        self._current_track_path: Optional[str] = None
        self._analysis_thread: Optional[threading.Thread] = None
        self._is_analyzing: bool = False
    
    @property
    def is_analyzed(self) -> bool:
        """Check if track has been analyzed."""
        return self._is_analyzed
    
    @property
    def is_analyzing(self) -> bool:
        """Check if analysis is in progress."""
        return self._is_analyzing
    
    @property
    def duration_ms(self) -> int:
        """Get track duration in milliseconds."""
        return self._duration_ms
    
    def analyze_file(self, file_path: str, callback: Optional[callable] = None) -> bool:
        """Analyze an audio file asynchronously.
        
        Args:
            file_path: Path to audio file.
            callback: Optional callback when analysis completes.
            
        Returns:
            True if analysis started, False if already analyzing.
        """
        if self._is_analyzing:
            return False
        
        # Cancel previous analysis if different track
        if self._current_track_path != file_path:
            self._spectrum_data = []
            self._is_analyzed = False
        
        self._current_track_path = file_path
        self._is_analyzing = True
        
        def analyze_thread():
            try:
                data = self._do_analysis(file_path)
                self._spectrum_data = data
                self._is_analyzed = True
            except Exception as e:
                print(f"[AudioAnalyzer] Analysis failed: {e}")
                self._spectrum_data = []
                self._is_analyzed = False
            finally:
                self._is_analyzing = False
                if callback:
                    callback(self._is_analyzed)
        
        self._analysis_thread = threading.Thread(target=analyze_thread, daemon=True)
        self._analysis_thread.start()
        return True
    
    def _do_analysis(self, file_path: str) -> List[SpectrumFrame]:
        """Perform actual FFT analysis on audio file."""
        if HAS_LIBROSA:
            return self._analyze_with_librosa(file_path)
        elif HAS_SCIPY:
            return self._analyze_with_scipy(file_path)
        else:
            print("[AudioAnalyzer] No audio library available (install librosa or scipy)")
            return []
    
    def _analyze_with_librosa(self, file_path: str) -> List[SpectrumFrame]:
        """Analyze using librosa (supports MP3, FLAC, OGG, etc.)."""
        try:
            # Load audio file
            y, sr = librosa.load(file_path, sr=22050, mono=True)
            
            # Calculate duration
            self._duration_ms = int(len(y) / sr * 1000)
            
            # Compute short-time FFT
            stft = np.abs(librosa.stft(y, hop_length=self.HOP_LENGTH, n_fft=2048))
            
            # Convert to frequency bands
            frequencies = librosa.fft_frequencies(sr=sr, n_fft=2048)
            
            # Create logarithmically spaced frequency bands
            bands = self._create_frequency_bands(frequencies, stft.shape[0])
            
            spectrum_frames = []
            frame_duration_ms = int(self.HOP_LENGTH / sr * 1000)
            
            for frame_idx in range(stft.shape[1]):
                # Get magnitude for each band
                band_values = []
                for low_idx, high_idx in bands:
                    band_magnitude = np.mean(stft[low_idx:high_idx, frame_idx])
                    band_values.append(float(band_magnitude))
                
                # Normalize to 0-1 range
                max_val = max(band_values) if band_values else 1.0
                if max_val > 0:
                    band_values = [v / max_val for v in band_values]
                
                # Apply smoothing and boost
                band_values = [min(1.0, v ** 0.7 * 1.2) for v in band_values]
                
                time_ms = frame_idx * frame_duration_ms
                spectrum_frames.append(SpectrumFrame(bands=band_values, time_ms=time_ms))
            
            return spectrum_frames
            
        except Exception as e:
            print(f"[AudioAnalyzer] Librosa analysis error: {e}")
            return []
    
    def _analyze_with_scipy(self, file_path: str) -> List[SpectrumFrame]:
        """Analyze using scipy (WAV only, or convert with ffmpeg)."""
        try:
            # Check if WAV
            if not file_path.lower().endswith('.wav'):
                # Try to convert with ffmpeg
                wav_path = self._convert_to_wav(file_path)
                if wav_path:
                    file_path = wav_path
                else:
                    return []
            
            sample_rate, data = wavfile.read(file_path)
            
            # Convert to mono if stereo
            if len(data.shape) > 1:
                data = np.mean(data, axis=1)
            
            # Normalize
            data = data.astype(np.float32) / np.iinfo(data.dtype).max
            
            self._duration_ms = int(len(data) / sample_rate * 1000)
            
            # Compute spectrogram
            frequencies, times, Sxx = signal.spectrogram(
                data, 
                sample_rate,
                nperseg=2048,
                noverlap=2048 - self.HOP_LENGTH
            )
            
            # Create frequency bands
            bands = self._create_frequency_bands(frequencies, len(frequencies))
            
            spectrum_frames = []
            frame_duration_ms = int(self.HOP_LENGTH / sample_rate * 1000)
            
            for frame_idx in range(Sxx.shape[1]):
                band_values = []
                for low_idx, high_idx in bands:
                    if high_idx <= len(Sxx):
                        band_magnitude = np.mean(Sxx[low_idx:high_idx, frame_idx])
                    else:
                        band_magnitude = np.mean(Sxx[low_idx:, frame_idx])
                    band_values.append(float(band_magnitude))
                
                max_val = max(band_values) if band_values else 1.0
                if max_val > 0:
                    band_values = [v / max_val for v in band_values]
                
                band_values = [min(1.0, v ** 0.7 * 1.2) for v in band_values]
                
                time_ms = frame_idx * frame_duration_ms
                spectrum_frames.append(SpectrumFrame(bands=band_values, time_ms=time_ms))
            
            return spectrum_frames
            
        except Exception as e:
            print(f"[AudioAnalyzer] Scipy analysis error: {e}")
            return []
    
    def _convert_to_wav(self, file_path: str) -> Optional[str]:
        """Convert audio file to WAV using ffmpeg."""
        try:
            import subprocess
            
            # Create temp file
            temp_wav = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
            temp_wav.close()
            
            # Convert with ffmpeg
            result = subprocess.run(
                ['ffmpeg', '-i', file_path, '-y', temp_wav.name],
                capture_output=True,
                timeout=30
            )
            
            if result.returncode == 0:
                return temp_wav.name
            else:
                os.unlink(temp_wav.name)
                return None
                
        except Exception as e:
            print(f"[AudioAnalyzer] FFmpeg conversion failed: {e}")
            return None
    
    def _create_frequency_bands(self, frequencies: np.ndarray, num_bins: int) -> List[Tuple[int, int]]:
        """Create logarithmically spaced frequency band indices.
        
        This creates bands that better match human hearing perception.
        Lower frequencies get more detail, higher frequencies less.
        """
        bands = []
        
        # Logarithmic spacing from ~60Hz to ~12000Hz
        min_freq = 60
        max_freq = min(12000, frequencies[-1] if len(frequencies) > 0 else 12000)
        
        # Create log-spaced frequency boundaries
        log_freqs = np.logspace(np.log10(min_freq), np.log10(max_freq), self.NUM_BANDS + 1)
        
        for i in range(self.NUM_BANDS):
            low_freq = log_freqs[i]
            high_freq = log_freqs[i + 1]
            
            # Find corresponding bin indices
            low_idx = np.searchsorted(frequencies, low_freq)
            high_idx = np.searchsorted(frequencies, high_freq)
            
            # Ensure at least one bin per band
            if high_idx <= low_idx:
                high_idx = low_idx + 1
            
            bands.append((int(low_idx), int(min(high_idx, num_bins))))
        
        return bands
    
    def get_spectrum_at_time(self, time_ms: int) -> List[float]:
        """Get spectrum data at a specific time position.
        
        Args:
            time_ms: Time position in milliseconds.
            
        Returns:
            List of 20 band values (0.0 - 1.0), or default if not analyzed.
        """
        if not self._is_analyzed or not self._spectrum_data:
            # Return default idle animation pattern
            return self._get_idle_pattern(time_ms)
        
        # Find the closest frame
        best_frame = None
        min_diff = float('inf')
        
        for frame in self._spectrum_data:
            diff = abs(frame.time_ms - time_ms)
            if diff < min_diff:
                min_diff = diff
                best_frame = frame
        
        if best_frame:
            return best_frame.bands
        
        return self._get_idle_pattern(time_ms)
    
    def _get_idle_pattern(self, time_ms: int) -> List[float]:
        """Generate idle animation pattern when no track is loaded."""
        import math
        pattern = []
        for i in range(self.NUM_BANDS):
            # Gentle wave pattern
            val = 0.3 + 0.2 * math.sin(time_ms / 500 + i * 0.5)
            pattern.append(max(0.1, min(1.0, val)))
        return pattern
    
    def clear(self) -> None:
        """Clear analysis data."""
        self._spectrum_data = []
        self._is_analyzed = False
        self._current_track_path = None