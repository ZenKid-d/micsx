# Changelog

All notable changes to Micsx will be documented in this file.

## [Unreleased]

### Added
- **Popup Notifications** - Toast notifications for player actions (play/pause, next/prev, shuffle, repeat, volume, seek)
- **Remove from Queue** - Press `x` or `Delete` to remove selected track from queue with notification
- **Track Index Numbers** - Display track numbers (1., 2., 3., ...) in the queue list
- **Playing Track Highlight** - Currently playing track is highlighted with cyan color and ▶ icon

### Changed
- **Improved Player Bar Design** - Larger height, better padding, thick primary color border
- **Improved Sidebar Design** - Added border-right separator, better spacing
- **Improved Track List Design** - Italic artist names, better color contrast
- **Removed Repeat All Mode** - Simplified repeat to OFF/ONE modes only

### Fixed
- **Auto-play Next Track** - Fixed VLC event handling using `call_from_thread` for thread-safe UI updates
- **CSS Validation** - Removed unsupported `border-radius` property

## [0.1.0] - Initial Release

### Added
- **TUI Interface** - Beautiful terminal interface built with Textual
- **Audio Playback** - MP3, FLAC, OGG, WAV, M4A support via VLC
- **Library Management** - Automatic scanning and metadata extraction
- **SQLite Database** - Persistent storage for track metadata
- **Cover Art Display** - Album artwork in Kitty terminal
- **Vim-like Navigation** - W/S/A/D keys for movement and seek
- **Playback Controls** - Play/pause, next/prev, shuffle, repeat one
- **Volume Control** - Increase/decrease volume, mute toggle
- **Seek Controls** - Forward/backward 5 seconds
- **Cross-platform** - Linux and Windows support