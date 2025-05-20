# MidiPlus SmartPad RGB Editor

**Version:** 0.1.0 (Beta)
**Author:** RegularRegs (GitHub: reg0lino)
**Development Assistance:** Google's Gemini 2.5 AI
**Date:** May 20, 2025

A desktop application for Windows, macOS, and Linux, built with Python and PyQt6, designed to control the RGB LEDs of the MidiPlus SmartPad (and potentially compatible 8x8 MIDI controllers that use velocity for color selection). This tool allows for direct pad painting and creation of simple frame-by-frame animations using the SmartPad's 8-color palette.

## Features

*   **MIDI Device Connection:** Auto-detects or allows manual selection of the SmartPad MIDI port.
*   **8x8 Pad Grid:** Visual representation of the SmartPad for direct interaction.
    *   Paint pads with an 8-color palette (Red, Green, Darkblue, Purple, Lightblue, Yellow, White, Off).
    *   Left-click to paint with selected color.
    *   Right-click to set pad to "Off" (erase).
    *   Drag-painting and drag-erasing supported.
*   **Color Palette:** Clearly selectable 8 SmartPad colors + Off.
*   **Static Pad Layouts:**
    *   Save the current 8x8 grid state as a named static layout.
    *   Load saved static layouts onto the grid.
    *   Delete saved layouts.
*   **Animation Sequencer:**
    *   **Frame Management:** Add blank frames or snapshot the current grid as new frames. Duplicate and delete frames.
    *   **Timeline:** Visual timeline with thumbnails of animation frames (supports up to 999 frames, horizontally scrollable).
    *   **Playback Controls:** Play, Pause, Stop animation.
    *   **Speed Control:** Adjustable animation speed (displayed as FPS and ms/frame).
    *   **Looping:** Toggle animation looping.
    *   **File Management:**
        *   Save current animation sequence to a JSON file.
        *   Load animation sequences from JSON files.
        *   "New Animation" clears the current sequence.
        *   Manage saved animations via a dropdown list (Load, Delete).
*   **Dark Theme UI:** Styled for a comfortable user experience.

## Screenshots

*(Consider adding a screenshot like the one you last provided here once the UI is more polished)*
![Screenshot of MidiPlus SmartPad RGB Editor](placeholder_screenshot.png)

## Requirements

*   Python 3.8+
*   PyQt6
*   mido
*   A MidiPlus SmartPad or compatible 8x8 MIDI controller.

(See `requirements.txt` for specific versions)

## Installation & Setup

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/reg0lino/MidiPlusSmartPadRGBEditor.git
    cd MidiPlusSmartPadRGBEditor
    ```
2.  **Create a virtual environment (recommended):**
    ```bash
    python -m venv venv
    # Activate it:
    # Windows:
    venv\Scripts\activate
    # macOS/Linux:
    source venv/bin/activate
    ```
3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
4.  **Run the application:**
    ```bash
    python smartpad_rgb_app.py
    ```

## Usage

1.  Connect your MidiPlus SmartPad to your computer.
2.  Launch the application (`smartpad_rgb_app.py`).
3.  Select the correct MIDI port for your SmartPad from the "MIDI Connection" dropdown and click "Connect". The device pads should clear.
4.  Use the "Color Palette" to select a color.
5.  Click or drag on the 8x8 grid to paint pads. Right-click or select "Off" from the palette to erase.
6.  Use the "Static Pad Layouts" section to save and load full grid designs.
7.  Use the "Animation Studio" and "Animation Controls" to create frame-by-frame animations.
    *   Use "Add" (Snapshot or Blank) to create frames.
    *   Click a frame in the "Animation Frames" timeline to edit it on the main grid.
    *   Use Play/Pause/Stop and speed controls for playback.
    *   Save your animations using the "Save As..." button in the "Animation Studio".

## Planned Features / To-Do (Future)

*   More robust error handling and user feedback.
*   Implementation of standard animator hotkeys (Undo/Redo, Copy/Paste frames, etc.).
*   Multi-frame selection and operations in the timeline.
*   Refined UI/UX elements (e.g., more detailed tooltips, status bar messages).
*   Option to configure "dead pads" on the hardware.
*   Export animations (e.g., as GIF).
*   Packaging as a standalone executable.

## Contributing

Contributions, bug reports, and feature requests are welcome! Please feel free to open an issue or submit a pull request.

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details.

## Acknowledgements

*   Developed by RegularRegs (reg0lino).
*   Initial development and problem-solving significantly assisted by Google's Gemini 2.5 AI.
*   Inspired by the functionality needed for simple MIDI-based LED controllers.