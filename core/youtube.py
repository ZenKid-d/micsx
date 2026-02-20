"""YouTube integration using yt-dlp."""

import yt_dlp
from typing import List, Dict, Any, Optional


class YouTubeClient:
    """YouTube integration for searching and streaming videos."""

    def __init__(self):
        """Initialize YouTube client with default options."""
        self.ydl_opts = {
            'format': 'bestaudio/best',
            'extract_audio': True,
            'quiet': True,
            'no_warnings': True,
            'no_playlist': True,
        }

    def search(self, query: str, max_results: int = 20) -> List[Dict[str, Any]]:
        """Search YouTube videos.

        Args:
            query: Search query string.
            max_results: Maximum number of results to return.

        Returns:
            List of video information dictionaries.
        """
        search_opts = self.ydl_opts.copy()
        search_opts['extract_flat'] = True

        try:
            with yt_dlp.YoutubeDL(search_opts) as ydl:
                search_query = f"ytsearch{max_results}:{query}"
                result = ydl.extract_info(search_query, download=False)

                if not result or 'entries' not in result:
                    return []

                videos = []
                for entry in result['entries']:
                    if not entry:
                        continue

                    video_info = {
                        'video_id': entry.get('id', ''),
                        'title': entry.get('title', 'Unknown Title'),
                        'uploader': entry.get('uploader', 'Unknown'),
                        'duration': entry.get('duration', 0),
                        'thumbnail': entry.get('thumbnail', ''),
                        'url': f"https://www.youtube.com/watch?v={entry.get('id', '')}",
                        'view_count': entry.get('view_count', 0),
                    }
                    videos.append(video_info)

                return videos

        except Exception as e:
            print(f"Error searching YouTube: {e}")
            return []

    def get_video_info(self, url_or_id: str) -> Optional[Dict[str, Any]]:
        """Extract metadata and streaming URL from a video.

        Args:
            url_or_id: YouTube video URL or video ID.

        Returns:
            Dictionary with video information including stream URL, or None if failed.
        """
        # Convert video ID to full URL if needed
        if not url_or_id.startswith('http'):
            url_or_id = f"https://www.youtube.com/watch?v={url_or_id}"

        info_opts = self.ydl_opts.copy()

        try:
            with yt_dlp.YoutubeDL(info_opts) as ydl:
                info = ydl.extract_info(url_or_id, download=False)

                if not info:
                    return None

                # Get the best audio stream URL
                stream_url = None
                if 'url' in info:
                    stream_url = info['url']
                elif 'formats' in info:
                    # Find best audio format
                    audio_formats = [f for f in info['formats'] if f.get('acodec') != 'none']
                    if audio_formats:
                        # Sort by audio quality and get the best
                        audio_formats.sort(key=lambda f: f.get('abr', 0) or 0, reverse=True)
                        stream_url = audio_formats[0]['url']

                if not stream_url:
                    return None

                return {
                    'video_id': info.get('id', ''),
                    'title': info.get('title', 'Unknown Title'),
                    'uploader': info.get('uploader', 'Unknown'),
                    'duration': info.get('duration', 0),
                    'thumbnail': info.get('thumbnail', ''),
                    'url': info.get('webpage_url', url_or_id),
                    'stream_url': stream_url,
                    'description': info.get('description', ''),
                    'view_count': info.get('view_count', 0),
                    'like_count': info.get('like_count', 0),
                }

        except Exception as e:
            print(f"Error getting video info: {e}")
            return None

    def get_stream_url(self, video_id: str) -> Optional[str]:
        """Get direct audio stream URL for VLC.

        Args:
            video_id: YouTube video ID.

        Returns:
            Stream URL string, or None if failed.
        """
        video_info = self.get_video_info(video_id)
        if video_info:
            return video_info.get('stream_url')
        return None
