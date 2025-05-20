# MidiPlusSmartPadRGBEditor/gui/pad_grid_widget.py

from PyQt6.QtWidgets import QWidget, QGridLayout, QPushButton, QSizePolicy, QFrame, QApplication
from PyQt6.QtCore import pyqtSignal, Qt, QSize
from PyQt6.QtGui import QMouseEvent, QColor

# --- Pad Grid Constants ---
GRID_ROWS = 8
GRID_COLS = 8
PAD_BUTTON_SIZE = 40  # Adjust for desired square size
PAD_SPACING = 2

# --- Color Definitions (consistent with ColorPaletteWidget and SmartPadController) ---
# Only need the display hex for GUI button background here
UI_COLORS_GRID_DISPLAY = {
    "RED": "#FF0000", "GREEN": "#00FF00", "DARKBLUE": "#00008B",
    "PURPLE": "#800080", "LIGHTBLUE": "#ADD8E6", "YELLOW": "#FFFF00",
    "WHITE": "#FFFFFF", "OFF": "#303030" # Slightly lighter than palette 'OFF' for visibility
}
DEFAULT_PAD_COLOR_NAME_ON_GRID = "OFF"


class PadButton(QPushButton):
    """Custom QPushButton for a single pad in the grid."""

    def __init__(self, row: int, col: int, parent: QWidget | None = None):
        super().__init__("", parent)
        self.row = row
        self.col = col
        self._current_color_name_gui = DEFAULT_PAD_COLOR_NAME_ON_GRID # Initialize stored color
        self.setFixedSize(PAD_BUTTON_SIZE, PAD_BUTTON_SIZE)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        # setMouseTracking(True) on individual PadButtons might not be necessary
        # if PadGridWidget handles all tracking.

    # Override mouse events to ensure they are handled by the parent PadGridWidget
    # for consistent drag-painting behavior.
    # By calling event.ignore(), we pass the event up the parent widget chain.
    # PadGridWidget's event handlers will then process it.

    def mousePressEvent(self, event: QMouseEvent):
        # print(f"PadButton ({self.row},{self.col}) mousePressEvent - Ignoring") # Debug print
        event.ignore() # Pass event to parent (PadGridWidget)

    def mouseMoveEvent(self, event: QMouseEvent):
        # print(f"PadButton ({self.row},{self.col}) mouseMoveEvent - Ignoring") # Debug print
        event.ignore() # Pass event to parent

    def mouseReleaseEvent(self, event: QMouseEvent):
        # print(f"PadButton ({self.row},{self.col}) mouseReleaseEvent - Ignoring") # Debug print
        event.ignore() # Pass event to parent


class PadGridWidget(QFrame):
    """
    Widget displaying the 8x8 SmartPad grid.
    Handles pad clicks and drag-painting, and updates pad colors.
    """
    # Emits (pad_index_0_63, mouse_button_type)
    pad_interaction_signal = pyqtSignal(int, Qt.MouseButton)

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setFrameShadow(QFrame.Shadow.Sunken)

        self.main_layout = QGridLayout(self)
        self.main_layout.setSpacing(PAD_SPACING)
        self.main_layout.setContentsMargins(PAD_SPACING, PAD_SPACING, PAD_SPACING, PAD_SPACING)

        self.pad_buttons: dict[tuple[int, int], PadButton] = {}
        self._is_mouse_dragging_on_grid = False
        self._last_dragged_pad_index_on_grid = -1

        for r in range(GRID_ROWS):
            for c in range(GRID_COLS):
                button = PadButton(r, c)
                self.update_pad_gui_color(r, c, DEFAULT_PAD_COLOR_NAME_ON_GRID)
                self.main_layout.addWidget(button, r, c, Qt.AlignmentFlag.AlignCenter)
                self.pad_buttons[(r, c)] = button
        
        self.setMouseTracking(True)

    def get_pad_button_at(self, row: int, col: int) -> PadButton | None:
        return self.pad_buttons.get((row,col))

    def get_current_grid_data_names(self) -> list[str]:
        grid_data = [DEFAULT_PAD_COLOR_NAME_ON_GRID] * (GRID_ROWS * GRID_COLS)
        for r_idx in range(GRID_ROWS): # Renamed r to r_idx
            for c_idx in range(GRID_COLS): # Renamed c to c_idx
                pad_idx = r_idx * GRID_COLS + c_idx
                button = self.pad_buttons.get((r_idx, c_idx))
                if button and hasattr(button, '_current_color_name_gui'):
                    grid_data[pad_idx] = button._current_color_name_gui
        return grid_data

    def update_pad_gui_color(self, row: int, col: int, color_name: str):
        button = self.pad_buttons.get((row, col))
        if button:
            upper_color_name = color_name.upper()
            display_hex = UI_COLORS_GRID_DISPLAY.get(upper_color_name, UI_COLORS_GRID_DISPLAY["OFF"])
            
            button.setStyleSheet(f"QPushButton {{ background-color: {display_hex}; border: 1px solid #444; }}"
                                 f"QPushButton:hover {{ border: 1px solid #888; }}")
            button._current_color_name_gui = upper_color_name

    def update_grid_from_data(self, color_names_list_0_63: list[str]):
        if len(color_names_list_0_63) == GRID_ROWS * GRID_COLS:
            for i, color_name in enumerate(color_names_list_0_63):
                row, col = i // GRID_COLS, i % GRID_COLS
                self.update_pad_gui_color(row, col, color_name)
        else:
            print(f"Warning: PadGridWidget received data list of incorrect length: {len(color_names_list_0_63)}")

    def clear_all_pads_gui(self):
        for r in range(GRID_ROWS):
            for c_idx in range(GRID_COLS): # Renamed c to c_idx
                self.update_pad_gui_color(r, c_idx, DEFAULT_PAD_COLOR_NAME_ON_GRID)

    def mousePressEvent(self, event: QMouseEvent):
        super().mousePressEvent(event)
        if event.button() in [Qt.MouseButton.LeftButton, Qt.MouseButton.RightButton]:
            self._is_mouse_dragging_on_grid = True
            self._last_dragged_pad_index_on_grid = -1
            self._process_mouse_interaction_event(event, event.button())

    def mouseMoveEvent(self, event: QMouseEvent):
        super().mouseMoveEvent(event)
        if self._is_mouse_dragging_on_grid and event.buttons() != Qt.MouseButton.NoButton:
            active_button_for_drag = Qt.MouseButton.NoButton
            if event.buttons() & Qt.MouseButton.LeftButton:
                active_button_for_drag = Qt.MouseButton.LeftButton
            elif event.buttons() & Qt.MouseButton.RightButton:
                active_button_for_drag = Qt.MouseButton.RightButton
            
            if active_button_for_drag != Qt.MouseButton.NoButton:
                self._process_mouse_interaction_event(event, active_button_for_drag, is_drag=True)

    def mouseReleaseEvent(self, event: QMouseEvent):
        super().mouseReleaseEvent(event)
        if event.button() in [Qt.MouseButton.LeftButton, Qt.MouseButton.RightButton]:
            self._is_mouse_dragging_on_grid = False
            self._last_dragged_pad_index_on_grid = -1

    def _process_mouse_interaction_event(self, event: QMouseEvent, effective_button: Qt.MouseButton, is_drag: bool = False):
        child_widget = self.childAt(event.position().toPoint())
        if isinstance(child_widget, PadButton):
            pad_index = child_widget.row * GRID_COLS + child_widget.col
            
            if is_drag:
                if pad_index != self._last_dragged_pad_index_on_grid:
                    self.pad_interaction_signal.emit(pad_index, effective_button)
                    self._last_dragged_pad_index_on_grid = pad_index
            else: 
                self.pad_interaction_signal.emit(pad_index, effective_button)
                self._last_dragged_pad_index_on_grid = pad_index


if __name__ == '__main__':
    from PyQt6.QtWidgets import QVBoxLayout, QLabel # For testing window

    app = QApplication([])
    window = QWidget()
    layout = QVBoxLayout(window)
    
    test_status_label = QLabel("Interact with grid...")
    pad_grid = PadGridWidget()
    
    def handle_pad_interaction(pad_idx, mouse_btn):
        r_idx, c_idx = pad_idx // GRID_COLS, pad_idx % GRID_COLS # Renamed r,c
        action = "LEFT CLICK/DRAG" if mouse_btn == Qt.MouseButton.LeftButton else "RIGHT CLICK/DRAG"
        test_status_label.setText(f"Pad ({r_idx},{c_idx}) Index {pad_idx} - {action}")
        
        color_to_set = "GREEN" if mouse_btn == Qt.MouseButton.LeftButton else "OFF"
        pad_grid.update_pad_gui_color(r_idx, c_idx, color_to_set)

    pad_grid.pad_interaction_signal.connect(handle_pad_interaction)
    
    layout.addWidget(test_status_label)
    layout.addWidget(pad_grid)
    
    window.setWindowTitle("PadGridWidget Test")
    window.show()
    app.exec()