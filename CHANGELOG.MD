# Changelog

All notable changes to this project will be documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [0.1.0] - 2025-05-20 - Beta Release

### Added
- Initial release of the MidiPlus SmartPad RGB Editor.
- Core functionality for connecting to MidiPlus SmartPad via MIDI.
- 8x8 GUI Pad Grid for direct color painting.
- 8-color palette (+ Off) for color selection.
- Drag-painting and right-click erase on the grid.
- Static Pad Layouts: Save, Load, Delete full 8x8 grid presets.
- Animation Sequencer:
    - Animation Studio for managing saved animation files (New, Load from ComboBox/Dialog, Save As, Delete).
    - Frame Timeline with visual thumbnails (up to 999 frames, horizontally scrollable).
    - Add (Snapshot/Blank), Duplicate, Delete animation frames.
    - Playback controls: Play, Pause, Stop.
    - Adjustable animation speed (FPS & ms/frame display).
    - Loop toggle.
- Dark theme UI based on QSS.
- Persistent window geometry settings.
- User data (layouts, animations) stored in `user_data_smartpad` subdirectory.
- Basic file menu with shortcuts for animation operations.

### Changed
- Increased maximum animation frames to 999.
- Increased maximum target FPS for animations (approx. 140-160 FPS, hardware dependent).
- Improved reliability of drag-painting initiation.
- Corrected file paths for user data storage.
- Resolved various UI bugs related to dialog flags and signal connections.

### Fixed
- Bug where deleting static layouts would cause a TypeError.
- Bug where loading animations from the dropdown list might fail due to filename reconstruction.
- Several `ImportError` and `AttributeError` issues during initial development.
- Ensured animation playback correctly sends "all off" then "all on" MIDI sequences per frame.

### Known Issues / To Implement Next
- Standard animator hotkeys (Undo/Redo, Copy/Paste, etc.).
- Multi-frame selection in the timeline.
- More comprehensive tooltips and status bar feedback.
- Further UI polishing and layout optimization.