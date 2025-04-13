#!/usr/bin/env python3
import sys
import os

# Add parent directory to path to import modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from ui.import_settings_panel import ImportSettingsPanel


class TestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Import Settings Test")
        self.setGeometry(100, 100, 600, 400)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        layout = QVBoxLayout(central_widget)
        
        # Import settings panel
        self.import_settings = ImportSettingsPanel()
        layout.addWidget(self.import_settings)
        
        # Connect signals
        self.import_settings.settings_changed.connect(self.handle_settings_changed)
    
    def handle_settings_changed(self):
        """Handler for settings changed signal."""
        print(f"Destination folder changed to: {self.import_settings.get_destination_folder()}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TestWindow()
    window.show()
    sys.exit(app.exec()) 