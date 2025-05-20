# MidiPlusSmartPadRGBEditor/gui/midi_connection_widget.py

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QComboBox, QPushButton, QLabel, QGroupBox, QApplication
)
from PyQt6.QtCore import pyqtSignal, Qt
import sys

class MidiConnectionWidget(QGroupBox): # Inherit from QGroupBox for easy title
    """
    Widget for MIDI port selection, connection, and status display.
    """
    connect_requested = pyqtSignal(str)      # Emits port name to connect to
    disconnect_requested = pyqtSignal()      # Emits when disconnect is requested

    def __init__(self, parent: QWidget | None = None):
        super().__init__("MIDI Connection", parent)
        
        # Main layout for this QGroupBox
        self.group_layout = QVBoxLayout(self) # Layout for the QGroupBox content

        # Horizontal layout for port selection and button
        connection_controls_layout = QHBoxLayout()

        self.port_label = QLabel("Port:")
        connection_controls_layout.addWidget(self.port_label)

        self.port_combo = QComboBox()
        self.port_combo.setPlaceholderText("Select MIDI Port")
        self.port_combo.setMinimumWidth(150)
        connection_controls_layout.addWidget(self.port_combo, 1) # ComboBox takes available stretch

        self.connect_button = QPushButton("Connect")
        self.connect_button.setCheckable(False) # It's a command button, not a toggle
        self.connect_button.clicked.connect(self._on_connect_button_clicked)
        connection_controls_layout.addWidget(self.connect_button)
        
        self.group_layout.addLayout(connection_controls_layout)

        # Status label (optional, could be handled by main window's status bar)
        # self.status_label = QLabel("Status: Disconnected")
        # self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # self.group_layout.addWidget(self.status_label)

        # Initial state
        self.update_ports_list([]) # Start with an empty list or "No ports"
        self.set_connection_status(False, "Disconnected")


    def _on_connect_button_clicked(self):
        if self.connect_button.text() == "Connect":
            selected_port = self.port_combo.currentText()
            if selected_port and selected_port != "No MIDI output ports found.":
                self.connect_requested.emit(selected_port)
            else:
                # self.status_label.setText("Status: Please select a valid port.")
                pass # MainWindow status bar can show this
        else: # Button text is "Disconnect"
            self.disconnect_requested.emit()

    def update_ports_list(self, ports: list[str]):
        """Populates the MIDI port combobox."""
        current_selection = self.port_combo.currentText()
        self.port_combo.blockSignals(True)
        self.port_combo.clear()
        if ports:
            self.port_combo.addItems(ports)
            # Try to re-select previous or find a smartpad-like port
            if current_selection in ports:
                self.port_combo.setCurrentText(current_selection)
            else:
                smartpad_port_index = -1
                for i, port_name in enumerate(ports):
                    # Simplified keyword check for initial selection
                    if any(keyword in port_name.lower() for keyword in ["smartpad", "midiplus", "usb midi"]):
                        smartpad_port_index = i
                        break
                if smartpad_port_index != -1:
                    self.port_combo.setCurrentIndex(smartpad_port_index)
                elif self.port_combo.count() > 0:
                     self.port_combo.setCurrentIndex(0)
            self.port_combo.setEnabled(True)
            self.connect_button.setEnabled(True)
        else:
            self.port_combo.addItem("No MIDI output ports found.")
            self.port_combo.setEnabled(False)
            self.connect_button.setEnabled(False) # Can't connect if no ports
        self.port_combo.blockSignals(False)

    def set_connection_status(self, is_connected: bool, message: str):
        """Updates the UI based on connection status."""
        if is_connected:
            self.connect_button.setText("Disconnect")
            self.port_combo.setEnabled(False) # Don't allow port change while connected
            # self.status_label.setText(f"Status: Connected to {message}")
        else:
            self.connect_button.setText("Connect")
            self.port_combo.setEnabled(self.port_combo.count() > 0 and self.port_combo.itemText(0) != "No MIDI output ports found.")
            # self.status_label.setText(f"Status: {message}")
        
        # Ensure connect button is enabled if there are valid ports and not connected
        if not is_connected and self.port_combo.isEnabled():
            self.connect_button.setEnabled(True)
        elif is_connected: # If connected, disconnect is always possible
             self.connect_button.setEnabled(True)
        else: # Not connected and no valid ports
             self.connect_button.setEnabled(False)


if __name__ == '__main__':
    # Example usage for testing MidiConnectionWidget standalone
    app = QApplication(sys.argv)
    widget = MidiConnectionWidget()
    
    # Simulate port data
    test_ports = ["Virtual MIDI Port 1", "MidiPlus SmartPAD", "Some Other MIDI Device"]
    widget.update_ports_list(test_ports)
    
    widget.show()
    sys.exit(app.exec())