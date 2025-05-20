# MidiPlusSmartPadRGBEditor/gui/static_layout_widget.py

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QComboBox, QPushButton,
    QGroupBox, QLabel, QInputDialog, QMessageBox # Ensured imports
)
from PyQt6.QtCore import pyqtSignal, Qt # Qt import kept for consistency, may not be used directly

class StaticLayoutWidget(QGroupBox):
    """
    Widget for managing static 8x8 pad layouts: selecting, applying, saving, and deleting.
    """
    apply_layout_requested = pyqtSignal(str)
    save_current_as_requested = pyqtSignal(str)
    delete_layout_requested = pyqtSignal(str)
    
    _request_current_grid_data_for_save = pyqtSignal(str)

    def __init__(self, parent: QWidget | None = None):
        super().__init__("Static Pad Layouts", parent)

        self.group_layout = QVBoxLayout(self)

        selection_layout = QHBoxLayout()
        self.layout_combo = QComboBox()
        self.layout_combo.setPlaceholderText("--- Select Static Layout ---")
        self.layout_combo.setMinimumWidth(150)
        self.layout_combo.currentIndexChanged.connect(self._on_combo_selection_changed)
        selection_layout.addWidget(self.layout_combo, 1)
        self.group_layout.addLayout(selection_layout)

        buttons_layout = QHBoxLayout()
        self.apply_button = QPushButton("Apply Layout")
        self.apply_button.setToolTip("Load the selected static layout onto the grid.")
        self.apply_button.clicked.connect(self._on_apply_clicked)
        buttons_layout.addWidget(self.apply_button)

        self.save_as_button = QPushButton("Save Current As...")
        self.save_as_button.setToolTip("Save the current 8x8 grid as a new static layout.")
        self.save_as_button.clicked.connect(self._on_save_as_clicked)
        buttons_layout.addWidget(self.save_as_button)
        
        self.group_layout.addLayout(buttons_layout)

        self.delete_button = QPushButton("Delete Selected Layout")
        self.delete_button.setToolTip("Delete the static layout selected in the dropdown.")
        self.delete_button.clicked.connect(self._on_delete_clicked)
        self.group_layout.addWidget(self.delete_button)

        self.update_layouts_list([])
        self._on_combo_selection_changed()

    def _on_combo_selection_changed(self):
        has_valid_selection = (self.layout_combo.currentIndex() >= 0 and
                               self.layout_combo.currentText() != "--- Select Static Layout ---" and
                               self.layout_combo.currentText() != "No layouts available.")
        self.apply_button.setEnabled(has_valid_selection)
        self.delete_button.setEnabled(has_valid_selection)

    def _on_apply_clicked(self):
        selected_layout_name = self.layout_combo.currentText()
        if selected_layout_name and selected_layout_name != "--- Select Static Layout ---" and selected_layout_name != "No layouts available.":
            self.apply_layout_requested.emit(selected_layout_name)

    def _on_save_as_clicked(self):
        layout_name, ok = QInputDialog.getText(
            self,
            "Save Static Layout",
            "Enter a name for the current grid layout:"
            # NO flags argument here
        )
        if ok and layout_name and layout_name.strip():
            self.save_current_as_requested.emit(layout_name.strip())
        elif ok and (not layout_name or not layout_name.strip()):
            QMessageBox.warning(self, "Save Layout Error", "Layout name cannot be empty.")

    def _on_delete_clicked(self):
        selected_layout_name = self.layout_combo.currentText()
        if selected_layout_name and selected_layout_name != "--- Select Static Layout ---" and selected_layout_name != "No layouts available.":
            reply = QMessageBox.question(
                self,
                "Confirm Delete",
                f"Are you sure you want to delete the static layout '{selected_layout_name}'?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
                # NO flags argument here
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.delete_layout_requested.emit(selected_layout_name)

    def update_layouts_list(self, layout_names: list[str]):
        current_selection = self.layout_combo.currentText()
        self.layout_combo.blockSignals(True)
        self.layout_combo.clear()
        
        if layout_names:
            self.layout_combo.addItem("--- Select Static Layout ---")
            self.layout_combo.addItems(sorted(layout_names))
            if current_selection in layout_names:
                self.layout_combo.setCurrentText(current_selection)
            elif current_selection == "--- Select Static Layout ---" or current_selection == "No layouts available.":
                 self.layout_combo.setCurrentIndex(0)
            else:
                 self.layout_combo.setCurrentIndex(0)
        else:
            self.layout_combo.addItem("No layouts available.")
        
        self.layout_combo.blockSignals(False)
        self._on_combo_selection_changed()

    def set_controls_enabled(self, enabled: bool):
        self.layout_combo.setEnabled(enabled)
        self.save_as_button.setEnabled(enabled)
        if enabled:
            self._on_combo_selection_changed()
        else:
            self.apply_button.setEnabled(False)
            self.delete_button.setEnabled(False)

if __name__ == '__main__':
    from PyQt6.QtWidgets import QApplication # Ensure QApplication is imported

    app = QApplication([])
    widget = StaticLayoutWidget()

    test_layouts = ["My Pattern 1", "Checkerboard", "Cool Design Alpha"]
    widget.update_layouts_list(test_layouts)

    widget.apply_layout_requested.connect(lambda name: print(f"Signal: Apply layout '{name}'"))
    widget.save_current_as_requested.connect(lambda name: print(f"Signal: Save current as '{name}'"))
    widget.delete_layout_requested.connect(lambda name: print(f"Signal: Delete layout '{name}'"))

    enable_button = QPushButton("Toggle Enabled (Test)")
    def toggle_widget_enabled():
        widget.set_controls_enabled(not widget.layout_combo.isEnabled())
    enable_button.clicked.connect(toggle_widget_enabled)
    
    temp_window = QWidget()
    temp_layout = QVBoxLayout(temp_window) # Ensure QVBoxLayout is imported
    temp_layout.addWidget(widget)
    temp_layout.addWidget(enable_button)
    temp_window.setWindowTitle("StaticLayoutWidget Test")
    temp_window.show()
    
    app.exec()