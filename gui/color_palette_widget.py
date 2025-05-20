# MidiPlusSmartPadRGBEditor/gui/color_palette_widget.py

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QButtonGroup, QGroupBox, QLabel
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QColor, QPalette # For setting button text color

# --- Color Definitions (should match SmartPadController and UI needs) ---
# UI display colors and order in the palette
UI_COLORS_SMARTPAD = {
    # Color Name: (Display Hex, Text Color Hex for good contrast)
    "RED":       ("#FF0000", "#FFFFFF"),
    "GREEN":     ("#00FF00", "#000000"),
    "DARKBLUE":  ("#00008B", "#FFFFFF"),
    "PURPLE":    ("#800080", "#FFFFFF"),
    "LIGHTBLUE": ("#ADD8E6", "#000000"),
    "YELLOW":    ("#FFFF00", "#000000"),
    "WHITE":     ("#FFFFFF", "#000000"),
    "OFF":       ("#202020", "#FFFFFF")  # Dark grey for "OFF" button
}
PALETTE_ORDER_SMARTPAD = ["RED", "GREEN", "DARKBLUE", "PURPLE", "LIGHTBLUE", "YELLOW", "WHITE", "OFF"]
DEFAULT_SELECTED_COLOR_NAME = "RED"

class ColorPaletteWidget(QGroupBox):
    """
    Widget displaying the SmartPad's 8-color palette (+ OFF) for selection.
    """
    color_selected = pyqtSignal(str)  # Emits the canonical color name (e.g., "RED", "OFF")

    def __init__(self, parent: QWidget | None = None):
        super().__init__("Color Palette", parent)

        self.group_layout = QVBoxLayout(self) # Layout for QGroupBox content
        self.button_group = QButtonGroup(self) # To manage exclusive selection visually
        self.button_group.setExclusive(True)

        self.color_buttons: dict[str, QPushButton] = {}
        self._selected_color_name = DEFAULT_SELECTED_COLOR_NAME

        for color_name in PALETTE_ORDER_SMARTPAD:
            # Ensure color_name is uppercase for dictionary lookup consistency
            upper_color_name = color_name.upper()
            display_hex, text_hex = UI_COLORS_SMARTPAD.get(upper_color_name, ("#000000", "#FFFFFF")) # Fallback
            
            button = QPushButton(color_name.title()) # e.g., "Red", "Lightblue"
            button.setCheckable(True) # Makes it behave like a radio button in a group
            button.setMinimumHeight(30) # Give buttons some decent height

            # Styling the button background and text color
            button.setStyleSheet(f"QPushButton {{ background-color: {display_hex}; border: 1px solid #555; }}"
                                 f"QPushButton:checked {{ border: 2px solid lightgreen; }}" # QSS handles checked state
                                 f"QPushButton:hover {{ border: 1px solid #999; }}")
            
            pal = button.palette()
            pal.setColor(QPalette.ColorRole.ButtonText, QColor(text_hex))
            button.setPalette(pal)
            
            # Pass the original color_name (not upper_color_name) for consistency if needed later
            button.clicked.connect(lambda checked, b=button, name=color_name: self._on_palette_button_clicked(b, name, checked))
            
            self.button_group.addButton(button)
            self.color_buttons[upper_color_name] = button # Store with uppercase key
            self.group_layout.addWidget(button)

        # Initial selection
        if DEFAULT_SELECTED_COLOR_NAME.upper() in self.color_buttons:
            self.color_buttons[DEFAULT_SELECTED_COLOR_NAME.upper()].setChecked(True)
            # No need to emit signal here, as it's initial state.
        
        self.group_layout.addStretch(1) # Push buttons to the top

    def _on_palette_button_clicked(self, button: QPushButton, color_name: str, checked: bool):
        if checked: 
            self._selected_color_name = color_name.upper() # Store and emit uppercase for consistency
            self.color_selected.emit(self._selected_color_name)

    def get_selected_color_name(self) -> str:
        return self._selected_color_name # Returns uppercase

    def set_selected_color_externally(self, color_name: str):
        upper_color_name = color_name.upper()
        if upper_color_name in self.color_buttons:
            current_button = self.color_buttons[upper_color_name]
            if not current_button.isChecked():
                # Setting checked will trigger the _on_palette_button_clicked lambda,
                # which in turn emits the signal and updates self._selected_color_name.
                current_button.setChecked(True) 
            else:
                # If already checked, ensure internal state is consistent
                self._selected_color_name = upper_color_name 
        else:
            print(f"Warning: Tried to set unknown color '{color_name}' externally on palette.")

if __name__ == '__main__':
    from PyQt6.QtWidgets import QApplication # Ensure QApplication is imported
    app = QApplication([]) 
    app.setStyleSheet("""
        QGroupBox { 
            font-weight: bold; 
            border: 1px solid gray; 
            border-radius: 3px; 
            margin-top: 0.5em; 
        }
        QGroupBox::title { 
            subcontrol-origin: margin; 
            subcontrol-position: top center; 
            padding: 0 3px; 
        }
    """)
    widget = ColorPaletteWidget()
    
    widget.status_label_test = QLabel(f"Selected: {widget.get_selected_color_name()}") # Test label
    widget.layout().addWidget(widget.status_label_test) 

    def handle_color_selection(name):
        print(f"Signal received: Color '{name}' selected.")
        widget.status_label_test.setText(f"Selected: {name}")

    widget.color_selected.connect(handle_color_selection)
    
    widget.show()
    app.exec()