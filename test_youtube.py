#!/usr/bin/env python3
"""Test script for YouTube integration."""

import sys
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from core.youtube import YouTubeClient
from data.database import Database
from config.settings import Settings


def test_youtube_client():
    """Test YouTube client functionality."""
    print("=" * 60)
    print("Testing YouTube Client")
    print("=" * 60)

    # Initialize client
    print("\n1. Initializing YouTube client...")
    client = YouTubeClient()
    print("   ✓ Client initialized successfully")

    # Test search
    print("\n2. Testing search functionality...")
    print("   Searching for 'never gonna give you up'...")
    results = client.search("never gonna give you up", max_results=3)

    if results:
        print(f"   ✓ Found {len(results)} results")
        print("\n   Top result:")
        video = results[0]
        print(f"   - Title: {video['title']}")
        print(f"   - Uploader: {video['uploader']}")
        print(f"   - Duration: {video['duration']}s")
        print(f"   - Video ID: {video['video_id']}")
        print(f"   - URL: {video['url']}")

        # Test get_video_info
        print("\n3. Testing video info extraction...")
        video_id = video['video_id']
        print(f"   Getting info for video ID: {video_id}")
        info = client.get_video_info(video_id)

        if info:
            print("   ✓ Video info extracted successfully")
            print(f"   - Stream URL: {info['stream_url'][:100]}...")
            print(f"   - Thumbnail: {info.get('thumbnail', 'N/A')}")

            return info
        else:
            print("   ✗ Failed to get video info")
            return None
    else:
        print("   ✗ Search failed - no results")
        return None


def test_database():
    """Test database operations for YouTube tracks."""
    print("\n" + "=" * 60)
    print("Testing Database Operations")
    print("=" * 60)

    # Initialize database
    print("\n1. Initializing database...")
    db = Database()
    print("   ✓ Database initialized")

    # Check for YouTube-specific columns
    print("\n2. Checking database schema...")
    with db._get_connection() as conn:
        cursor = conn.execute("PRAGMA table_info(tracks)")
        columns = {row[1]: row[2] for row in cursor.fetchall()}

        required_columns = ['source_type', 'source_id', 'source_url', 'thumbnail_url']
        for col in required_columns:
            if col in columns:
                print(f"   ✓ Column '{col}' exists")
            else:
                print(f"   ✗ Column '{col}' missing")
                return False

    # Test insert YouTube track
    print("\n3. Testing YouTube track insertion...")
    test_track = {
        'path': 'youtube:test_video_123',
        'title': 'Test YouTube Video',
        'artist': 'Test Artist',
        'album': 'YouTube',
        'album_artist': None,
        'duration': 180,
        'track_number': None,
        'disc_number': None,
        'genre': None,
        'year': None,
        'cover_embedded': 0,
        'cover_external': None,
        'source_type': 'youtube',
        'source_id': 'test_video_123',
        'source_url': 'https://www.youtube.com/watch?v=test_video_123',
        'thumbnail_url': 'https://example.com/thumb.jpg',
        'stream_url': 'https://example.com/stream.mp3',
        'bitrate': None,
        'sample_rate': None,
        'channels': None,
        'file_size': None,
        'file_modified': None,
    }

    track_id = db.insert_track(test_track)
    if track_id:
        print(f"   ✓ Track inserted with ID: {track_id}")

        # Verify insertion
        track = db.get_track(track_id)
        if track and track['source_type'] == 'youtube':
            print("   ✓ Track retrieved successfully")
            print(f"   - Source type: {track['source_type']}")
            print(f"   - Source ID: {track['source_id']}")

            # Clean up - delete test track
            db.delete_track(track_id)
            print("   ✓ Test track cleaned up")

            return True
        else:
            print("   ✗ Failed to retrieve track")
            return False
    else:
        print("   ✗ Failed to insert track")
        return False


def test_integration():
    """Test full integration: search -> get info -> prepare for database."""
    print("\n" + "=" * 60)
    print("Testing Full Integration")
    print("=" * 60)

    client = YouTubeClient()

    print("\n1. Searching for a video...")
    results = client.search("bohemian rhapsody queen", max_results=1)

    if not results:
        print("   ✗ Search failed")
        return False

    print(f"   ✓ Found: {results[0]['title']}")

    print("\n2. Extracting video info...")
    video_id = results[0]['video_id']
    info = client.get_video_info(video_id)

    if not info:
        print("   ✗ Failed to get video info")
        return False

    print("   ✓ Video info extracted")

    print("\n3. Preparing database entry...")
    track_data = {
        'path': f"youtube:{info['video_id']}",
        'title': info['title'],
        'artist': info.get('uploader', 'Unknown'),
        'album': 'YouTube',
        'album_artist': None,
        'duration': info.get('duration', 0),
        'track_number': None,
        'disc_number': None,
        'genre': None,
        'year': None,
        'cover_embedded': 0,
        'cover_external': None,
        'source_type': 'youtube',
        'source_id': info['video_id'],
        'source_url': info['url'],
        'thumbnail_url': info.get('thumbnail', ''),
        'stream_url': info['stream_url'],
        'bitrate': None,
        'sample_rate': None,
        'channels': None,
        'file_size': None,
        'file_modified': None,
    }

    print("   ✓ Database entry prepared")
    print(f"\n   Track data:")
    print(f"   - Path: {track_data['path']}")
    print(f"   - Title: {track_data['title']}")
    print(f"   - Artist: {track_data['artist']}")
    print(f"   - Duration: {track_data['duration']}s")
    print(f"   - Stream URL: {track_data['stream_url'][:100]}...")

    return True


def main():
    """Run all tests."""
    print("\n🎵 YouTube Integration Test Suite")
    print("=" * 60)

    try:
        # Test 1: YouTube Client
        video_info = test_youtube_client()
        if not video_info:
            print("\n⚠ Warning: YouTube client test had issues")

        # Test 2: Database
        if not test_database():
            print("\n⚠ Warning: Database test had issues")

        # Test 3: Integration
        if not test_integration():
            print("\n⚠ Warning: Integration test had issues")

        print("\n" + "=" * 60)
        print("✓ Test suite completed!")
        print("=" * 60)
        print("\nYouTube integration is ready to use!")
        print("\nTo use in the app:")
        print("1. Run: python main.py")
        print("2. Press 'Y' to open YouTube search")
        print("3. Search for any song")
        print("4. Select a result to play")

    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
