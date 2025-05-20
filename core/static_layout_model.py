# MidiPlusSmartPadRGBEditor/core/static_layout_model.py
import json
import os
import re
from PyQt6.QtCore import QObject, pyqtSignal

# Constants from animation_model or defined similarly for consistency
DEFAULT_COLOR_NAME = "OFF"
VALID_COLOR_NAMES = ["OFF", "WHITE", "YELLOW", "LIGHTBLUE", "PURPLE", "DARKBLUE", "GREEN", "RED"]
USER_LAYOUTS_SUBDIR = "user_static_layouts" # Subdirectory within a base path for user layouts

class StaticLayoutModel(QObject):
    """
    Manages saving, loading, and deleting static 8x8 pad layouts for the SmartPad.
    Layouts are stored as JSON files containing a list of 64 color names.
    """
    layouts_list_changed = pyqtSignal() # Emitted when layouts are added or deleted
    error_occurred = pyqtSignal(str)    # For reporting errors

    def __init__(self, base_storage_path: str, parent: QObject | None = None):
        super().__init__(parent)
        self.layouts_dir = os.path.join(base_storage_path, USER_LAYOUTS_SUBDIR)
        os.makedirs(self.layouts_dir, exist_ok=True)
        # print(f"StaticLayoutModel: Using layout directory: {self.layouts_dir}")

    def _sanitize_filename(self, name: str) -> str:
        """Sanitizes a string to be a valid filename (and internal key)."""
        name = str(name).strip()
        # Remove invalid characters, replace spaces/multiple hyphens with single underscore
        name = re.sub(r'[^\w\s-]', '', name)
        name = re.sub(r'[-\s]+', '_', name)
        return name.lower() # Use lowercase for consistency in filenames

    def _get_filepath(self, layout_name_sanitized: str) -> str:
        """Constructs the full filepath for a given sanitized layout name."""
        return os.path.join(self.layouts_dir, f"{layout_name_sanitized}.json")

    def get_available_layout_names(self) -> list[str]:
        """
        Scans the layouts directory and returns a list of user-friendly layout names.
        Reads the 'name' field from the JSON if available, otherwise uses filename.
        """
        available_layouts = {} # display_name: sanitized_filename
        if not os.path.isdir(self.layouts_dir):
            return []

        for filename in os.listdir(self.layouts_dir):
            if filename.endswith(".json"):
                sanitized_name_from_file = filename[:-5] # Remove .json
                filepath = self._get_filepath(sanitized_name_from_file)
                try:
                    with open(filepath, 'r') as f:
                        data = json.load(f)
                    # Prefer display name from JSON, fallback to a cleaned-up filename
                    display_name = data.get("display_name", sanitized_name_from_file.replace("_", " ").title())
                    available_layouts[display_name] = sanitized_name_from_file
                except (json.JSONDecodeError, IOError, KeyError) as e:
                    print(f"Warning: Could not read or parse layout file {filename}: {e}. Skipping.")
                    # Fallback to using sanitized filename as display name if file is problematic but exists
                    # display_name = sanitized_name_from_file.replace("_", " ").title()
                    # available_layouts[display_name] = sanitized_name_from_file


        # Sort by display name for user convenience
        return sorted(available_layouts.keys())


    def save_layout(self, display_name: str, layout_color_names: list[str]) -> bool:
        """
        Saves a layout.
        Args:
            display_name (str): The user-friendly name for the layout.
            layout_color_names (list[str]): A list of 64 SmartPad color names.
        Returns:
            bool: True if successful, False otherwise.
        """
        if not display_name.strip():
            self.error_occurred.emit("Layout name cannot be empty.")
            return False

        if not (isinstance(layout_color_names, list) and len(layout_color_names) == 64):
            self.error_occurred.emit("Invalid layout data: Must be a list of 64 color names.")
            return False

        # Validate all color names in the list
        validated_colors = []
        for i, cn in enumerate(layout_color_names):
            upper_cn = cn.upper()
            if upper_cn in VALID_COLOR_NAMES:
                validated_colors.append(upper_cn)
            else:
                # print(f"Warning: Invalid color '{cn}' at index {i} in save_layout. Using OFF.")
                validated_colors.append(DEFAULT_COLOR_NAME)
        
        sanitized_filename_base = self._sanitize_filename(display_name)
        if not sanitized_filename_base: # If sanitization results in empty string
            self.error_occurred.emit("Invalid layout name after sanitization.")
            return False
            
        filepath = self._get_filepath(sanitized_filename_base)

        data_to_save = {
            "display_name": display_name.strip(), # Store the original user-friendly name
            "layout_data": validated_colors
        }

        try:
            with open(filepath, 'w') as f:
                json.dump(data_to_save, f, indent=4)
            self.layouts_list_changed.emit()
            return True
        except IOError as e:
            error_msg = f"Error saving layout '{display_name}' to {filepath}: {e}"
            print(error_msg)
            self.error_occurred.emit(error_msg)
            return False

    def load_layout(self, display_name_or_sanitized_name: str) -> list[str] | None:
        """
        Loads a layout's color data.
        Args:
            display_name_or_sanitized_name (str): The user-friendly name or the sanitized filename base.
        Returns:
            list[str] | None: A list of 64 color names if successful, None otherwise.
        """
        sanitized_name_to_try = self._sanitize_filename(display_name_or_sanitized_name)
        filepath = self._get_filepath(sanitized_name_to_try)

        if not os.path.exists(filepath):
            # Try to find it by iterating if display_name was given
            all_layouts = self.get_available_layout_names() # This gives display names
            found_sanitized = None
            for dn in all_layouts:
                if dn.lower() == display_name_or_sanitized_name.lower(): # Case-insensitive match on display name
                    # Need to re-derive sanitized name from this display name if it was found
                    # This is a bit indirect. Ideally, get_available_layout_names would return a dict.
                    # For now, let's assume the sanitized name from display name is what we need.
                    found_sanitized = self._sanitize_filename(dn)
                    break
            if found_sanitized:
                filepath = self._get_filepath(found_sanitized)
            else:
                # self.error_occurred.emit(f"Layout '{display_name_or_sanitized_name}' not found.")
                return None
        
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            
            layout_data = data.get("layout_data")
            if isinstance(layout_data, list) and len(layout_data) == 64:
                # Further validation of color names within the loaded data
                validated_colors = [cn if cn.upper() in VALID_COLOR_NAMES else DEFAULT_COLOR_NAME for cn in layout_data]
                return validated_colors
            else:
                error_msg = f"Invalid data format in layout file: {filepath}"
                print(error_msg)
                self.error_occurred.emit(error_msg)
                return None
        except (json.JSONDecodeError, IOError, KeyError) as e:
            error_msg = f"Error loading layout '{display_name_or_sanitized_name}' from {filepath}: {e}"
            print(error_msg)
            self.error_occurred.emit(error_msg)
            return None

    def delete_layout(self, display_name_or_sanitized_name: str) -> bool:
        """
        Deletes a layout file.
        Args:
            display_name_or_sanitized_name (str): The user-friendly name or sanitized filename base.
        Returns:
            bool: True if successful or file didn't exist, False on error.
        """
        sanitized_name_to_delete = self._sanitize_filename(display_name_or_sanitized_name)
        filepath = self._get_filepath(sanitized_name_to_delete)
        
        # If display name was passed, we need to ensure we get the correct sanitized filename
        # This is tricky if get_available_layout_names() only returns display names.
        # A robust way is to iterate, find the matching display name, then get its true sanitized filename.
        # For now, this assumes that sanitizing the passed name is sufficient.
        # If the combo box stores (display_name, sanitized_name_key) this becomes easier.

        if not os.path.exists(filepath):
            # Try to find it by iterating display names if a non-sanitized name was passed
            all_layouts = self.get_available_layout_names()
            found = False
            for dn in all_layouts:
                if dn.lower() == display_name_or_sanitized_name.lower():
                    filepath_to_delete_by_display_name = self._get_filepath(self._sanitize_filename(dn))
                    if os.path.exists(filepath_to_delete_by_display_name):
                        filepath = filepath_to_delete_by_display_name # Use this exact path
                        found = True
                        break
            if not found: # Still not found after checking display names
                # self.error_occurred.emit(f"Layout '{display_name_or_sanitized_name}' not found for deletion.")
                return True # File doesn't exist, so "deletion" is effectively done

        try:
            os.remove(filepath)
            self.layouts_list_changed.emit()
            return True
        except OSError as e:
            error_msg = f"Error deleting layout file {filepath}: {e}"
            print(error_msg)
            self.error_occurred.emit(error_msg)
            return False

if __name__ == '__main__':
    print("StaticLayoutModel Test")
    # Create a temporary directory for testing
    test_base_path = "_test_static_layouts_storage"
    if not os.path.exists(test_base_path):
        os.makedirs(test_base_path)

    model = StaticLayoutModel(base_storage_path=test_base_path)

    def on_list_changed():
        print("Event: Layouts list changed. Current layouts:")
        names = model.get_available_layout_names()
        if names:
            for name in names: print(f"  - {name}")
        else:
            print("  (No layouts)")

    def on_error(err_msg):
        print(f"Model Error: {err_msg}")

    model.layouts_list_changed.connect(on_list_changed)
    model.error_occurred.connect(on_error)

    print(f"Layouts directory: {model.layouts_dir}")
    on_list_changed() # Initial list

    # Test save
    layout1_data = ["RED"] * 64
    layout2_data = ["GREEN" if i % 2 == 0 else "BLUE" for i in range(64)] # Typo: BLUE not in VALID_COLOR_NAMES; should default
    layout2_data_corrected = ["GREEN" if i % 2 == 0 else "DARKBLUE" for i in range(64)]


    print("\nSaving 'My First Layout'...")
    model.save_layout("My First Layout", layout1_data)
    
    print("\nSaving 'Another Cool Layout'...")
    model.save_layout("Another Cool Layout", layout2_data_corrected)
    
    print("\nSaving layout with invalid color names (should be corrected to OFF)...")
    invalid_color_data = ["RED", "NOT_A_COLOR", "GREEN"] + ["OFF"]*61
    model.save_layout("Test Invalid Colors", invalid_color_data)


    # Test load
    print("\nLoading 'My First Layout'...")
    loaded_data1 = model.load_layout("My First Layout")
    if loaded_data1:
        print(f"  Loaded {len(loaded_data1)} colors. First color: {loaded_data1[0]}")
    else:
        print("  Failed to load.")

    print("\nLoading 'Test Invalid Colors'...")
    loaded_invalid_data = model.load_layout("Test Invalid Colors")
    if loaded_invalid_data:
        print(f"  Loaded {len(loaded_invalid_data)} colors for 'Test Invalid Colors'. Second color (should be OFF): {loaded_invalid_data[1]}")

    print("\nLoading non-existent layout...")
    model.load_layout("Non Existent Layout") # Should emit error or return None

    # Test delete
    print("\nDeleting 'My First Layout'...")
    model.delete_layout("My First Layout")
    
    print("\nAttempting to delete already deleted/non-existent layout...")
    model.delete_layout("My First Layout") # Should be fine, file is gone

    on_list_changed() # Show list after deletions

    # Clean up test directory (optional)
    # import shutil
    # print(f"\nCleaning up test directory: {test_base_path}")
    # shutil.rmtree(test_base_path)
    print("\nTest finished. You may need to manually delete the '_test_static_layouts_storage' directory.")