# MidiPlusSmartPadRGBEditor/gui/animation_controls_widget.py

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QSlider, QSpinBox, QFrame, QMenu, QCheckBox, QGroupBox, QSpacerItem, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal, QPoint
from PyQt6.QtGui import QAction

# Default values (can be imported from animation_model if preferred)
DEFAULT_ANIM_DELAY_MS = 200
MIN_ANIM_DELAY_MS = 7     # New value for ~142 FPS (1000 / 7 = 142.8)
MAX_ANIM_DELAY_MS = 2000 # 0.5 FPS (can keep this or adjust)

# Icons
ICON_PLAY = "▶️ Play"
ICON_PAUSE = "⏸️ Pause"
ICON_STOP = "⏹️ Stop"
ICON_ADD_FRAME_CTRL = "➕ Add" # Main add button, menu for type
ICON_DUPLICATE_FRAME_CTRL = "📋 Dup"
ICON_DELETE_FRAME_CTRL = "🗑️ Del"


class AnimationControlsWidget(QGroupBox):
    """
    Widget for animation playback controls (Play, Pause, Stop), frame manipulation
    (Add, Delete, Duplicate), and speed/loop settings.
    """
    # Playback signals
    play_requested = pyqtSignal()
    pause_requested = pyqtSignal()
    stop_requested = pyqtSignal()

    # Frame manipulation signals (emitted by this widget, handled by MainWindow)
    add_frame_dialog_requested = pyqtSignal() # Could have a context menu for type of add
    # Or specific add signals:
    add_snapshot_frame_ctrl_requested = pyqtSignal()
    add_blank_frame_ctrl_requested = pyqtSignal()
    duplicate_selected_frame_ctrl_requested = pyqtSignal()
    delete_selected_frame_ctrl_requested = pyqtSignal()

    # Property change signals
    frame_delay_changed = pyqtSignal(int) # Emits new delay in ms
    loop_toggle_changed = pyqtSignal(bool) # Emits new loop state

    def __init__(self, parent: QWidget | None = None):
        super().__init__("Animation Controls", parent)

        self.group_layout = QVBoxLayout(self)

        # --- Row 1: Playback and Basic Frame Ops ---
        row1_layout = QHBoxLayout()

        self.play_pause_button = QPushButton(ICON_PLAY)
        self.play_pause_button.setCheckable(True) # Toggles between Play and Pause state
        self.play_pause_button.setToolTip("Play or Pause the animation.")
        self.play_pause_button.clicked.connect(self._on_play_pause_toggled)
        row1_layout.addWidget(self.play_pause_button)

        self.stop_button = QPushButton(ICON_STOP)
        self.stop_button.setToolTip("Stop the animation and reset to selected/first frame.")
        self.stop_button.clicked.connect(self.stop_requested)
        row1_layout.addWidget(self.stop_button)
        
        row1_layout.addSpacerItem(QSpacerItem(10, 0, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum))

        self.add_frame_button = QPushButton(ICON_ADD_FRAME_CTRL)
        self.add_frame_button.setToolTip("Add a new frame (Right-click for options: Snapshot/Blank).")
        self.add_frame_button.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.add_frame_button.customContextMenuRequested.connect(self._show_add_frame_menu)
        self.add_frame_button.clicked.connect(self.add_snapshot_frame_ctrl_requested) # Default click is snapshot
        row1_layout.addWidget(self.add_frame_button)

        self.duplicate_button = QPushButton(ICON_DUPLICATE_FRAME_CTRL)
        self.duplicate_button.setToolTip("Duplicate the currently selected frame.")
        self.duplicate_button.clicked.connect(self.duplicate_selected_frame_ctrl_requested)
        row1_layout.addWidget(self.duplicate_button)

        self.delete_button = QPushButton(ICON_DELETE_FRAME_CTRL)
        self.delete_button.setToolTip("Delete the currently selected frame.")
        self.delete_button.clicked.connect(self.delete_selected_frame_ctrl_requested)
        row1_layout.addWidget(self.delete_button)
        
        row1_layout.addStretch(1)
        self.group_layout.addLayout(row1_layout)

        # --- Row 2: Speed Control & Loop ---
        row2_layout = QHBoxLayout()
        row2_layout.addWidget(QLabel("Speed:"))
        
        self.speed_slider = QSlider(Qt.Orientation.Horizontal)
        # Slider value will represent delay_ms directly for simplicity here, inverted by user
        self.speed_slider.setRange(MIN_ANIM_DELAY_MS, MAX_ANIM_DELAY_MS) 
        self.speed_slider.setValue(DEFAULT_ANIM_DELAY_MS)
        self.speed_slider.setInvertedAppearance(True) # Higher value on left = faster (less delay)
        self.speed_slider.setSingleStep(10)
        self.speed_slider.setPageStep(100)
        self.speed_slider.valueChanged.connect(self._on_speed_slider_changed)
        row2_layout.addWidget(self.speed_slider, 1)

        self.speed_label = QLabel(f"{1000/DEFAULT_ANIM_DELAY_MS:.1f} FPS ({DEFAULT_ANIM_DELAY_MS}ms)")
        self.speed_label.setMinimumWidth(100) # Ensure enough space for text
        self.speed_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        row2_layout.addWidget(self.speed_label)

        self.loop_checkbox = QCheckBox("Loop")
        self.loop_checkbox.setChecked(True)
        self.loop_checkbox.toggled.connect(self.loop_toggle_changed)
        row2_layout.addWidget(self.loop_checkbox)

        self.group_layout.addLayout(row2_layout)

        # Hidden SpinBox to sync with slider if precise input is ever needed (not primary UI)
        self.delay_ms_spinbox = QSpinBox()
        self.delay_ms_spinbox.setRange(MIN_ANIM_DELAY_MS, MAX_ANIM_DELAY_MS)
        self.delay_ms_spinbox.setValue(DEFAULT_ANIM_DELAY_MS)
        self.delay_ms_spinbox.valueChanged.connect(self._on_delay_spinbox_changed)
        # self.delay_ms_spinbox.setVisible(False) # Hide for now

    def _show_add_frame_menu(self, position: QPoint): # QPoint is used here
        menu = QMenu(self)
        action_snap = QAction("📷 Add Snapshot", self)
        action_snap.triggered.connect(self.add_snapshot_frame_ctrl_requested)
        menu.addAction(action_snap)

        action_blank = QAction("⬛ Add Blank", self)
        action_blank.triggered.connect(self.add_blank_frame_ctrl_requested)
        menu.addAction(action_blank)
        menu.exec(self.add_frame_button.mapToGlobal(position))


    def _on_play_pause_toggled(self, checked: bool):
        if checked:
            self.play_pause_button.setText(ICON_PAUSE)
            self.play_requested.emit()
        else:
            self.play_pause_button.setText(ICON_PLAY)
            self.pause_requested.emit()

    def _on_speed_slider_changed(self, value: int):
        delay_ms = value # Slider directly represents delay
        fps = 1000.0 / delay_ms if delay_ms > 0 else 0
        self.speed_label.setText(f"{fps:.1f} FPS ({delay_ms}ms)")
        
        self.delay_ms_spinbox.blockSignals(True)
        self.delay_ms_spinbox.setValue(delay_ms)
        self.delay_ms_spinbox.blockSignals(False)
        
        self.frame_delay_changed.emit(delay_ms)

    def _on_delay_spinbox_changed(self, delay_ms: int): # If spinbox was visible
        self.speed_slider.blockSignals(True)
        self.speed_slider.setValue(delay_ms)
        self.speed_slider.blockSignals(False)
        
        fps = 1000.0 / delay_ms if delay_ms > 0 else 0
        self.speed_label.setText(f"{fps:.1f} FPS ({delay_ms}ms)")
        # self.frame_delay_changed.emit(delay_ms) # Already emitted by slider change

    def update_playback_button_ui(self, is_playing: bool):
        """Called by MainWindow to sync button state if model changes playback state."""
        self.play_pause_button.blockSignals(True)
        self.play_pause_button.setChecked(is_playing)
        self.play_pause_button.setText(ICON_PAUSE if is_playing else ICON_PLAY)
        self.play_pause_button.blockSignals(False)

    def set_current_delay_ui(self, delay_ms: int):
        """Called by MainWindow to set the speed controls from the model."""
        self.speed_slider.blockSignals(True)
        self.delay_ms_spinbox.blockSignals(True)
        
        clamped_delay = max(MIN_ANIM_DELAY_MS, min(delay_ms, MAX_ANIM_DELAY_MS))
        self.speed_slider.setValue(clamped_delay)
        self.delay_ms_spinbox.setValue(clamped_delay)
        
        fps = 1000.0 / clamped_delay if clamped_delay > 0 else 0
        self.speed_label.setText(f"{fps:.1f} FPS ({clamped_delay}ms)")
        
        self.speed_slider.blockSignals(False)
        self.delay_ms_spinbox.blockSignals(False)

    def set_current_loop_ui(self, loop_state: bool):
        """Called by MainWindow to set the loop checkbox state."""
        self.loop_checkbox.blockSignals(True)
        self.loop_checkbox.setChecked(loop_state)
        self.loop_checkbox.blockSignals(False)

    def set_controls_enabled(self, enabled: bool, has_frames: bool, frame_selected: bool):
        """Enable/disable controls based on overall state and animation properties."""
        self.play_pause_button.setEnabled(enabled and has_frames)
        self.stop_button.setEnabled(enabled and has_frames) # Or if currently playing

        self.add_frame_button.setEnabled(enabled) # Always possible to add if controls are generally enabled
        
        can_operate_on_selected_frame = enabled and has_frames and frame_selected
        self.duplicate_button.setEnabled(can_operate_on_selected_frame)
        self.delete_button.setEnabled(can_operate_on_selected_frame)

        self.speed_slider.setEnabled(enabled and has_frames)
        self.speed_label.setEnabled(enabled and has_frames)
        self.loop_checkbox.setEnabled(enabled and has_frames)
        
        # If overall disabled, ensure play_pause is not in 'Pause' text state
        if not enabled or not has_frames:
            self.update_playback_button_ui(is_playing=False)


if __name__ == '__main__':
    from PyQt6.QtWidgets import QApplication # Ensure QApplication is imported
    # QPoint is already imported at the top of the file

    app = QApplication([])
    widget = AnimationControlsWidget()

    widget.play_requested.connect(lambda: print("Signal: Play Requested"))
    widget.pause_requested.connect(lambda: print("Signal: Pause Requested"))
    widget.stop_requested.connect(lambda: print("Signal: Stop Requested"))
    widget.add_snapshot_frame_ctrl_requested.connect(lambda: print("Signal: Add Snapshot Requested (Controls)"))
    widget.add_blank_frame_ctrl_requested.connect(lambda: print("Signal: Add Blank Requested (Controls)"))
    widget.duplicate_selected_frame_ctrl_requested.connect(lambda: print("Signal: Duplicate Frame Requested (Controls)"))
    widget.delete_selected_frame_ctrl_requested.connect(lambda: print("Signal: Delete Frame Requested (Controls)"))
    widget.frame_delay_changed.connect(lambda ms: print(f"Signal: Frame Delay Changed: {ms}ms"))
    widget.loop_toggle_changed.connect(lambda state: print(f"Signal: Loop Toggled: {state}"))

    # Simulate state changes
    widget.set_controls_enabled(enabled=True, has_frames=True, frame_selected=True)
    
    temp_window = QWidget()
    temp_layout = QVBoxLayout(temp_window)
    temp_layout.addWidget(widget)
    temp_window.setWindowTitle("AnimationControlsWidget Test")
    temp_window.show()
    
    app.exec()