# MidiPlusSmartPadRGBEditor/main_window.py

import sys
import os
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QStatusBar, QSizePolicy, QFrame, QMessageBox, QInputDialog,
    QComboBox, QPushButton, QFileDialog, QGroupBox # Added QGroupBox
)
from PyQt6.QtCore import Qt, QSettings, QTimer, QByteArray
from PyQt6.QtGui import QAction, QIcon, QColor, QKeySequence

# --- Configuration Constants ---
APP_NAME_FULL = "MidiPlus SmartPad RGB Editor"
APP_AUTHOR_SETTINGS = "SmartPadAppDev"
INITIAL_WINDOW_WIDTH = 950
INITIAL_WINDOW_HEIGHT = 750
DEFAULT_USER_DATA_PATH = "user_data_smartpad"
ANIMATIONS_SUBDIR = "animations" # Subdirectory for saved animations

# --- SmartPad Color Definitions ---
UI_COLORS_SMARTPAD_MAIN = {
    "RED": "#FF0000", "GREEN": "#00FF00", "DARKBLUE": "#00008B",
    "PURPLE": "#800080", "LIGHTBLUE": "#ADD8E6", "YELLOW": "#FFFF00",
    "WHITE": "#FFFFFF", "OFF": "#202020"
}
DEFAULT_PAINT_COLOR_NAME = "RED"
DEFAULT_PAD_COLOR_ON_GRID_MAIN = "OFF"

# --- Import custom widgets ---
try:
    from gui.midi_connection_widget import MidiConnectionWidget
    from gui.color_palette_widget import ColorPaletteWidget
    from gui.pad_grid_widget import PadGridWidget, GRID_ROWS, GRID_COLS
    from gui.static_layout_widget import StaticLayoutWidget
    from gui.animation_timeline_widget import AnimationTimelineWidget
    from gui.animation_controls_widget import AnimationControlsWidget
except ImportError as e:
    print(f"FATAL ERROR MainWindow: Error importing a GUI widget module: {e}")
    sys.exit(1)

# --- Import core components ---
try:
    from core.smartpad_controller import SmartPadController
    from core.animation_model import SmartPadAnimationModel # MAX_ANIMATION_FRAMES removed from import
    from core.static_layout_model import StaticLayoutModel
except ImportError as e:
    print(f"FATAL ERROR MainWindow: Error importing a core component module: {e}")
    sys.exit(1)


class MainWindow(QMainWindow):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)

        self.setWindowTitle(APP_NAME_FULL)
        # Icon set in smartpad_rgb_app.py, but can be a fallback here
        icon_path = os.path.join(os.path.dirname(__file__), "..", "resources", "icons", "app_icon.png")
        if os.path.exists(icon_path):
             self.setWindowIcon(QIcon(icon_path))
        self.load_settings()

        self._current_paint_color_name: str = DEFAULT_PAINT_COLOR_NAME

        script_dir = os.path.dirname(os.path.abspath(__file__)) # gui directory
        project_root_dir = os.path.dirname(os.path.abspath(__file__))
        self.user_data_base_path = os.path.join(project_root_dir, DEFAULT_USER_DATA_PATH)
        os.makedirs(self.user_data_base_path, exist_ok=True)
        
        self.animations_dir = os.path.join(self.user_data_base_path, ANIMATIONS_SUBDIR)
        os.makedirs(self.animations_dir, exist_ok=True)
        self.animations_dir = os.path.join(self.user_data_base_path, ANIMATIONS_SUBDIR)
        os.makedirs(self.animations_dir, exist_ok=True)
        print(f"INFO: Project root directory considered by MainWindow: {project_root_dir}")
        print(f"INFO: Using user data base path: {self.user_data_base_path}")
        print(f"INFO: Animations directory: {self.animations_dir}")

        self.smartpad_controller = SmartPadController(parent=self)
        self.animation_model = SmartPadAnimationModel(parent=self)
        self.static_layout_model = StaticLayoutModel(base_storage_path=self.user_data_base_path, parent=self)

        # --- UI Widgets (will be fully populated in _init_ui_layout_and_widgets) ---
        self.midi_connection_widget: MidiConnectionWidget | None = None
        self.color_palette_widget: ColorPaletteWidget | None = None
        self.pad_grid_widget: PadGridWidget | None = None
        self.static_layout_widget: StaticLayoutWidget | None = None
        
        # For "Animation Studio" section
        self.animation_studio_group: QGroupBox | None = None
        self.saved_animations_combo: QComboBox | None = None
        self.load_animation_button: QPushButton | None = None
        self.new_animation_button: QPushButton | None = None # Replaces File menu action for UI
        self.save_animation_as_button: QPushButton | None = None # Replaces File menu action for UI
        self.delete_animation_button: QPushButton | None = None

        self.animation_timeline_widget: AnimationTimelineWidget | None = None
        self.animation_controls_widget: AnimationControlsWidget | None = None

        self._init_ui_layout_and_widgets()
        self._create_actions_and_menus() # Combined for simplicity

        self._connect_signals()

        self.status_bar.showMessage("Ready. Please connect to SmartPad.", 5000)
        self.midi_connection_widget.update_ports_list(self.smartpad_controller.get_available_ports())
        self.color_palette_widget.set_selected_color_externally(self._current_paint_color_name)
        self.static_layout_widget.update_layouts_list(self.static_layout_model.get_available_layout_names())
        self._populate_saved_animations_combo() # New method to populate anim combo
        self._update_animation_ui_from_model()
        self._update_ui_enabled_state()

        self.playback_timer = QTimer(self)
        self.playback_timer.timeout.connect(self._on_playback_timer_tick)


    def _init_ui_layout_and_widgets(self):
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QHBoxLayout(self.central_widget)

        # --- Left Panel ---
        self.left_panel = QFrame()
        self.left_panel_layout = QVBoxLayout(self.left_panel)
        self.left_panel.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        self.pad_grid_widget = PadGridWidget(parent=self)
        self.pad_grid_widget.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed) # Fixed VSize
        self.left_panel_layout.addWidget(self.pad_grid_widget, 0, Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop)

        # --- Animation Studio GroupBox ---
        self.animation_studio_group = QGroupBox("Animation Studio")
        anim_studio_layout = QVBoxLayout(self.animation_studio_group)

        # Row 1: Animation Selection and Load
        anim_selection_layout = QHBoxLayout()
        anim_selection_layout.addWidget(QLabel("Animation:"))
        self.saved_animations_combo = QComboBox()
        self.saved_animations_combo.setPlaceholderText("--- Select Saved Animation ---")
        anim_selection_layout.addWidget(self.saved_animations_combo, 1)
        self.load_animation_button = QPushButton("Load")
        anim_selection_layout.addWidget(self.load_animation_button)
        anim_studio_layout.addLayout(anim_selection_layout)

        # Row 2: Animation Actions
        anim_actions_layout = QHBoxLayout()
        self.new_animation_button = QPushButton("✨ New")
        anim_actions_layout.addWidget(self.new_animation_button)
        self.save_animation_as_button = QPushButton("💾 Save As...")
        anim_actions_layout.addWidget(self.save_animation_as_button)
        self.delete_animation_button = QPushButton("🗑️ Delete")
        anim_actions_layout.addWidget(self.delete_animation_button)
        anim_actions_layout.addStretch(1)
        anim_studio_layout.addLayout(anim_actions_layout)
        self.left_panel_layout.addWidget(self.animation_studio_group)


        self.animation_timeline_widget = AnimationTimelineWidget(parent=self)
        self.left_panel_layout.addWidget(self.animation_timeline_widget)

        self.animation_controls_widget = AnimationControlsWidget(parent=self)
        self.left_panel_layout.addWidget(self.animation_controls_widget)
        
        self.left_panel_layout.addStretch(1) # Push everything in left panel up
        self.main_layout.addWidget(self.left_panel, 2)


        # --- Right Panel ---
        self.right_panel = QFrame()
        self.right_panel_layout = QVBoxLayout(self.right_panel)
        self.right_panel.setMinimumWidth(300)
        self.right_panel.setMaximumWidth(380) # Increased max width slightly
        self.right_panel.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)

        self.midi_connection_widget = MidiConnectionWidget(parent=self)
        self.right_panel_layout.addWidget(self.midi_connection_widget)

        self.color_palette_widget = ColorPaletteWidget(parent=self)
        self.right_panel_layout.addWidget(self.color_palette_widget)

        self.static_layout_widget = StaticLayoutWidget(parent=self)
        self.right_panel_layout.addWidget(self.static_layout_widget)
        
        self.right_panel_layout.addStretch(1)
        self.main_layout.addWidget(self.right_panel, 1)

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

    def _create_actions_and_menus(self):
        # Standard Exit Action
        self.exit_action = QAction(QIcon.fromTheme("application-exit"), "&Exit", self)
        self.exit_action.setShortcut(QKeySequence("Ctrl+Q")) # String literal
        self.exit_action.setStatusTip("Exit the application")
        self.exit_action.triggered.connect(self.close)
        
        self.menu_bar = self.menuBar()
        self.file_menu = self.menu_bar.addMenu("&File")
        
        # New Animation Action
        new_action_menu = QAction("✨ &New Animation", self)
        new_action_menu.setShortcut(QKeySequence.StandardKey.New) # Uses standard Ctrl+N
        new_action_menu.triggered.connect(self._on_new_animation_button_clicked)
        self.file_menu.addAction(new_action_menu)

        # Open Animation Action
        open_action_menu = QAction("📂 &Open Animation...", self)
        open_action_menu.setShortcut(QKeySequence.StandardKey.Open) # Uses standard Ctrl+O
        open_action_menu.triggered.connect(self._on_load_animation_button_clicked)
        self.file_menu.addAction(open_action_menu)
        
        # Save Animation As Action
        save_as_action_menu = QAction("💾 Save Animation &As...", self)
        save_as_action_menu.setShortcut(QKeySequence("Ctrl+Shift+S")) # Explicit string for Ctrl+Shift+S
        save_as_action_menu.triggered.connect(self._on_save_animation_as_button_clicked)
        self.file_menu.addAction(save_as_action_menu)

        # Optional: "Save" Action (Ctrl+S) - distinct from "Save As"
        # For now, we only have "Save As" in the menu. If you add a "Save" action:
        # self.save_anim_action_menu = QAction("💾 &Save Animation", self)
        # self.save_anim_action_menu.setShortcut(QKeySequence.StandardKey.Save) # Uses standard Ctrl+S
        # self.save_anim_action_menu.triggered.connect(self._on_save_animation_button_clicked_menu) # A new slot
        # self.file_menu.addAction(self.save_anim_action_menu)

        self.file_menu.addSeparator()
        self.file_menu.addAction(self.exit_action)

    def _connect_signals(self):
        # SmartPad Controller
        self.smartpad_controller.connection_status_changed.connect(self.on_smartpad_connection_status_changed)
        self.smartpad_controller.error_occurred.connect(lambda msg: self.status_bar.showMessage(f"MIDI Error: {msg}", 7000))

        # MIDI Connection Widget
        self.midi_connection_widget.connect_requested.connect(self.smartpad_controller.connect)
        self.midi_connection_widget.disconnect_requested.connect(self.smartpad_controller.disconnect)

        # Color Palette Widget
        self.color_palette_widget.color_selected.connect(self._on_paint_color_selected)

        # Pad Grid Widget
        if self.pad_grid_widget:
            self.pad_grid_widget.pad_interaction_signal.connect(self._on_pad_grid_interaction)

        # Static Layout Model & Widget
        self.static_layout_model.layouts_list_changed.connect(
            lambda: self.static_layout_widget.update_layouts_list(self.static_layout_model.get_available_layout_names())
        )
        self.static_layout_model.error_occurred.connect(
            lambda msg: self.status_bar.showMessage(f"Layout Error: {msg}", 5000)
        )
        self.static_layout_widget.apply_layout_requested.connect(self._on_apply_static_layout)
        self.static_layout_widget.save_current_as_requested.connect(self._on_save_current_as_static_layout)
        self.static_layout_widget.delete_layout_requested.connect(self._on_delete_static_layout) # New slot

        # Animation Model
        self.animation_model.frames_changed.connect(self._update_animation_ui_from_model)
        self.animation_model.frame_content_updated.connect(self._on_animation_model_frame_content_updated)
        self.animation_model.current_edit_frame_changed.connect(self._on_animation_model_edit_frame_changed)
        self.animation_model.properties_changed.connect(self._update_animation_ui_from_model)
        self.animation_model.playback_state_changed.connect(self._on_animation_model_playback_state_changed)

        # Animation Studio UI Buttons
        self.load_animation_button.clicked.connect(self._on_load_animation_button_clicked)
        self.new_animation_button.clicked.connect(self._on_new_animation_button_clicked)
        self.save_animation_as_button.clicked.connect(self._on_save_animation_as_button_clicked)
        self.delete_animation_button.clicked.connect(self._on_delete_animation_button_clicked)
        self.saved_animations_combo.currentIndexChanged.connect(self._on_saved_animation_combo_changed)


        # Animation Timeline Widget
        self.animation_timeline_widget.frame_selected.connect(self.animation_model.set_current_edit_frame_index)
        self.animation_timeline_widget.add_snapshot_frame_requested.connect(self._on_add_frame_requested_snapshot)
        self.animation_timeline_widget.add_blank_frame_requested.connect(self._on_add_frame_requested_blank)
        self.animation_timeline_widget.duplicate_selected_frame_requested.connect(self._on_duplicate_frame_requested)
        self.animation_timeline_widget.delete_selected_frame_requested.connect(self._on_delete_frame_requested)
        
        # Animation Controls Widget
        self.animation_controls_widget.play_requested.connect(self._on_play_animation)
        self.animation_controls_widget.pause_requested.connect(self._on_pause_animation)
        self.animation_controls_widget.stop_requested.connect(self._on_stop_animation)
        self.animation_controls_widget.add_snapshot_frame_ctrl_requested.connect(self._on_add_frame_requested_snapshot)
        self.animation_controls_widget.add_blank_frame_ctrl_requested.connect(self._on_add_frame_requested_blank)
        self.animation_controls_widget.duplicate_selected_frame_ctrl_requested.connect(self._on_duplicate_frame_requested)
        self.animation_controls_widget.delete_selected_frame_ctrl_requested.connect(self._on_delete_frame_requested)
        self.animation_controls_widget.frame_delay_changed.connect(self.animation_model.set_frame_delay_ms)
        self.animation_controls_widget.loop_toggle_changed.connect(self.animation_model.set_loop)

    # --- Slot Implementations (Many existing, some new/modified) ---
    def on_smartpad_connection_status_changed(self, is_connected: bool, message: str):
        self.midi_connection_widget.set_connection_status(is_connected, message)
        if not is_connected:
             self.midi_connection_widget.update_ports_list(self.smartpad_controller.get_available_ports())
        
        status_prefix = "Connected to: " if is_connected else "Status: " # Adjusted prefix
        self.status_bar.showMessage(status_prefix + message, 5000)
        if is_connected:
            self.smartpad_controller.clear_all_pads_on_device()
            # On connect, load current edit frame to hardware, or clear if no frame
            self._on_animation_model_edit_frame_changed(self.animation_model.get_current_edit_frame_index())
        self._update_ui_enabled_state()

    def _on_paint_color_selected(self, color_name: str):
        self._current_paint_color_name = color_name
        self.status_bar.showMessage(f"Paint: {color_name.title()}", 2000)

    def _on_pad_grid_interaction(self, pad_index_0_63: int, mouse_button: Qt.MouseButton):
        if not self.smartpad_controller.is_connected() or self.animation_model.get_is_playing(): # Prevent edit while playing
            if not self.smartpad_controller.is_connected():
                self.status_bar.showMessage("Connect SmartPad to paint.", 3000)
            return

        target_color_name = self._current_paint_color_name
        if mouse_button == Qt.MouseButton.RightButton:
            target_color_name = "OFF"
        
        row, col = pad_index_0_63 // GRID_COLS, pad_index_0_63 % GRID_COLS
        self.pad_grid_widget.update_pad_gui_color(row, col, target_color_name)
        self.smartpad_controller.set_pad_color_by_name(pad_index_0_63, target_color_name, silent=True) # Silent for speed
        if self.animation_model.get_current_edit_frame_index() != -1:
            self.animation_model.update_pad_in_current_edit_frame(pad_index_0_63, target_color_name)

    def _clear_current_grid_and_model_frame(self):
        self.pad_grid_widget.clear_all_pads_gui()
        current_edit_idx = self.animation_model.get_current_edit_frame_index()
        if current_edit_idx != -1:
            current_frame_obj = self.animation_model.get_frame_object(current_edit_idx)
            if current_frame_obj:
                for i in range(GRID_ROWS * GRID_COLS):
                    current_frame_obj.set_pad_color_name(i, DEFAULT_PAD_COLOR_ON_GRID_MAIN)
                self.animation_model.frame_content_updated.emit(current_edit_idx)
                self.animation_model._mark_modified()

    # --- Static Layout Slots ---
    def _on_apply_static_layout(self, layout_display_name: str):
        self._stop_animation_playback_if_active()
        print(f"DEBUG: Attempting to apply static layout: '{layout_display_name}'") # Debug Print
        layout_data = self.static_layout_model.load_layout(layout_display_name)
        print(f"DEBUG: Loaded layout data for '{layout_display_name}': {str(layout_data)[:100]}...") # Debug Print

        if layout_data:
            self.pad_grid_widget.update_grid_from_data(layout_data)
            if self.smartpad_controller.is_connected():
                self.smartpad_controller.set_all_pads_from_color_names(layout_data)
            
            current_edit_idx = self.animation_model.get_current_edit_frame_index()
            if current_edit_idx != -1:
                frame_obj = self.animation_model.get_frame_object(current_edit_idx)
                if frame_obj:
                    for i, color_name in enumerate(layout_data):
                        frame_obj.set_pad_color_name(i, color_name)
                    self.animation_model.frame_content_updated.emit(current_edit_idx)
                    self.animation_model._mark_modified()
            self.status_bar.showMessage(f"Layout '{layout_display_name}' applied.", 3000)
        else:
            self.status_bar.showMessage(f"Failed to load layout '{layout_display_name}'.", 3000)

    def _on_save_current_as_static_layout(self, display_name: str):
        self._stop_animation_playback_if_active()
        # Save the current state of the PadGridWidget's GUI
        current_grid_data = self.pad_grid_widget.get_current_grid_data_names()
        if self.static_layout_model.save_layout(display_name, current_grid_data):
            self.status_bar.showMessage(f"Static layout '{display_name}' saved.", 3000)
        # List will be updated by model's signal (layouts_list_changed)

    def _on_delete_static_layout(self, display_name: str):
        self._stop_animation_playback_if_active()
        if self.static_layout_model.delete_layout(display_name):
             self.status_bar.showMessage(f"Static layout '{display_name}' deleted.", 3000)
        # List will be updated by model's signal

    # --- Animation Model Update Slots ---
    def _update_animation_ui_from_model(self):
        all_frames_color_data = []
        for i in range(self.animation_model.get_frame_count()):
            frame_obj = self.animation_model.get_frame_object(i)
            if frame_obj:
                all_frames_color_data.append(frame_obj.get_all_color_names())
            else: # Should not happen with a valid model
                all_frames_color_data.append([DEFAULT_PAD_COLOR_ON_GRID_MAIN] * (GRID_ROWS * GRID_COLS))

        self.animation_timeline_widget.update_frames_display(
            frames_data_list=all_frames_color_data, # Pass the list of color lists
            current_edit_index=self.animation_model.get_current_edit_frame_index(),
            current_playback_index=self.animation_model.get_current_playback_frame_index()
        )
        self.animation_controls_widget.set_current_delay_ui(self.animation_model.frame_delay_ms)
        self.animation_controls_widget.set_current_loop_ui(self.animation_model.loop)
        self.animation_controls_widget.update_playback_button_ui(self.animation_model.get_is_playing())
        self.setWindowTitle(f"{APP_NAME_FULL} - {self.animation_model.name}{'*' if self.animation_model.is_modified else ''}")
        self._update_ui_enabled_state()

    def _on_animation_model_frame_content_updated(self, frame_index: int):
        if frame_index == self.animation_model.get_current_edit_frame_index():
            current_frame_obj = self.animation_model.get_frame_object(frame_index)
            if current_frame_obj:
                frame_data = current_frame_obj.get_all_color_names()
                self.pad_grid_widget.update_grid_from_data(frame_data)
        self.setWindowTitle(f"{APP_NAME_FULL} - {self.animation_model.name}{'*' if self.animation_model.is_modified else ''}")
        self._update_animation_ui_from_model() # Full refresh to ensure timeline thumbnails update

    def _on_animation_model_edit_frame_changed(self, new_edit_index: int):
        self._stop_animation_playback_if_active()
        if new_edit_index != -1:
            current_frame_obj = self.animation_model.get_frame_object(new_edit_index)
            if current_frame_obj:
                frame_data = current_frame_obj.get_all_color_names()
                self.pad_grid_widget.update_grid_from_data(frame_data)
                if self.smartpad_controller.is_connected():
                    self.smartpad_controller.set_all_pads_from_color_names(frame_data, silent=True)
            else:
                self.pad_grid_widget.clear_all_pads_gui()
        else:
            self.pad_grid_widget.clear_all_pads_gui()
            if self.smartpad_controller.is_connected():
                 self.smartpad_controller.clear_all_pads_on_device(silent=True)
        
        self.animation_timeline_widget.set_selected_frame_by_index(new_edit_index)
        self.setWindowTitle(f"{APP_NAME_FULL} - {self.animation_model.name}{'*' if self.animation_model.is_modified else ''}")
        self._update_ui_enabled_state()

    def _on_animation_model_playback_state_changed(self, is_playing: bool):
        self.animation_controls_widget.update_playback_button_ui(is_playing)
        if is_playing:
            self.status_bar.showMessage("Animation Playing...", 0)
            self.playback_timer.start(self.animation_model.frame_delay_ms)
        else:
            self.playback_timer.stop()
            if self.animation_model.get_current_playback_frame_index() == 0 and not self.playback_timer.isActive():
                self.status_bar.showMessage("Animation Stopped.", 3000)
                self._on_animation_model_edit_frame_changed(self.animation_model.get_current_edit_frame_index())
            else:
                self.status_bar.showMessage("Animation Paused.", 3000)
        self._update_ui_enabled_state()

    # --- Animation Control Slots & Animation Studio Button Slots ---
    def _stop_animation_playback_if_active(self):
        if self.animation_model.get_is_playing() or self.playback_timer.isActive():
            self.animation_model.stop_playback()

    def _on_play_animation(self):
        self._stop_animation_playback_if_active()
        if self.smartpad_controller.is_connected():
            if self.animation_model.get_frame_count() > 0:
                self.animation_model.start_playback()
            else:
                self.status_bar.showMessage("No frames to play.", 2000)
                self.animation_controls_widget.update_playback_button_ui(False)
        else:
            self.status_bar.showMessage("Connect SmartPad to play animation.", 3000)
            self.animation_controls_widget.update_playback_button_ui(False)

    def _on_pause_animation(self): self.animation_model.pause_playback()
    def _on_stop_animation(self): self.animation_model.stop_playback()

    def _on_add_frame_requested_snapshot(self):
        self._stop_animation_playback_if_active()
        # MAX_ANIMATION_FRAMES is now handled by the model, no need to check here
        snapshot_data = self.pad_grid_widget.get_current_grid_data_names() # Save current GUI state
        self.animation_model.add_frame(snapshot_data)

    def _on_add_frame_requested_blank(self):
        self._stop_animation_playback_if_active()
        self.animation_model.add_frame(None)

    def _on_duplicate_frame_requested(self):
        self._stop_animation_playback_if_active()
        current_idx = self.animation_model.get_current_edit_frame_index()
        if current_idx != -1:
            self.animation_model.duplicate_frame(current_idx)
        else:
            self.status_bar.showMessage("No frame selected to duplicate.", 2000)

    def _on_delete_frame_requested(self):
        self._stop_animation_playback_if_active()
        current_idx = self.animation_model.get_current_edit_frame_index()
        if current_idx != -1:
            self.animation_model.delete_frame(current_idx)
        else:
            self.status_bar.showMessage("No frame selected to delete.", 2000)

    # In MainWindow
    def _on_playback_timer_tick(self):
        if not self.animation_model.get_is_playing() or not self.smartpad_controller.is_connected():
            self.animation_model.stop_playback() 
            return

        current_playback_frame_index_before_step = self.animation_model.get_current_playback_frame_index() # Get index before stepping
        colors = self.animation_model.step_and_get_playback_frame_colors()
        
        # print(f"DEBUG MW: Playback Tick. Frame Index (just played): {current_playback_frame_index_before_step}. Colors to display: {str(colors)[:100]}...") # Print first few colors

        if colors:
            self.pad_grid_widget.update_grid_from_data(colors) 
            # print(f"DEBUG MW: About to call set_all_pads_from_color_names for frame {current_playback_frame_index_before_step}")
            self.smartpad_controller.set_all_pads_from_color_names(colors, silent=False) # <<<< TEMPORARILY SET silent=False
            
            all_frames_color_data = []
            for i in range(self.animation_model.get_frame_count()):
                frame_obj = self.animation_model.get_frame_object(i)
                if frame_obj: all_frames_color_data.append(frame_obj.get_all_color_names())
                else: all_frames_color_data.append([DEFAULT_PAD_COLOR_ON_GRID_MAIN] * (GRID_ROWS*GRID_COLS))

            # Determine which frame index to highlight as "just played"
            # If playback_frame_index has already advanced for the *next* frame, then current_playback_frame_index_before_step is correct.
            playback_highlight_idx = current_playback_frame_index_before_step

            self.animation_timeline_widget.update_frames_display(
                all_frames_color_data,
                self.animation_model.get_current_edit_frame_index(),
                playback_highlight_idx # Highlight the frame that was just displayed
            )
        
        if not self.animation_model.get_is_playing(): 
            self.playback_timer.stop()
            self._on_animation_model_playback_state_changed(False)
        

    # --- Animation File Operations (New Animation Studio Buttons) ---
    def _prompt_save_if_modified(self) -> bool:
        """Prompts to save if modified. Returns True if safe to proceed, False if cancelled."""
        if self.animation_model.is_modified:
            reply = QMessageBox.question(self, "Unsaved Changes",
                                         f"Animation '{self.animation_model.name}' has unsaved changes. Save now?",
                                         QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel,
                                         QMessageBox.StandardButton.Cancel)
            if reply == QMessageBox.StandardButton.Save:
                return self._on_save_animation_as_button_clicked() # Save As for now, can be smarter later
            elif reply == QMessageBox.StandardButton.Cancel:
                return False
        return True # Not modified or user chose to discard

    def _on_new_animation_button_clicked(self):
        self._stop_animation_playback_if_active()
        if not self._prompt_save_if_modified(): return

        self.animation_model.new_sequence()
        self._clear_current_grid_and_model_frame()
        if self.smartpad_controller.is_connected():
            self.smartpad_controller.clear_all_pads_on_device()
        self.status_bar.showMessage("New animation created.", 3000)
        self._populate_saved_animations_combo() # Refresh combo, might deselect
        self._update_animation_ui_from_model()

    def _get_animation_filenames(self) -> list[str]:
        """Returns a list of .json filenames from the animations directory."""
        if not os.path.isdir(self.animations_dir):
            return []
        return [f for f in os.listdir(self.animations_dir) if f.endswith(".json")]

    def _populate_saved_animations_combo(self):
        self.saved_animations_combo.blockSignals(True)
        self.saved_animations_combo.clear()
        self.saved_animations_combo.addItem("--- Select Saved Animation ---", userData=None) # Placeholder
        
        filenames_on_disk = self._get_animation_filenames() # e.g., ["duck_blinking.json", "my_anim_01.json"]
        
        # Create a list of tuples: (display_name, original_filename_base)
        animation_items = []
        for f_name_ext in filenames_on_disk:
            original_filename_base = os.path.splitext(f_name_ext)[0] # "duck_blinking"
            # Create a more user-friendly display name
            display_name = original_filename_base.replace("_", " ").replace("-", " ").title() # "Duck Blinking"
            animation_items.append((display_name, original_filename_base))
        
        # Sort by display name
        animation_items.sort(key=lambda item: item[0])
        
        if animation_items:
            for display_name, original_file_base in animation_items:
                self.saved_animations_combo.addItem(display_name, userData=original_file_base)
        else:
            self.saved_animations_combo.addItem("No saved animations.", userData=None)
            
        self.saved_animations_combo.setCurrentIndex(0)
        self.saved_animations_combo.blockSignals(False)
        self._on_saved_animation_combo_changed()

    def _on_saved_animation_combo_changed(self):
        is_valid_selection = (self.saved_animations_combo.currentIndex() > 0 and
                              self.saved_animations_combo.currentText() != "No saved animations.")
        self.load_animation_button.setEnabled(is_valid_selection and not self.animation_model.get_is_playing())
        self.delete_animation_button.setEnabled(is_valid_selection and not self.animation_model.get_is_playing())


    def _on_load_animation_button_clicked(self):
        self._stop_animation_playback_if_active()
        if not self._prompt_save_if_modified(): return

        filepath = None # Initialize filepath
        selected_index = self.saved_animations_combo.currentIndex()
        original_filename_base_from_combo = self.saved_animations_combo.itemData(selected_index)

        if original_filename_base_from_combo: # If userData (filename base) is valid
            filepath = os.path.join(self.animations_dir, f"{original_filename_base_from_combo}.json")
            print(f"DEBUG: Loading animation from combo selection. Filename base: '{original_filename_base_from_combo}', Path: '{filepath}'")
        else:
            # Fallback: Open file dialog if nothing good selected in combo or no userData
            print(f"DEBUG: No valid filename base from combo (userData: {original_filename_base_from_combo}). Opening file dialog.")
            dialog_filepath, _ = QFileDialog.getOpenFileName(
                self, "Open Animation", self.animations_dir, "SmartPad Animation Files (*.json)"
            )
            if dialog_filepath: # User selected a file
                 filepath = dialog_filepath
            # If user cancelled dialog, filepath remains None

        if filepath and os.path.exists(filepath): # Added os.path.exists check before loading
            if self.animation_model.load_from_file(filepath):
                self.status_bar.showMessage(f"Animation '{self.animation_model.name}' loaded.", 3000)
                # Try to re-select it in the combo based on the *new* model name (which comes from the file)
                # This is important if the display name in combo was slightly different from name in file
                self._select_animation_in_combo_by_name(self.animation_model.name)
            else:
                QMessageBox.warning(self, "Load Error", f"Could not parse animation from '{os.path.basename(filepath)}'.")
        elif filepath: # Filepath was determined, but it doesn't exist
            QMessageBox.warning(self, "Load Error", f"Animation file not found: '{os.path.basename(filepath)}'.")
            print(f"ERROR: File not found at path: {filepath}")
        # If filepath is None (dialog cancelled), do nothing further.
            
        self._update_animation_ui_from_model()

    def _select_animation_in_combo_by_name(self, animation_name_from_file: str):
        """Tries to select an item in the saved_animations_combo that matches the given name."""
        target_filename_base = animation_name_from_file.replace(" ", "_") # Simple guess
        found_idx = -1
        for i in range(self.saved_animations_combo.count()):
            item_data_filename_base = self.saved_animations_combo.itemData(i)

            if self.saved_animations_combo.itemText(i).lower() == animation_name_from_file.lower():
                found_idx = i
                break
            # Fallback: if userData (original_filename_base) matches a simple sanitized version
            if item_data_filename_base and item_data_filename_base.lower() == target_filename_base.lower():
                 found_idx = i
                 # break # Don't break, prefer display name match if possible
        if found_idx != -1:
            self.saved_animations_combo.setCurrentIndex(found_idx)
        else:
            self.saved_animations_combo.setCurrentIndex(0) # Default to placeholder
        self._on_saved_animation_combo_changed()
    
    def _on_save_animation_as_button_clicked(self) -> bool: # Returns True on successful save
        self._stop_animation_playback_if_active()
        if self.animation_model.get_frame_count() == 0:
            QMessageBox.information(self, "Save Animation", "Cannot save: Animation has no frames.")
            return False
        current_name_suggestion = self.animation_model.name if self.animation_model.name != "New Animation" else ""
        filepath, _ = QFileDialog.getSaveFileName(
            self, "Save Animation As",
            os.path.join(self.animations_dir, current_name_suggestion.replace(" ", "_") + ".json"),
            "SmartPad Animation Files (*.json)"
        )
        if filepath:
            # Update model name from filename if user changed it
            new_name = os.path.splitext(os.path.basename(filepath))[0].replace("_", " ")
            self.animation_model.set_name(new_name)
            if self.animation_model.save_to_file(filepath):
                self.status_bar.showMessage(f"Animation '{new_name}' saved.", 3000)
                self._populate_saved_animations_combo() # Refresh list
                # Try to select the newly saved item
                idx = self.saved_animations_combo.findText(new_name, Qt.MatchFlag.MatchFixedString | Qt.MatchFlag.MatchCaseSensitive)
                if idx !=-1: self.saved_animations_combo.setCurrentIndex(idx)
                self._update_animation_ui_from_model() # Update title bar, etc.
                return True
            else:
                QMessageBox.critical(self, "Save Error", f"Could not save animation to '{filepath}'.")
        return False

    def _on_delete_animation_button_clicked(self):
        self._stop_animation_playback_if_active()
        selected_display_name = self.saved_animations_combo.currentText()
        if self.saved_animations_combo.currentIndex() <= 0 or selected_display_name == "No saved animations.":
            self.status_bar.showMessage("No animation selected to delete.", 2000)
            return

        reply = QMessageBox.question(self, "Confirm Delete Animation",
                                     f"Are you sure you want to permanently delete the animation file for '{selected_display_name}'?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                     QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            filename_base = selected_display_name.replace(" ", "_")
            filepath_to_delete = os.path.join(self.animations_dir, f"{filename_base}.json")
            try:
                if os.path.exists(filepath_to_delete):
                    os.remove(filepath_to_delete)
                    self.status_bar.showMessage(f"Animation '{selected_display_name}' deleted.", 3000)
                    # If deleted animation was the current one, effectively 'new' it
                    if self.animation_model.loaded_filepath and \
                       os.path.normpath(self.animation_model.loaded_filepath) == os.path.normpath(filepath_to_delete):
                        self.animation_model.new_sequence()
                        self._update_animation_ui_from_model()
                else:
                    self.status_bar.showMessage(f"File for '{selected_display_name}' not found for deletion.", 3000)
            except OSError as e:
                QMessageBox.critical(self, "Delete Error", f"Could not delete file: {e}")
            finally:
                self._populate_saved_animations_combo() # Refresh list

    # --- General UI State ---
    def _update_ui_enabled_state(self):
        # ... (Implementation remains largely the same as previous full MainWindow script,
        #      but now needs to consider enabled state of new Animation Studio buttons)
        is_connected = self.smartpad_controller.is_connected()
        is_playing = self.animation_model.get_is_playing()
        has_frames = self.animation_model.get_frame_count() > 0
        frame_selected = self.animation_model.get_current_edit_frame_index() != -1

        can_edit_globally = is_connected and not is_playing
        
        self.color_palette_widget.setEnabled(can_edit_globally)
        self.pad_grid_widget.setEnabled(can_edit_globally)
        self.static_layout_widget.set_controls_enabled(can_edit_globally)
        self.animation_timeline_widget.set_controls_enabled(can_edit_globally)

        self.animation_controls_widget.set_controls_enabled(
            enabled=is_connected, has_frames=has_frames, frame_selected=frame_selected
        )
        if is_playing: # Further restrictions if playing
            self.animation_controls_widget.add_frame_button.setEnabled(False)
            self.animation_controls_widget.duplicate_button.setEnabled(False)
            self.animation_controls_widget.delete_button.setEnabled(False)
        
        # Animation Studio buttons
        self.saved_animations_combo.setEnabled(not is_playing)
        # Load and Delete buttons enabled state handled by _on_saved_animation_combo_changed
        self._on_saved_animation_combo_changed() # Call to ensure their state is correct
        self.new_animation_button.setEnabled(not is_playing)
        self.save_animation_as_button.setEnabled(not is_playing and has_frames) # Can only save if frames exist


    # --- Window State Saving/Loading & CloseEvent ---
    def save_settings(self):
        settings = QSettings(APP_AUTHOR_SETTINGS, APP_NAME_FULL)
        settings.setValue("geometry", self.saveGeometry())
        settings.setValue("windowState", self.saveState())

    def load_settings(self):
        settings = QSettings(APP_AUTHOR_SETTINGS, APP_NAME_FULL)
        geometry = settings.value("geometry")
        if geometry and isinstance(geometry, QByteArray): self.restoreGeometry(geometry)
        else: self.setGeometry(150, 150, INITIAL_WINDOW_WIDTH, INITIAL_WINDOW_HEIGHT)
        window_state = settings.value("windowState")
        if window_state and isinstance(window_state, QByteArray): self.restoreState(window_state)

    def closeEvent(self, event):
        if not self._prompt_save_if_modified():
            event.ignore()
            return
        self._stop_animation_playback_if_active()
        if self.smartpad_controller and self.smartpad_controller.is_connected():
            self.smartpad_controller.disconnect(turn_all_off=True)
        self.save_settings()
        super().closeEvent(event)

if __name__ == '__main__':
    if not QApplication.instance(): app = QApplication(sys.argv)
    else: app = QApplication.instance()
    qss_file = os.path.join(os.path.dirname(__file__), "..", "resources", "styles", "smartpad_style.qss") # Path relative to main_window.py
    if os.path.exists(qss_file):
        with open(qss_file, "r") as f: app.setStyleSheet(f.read())
    window = MainWindow()
    window.show()
    if not hasattr(app, '_exec_called_mw'):
        app._exec_called_mw = True
        sys.exit(app.exec())