"""Main application window using PyQt6."""

from PyQt6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QStackedWidget,
    QMenuBar,
    QMenu,
    QToolBar,
    QStatusBar,
    QMessageBox,
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QAction, QIcon

from config.settings import Settings
from core.player import AudioPlayer
from core.playlist import PlaylistManager
from core.library import LibraryManager


class MainWindow(QMainWindow):
    """Main application window for Micsx."""

    def __init__(
        self,
        settings: Settings,
        player: AudioPlayer,
        playlist_manager: PlaylistManager,
        library_manager: LibraryManager,
    ):
        """Initialize the main window.

        Args:
            settings: Application settings.
            player: Audio player instance.
            playlist_manager: Playlist manager instance.
            library_manager: Library manager instance.
        """
        super().__init__()

        self.settings = settings
        self.player = player
        self.playlist_manager = playlist_manager
        self.library_manager = library_manager

        # Initialize UI
        self._setup_window()
        self._create_menu_bar()
        self._create_tool_bar()
        self._create_status_bar()
        self._create_central_widget()
        self._connect_signals()

    def _setup_window(self) -> None:
        """Setup window properties."""
        self.setWindowTitle("Micsx - Music Player")
        self.setMinimumSize(800, 600)
        self.resize(1200, 800)

    def _create_menu_bar(self) -> None:
        """Create the menu bar."""
        menu_bar = self.menuBar()

        # File menu
        file_menu = menu_bar.addMenu("&File")

        scan_action = QAction("&Scan Library", self)
        scan_action.setShortcut("Ctrl+R")
        scan_action.triggered.connect(self._on_scan_library)
        file_menu.addAction(scan_action)

        file_menu.addSeparator()

        import_playlist_action = QAction("&Import Playlist...", self)
        import_playlist_action.triggered.connect(self._on_import_playlist)
        file_menu.addAction(import_playlist_action)

        export_playlist_action = QAction("&Export Playlist...", self)
        export_playlist_action.triggered.connect(self._on_export_playlist)
        file_menu.addAction(export_playlist_action)

        file_menu.addSeparator()

        quit_action = QAction("&Quit", self)
        quit_action.setShortcut("Ctrl+Q")
        quit_action.triggered.connect(self.close)
        file_menu.addAction(quit_action)

        # View menu
        view_menu = menu_bar.addMenu("&View")

        main_action = QAction("&Main Player", self)
        main_action.setShortcut("Ctrl+1")
        main_action.triggered.connect(lambda: self._switch_panel("main"))
        view_menu.addAction(main_action)

        library_action = QAction("&Library", self)
        library_action.setShortcut("Ctrl+2")
        library_action.triggered.connect(lambda: self._switch_panel("library"))
        view_menu.addAction(library_action)

        playlists_action = QAction("&Playlists", self)
        playlists_action.setShortcut("Ctrl+3")
        playlists_action.triggered.connect(lambda: self._switch_panel("playlists"))
        view_menu.addAction(playlists_action)

        if self.settings.youtube_enabled:
            youtube_action = QAction("&YouTube", self)
            youtube_action.setShortcut("Ctrl+4")
            youtube_action.triggered.connect(lambda: self._switch_panel("youtube"))
            view_menu.addAction(youtube_action)

        # Playback menu
        playback_menu = menu_bar.addMenu("&Playback")

        play_pause_action = QAction("&Play/Pause", self)
        play_pause_action.setShortcut("Space")
        play_pause_action.triggered.connect(self._on_play_pause)
        playback_menu.addAction(play_pause_action)

        next_action = QAction("&Next Track", self)
        next_action.setShortcut("Ctrl+Right")
        next_action.triggered.connect(self._on_next_track)
        playback_menu.addAction(next_action)

        previous_action = QAction("&Previous Track", self)
        previous_action.setShortcut("Ctrl+Left")
        previous_action.triggered.connect(self._on_previous_track)
        playback_menu.addAction(previous_action)

        playback_menu.addSeparator()

        shuffle_action = QAction("&Shuffle", self)
        shuffle_action.setShortcut("Ctrl+S")
        shuffle_action.triggered.connect(self._on_toggle_shuffle)
        playback_menu.addAction(shuffle_action)

        repeat_action = QAction("&Repeat", self)
        repeat_action.setShortcut("Ctrl+R")
        repeat_action.triggered.connect(self._on_toggle_repeat)
        playback_menu.addAction(repeat_action)

        # Help menu
        help_menu = menu_bar.addMenu("&Help")

        about_action = QAction("&About", self)
        about_action.triggered.connect(self._on_about)
        help_menu.addAction(about_action)

    def _create_tool_bar(self) -> None:
        """Create the toolbar."""
        toolbar = QToolBar("Main Toolbar")
        toolbar.setIconSize(QSize(24, 24))
        self.addToolBar(toolbar)

        # Navigation actions
        main_action = QAction("Main", self)
        main_action.triggered.connect(lambda: self._switch_panel("main"))
        toolbar.addAction(main_action)

        library_action = QAction("Library", self)
        library_action.triggered.connect(lambda: self._switch_panel("library"))
        toolbar.addAction(library_action)

        playlists_action = QAction("Playlists", self)
        playlists_action.triggered.connect(lambda: self._switch_panel("playlists"))
        toolbar.addAction(playlists_action)

        if self.settings.youtube_enabled:
            youtube_action = QAction("YouTube", self)
            youtube_action.triggered.connect(lambda: self._switch_panel("youtube"))
            toolbar.addAction(youtube_action)

    def _create_status_bar(self) -> None:
        """Create the status bar."""
        status_bar = QStatusBar()
        self.setStatusBar(status_bar)
        self.status_bar = status_bar
        status_bar.showMessage("Ready")

    def _create_central_widget(self) -> None:
        """Create the central widget with stacked panels."""
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)

        # Stacked widget for panels
        self.stacked_widget = QStackedWidget()
        layout.addWidget(self.stacked_widget)

        # Create panels (will be implemented separately)
        # For now, create placeholder widgets
        self.main_panel = self._create_placeholder_panel("Main Player Panel")
        self.library_panel = self._create_placeholder_panel("Library Panel")
        self.playlists_panel = self._create_placeholder_panel("Playlists Panel")

        self.stacked_widget.addWidget(self.main_panel)
        self.stacked_widget.addWidget(self.library_panel)
        self.stacked_widget.addWidget(self.playlists_panel)

        if self.settings.youtube_enabled:
            self.youtube_panel = self._create_placeholder_panel("YouTube Panel")
            self.stacked_widget.addWidget(self.youtube_panel)

        # Show main panel by default
        self._switch_panel("main")

    def _create_placeholder_panel(self, title: str) -> QWidget:
        """Create a placeholder panel widget.

        Args:
            title: Panel title.

        Returns:
            Placeholder widget.
        """
        from PyQt6.QtWidgets import QLabel

        widget = QWidget()
        layout = QVBoxLayout(widget)
        label = QLabel(title)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet("font-size: 24px; color: #7c3aed;")
        layout.addWidget(label)
        return widget

    def _connect_signals(self) -> None:
        """Connect signals to slots."""
        # Player signals
        self.player.state_changed.connect(self._on_player_state_changed)
        self.player.position_changed.connect(self._on_position_changed)

        # Playlist signals
        self.playlist_manager.track_changed.connect(self._on_track_changed)
        self.playlist_manager.queue_changed.connect(self._on_queue_changed)

        # Library signals
        self.library_manager.scan_progress.connect(self._on_scan_progress)
        self.library_manager.scan_complete.connect(self._on_scan_complete)

    def _switch_panel(self, panel_name: str) -> None:
        """Switch to a different panel.

        Args:
            panel_name: Name of the panel to switch to.
        """
        panel_map = {
            "main": 0,
            "library": 1,
            "playlists": 2,
            "youtube": 3,
        }

        if panel_name in panel_map:
            self.stacked_widget.setCurrentIndex(panel_map[panel_name])
            self.status_bar.showMessage(f"View: {panel_name.title()}")

    # ==================== Menu Action Handlers ====================

    def _on_scan_library(self) -> None:
        """Handle scan library action."""
        from PyQt6.QtCore import QThread

        self.status_bar.showMessage("Scanning library...")

        # Run scan in background thread
        class ScanThread(QThread):
            def __init__(self, library_manager):
                super().__init__()
                self.library_manager = library_manager

            def run(self):
                self.library_manager.scan_library()

        self.scan_thread = ScanThread(self.library_manager)
        self.scan_thread.start()

    def _on_import_playlist(self) -> None:
        """Handle import playlist action."""
        from PyQt6.QtWidgets import QFileDialog

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Import Playlist",
            "",
            "Playlist Files (*.m3u *.m3u8 *.pls);;All Files (*)",
        )

        if file_path:
            # Import logic will be handled by playlists panel
            self.status_bar.showMessage(f"Imported: {file_path}")

    def _on_export_playlist(self) -> None:
        """Handle export playlist action."""
        from PyQt6.QtWidgets import QFileDialog

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Playlist",
            "",
            "M3U Playlist (*.m3u);;M3U8 Playlist (*.m3u8);;PLS Playlist (*.pls)",
        )

        if file_path:
            # Export logic will be handled by playlists panel
            self.status_bar.showMessage(f"Exported: {file_path}")

    def _on_play_pause(self) -> None:
        """Handle play/pause action."""
        if self.player.state.value == "playing":
            self.player.pause()
        else:
            self.player.play()

    def _on_next_track(self) -> None:
        """Handle next track action."""
        next_track = self.playlist_manager.advance()
        if next_track:
            self.player.load_track(next_track)
            self.player.play()

    def _on_previous_track(self) -> None:
        """Handle previous track action."""
        prev_track = self.playlist_manager.go_back()
        if prev_track:
            self.player.load_track(prev_track)
            self.player.play()

    def _on_toggle_shuffle(self) -> None:
        """Handle toggle shuffle action."""
        self.playlist_manager.toggle_shuffle()

    def _on_toggle_repeat(self) -> None:
        """Handle toggle repeat action."""
        self.playlist_manager.toggle_repeat()

    def _on_about(self) -> None:
        """Handle about action."""
        QMessageBox.about(
            self,
            "About Micsx",
            "Micsx - Music Player\n\n"
            "A modern music player with library management,\n"
            "YouTube integration, and playlist support.\n\n"
            "Version: 1.0.0\n"
            "Built with PyQt6",
        )

    # ==================== Signal Handlers ====================

    def _on_player_state_changed(self, state) -> None:
        """Handle player state change."""
        state_name = state.value.capitalize()
        self.status_bar.showMessage(f"Player: {state_name}")

    def _on_position_changed(self, position: float, current_seconds: int) -> None:
        """Handle player position change."""
        # Update seek bar (will be implemented in player controls)
        pass

    def _on_track_changed(self, track: dict) -> None:
        """Handle track change."""
        if track:
            title = track.get("title", "Unknown")
            artist = track.get("artist", "Unknown Artist")
            self.status_bar.showMessage(f"Now Playing: {artist} - {title}")

    def _on_queue_changed(self) -> None:
        """Handle queue change."""
        queue_length = self.playlist_manager.queue_length
        self.status_bar.showMessage(f"Queue: {queue_length} tracks")

    def _on_scan_progress(self, path: str, current: int, total: int) -> None:
        """Handle scan progress."""
        self.status_bar.showMessage(f"Scanning ({current}/{total}): {path}")

    def _on_scan_complete(self, result) -> None:
        """Handle scan complete."""
        from data.scanner import ScanResult
        if hasattr(result, 'added'):
            self.status_bar.showMessage(
                f"Scan complete: {result.added} added, {result.updated} updated, {result.removed} removed"
            )

    def closeEvent(self, event) -> None:
        """Handle window close event."""
        # Save settings
        self.settings.save()

        # Cleanup player
        self.player.cleanup()

        event.accept()
