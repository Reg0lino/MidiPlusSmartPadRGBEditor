# MidiPlusSmartPadRGBEditor/core/animation_model.py
import json
import os
from PyQt6.QtCore import QObject, pyqtSignal

# --- Default Values ---
DEFAULT_FRAME_DELAY_MS = 200  # Corresponds to 5 FPS
MAX_ANIMATION_FRAMES = 999 # Max frames for SmartPad animation
DEFAULT_COLOR_NAME = "OFF"  # Default color for new pads or invalid colors

# SmartPad specific color palette names (ensure these match SmartPadController and UI)
VALID_COLOR_NAMES = ["OFF", "WHITE", "YELLOW", "LIGHTBLUE", "PURPLE", "DARKBLUE", "GREEN", "RED"]


class AnimationFrameSmartPad:
    """Represents a single frame in a SmartPad animation, storing 64 color names."""
    def __init__(self, color_names: list[str] | None = None):
        if color_names and isinstance(color_names, list) and len(color_names) == 64:
            # Validate each color name
            self.color_names = [cn if cn.upper() in VALID_COLOR_NAMES else DEFAULT_COLOR_NAME for cn in color_names]
        else:
            self.color_names = [DEFAULT_COLOR_NAME] * 64 # Default to all "OFF"

    def set_pad_color_name(self, pad_index_0_63: int, color_name: str):
        if 0 <= pad_index_0_63 < 64:
            upper_color_name = color_name.upper()
            if upper_color_name in VALID_COLOR_NAMES:
                self.color_names[pad_index_0_63] = upper_color_name
            else:
                self.color_names[pad_index_0_63] = DEFAULT_COLOR_NAME
                # print(f"Warning: Invalid color name '{color_name}' for pad {pad_index_0_63}. Set to OFF.")

    def get_pad_color_name(self, pad_index_0_63: int) -> str:
        if 0 <= pad_index_0_63 < 64:
            return self.color_names[pad_index_0_63]
        return DEFAULT_COLOR_NAME # Should not happen if index is always checked

    def get_all_color_names(self) -> list[str]:
        return list(self.color_names) # Return a copy

    def __eq__(self, other):
        if isinstance(other, AnimationFrameSmartPad):
            return self.color_names == other.color_names
        return False


class SmartPadAnimationModel(QObject):
    """
    Manages an animation sequence for the SmartPad.
    Stores frames, playback properties, and handles basic file I/O.
    """
    # Signals for UI updates
    frames_changed = pyqtSignal()  # Emitted when frames are added, deleted, reordered
    frame_content_updated = pyqtSignal(int)  # Emits index of the updated frame
    current_edit_frame_changed = pyqtSignal(int)  # Emits new edit frame index (-1 if none)
    properties_changed = pyqtSignal()  # Emitted when name, delay, or loop status changes
    playback_state_changed = pyqtSignal(bool)  # Emits True if playing, False if paused/stopped

    def __init__(self, name: str = "New Animation", parent: QObject | None = None):
        super().__init__(parent)
        self.name: str = name
        self.frame_delay_ms: int = DEFAULT_FRAME_DELAY_MS
        self.loop: bool = True
        self.frames: list[AnimationFrameSmartPad] = []
        
        self._current_edit_frame_index: int = -1
        self._is_playing: bool = False
        self._playback_frame_index: int = 0 # Current frame index during playback

        self.loaded_filepath: str | None = None
        self.is_modified: bool = False # Track unsaved changes

    def _mark_modified(self, modified_state: bool = True):
        if self.is_modified != modified_state:
            self.is_modified = modified_state
            # print(f"AnimationModel '{self.name}' modified state: {self.is_modified}")
            # Could emit a specific 'modified_status_changed' signal if needed

    def get_frame_count(self) -> int:
        return len(self.frames)

    def get_frame_object(self, index: int) -> AnimationFrameSmartPad | None:
        if 0 <= index < len(self.frames):
            return self.frames[index]
        return None

    def get_current_edit_frame_object(self) -> AnimationFrameSmartPad | None:
        return self.get_frame_object(self._current_edit_frame_index)

    def set_current_edit_frame_index(self, index: int):
        target_index = -1
        if not self.frames:
            target_index = -1
        elif 0 <= index < len(self.frames):
            target_index = index
        elif self.frames: # Index out of bounds but frames exist, select first
            target_index = 0
        
        if self._current_edit_frame_index != target_index:
            self._current_edit_frame_index = target_index
            self.current_edit_frame_changed.emit(self._current_edit_frame_index)

    def get_current_edit_frame_index(self) -> int:
        return self._current_edit_frame_index

    def update_pad_in_current_edit_frame(self, pad_index_0_63: int, color_name: str) -> bool:
        current_frame = self.get_current_edit_frame_object()
        if current_frame:
            # Check if actual change will occur
            old_color = current_frame.get_pad_color_name(pad_index_0_63)
            upper_new_color = color_name.upper()
            if upper_new_color not in VALID_COLOR_NAMES:
                upper_new_color = DEFAULT_COLOR_NAME

            if old_color != upper_new_color:
                current_frame.set_pad_color_name(pad_index_0_63, upper_new_color)
                self.frame_content_updated.emit(self._current_edit_frame_index)
                self._mark_modified()
            return True
        return False

    def add_frame(self, frame_data_or_object: AnimationFrameSmartPad | list[str] | None = None, at_index: int | None = None) -> int:
        """
        Adds a new frame to the animation.
        If frame_data_or_object is None, a blank (all "OFF") frame is added.
        If it's a list of 64 color names, a new frame is created from it.
        If it's an AnimationFrameSmartPad object, a copy is added.
        Returns the index of the newly added frame, or -1 if limit reached.
        """
        if self.get_frame_count() >= MAX_ANIMATION_FRAMES:
            print(f"Cannot add frame: Maximum {MAX_ANIMATION_FRAMES} frames reached.")
            return -1

        new_frame: AnimationFrameSmartPad
        if isinstance(frame_data_or_object, AnimationFrameSmartPad):
            # Create a new instance from the provided object's data to ensure it's a copy
            new_frame = AnimationFrameSmartPad(color_names=frame_data_or_object.get_all_color_names())
        elif isinstance(frame_data_or_object, list):
            new_frame = AnimationFrameSmartPad(color_names=frame_data_or_object)
        else: # None or other, add blank
            new_frame = AnimationFrameSmartPad() # Defaults to all "OFF"

        if at_index is None or not (0 <= at_index <= len(self.frames)):
            self.frames.append(new_frame)
            new_index = len(self.frames) - 1
        else:
            self.frames.insert(at_index, new_frame)
            new_index = at_index
        
        self.set_current_edit_frame_index(new_index)
        self.frames_changed.emit()
        self._mark_modified()
        return new_index

    def delete_frame(self, index: int) -> bool:
        if 0 <= index < len(self.frames):
            del self.frames[index]
            
            # Adjust current_edit_frame_index
            if not self.frames: # No frames left
                new_edit_idx = -1
            elif self._current_edit_frame_index == index: # Deleted the selected frame
                new_edit_idx = min(index, len(self.frames) - 1) if self.frames else -1
            elif self._current_edit_frame_index > index: # Deleted frame before selection
                new_edit_idx = self._current_edit_frame_index - 1
            else: # Deleted frame after selection, index is fine
                new_edit_idx = self._current_edit_frame_index
            
            self.set_current_edit_frame_index(new_edit_idx)
            self.frames_changed.emit()
            self._mark_modified()
            return True
        return False

    def duplicate_frame(self, index: int) -> int:
        """Duplicates the frame at the given index and inserts it after. Returns new index or -1."""
        if self.get_frame_count() >= MAX_ANIMATION_FRAMES:
            print(f"Cannot duplicate frame: Maximum {MAX_ANIMATION_FRAMES} frames reached.")
            return -1
            
        source_frame = self.get_frame_object(index)
        if source_frame:
            # Create a new AnimationFrameSmartPad instance by copying data
            return self.add_frame(frame_data_or_object=source_frame, at_index=index + 1)
        return -1

    def set_name(self, name: str):
        if self.name != name:
            self.name = name
            self.properties_changed.emit()
            self._mark_modified()

    def set_frame_delay_ms(self, delay_ms: int):
        delay_ms = max(20, int(delay_ms)) # Min 20ms (50 FPS max)
        if self.frame_delay_ms != delay_ms:
            self.frame_delay_ms = delay_ms
            self.properties_changed.emit()
            self._mark_modified()
    
    def set_loop(self, loop: bool):
        if self.loop != loop:
            self.loop = loop
            self.properties_changed.emit()
            self._mark_modified()

    # --- Playback ---
    def start_playback(self, start_index: int | None = None):
        if self.get_frame_count() > 0:
            self._is_playing = True
            if start_index is not None and 0 <= start_index < self.get_frame_count():
                self._playback_frame_index = start_index
            elif self._current_edit_frame_index != -1 : # Start from edit frame if no explicit start
                 self._playback_frame_index = self._current_edit_frame_index
            else: # Fallback to 0 if no edit frame and no start_index
                self._playback_frame_index = 0

            self.playback_state_changed.emit(True)
            return True
        self.playback_state_changed.emit(False)
        return False

    def pause_playback(self):
        if self._is_playing:
            self._is_playing = False
            self.playback_state_changed.emit(False)

    def stop_playback(self):
        if self._is_playing or self._playback_frame_index != 0:
            self._is_playing = False
            self._playback_frame_index = 0
            self.playback_state_changed.emit(False)

    def get_is_playing(self) -> bool:
        return self._is_playing

    def get_current_playback_frame_index(self) -> int:
        return self._playback_frame_index

    def step_and_get_playback_frame_colors(self) -> list[str] | None:
        if not self._is_playing or self.get_frame_count() == 0:
            self.stop_playback()
            return None

        frame_obj = self.get_frame_object(self._playback_frame_index)
        if not frame_obj:
            self.stop_playback()
            return None
        
        colors_to_return = frame_obj.get_all_color_names()
        
        self._playback_frame_index += 1
        if self._playback_frame_index >= self.get_frame_count():
            if self.loop:
                self._playback_frame_index = 0
            else:
                self._is_playing = False # Will stop after this frame
                # playback_state_changed will be emitted by MainWindow's timer loop when it sees _is_playing is False

        return colors_to_return

    # --- Serialization ---
    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "frame_delay_ms": self.frame_delay_ms,
            "loop": self.loop,
            "frames": [frame.get_all_color_names() for frame in self.frames]
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'SmartPadAnimationModel | None':
        try:
            model = cls(name=data.get("name", "Untitled Animation"))
            model.frame_delay_ms = data.get("frame_delay_ms", DEFAULT_FRAME_DELAY_MS)
            model.loop = data.get("loop", True)
            
            loaded_frames_data = data.get("frames", [])
            for i, frame_colors_list in enumerate(loaded_frames_data):
                if i >= MAX_ANIMATION_FRAMES:
                    print(f"Warning: Animation file has more than {MAX_ANIMATION_FRAMES} frames. Truncating.")
                    break
                if isinstance(frame_colors_list, list) and len(frame_colors_list) == 64:
                    model.frames.append(AnimationFrameSmartPad(color_names=frame_colors_list))
                else:
                    print(f"Warning: Invalid frame data at index {i} in loaded animation. Skipping.")
            
            model._current_edit_frame_index = 0 if model.frames else -1
            model._mark_modified(False) # Freshly loaded is not modified from file
            return model
        except Exception as e:
            print(f"Error creating SmartPadAnimationModel from dict: {e}")
            return None

    def load_from_file(self, filepath: str) -> bool:
        try:
            with open(filepath, "r") as f:
                data = json.load(f)
            
            # Re-initialize self from dict data
            loaded_model = SmartPadAnimationModel.from_dict(data)
            if loaded_model:
                self.name = loaded_model.name
                self.frame_delay_ms = loaded_model.frame_delay_ms
                self.loop = loaded_model.loop
                self.frames = loaded_model.frames # This is already a list of AnimationFrameSmartPad
                self._current_edit_frame_index = loaded_model.get_current_edit_frame_index()
                
                self.loaded_filepath = filepath
                self._mark_modified(False)
                
                self.frames_changed.emit()
                self.properties_changed.emit()
                self.current_edit_frame_changed.emit(self._current_edit_frame_index)
                return True
            return False
        except json.JSONDecodeError:
            print(f"Error: Could not decode JSON from animation file: {filepath}")
            return False
        except Exception as e:
            print(f"Error loading animation from file {filepath}: {e}")
            return False

    def save_to_file(self, filepath: str) -> bool:
        try:
            data_to_save = self.to_dict()
            with open(filepath, "w") as f:
                json.dump(data_to_save, f, indent=4)
            self.loaded_filepath = filepath
            self._mark_modified(False)
            return True
        except Exception as e:
            print(f"Error saving animation to file {filepath}: {e}")
            return False

    def new_sequence(self, name="New Animation"):
        """Resets the model to a new, empty sequence."""
        self.name = name
        self.frame_delay_ms = DEFAULT_FRAME_DELAY_MS
        self.loop = True
        self.frames.clear()
        self._current_edit_frame_index = -1
        self._is_playing = False
        self._playback_frame_index = 0
        self.loaded_filepath = None
        self._mark_modified(False) # A new sequence is not 'modified' until edited

        self.frames_changed.emit()
        self.properties_changed.emit()
        self.current_edit_frame_changed.emit(self._current_edit_frame_index)


if __name__ == '__main__':
    print("SmartPadAnimationModel Test")
    model = SmartPadAnimationModel("Test Sequence")

    def on_frames_changed(): print("Event: Frames Changed")
    def on_props_changed(): print(f"Event: Properties Changed (Name: {model.name}, Delay: {model.frame_delay_ms}ms)")
    def on_edit_frame_changed(idx): print(f"Event: Edit Frame Changed to {idx}")

    model.frames_changed.connect(on_frames_changed)
    model.properties_changed.connect(on_props_changed)
    model.current_edit_frame_changed.connect(on_edit_frame_changed)

    print(f"Initial: Name='{model.name}', Frames={model.get_frame_count()}, Delay={model.frame_delay_ms}ms")

    idx1 = model.add_frame() # Add blank
    print(f"Added blank frame at index {idx1}. Current edit: {model.get_current_edit_frame_index()}")
    
    frame1_colors = ["RED"] * 32 + ["GREEN"] * 32
    idx2 = model.add_frame(frame1_colors)
    print(f"Added color frame at index {idx2}. Current edit: {model.get_current_edit_frame_index()}")

    print(f"Frame count: {model.get_frame_count()}")

    if model.get_frame_count() > 0:
        model.update_pad_in_current_edit_frame(0, "YELLOW")
        print(f"Updated pad 0 of frame {model.get_current_edit_frame_index()} to YELLOW.")
        print(f"Frame {model.get_current_edit_frame_index()} colors: {model.get_current_edit_frame_object().get_pad_color_name(0)}")

    idx3 = model.duplicate_frame(1) # Duplicate the RED/GREEN frame
    print(f"Duplicated frame 1 to index {idx3}. Frame count: {model.get_frame_count()}")

    model.delete_frame(0) # Delete the first (blank) frame
    print(f"Deleted frame 0. Frame count: {model.get_frame_count()}. Current edit: {model.get_current_edit_frame_index()}")

    model.set_name("My Awesome Animation")
    model.set_frame_delay_ms(100)

    test_file = "test_smartpad_anim.json"
    if model.save_to_file(test_file):
        print(f"Saved to {test_file}")
        
        new_model = SmartPadAnimationModel()
        if new_model.load_from_file(test_file):
            print(f"Loaded '{new_model.name}' with {new_model.get_frame_count()} frames from {test_file}")
            print(f"  Frame 0, Pad 0 color: {new_model.get_frame_object(0).get_pad_color_name(0) if new_model.get_frame_count() > 0 else 'N/A'}")
        else:
            print(f"Failed to load from {test_file}")
        # os.remove(test_file) # Clean up
    else:
        print(f"Failed to save to {test_file}")

    # Test max frames
    print(f"\nTesting max frames ({MAX_ANIMATION_FRAMES})...")
    model.new_sequence("Max Frame Test")
    for i in range(MAX_ANIMATION_FRAMES + 2):
        added_idx = model.add_frame()
        if added_idx == -1:
            print(f"Could not add frame {i+1}, limit reached.")
        else:
            print(f"Added frame {i+1}, index {added_idx}. Count: {model.get_frame_count()}")
    print(f"Final frame count: {model.get_frame_count()}")