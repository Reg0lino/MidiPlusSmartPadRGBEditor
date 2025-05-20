# MidiPlus SmartPad RGB Editor

**Version:** 0.1.1 (Windows Executable Beta)
**Author:** RegularRegs (GitHub: reg0lino)
**Development Assistance:** Google's Gemini 2.5 AI
**Date:** May 20, 2025

A desktop application for Windows (with source code potentially adaptable for macOS/Linux), built with Python and PyQt6. It's designed to control the RGB LEDs of the MidiPlus SmartPad and similar 8x8 MIDI controllers that use velocity for color selection. This tool allows for direct pad painting and creation of simple frame-by-frame animations using the SmartPad's 8-color palette.

This project provides a functional base. While the original author (RegularRegs) may be moving on to other projects (potentially involving disassembling this specific SmartPad for parts!), the source code is provided for the community to use, learn from, and build upon.

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
    *   **File Management (Animation Studio):**
        *   Save current animation sequence to a JSON file (prompts for name).
        *   Load animation sequences from JSON files (via dialog or dropdown).
        *   "New Animation" clears the current sequence.
        *   Manage saved animations via a dropdown list (Load, Delete).
*   **Dark Theme UI:** Styled for a comfortable user experience.
*   **Windows Executable:** Packaged for easier use on Windows without needing a Python environment.

## Screenshots

![Screenshot of MidiPlus SmartPad RGB Editor](https://github.com/user-attachments/assets/dbd04447-624d-4df7-9aee-a084fbaf22e7)

## Requirements

*   **For running from source:**
    *   Python 3.8+
    *   PyQt6
    *   mido
    *   python-rtmidi (for MIDI backend on some systems)
    *   (See `requirements.txt` for specific versions)
*   **For using the Windows Executable:**
    *   Windows 10/11.
*   A MidiPlus SmartPad or compatible 8x8 MIDI controller.

## Installation & Setup

**Option 1: Using the Windows Executable (Recommended for most Windows users)**

1.  Go to the [Releases page](https://github.com/reg0lino/MidiPlusSmartPadRGBEditor/releases) of this repository.
2.  Download the latest `SmartPadEditor_Windows.zip` (or similar) file.
3.  Extract the ZIP file to a folder on your computer.
4.  Navigate into the extracted folder (e.g., `SmartPadEditor`) and run `SmartPadEditor.exe`.

**Option 2: Running from Source (For developers or other platforms)**

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
2.  Launch the application (`SmartPadEditor.exe` or `python smartpad_rgb_app.py`).
3.  Select the correct MIDI port for your SmartPad from the "MIDI Connection" dropdown and click "Connect". The device pads should clear.
4.  Use the "Color Palette" to select a color.
5.  Click or drag on the 8x8 grid to paint pads. Right-click or select "Off" from the palette to erase.
6.  Use the "Static Pad Layouts" section to save and load full grid designs.
7.  Use the "Animation Studio" and "Animation Controls" to create frame-by-frame animations.
    *   Use "Add" (Snapshot or Blank) to create frames.
    *   Click a frame in the "Animation Frames" timeline to edit it on the main grid.
    *   Use Play/Pause/Stop and speed controls for playback.
    *   Save your animations using the "Save As..." button in the "Animation Studio".

## Future Development & Contributing

NONE. I have used AI and developed this application to a functional beta state (v0.1.1) and is likely concluding direct feature development due to other projects.
(Like taking it apart for to make a DIY robot. lol)
Please feel free to take the code and build on it. I highly recommend using Gemini 2.5 if you are new to coding. 

**The project is open for community contributions!** If you'd like to expand on it, here are some ideas that were considered or would be valuable additions:

*   **Standard Animator Hotkeys:** Undo/Redo, Copy/Paste frames, etc.
*   **Multi-Frame Selection:** For batch operations in the timeline (delete, duplicate, copy/paste multiple frames at once).
*   **Enhanced Tooltips & Status Bar:** More descriptive feedback throughout the UI.
*   **UI Polishing:** Further refinement of layouts and visual elements.
*   **"Dead Pad" Configuration:** A way for users to mark specific pads on their hardware as unresponsive so the GUI can reflect this.
*   **Animation Export:** e.g., as an animated GIF.
*   **Cross-Platform Executables:** Creating bundled versions for macOS and Linux.
*   **More Robust Error Handling.**

Contributions, bug reports, and feature requests are welcome! Please feel free to open an issue or submit a pull request.

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details.

## Acknowledgements

*   Developed by RegularRegs (reg0lino).
*   Initial development and problem-solving significantly assisted by Google's Gemini 2.5 AI.
*   Inspired by the functionality needed for simple MIDI-based LED controllers.