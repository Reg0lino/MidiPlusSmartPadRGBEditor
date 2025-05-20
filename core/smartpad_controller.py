# MidiPlusSmartPadRGBEditor/core/smartpad_controller.py

import mido
import time
from PyQt6.QtCore import QObject, pyqtSignal

# --- SmartPad Configuration (from MidiPlusSmartPadEditor.py findings) ---
SMARTPAD_KEYWORDS = ["smartpad", "midiplus", "usb midi"]
TARGET_MIDI_CHANNEL = 0  # Typically channel 0 (which is MIDI channel 1)

# Mapping of canonical color names to SmartPad MIDI velocities
COLOR_TO_VELOCITY = {
    "OFF": 0,       # Note On Vel 0 for "OFF" command to turn off, Note Off for explicit turn off
    "WHITE": 1,
    "YELLOW": 17,
    "LIGHTBLUE": 33,
    "PURPLE": 49,
    "DARKBLUE": 65,
    "GREEN": 81,
    "RED": 97
}

# MIDI Note numbers for each pad in the 8x8 grid (0-63 mapping to notes)
# Based on the layout from MidiPlusSmartPadEditor.py
# Pad (row, col) -> PAD_GRID_NOTES[row][col]
PAD_GRID_NOTES = [
    [0, 1, 2, 3, 4, 5, 6, 7],         # Row 0 (Top Row)
    [16, 17, 18, 19, 20, 21, 22, 23], # Row 1
    [32, 33, 34, 35, 36, 37, 38, 39], # Row 2
    [48, 49, 50, 51, 52, 53, 54, 55], # Row 3
    [64, 65, 66, 67, 68, 69, 70, 71], # Row 4
    [80, 81, 82, 83, 84, 85, 86, 87], # Row 5
    [96, 97, 98, 99, 100, 101, 102, 103], # Row 6
    [112, 113, 114, 115, 116, 117, 118, 119]  # Row 7 (Bottom Row)
]

# Delay between sending Note Off and subsequent Note On.
# Can be 0.0 if the hardware handles rapid messages well.
# The Tkinter script used 0.02. Let's start with a small configurable value.
DEFAULT_INTER_COMMAND_DELAY = 0.001 # 1 ms, very short. Can be tuned.


class SmartPadController(QObject):
    """
    Handles MIDI communication with the MidiPlus SmartPad.
    """
    connection_status_changed = pyqtSignal(bool, str)  # is_connected, port_name_or_message
    error_occurred = pyqtSignal(str) # For reporting general errors

    def __init__(self, parent=None):
        super().__init__(parent)
        self._midi_port: mido.ports.BaseOutput | None = None
        self._port_name_used: str | None = None
        self.inter_command_delay: float = DEFAULT_INTER_COMMAND_DELAY

    @staticmethod
    def get_available_ports() -> list[str]:
        print("DEBUG SC: get_available_ports() called") # New print
        try:
            ports = mido.get_output_names()
            print(f"DEBUG SC: mido.get_output_names() returned: {ports}") # New print
            return ports
        except Exception as e:
            print(f"DEBUG SC: Error in mido.get_output_names(): {e}") # New print
            # self.error_occurred.emit(f"MIDI Port Discovery Error: {e}") # Careful with emitting signals from static method
            return []

    def connect(self, port_name: str = None) -> bool:
        """
        Connects to the SmartPad.
        If port_name is None, it tries to find a suitable port.
        Returns True on success, False on failure.
        """
        if self.is_connected():
            if port_name == self._port_name_used:
                self.connection_status_changed.emit(True, f"Already connected to {self._port_name_used}")
                return True
            else:
                self.disconnect() # Disconnect if trying to connect to a different port

        target_port_name = port_name
        if not target_port_name:
            available_ports = self.get_available_ports()
            if not available_ports:
                self.error_occurred.emit("No MIDI output ports found.")
                self.connection_status_changed.emit(False, "No MIDI output ports found.")
                return False

            for p_name in available_ports:
                for keyword in SMARTPAD_KEYWORDS:
                    if keyword.lower() in p_name.lower():
                        target_port_name = p_name
                        break
                if target_port_name:
                    break
            
            if not target_port_name:
                msg = "SmartPad port not automatically found. Please select manually."
                self.error_occurred.emit(msg)
                self.connection_status_changed.emit(False, msg)
                return False
            print(f"DEBUG SC: Attempting to connect to target_port_name: '{target_port_name}'") # New print
        
        try:
            self._midi_port = mido.open_output(target_port_name)
            self._port_name_used = target_port_name
            print(f"Successfully opened MIDI port: {self._port_name_used}")
            self.connection_status_changed.emit(True, self._port_name_used)
            self.clear_all_pads_on_device() # Clear pads on successful connection
            return True
        except OSError as e:
            error_msg = f"OSError connecting to {target_port_name}: {e}"
            print(f"Error: {error_msg}")
            self.error_occurred.emit(error_msg)
            self._midi_port = None
            self._port_name_used = None
            self.connection_status_changed.emit(False, f"Failed to open {target_port_name}")
            return False
        except Exception as e:
            error_msg = f"Unexpected error connecting to {target_port_name}: {e}"
            print(f"Error: {error_msg}")
            self.error_occurred.emit(error_msg)
            self._midi_port = None
            self._port_name_used = None
            self.connection_status_changed.emit(False, f"Failed to open {target_port_name}")
            return False


    def disconnect(self, turn_all_off=True) -> None:
        """Closes the MIDI port."""
        if self._midi_port:
            if turn_all_off:
                print("Turning all SmartPad pads off before closing...")
                self.clear_all_pads_on_device(silent=True) # silent to avoid extra prints during disconnect
                if self.inter_command_delay > 0: # Give a moment for last commands
                    time.sleep(self.inter_command_delay * 5 + 0.05) # A small buffer
            try:
                self._midi_port.close()
                print(f"MIDI port {self._port_name_used} closed.")
            except Exception as e:
                print(f"Error closing MIDI port {self._port_name_used}: {e}")
            
        self._midi_port = None
        old_port_name = self._port_name_used
        self._port_name_used = None
        self.connection_status_changed.emit(False, f"Disconnected from {old_port_name}" if old_port_name else "Disconnected")

    def is_connected(self) -> bool:
        """Returns True if the MIDI port is open, False otherwise."""
        return self._midi_port is not None and not self._midi_port.closed

    def get_connected_port_name(self) -> str | None:
        return self._port_name_used

    def _send_raw_midi_message(self, msg: mido.Message):
        """Internal helper to send a message with error handling."""
        if self.is_connected():
            try:
                self._midi_port.send(msg)
                # print(f"Sent: {msg}") # Optional: for heavy debugging
            except Exception as e:
                print(f"Error sending MIDI message {msg}: {e}")
                # Potentially disconnect or mark port as problematic
                # self.error_occurred.emit(f"MIDI send error: {e}")
                # self.disconnect(turn_all_off=False) # Risky to auto-disconnect here
        # else:
            # print(f"MIDI port not open. Cannot send: {msg}")

    def set_pad_color_by_name(self, pad_index_0_63: int, color_name: str, silent: bool = False) -> None:
        """
        Sets the color of a specific pad using its 0-63 index and color name.
        Manages the Note Off -> (optional delay) -> Note On sequence.
        """
        if not self.is_connected():
            if not silent:
                self.error_occurred.emit("Not connected. Cannot set pad color.")
            return

        if not (0 <= pad_index_0_63 < 64):
            if not silent:
                print(f"Warning: Invalid pad_index_0_63: {pad_index_0_63}")
            return

        row = pad_index_0_63 // 8
        col = pad_index_0_63 % 8
        
        try:
            pad_note_number = PAD_GRID_NOTES[row][col]
        except IndexError:
            if not silent:
                print(f"Warning: Could not find note for pad_index {pad_index_0_63} (row:{row}, col:{col})")
            return

        color_name_upper = color_name.upper()
        
        # 1. Always send Note Off first
        off_msg = mido.Message('note_off', channel=TARGET_MIDI_CHANNEL, note=pad_note_number, velocity=0)
        self._send_raw_midi_message(off_msg)
        if not silent:
            print(f"Sent Note Off to pad {pad_index_0_63} (Note {pad_note_number})")

        # 2. If the command is not "OFF", send Note On after a very short delay
        if color_name_upper != "OFF":
            if color_name_upper in COLOR_TO_VELOCITY:
                velocity = COLOR_TO_VELOCITY[color_name_upper]
                
                # Apply delay only if we are going to send an ON message
                if self.inter_command_delay > 0:
                    time.sleep(self.inter_command_delay)

                on_msg = mido.Message('note_on', channel=TARGET_MIDI_CHANNEL, note=pad_note_number, velocity=velocity)
                self._send_raw_midi_message(on_msg)
                if not silent:
                    print(f"Sent Note On to pad {pad_index_0_63} (Note {pad_note_number}), Vel {velocity} for {color_name_upper}")
            else:
                if not silent:
                    print(f"Warning: Color '{color_name}' not found in COLOR_TO_VELOCITY map.")
        # If color_name_upper IS "OFF", we've already sent the Note Off, and that's sufficient.

    def set_all_pads_from_color_names(self, color_names_list: list[str], silent: bool = False) -> None:
        """
        Sets all 64 pads based on a list of color names.
        Sends commands sequentially for each pad.
        """
        if not self.is_connected():
            if not silent:
                self.error_occurred.emit("Not connected. Cannot set all pads.")
            return

        if len(color_names_list) != 64:
            if not silent:
                print(f"Warning: color_names_list must have 64 elements, got {len(color_names_list)}")
            return

        # Option 1: Send all Note Offs, tiny pause, then all Note Ons
        # This might provide a smoother visual update if supported well by the device.
        
        # First, send all Note Off messages
        for i in range(64):
            row, col = i // 8, i % 8
            try:
                pad_note_number = PAD_GRID_NOTES[row][col]
                off_msg = mido.Message('note_off', channel=TARGET_MIDI_CHANNEL, note=pad_note_number, velocity=0)
                self._send_raw_midi_message(off_msg)
            except IndexError:
                if not silent: print(f"Skipping Note Off for invalid pad index {i} in set_all_pads")
                continue
        
        # if not silent: print("Sent all Note Offs for set_all_pads_from_color_names.")

        # Short delay after all Note Offs before sending Note Ons
        if self.inter_command_delay > 0:
            time.sleep(self.inter_command_delay * 2) # Currently 2ms if inter_command_delay is 1ms


        # Then, send all Note On messages for non-"OFF" colors
        for i in range(64):
            color_name = color_names_list[i]
            color_name_upper = color_name.upper()

            if color_name_upper != "OFF" and color_name_upper in COLOR_TO_VELOCITY:
                row, col = i // 8, i % 8
                try:
                    pad_note_number = PAD_GRID_NOTES[row][col]
                    velocity = COLOR_TO_VELOCITY[color_name_upper]
                    on_msg = mido.Message('note_on', channel=TARGET_MIDI_CHANNEL, note=pad_note_number, velocity=velocity)
                    self._send_raw_midi_message(on_msg)
                except IndexError:
                    if not silent: print(f"Skipping Note On for invalid pad index {i} in set_all_pads")
                    continue
            # If color is "OFF", no Note On is needed as Note Off was already sent.

       #  if not silent: print("Finished sending Note Ons for set_all_pads_from_color_names.")


        # --- Original sequential method (kept for reference/fallback if batching causes issues) ---
        # for i, color_name in enumerate(color_names_list):
        #     self.set_pad_color_by_name(i, color_name, silent=True) # Call individual method
        # if not silent:
        #     print("Finished set_all_pads_from_color_names.")


    def clear_all_pads_on_device(self, silent: bool = False) -> None:
        """Turns off all pads on the SmartPad device."""
        if not self.is_connected() and not silent:
            self.error_occurred.emit("Not connected. Cannot clear pads.")
            return
            
        if not silent:
            print("Clearing all pads on SmartPad device...")

        # Efficiently send Note Off to all relevant notes
        all_notes_to_turn_off = set()
        for r in range(8):
            for c in range(8):
                try:
                    all_notes_to_turn_off.add(PAD_GRID_NOTES[r][c])
                except IndexError:
                    pass # Should not happen with 8x8 grid

        for note in sorted(list(all_notes_to_turn_off)): # Sending in order might be slightly cleaner
            off_msg = mido.Message('note_off', channel=TARGET_MIDI_CHANNEL, note=note, velocity=0)
            self._send_raw_midi_message(off_msg)
        
        if not silent:
            print("All pads cleared on device.")

if __name__ == '__main__':
    # Example Usage (requires a connected SmartPad or virtual MIDI port)
    print("SmartPadController Test Script")
    controller = SmartPadController()

    def on_status_change(is_connected, message):
        print(f"Connection Status: {is_connected}, Message: {message}")

    controller.connection_status_changed.connect(on_status_change)
    controller.error_occurred.connect(lambda err_msg: print(f"Controller Error: {err_msg}"))

    ports = SmartPadController.get_available_ports()
    if not ports:
        print("No MIDI ports found. Exiting test.")
        exit()
    
    print("\nAvailable MIDI output ports:")
    for i, p_name in enumerate(ports):
        print(f"  {i}: {p_name}")

    # --- TRY TO AUTO-CONNECT ---
    if controller.connect(): # Tries to find SmartPad automatically
        print("\n--- Auto-connection successful ---")
        
        print("\nTesting single pad colors...")
        controller.set_pad_color_by_name(0, "RED")    # Top-left
        time.sleep(0.5)
        controller.set_pad_color_by_name(7, "GREEN")  # Top-right
        time.sleep(0.5)
        controller.set_pad_color_by_name(56, "BLUE") # Bottom-left (using a name not in our map, should warn) - Changed to DARKBLUE
        controller.set_pad_color_by_name(56, "DARKBLUE")
        time.sleep(0.5)
        controller.set_pad_color_by_name(63, "WHITE") # Bottom-right
        time.sleep(0.5)
        
        print("\nSetting pad 0 to OFF...")
        controller.set_pad_color_by_name(0, "OFF")
        time.sleep(0.5)

        print("\nTesting set_all_pads_from_color_names (checkerboard YELLOW/PURPLE)...")
        checkerboard_colors = []
        for r in range(8):
            for c in range(8):
                if (r + c) % 2 == 0:
                    checkerboard_colors.append("YELLOW")
                else:
                    checkerboard_colors.append("PURPLE")
        controller.set_all_pads_from_color_names(checkerboard_colors)
        time.sleep(2)

        print("\nClearing all pads...")
        controller.clear_all_pads_on_device()
        time.sleep(1)

        controller.disconnect()
    else:
        print("\n--- Auto-connection failed. Please test manually if ports are available. ---")

    print("\nTest finished.")