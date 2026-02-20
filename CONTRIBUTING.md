# Contributing to Micsx

Thanks for your interest in contributing to Micsx! This document provides guidelines and instructions for contributing.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Project Structure](#project-structure)
- [Code Style](#code-style)
- [Git Flow](#git-flow)
- [Pull Requests](#pull-requests)
- [Adding New Features](#adding-new-features)
- [Bug Reports](#bug-reports)

## Code of Conduct

Be respectful and inclusive. We welcome contributions from everyone.

## Getting Started

### Prerequisites

- Python 3.10+
- VLC Media Player
- Git

### Development Setup

1. **Fork the repository**

   Click the "Fork" button on GitHub.

2. **Clone your fork**
   ```bash
   git clone https://github.com/YOUR_USERNAME/micsx.git
   cd micsx
   ```

3. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/macOS
   # or
   .\venv\Scripts\activate  # Windows
   ```

4. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt  # Development dependencies
   ```

5. **Run the application**
   ```bash
   python main.py
   ```

## Project Structure

```
micsx/
├── config/           # Configuration and settings
│   ├── settings.py   # Application settings
│   └── theme.py      # Theme definitions
├── data/             # Data handling
│   ├── database.py   # SQLite database operations
│   ├── metadata.py   # Audio metadata extraction
│   └── scanner.py    # File system scanning
├── core/             # Business logic
│   ├── player.py     # Audio player (VLC backend)
│   ├── playlist.py   # Playlist management
│   ├── library.py    # Library management
│   ├── search.py     # Search engine
│   └── hotkeys.py    # Global hotkey handling
├── ui/               # User interface (Textual)
│   ├── app.py        # Main application class
│   ├── screens/      # Screen components
│   │   ├── main.py   # Main playback screen
│   │   ├── library.py # Library browser
│   │   ├── playlists.py # Playlist manager
│   │   └── search.py # Search screen
│   └── widgets/      # Reusable widgets
│       ├── track_list.py  # Track listing
│       ├── player_bar.py  # Player controls
│       └── cover_display.py # Album art
├── main.py           # Application entry point
└── requirements.txt  # Dependencies
```

## Code Style

### Python Conventions

- Follow [PEP 8](https://pep8.org/) style guide
- Use type hints for function parameters and return values
- Write docstrings for all public functions and classes
- Maximum line length: 100 characters

### Example

```python
from typing import Optional, List, Dict, Any


def search_tracks(query: str, limit: int = 50) -> List[Dict[str, Any]]:
    """Search tracks by query string.
    
    Args:
        query: Search query string.
        limit: Maximum number of results.
        
    Returns:
        List of track dictionaries matching the query.
    """
    if not query:
        return []
    
    # Implementation here
    return []
```

### Formatting Tools

We use the following tools:

- **Black** - Code formatter
- **isort** - Import sorter
- **flake8** - Linter
- **mypy** - Type checker

Run before committing:

```bash
black .
isort .
flake8 .
mypy .
```

## Git Flow

### Branches

- `main` - Stable release branch
- `develop` - Development branch
- `feature/*` - New features
- `fix/*` - Bug fixes
- `docs/*` - Documentation updates

### Commit Messages

Use conventional commits:

```
type(scope): description

[optional body]
```

Types:
- `feat` - New feature
- `fix` - Bug fix
- `docs` - Documentation
- `style` - Code style (formatting)
- `refactor` - Code refactoring
- `test` - Adding tests
- `chore` - Maintenance

Examples:
```
feat(player): add crossfade support
fix(database): resolve track duplication issue
docs(readme): update installation instructions
```

### Creating a Feature Branch

```bash
git checkout main
git pull origin main
git checkout -b feature/my-new-feature
```

## Pull Requests

1. **Create a branch** for your changes

2. **Make your changes** following code style guidelines

3. **Test your changes**
   ```bash
   python -m pytest tests/
   ```

4. **Commit your changes**
   ```bash
   git add .
   git commit -m "feat: description of your changes"
   ```

5. **Push to your fork**
   ```bash
   git push origin feature/my-new-feature
   ```

6. **Open a Pull Request**
   - Go to GitHub and create a PR
   - Fill in the PR template
   - Link any related issues

### PR Checklist

- [ ] Code follows project style guidelines
- [ ] Tests pass locally
- [ ] New features have tests
- [ ] Documentation updated if needed
- [ ] Commit messages follow conventions

## Adding New Features

### Adding a New Screen

1. Create file in `ui/screens/`
2. Inherit from `textual.screen.Screen`
3. Define `BINDINGS` for keyboard shortcuts
4. Define `CSS` for styling
5. Implement `compose()` method
6. Register in `ui/app.py` `SCREENS` dict

### Adding a New Widget

1. Create file in `ui/widgets/`
2. Inherit from appropriate Textual widget
3. Define CSS and behavior
4. Export in `ui/widgets/__init__.py`

### Adding a Core Feature

1. Create module in `core/`
2. Implement with clear interface
3. Integrate with `ui/app.py` if needed
4. Add configuration in `config/settings.py`

## Bug Reports

When reporting bugs, include:

1. **Description** - Clear description of the bug
2. **Steps to reproduce** - How to trigger the bug
3. **Expected behavior** - What should happen
4. **Actual behavior** - What actually happens
5. **Environment**:
   - OS and version
   - Python version
   - VLC version
   - Terminal used
6. **Logs** - Any relevant error messages

Use the issue template on GitHub.

## Testing

### Running Tests

```bash
# Run all tests
python -m pytest

# Run with coverage
python -m pytest --cov=. --cov-report=html

# Run specific test file
python -m pytest tests/test_player.py
```

### Writing Tests

- Place tests in `tests/` directory
- Name test files `test_*.py`
- Use pytest fixtures for common setup

```python
import pytest
from core.player import AudioPlayer


@pytest.fixture
def player():
    """Create a player instance for testing."""
    return AudioPlayer()


def test_player_initial_state(player):
    """Test player starts with correct initial state."""
    assert player.volume == 80
    assert player.state == PlayerState.STOPPED
```

## Questions?

Feel free to open an issue for questions or discussions.

---

Thank you for contributing to Micsx! 🎵