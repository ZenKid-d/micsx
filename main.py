#!/usr/bin/env python3
"""Micsx - CLI Music Player with beautiful TUI interface."""

import argparse
import sys
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from ui.app import MicsxApp


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        prog="micsx",
        description="🎵 Micsx - CLI Music Player with beautiful TUI interface"
    )
    
    parser.add_argument(
        "path",
        nargs="?",
        help="Path to music directory or file"
    )
    
    parser.add_argument(
        "-v", "--version",
        action="version",
        version="%(prog)s 1.0.0"
    )
    
    parser.add_argument(
        "-s", "--scan",
        action="store_true",
        help="Force library rescan on startup"
    )
    
    parser.add_argument(
        "--no-hotkeys",
        action="store_true",
        help="Disable global hotkeys"
    )
    
    return parser.parse_args()


def main():
    """Main entry point."""
    args = parse_args()
    
    # Determine music path
    music_path = args.path
    
    # If path provided, validate it
    if music_path:
        path = Path(music_path).expanduser().resolve()
        if not path.exists():
            print(f"Error: Path not found: {path}")
            sys.exit(1)
        music_path = str(path)
    
    # Create and run app
    app = MicsxApp(music_path=music_path)
    
    # Apply CLI overrides
    if args.scan:
        app.settings.scan_on_startup = True
    
    if args.no_hotkeys:
        app.settings.global_hotkeys_enabled = False
    
    # Run the app
    try:
        app.run()
    except KeyboardInterrupt:
        pass
    finally:
        print("\n🎵 Thanks for using Micsx!")


if __name__ == "__main__":
    main()