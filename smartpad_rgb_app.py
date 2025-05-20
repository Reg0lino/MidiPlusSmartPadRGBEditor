# MidiPlusSmartPadRGBEditor/smartpad_rgb_app.py

import sys
import os
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import Qt # <<< ENSURE Qt is imported for attributes

# Attempt to import MainWindow. It will be created in a subsequent step.
# If this script is run before main_window.py is created, this will fail.
try:
    from main_window import MainWindow
except ImportError:
    print("ERROR: main_window.py not found or MainWindow class not defined yet.")
    print("Please ensure main_window.py is created before running this application.")
    sys.exit(1) # Exit if MainWindow can't be imported

APP_NAME = "MidiPlus SmartPad RGB Editor"
APP_VERSION = "0.1.0"
APP_AUTHOR = "YourAppNameOrAuthor" # Replace with your name/project name

# --- Define paths ---
# Determine if running as a script or frozen/packaged (e.g., by PyInstaller)
if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
    # Running in a PyInstaller bundle
    APP_BASE_PATH = sys._MEIPASS
else:
    # Running as a normal script
    APP_BASE_PATH = os.path.dirname(os.path.abspath(__file__))

RESOURCES_PATH = os.path.join(APP_BASE_PATH, "resources")
STYLES_PATH = os.path.join(RESOURCES_PATH, "styles")
ICONS_PATH = os.path.join(RESOURCES_PATH, "icons")


def load_stylesheet(app: QApplication) -> None:
    """Loads the QSS stylesheet."""
    stylesheet_file = os.path.join(STYLES_PATH, "smartpad_style.qss")
    if os.path.exists(stylesheet_file):
        try:
            with open(stylesheet_file, "r", encoding='utf-8') as f:
                app.setStyleSheet(f.read())
            print(f"INFO: Stylesheet '{stylesheet_file}' loaded successfully.")
        except Exception as e:
            print(f"WARNING: Could not load stylesheet '{stylesheet_file}': {e}")
    else:
        print(f"WARNING: Stylesheet file not found: '{stylesheet_file}'. Using default Qt style.")

def set_application_icon(app: QApplication) -> None:
    """Sets the application icon."""
    icon_file = os.path.join(ICONS_PATH, "app_icon.png")
    if os.path.exists(icon_file):
        app.setWindowIcon(QIcon(icon_file))
        print(f"INFO: Application icon '{icon_file}' set.")
    else:
        print(f"WARNING: Application icon file not found: '{icon_file}'.")


def main():
    """Main function to initialize and run the application."""
    # Enable High DPI scaling for PyQt6
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough # This is a valid Qt6 approach
    )
    # The following AA_ attributes are often problematic or handled differently in Qt6 directly
    # For AA_UseHighDpiPixmaps, it's generally on by default if resources are prepared correctly.
    # If you still face issues with pixmap quality, you might need to ensure your QIcon/QPixmap
    # usage includes high-resolution variants or SVG.

    # Let's comment out both problematic AA_ setAttribute calls for now to ensure the app launches.
    # QApplication.setAttribute(Qt.AA_EnableHighDpiScaling) # REMOVED/COMMENTED
    # QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)   # COMMENTED FOR NOW

    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(APP_VERSION)
    # app.setOrganizationName(APP_AUTHOR) # Optional

    print(f"--- Starting {APP_NAME} v{APP_VERSION} ---")
    print(f"Application Base Path: {APP_BASE_PATH}")
    print(f"Resources Path: {RESOURCES_PATH}")

    load_stylesheet(app)
    set_application_icon(app) # Set icon for the application globally (affects taskbar, etc.)

    try:
        main_window = MainWindow()
        main_window.setWindowTitle(f"{APP_NAME} v{APP_VERSION}") # Also set version in title
        main_window.show()
        sys.exit(app.exec())
    except Exception as e:
        print(f"FATAL ERROR: Could not initialize or run MainWindow: {e}")
        # Potentially show a QMessageBox here in a real app before exiting
        sys.exit(1)

if __name__ == '__main__':
    main()