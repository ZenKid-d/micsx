"""Metadata extraction from audio files using mutagen."""

import os
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass

import mutagen
from mutagen.mp3 import MP3
from mutagen.flac import FLAC
from mutagen.oggvorbis import OggVorbis
from mutagen.wavpack import WavPack
from mutagen.mp4 import MP4
from mutagen.wave import WAVE
from mutagen.id3 import ID3


@dataclass
class AudioMetadata:
    """Container for audio metadata."""
    title: Optional[str] = None
    artist: Optional[str] = None
    album: Optional[str] = None
    album_artist: Optional[str] = None
    duration: float = 0.0
    track_number: Optional[int] = None
    disc_number: Optional[int] = None
    genre: Optional[str] = None
    year: Optional[int] = None
    cover_data: Optional[bytes] = None
    cover_mime: Optional[str] = None
    bitrate: Optional[int] = None
    sample_rate: Optional[int] = None
    channels: Optional[int] = None


class MetadataExtractor:
    """Extract metadata from various audio file formats."""
    
    # Mapping of file extensions to mutagen types
    FORMAT_HANDLERS = {
        ".mp3": MP3,
        ".flac": FLAC,
        ".ogg": OggVorbis,
        ".oga": OggVorbis,
        ".wv": WavPack,
        ".m4a": MP4,
        ".mp4": MP4,
        ".m4b": MP4,
        ".wav": WAVE,
    }
    
    @classmethod
    def is_supported(cls, file_path: Path) -> bool:
        """Check if file format is supported."""
        return file_path.suffix.lower() in cls.FORMAT_HANDLERS
    
    @classmethod
    def extract(cls, file_path: Path) -> AudioMetadata:
        """Extract metadata from an audio file.
        
        Args:
            file_path: Path to the audio file.
            
        Returns:
            AudioMetadata object with extracted information.
        """
        suffix = file_path.suffix.lower()
        
        if suffix not in cls.FORMAT_HANDLERS:
            return AudioMetadata(title=file_path.stem)
        
        handler = cls.FORMAT_HANDLERS[suffix]
        
        try:
            audio = handler(file_path)
            return cls._extract_metadata(audio, file_path, suffix)
        except Exception as e:
            # Return basic metadata if extraction fails
            return AudioMetadata(title=file_path.stem)
    
    @classmethod
    def _extract_metadata(cls, audio: mutagen.FileType, file_path: Path, suffix: str) -> AudioMetadata:
        """Extract metadata based on file format."""
        metadata = AudioMetadata()
        metadata.duration = getattr(audio.info, 'length', 0.0)
        metadata.bitrate = getattr(audio.info, 'bitrate', None)
        metadata.sample_rate = getattr(audio.info, 'sample_rate', None)
        metadata.channels = getattr(audio.info, 'channels', None)
        
        if suffix in (".mp3",):
            cls._extract_id3(audio, metadata)
        elif suffix in (".flac", ".ogg", ".oga", ".wv"):
            cls._extract_vorbis(audio, metadata)
        elif suffix in (".m4a", ".mp4", ".m4b"):
            cls._extract_mp4(audio, metadata)
        elif suffix in (".wav",):
            cls._extract_wave(audio, metadata)
        
        # Default title to filename if not found
        if not metadata.title:
            metadata.title = file_path.stem
        
        return metadata
    
    @classmethod
    def _extract_id3(cls, audio: MP3, metadata: AudioMetadata) -> None:
        """Extract metadata from ID3 tags."""
        if not hasattr(audio, 'tags') or audio.tags is None:
            return
        
        tags = audio.tags
        
        # Title
        if "TIT2" in tags:
            metadata.title = str(tags["TIT2"])
        
        # Artist
        if "TPE1" in tags:
            metadata.artist = str(tags["TPE1"])
        
        # Album
        if "TALB" in tags:
            metadata.album = str(tags["TALB"])
        
        # Album Artist
        if "TPE2" in tags:
            metadata.album_artist = str(tags["TPE2"])
        
        # Track number
        if "TRCK" in tags:
            track_str = str(tags["TRCK"])
            if "/" in track_str:
                metadata.track_number = int(track_str.split("/")[0])
            else:
                try:
                    metadata.track_number = int(track_str)
                except ValueError:
                    pass
        
        # Disc number
        if "TPOS" in tags:
            disc_str = str(tags["TPOS"])
            if "/" in disc_str:
                metadata.disc_number = int(disc_str.split("/")[0])
            else:
                try:
                    metadata.disc_number = int(disc_str)
                except ValueError:
                    pass
        
        # Genre
        if "TCON" in tags:
            metadata.genre = str(tags["TCON"])
        
        # Year
        if "TDRC" in tags:
            year_str = str(tags["TDRC"])[:4]
            try:
                metadata.year = int(year_str)
            except ValueError:
                pass
        elif "TYER" in tags:
            try:
                metadata.year = int(str(tags["TYER"]))
            except ValueError:
                pass
        
        # Cover art
        for key in ["APIC:", "APIC"]:
            if key in tags:
                apic = tags[key]
                metadata.cover_data = apic.data
                metadata.cover_mime = apic.mime
                break
    
    @classmethod
    def _extract_vorbis(cls, audio, metadata: AudioMetadata) -> None:
        """Extract metadata from Vorbis comments (FLAC, OGG)."""
        if not hasattr(audio, 'tags') or audio.tags is None:
            return
        
        tags = audio.tags
        
        # Standard Vorbis comment fields
        field_map = {
            "TITLE": "title",
            "ARTIST": "artist",
            "ALBUM": "album",
            "ALBUMARTIST": "album_artist",
            "ALBUM ARTIST": "album_artist",
            "GENRE": "genre",
        }
        
        for key, value in tags.items():
            key_upper = key.upper()
            
            if key_upper in field_map:
                setattr(metadata, field_map[key_upper], str(value[0]) if value else None)
            elif key_upper == "TRACKNUMBER":
                try:
                    metadata.track_number = int(str(value[0]).split("/")[0])
                except (ValueError, IndexError):
                    pass
            elif key_upper == "DISCNUMBER":
                try:
                    metadata.disc_number = int(str(value[0]).split("/")[0])
                except (ValueError, IndexError):
                    pass
            elif key_upper in ("DATE", "YEAR"):
                try:
                    year_str = str(value[0])[:4]
                    metadata.year = int(year_str)
                except (ValueError, IndexError):
                    pass
        
        # Cover art for FLAC
        if hasattr(audio, 'pictures') and audio.pictures:
            picture = audio.pictures[0]
            metadata.cover_data = picture.data
            metadata.cover_mime = picture.mime
    
    @classmethod
    def _extract_mp4(cls, audio: MP4, metadata: AudioMetadata) -> None:
        """Extract metadata from MP4/M4A tags."""
        if not hasattr(audio, 'tags') or audio.tags is None:
            return
        
        tags = audio.tags
        
        # MP4 tag mapping
        if "\xa9nam" in tags:
            metadata.title = str(tags["\xa9nam"][0])
        
        if "\xa9ART" in tags:
            metadata.artist = str(tags["\xa9ART"][0])
        
        if "\xa9alb" in tags:
            metadata.album = str(tags["\xa9alb"][0])
        
        if "aART" in tags:
            metadata.album_artist = str(tags["aART"][0])
        
        if "\xa9gen" in tags:
            metadata.genre = str(tags["\xa9gen"][0])
        
        if "\xa9day" in tags:
            try:
                metadata.year = int(str(tags["\xa9day"][0])[:4])
            except (ValueError, IndexError):
                pass
        
        if "trkn" in tags:
            try:
                metadata.track_number = tags["trkn"][0][0]
            except (IndexError, TypeError):
                pass
        
        if "disk" in tags:
            try:
                metadata.disc_number = tags["disk"][0][0]
            except (IndexError, TypeError):
                pass
        
        # Cover art
        if "covr" in tags:
            cover = tags["covr"][0]
            metadata.cover_data = bytes(cover)
            # MP4 covers are typically JPEG or PNG
            if cover.imageformat == 14:  # PNG
                metadata.cover_mime = "image/png"
            else:  # JPEG
                metadata.cover_mime = "image/jpeg"
    
    @classmethod
    def _extract_wave(cls, audio: WAVE, metadata: AudioMetadata) -> None:
        """Extract metadata from WAV files."""
        # WAV files often have limited metadata
        if hasattr(audio, 'tags') and audio.tags:
            tags = audio.tags
            
            if "TITLE" in tags:
                metadata.title = str(tags["TITLE"][0])
            if "ARTIST" in tags:
                metadata.artist = str(tags["ARTIST"][0])
    
    @classmethod
    def get_duration(cls, file_path: Path) -> float:
        """Get duration of an audio file in seconds."""
        try:
            audio = mutagen.File(file_path)
            if audio:
                return getattr(audio.info, 'length', 0.0)
        except Exception:
            pass
        return 0.0
    
    @classmethod
    def has_embedded_cover(cls, file_path: Path) -> bool:
        """Check if file has embedded cover art."""
        metadata = cls.extract(file_path)
        return metadata.cover_data is not None
    
    @classmethod
    def extract_cover(cls, file_path: Path) -> Optional[Tuple[bytes, str]]:
        """Extract cover art from file.
        
        Returns:
            Tuple of (image_data, mime_type) or None.
        """
        metadata = cls.extract(file_path)
        if metadata.cover_data:
            return (metadata.cover_data, metadata.cover_mime or "image/jpeg")
        return None