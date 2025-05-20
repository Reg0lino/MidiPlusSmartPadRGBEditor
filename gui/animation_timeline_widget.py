# MidiPlusSmartPadRGBEditor/gui/animation_timeline_widget.py

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QListWidget, QListWidgetItem,
    QAbstractItemView, QMenu, QGroupBox, QStyledItemDelegate,
    QStyleOptionViewItem, QStyle, QApplication # Added QApplication for fallback colors
)
from PyQt6.QtCore import pyqtSignal, Qt, QPoint, QModelIndex, QSize, QRect
from PyQt6.QtGui import QAction, QPainter, QColor, QBrush, QPen

# --- Icons (can be simple text or unicode) ---
ICON_ADD_SNAPSHOT_TIMELINE = "📷 Snap"
ICON_ADD_BLANK_TIMELINE = "⬛ Blank"
ICON_DUPLICATE_TIMELINE = "📋 Dup"
ICON_DELETE_TIMELINE = "🗑️ Del"

# --- Thumbnail Constants (can be tuned) ---
THUMB_PAD_SIZE = 3
THUMB_PAD_SPACING = 1
THUMB_GRID_ROWS = 8
THUMB_GRID_COLS = 8
THUMB_TEXT_HEIGHT = 15
THUMB_PADDING_TOP = 3 # Increased slightly
THUMB_PADDING_TEXT_GRID = 4 # Increased slightly
THUMB_PADDING_BOTTOM = 3 # Increased slightly
THUMB_PADDING_HORIZONTAL = 5 # Increased slightly

THUMB_GRID_WIDTH = (THUMB_GRID_COLS * THUMB_PAD_SIZE) + ((THUMB_GRID_COLS - 1) * THUMB_PAD_SPACING if THUMB_GRID_COLS > 0 else 0)
THUMB_GRID_HEIGHT = (THUMB_GRID_ROWS * THUMB_PAD_SIZE) + ((THUMB_GRID_ROWS - 1) * THUMB_PAD_SPACING if THUMB_GRID_ROWS > 0 else 0) # Corrected formula

TOTAL_THUMB_ITEM_WIDTH = max(THUMB_GRID_WIDTH, 60) + (2 * THUMB_PADDING_HORIZONTAL) # Ensure min width for "Frame XX"
TOTAL_THUMB_ITEM_HEIGHT = THUMB_PADDING_TOP + THUMB_TEXT_HEIGHT + THUMB_PADDING_TEXT_GRID + THUMB_GRID_HEIGHT + THUMB_PADDING_BOTTOM

# Attempt to import UI_COLORS_GRID_DISPLAY from pad_grid_widget for consistency
# This creates a dependency; a shared constants module would be better in a larger app.
try:
    from .pad_grid_widget import UI_COLORS_GRID_DISPLAY
except ImportError:
    print("WARNING (AnimationTimelineWidget): Could not import UI_COLORS_GRID_DISPLAY from pad_grid_widget. Using fallback.")
    UI_COLORS_GRID_DISPLAY = {
        "RED": "#FF0000", "GREEN": "#00FF00", "DARKBLUE": "#00008B",
        "PURPLE": "#800080", "LIGHTBLUE": "#ADD8E6", "YELLOW": "#FFFF00",
        "WHITE": "#FFFFFF", "OFF": "#303030", "DEFAULT": "#1C1C1C"
    }

class FrameThumbnailDelegate(QStyledItemDelegate):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._frames_color_data_cache: list[list[str]] = []
        self._current_edit_idx = -1
        self._current_playback_idx = -1
        # self.ui_colors_map = UI_COLORS_GRID_DISPLAY # Use imported or fallback

    def set_frames_data(self, frames_data: list[list[str]], edit_idx: int, playback_idx: int):
        self._frames_color_data_cache = frames_data
        self._current_edit_idx = edit_idx
        self._current_playback_idx = playback_idx

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex):
        painter.save()
        rect = option.rect

        is_selected = bool(option.state & QStyle.StateFlag.State_Selected)
        is_edit_frame = (index.row() == self._current_edit_idx)
        is_playback_frame = (index.row() == self._current_playback_idx)

        # Determine background color
        if is_selected:
            bg_color = option.palette.highlight().color()
        elif is_edit_frame: # Edit frame highlight (non-selected)
            bg_color = option.palette.base().color().darker(110) # Darker version of base for subtle highlight
            if bg_color == option.palette.base().color(): bg_color = QColor("#404030") # Fallback gold-ish tint
        elif is_playback_frame: # Playback frame highlight (non-selected, and not edit frame)
            bg_color = option.palette.base().color().darker(110)
            if bg_color == option.palette.base().color(): bg_color = QColor("#304040") # Fallback cyan-ish tint
        else:
            bg_color = option.palette.base().color()
        painter.fillRect(rect, bg_color)

        # Frame Text ("Frame X")
        text = f"Frame {index.row() + 1}"
        text_rect = QRect(rect.x() + THUMB_PADDING_HORIZONTAL,
                          rect.y() + THUMB_PADDING_TOP,
                          rect.width() - (2 * THUMB_PADDING_HORIZONTAL),
                          THUMB_TEXT_HEIGHT)
        
        text_pen_color = option.palette.highlightedText().color() if is_selected else option.palette.text().color()
        painter.setPen(text_pen_color)
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter, text)

        # Thumbnail Grid
        grid_top_y = text_rect.bottom() + THUMB_PADDING_TEXT_GRID
        grid_start_x = rect.x() + (rect.width() - THUMB_GRID_WIDTH) // 2 # Center the grid horizontally

        frame_colors = None
        if 0 <= index.row() < len(self._frames_color_data_cache):
            frame_colors = self._frames_color_data_cache[index.row()]

        if frame_colors and len(frame_colors) == THUMB_GRID_ROWS * THUMB_GRID_COLS:
            for r in range(THUMB_GRID_ROWS):
                for c in range(THUMB_GRID_COLS):
                    pad_idx = r * THUMB_GRID_COLS + c
                    color_name = frame_colors[pad_idx].upper() # Ensure uppercase for lookup
                    hex_color_str = UI_COLORS_GRID_DISPLAY.get(color_name, UI_COLORS_GRID_DISPLAY["OFF"])
                    
                    pad_rect_x = grid_start_x + c * (THUMB_PAD_SIZE + THUMB_PAD_SPACING)
                    pad_rect_y = grid_top_y + r * (THUMB_PAD_SIZE + THUMB_PAD_SPACING)
                    
                    painter.fillRect(pad_rect_x, pad_rect_y, THUMB_PAD_SIZE, THUMB_PAD_SIZE, QColor(hex_color_str))
        else:
            no_data_rect = QRect(grid_start_x, grid_top_y, THUMB_GRID_WIDTH, THUMB_GRID_HEIGHT)
            painter.setPen(option.palette.text().color()) # Use default text color for "N/A"
            painter.drawText(no_data_rect, Qt.AlignmentFlag.AlignCenter, "N/A")

        # Distinct Border for Edit/Playback if not selected (selection already has highlight bg)
        border_pen = QPen(Qt.GlobalColor.transparent)
        border_width = 1 # Default to 1 for non-selected special states
        if is_selected:
            # Selected items get a border from the style's highlight usually,
            # or we can draw a specific one here too.
            # For now, let background differentiate selected.
            pass
        elif is_edit_frame:
            border_pen.setColor(Qt.GlobalColor.yellow)
            border_width = 2 # Make edit frame border more prominent
        elif is_playback_frame:
            border_pen.setColor(Qt.GlobalColor.cyan)
        
        if border_pen.color() != Qt.GlobalColor.transparent:
            border_pen.setWidth(border_width)
            painter.setPen(border_pen)
            # Adjust rect for border to be drawn inside
            painter.drawRect(rect.adjusted(border_width // 2, border_width // 2, -border_width, -border_width))


        painter.restore()

    def sizeHint(self, option: QStyleOptionViewItem, index: QModelIndex) -> QSize:
        return QSize(TOTAL_THUMB_ITEM_WIDTH, TOTAL_THUMB_ITEM_HEIGHT)


class AnimationTimelineWidget(QGroupBox):
    frame_selected = pyqtSignal(int)
    add_snapshot_frame_requested = pyqtSignal()
    add_blank_frame_requested = pyqtSignal()
    duplicate_selected_frame_requested = pyqtSignal()
    delete_selected_frame_requested = pyqtSignal()

    def __init__(self, parent: QWidget | None = None):
        super().__init__("Animation Frames", parent)
        self.group_layout = QVBoxLayout(self)

        self.frame_list_widget = QListWidget()
        self.frame_list_widget.setViewMode(QListWidget.ViewMode.IconMode)
        self.frame_list_widget.setFlow(QListWidget.Flow.LeftToRight)
        self.frame_list_widget.setWrapping(False)
        self.frame_list_widget.setResizeMode(QListWidget.ResizeMode.Adjust)
        
        list_widget_height = TOTAL_THUMB_ITEM_HEIGHT + 20 # +20 for scrollbar and margins
        self.frame_list_widget.setFixedHeight(list_widget_height)
        
        self.frame_list_widget.setUniformItemSizes(True)
        self.frame_list_widget.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.frame_list_widget.currentItemChanged.connect(self._on_current_item_changed)

        self.frame_list_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.frame_list_widget.customContextMenuRequested.connect(self.show_timeline_context_menu)
        
        self.thumbnail_delegate = FrameThumbnailDelegate(self.frame_list_widget)
        self.frame_list_widget.setItemDelegate(self.thumbnail_delegate)
        
        self.group_layout.addWidget(self.frame_list_widget)

    def _on_current_item_changed(self, current: QListWidgetItem, previous: QListWidgetItem):
        if current:
            index = self.frame_list_widget.row(current)
            self.frame_selected.emit(index)
        else:
            self.frame_selected.emit(-1)

    def show_timeline_context_menu(self, position: QPoint):
        menu = QMenu(self)
        item_at_pos = self.frame_list_widget.itemAt(position)
        
        action_add_snap = QAction(ICON_ADD_SNAPSHOT_TIMELINE, self)
        action_add_snap.triggered.connect(self.add_snapshot_frame_requested)
        menu.addAction(action_add_snap)

        action_add_blank = QAction(ICON_ADD_BLANK_TIMELINE, self)
        action_add_blank.triggered.connect(self.add_blank_frame_requested)
        menu.addAction(action_add_blank)
        
        if item_at_pos:
            menu.addSeparator()
            action_duplicate = QAction(ICON_DUPLICATE_TIMELINE, self)
            action_duplicate.triggered.connect(self.duplicate_selected_frame_requested)
            menu.addAction(action_duplicate)

            action_delete = QAction(ICON_DELETE_TIMELINE, self)
            action_delete.triggered.connect(self.delete_selected_frame_requested)
            menu.addAction(action_delete)
        
        menu.exec(self.frame_list_widget.mapToGlobal(position))

    def update_frames_display(self, frames_data_list: list[list[str]], 
                              current_edit_index: int, 
                              current_playback_index: int = -1):
        self.frame_list_widget.blockSignals(True)
        
        self.thumbnail_delegate.set_frames_data(frames_data_list, current_edit_index, current_playback_index)

        previously_selected_row = self.get_selected_frame_index()
        
        current_item_count = self.frame_list_widget.count()
        target_item_count = len(frames_data_list)

        if current_item_count > target_item_count:
            for _ in range(current_item_count - target_item_count):
                self.frame_list_widget.takeItem(self.frame_list_widget.count() - 1)
        elif target_item_count > current_item_count:
            for _ in range(target_item_count - current_item_count):
                item = QListWidgetItem()
                self.frame_list_widget.addItem(item)
        
        self.frame_list_widget.update() # Crucial: Tell list to repaint its items using the delegate

        new_selection_to_set = -1
        if 0 <= current_edit_index < target_item_count:
            new_selection_to_set = current_edit_index
        elif 0 <= previously_selected_row < target_item_count:
            new_selection_to_set = previously_selected_row
        elif target_item_count > 0:
            new_selection_to_set = 0
        
        if new_selection_to_set != -1:
            self.frame_list_widget.setCurrentRow(new_selection_to_set)
            self.frame_list_widget.scrollToItem(self.frame_list_widget.item(new_selection_to_set), 
                                                QAbstractItemView.ScrollHint.EnsureVisible)
        
        self.frame_list_widget.blockSignals(False)
        
        # Manually emit signal if programmatic selection changed
        current_selected_row_after_update = self.get_selected_frame_index()
        if current_selected_row_after_update != previously_selected_row:
             self.frame_selected.emit(current_selected_row_after_update)


    def get_selected_frame_index(self) -> int:
        current_item = self.frame_list_widget.currentItem()
        return self.frame_list_widget.row(current_item) if current_item else -1

    def set_selected_frame_by_index(self, index: int):
        if 0 <= index < self.frame_list_widget.count():
            self.frame_list_widget.setCurrentRow(index)
        elif self.frame_list_widget.count() == 0 or index == -1:
             # If setting to -1 or list is empty, clear selection by setting invalid row
             self.frame_list_widget.setCurrentRow(-1) 


    def set_controls_enabled(self, enabled: bool):
        self.setEnabled(enabled) # Disables the groupbox and its children


if __name__ == '__main__':
    from PyQt6.QtWidgets import QApplication # Ensure QApplication is imported
    import sys # For sys.argv in standalone test

    app = QApplication(sys.argv)
    # Example: Create a dummy list of frame data for testing the delegate
    dummy_frames_data = []
    colors = list(UI_COLORS_GRID_DISPLAY.keys())
    for i in range(10): # 10 test frames
        frame_color_list = [(colors[(i + j) % len(colors)]) for j in range(64)]
        dummy_frames_data.append(frame_color_list)

    widget = AnimationTimelineWidget()
    widget.update_frames_display(frames_data_list=dummy_frames_data, current_edit_index=1, current_playback_index=3)

    widget.frame_selected.connect(lambda idx: print(f"Signal: Frame selected: {idx}"))
    widget.add_snapshot_frame_requested.connect(lambda: print("Signal: Add Snapshot Requested"))
    widget.add_blank_frame_requested.connect(lambda: print("Signal: Add Blank Requested"))
    # ... (other signal connections for test)

    temp_window = QWidget()
    temp_layout = QVBoxLayout(temp_window)
    temp_layout.addWidget(widget)
    temp_window.setWindowTitle("AnimationTimelineWidget Test with Delegate")
    temp_window.resize(600, 150) # Give it some width to see horizontal scroll
    temp_window.show()
    
    sys.exit(app.exec())