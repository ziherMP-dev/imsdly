#!/usr/bin/env python3
import sys
import os

# Add parent directory to path to import modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QLabel, QHBoxLayout
from PyQt6.QtCore import Qt
from ui.import_settings_panel import ImportSettingsPanel


class TestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Import Settings Test")
        self.setGeometry(100, 100, 800, 700)
        self.setStyleSheet("background-color: #1e1e1e; color: white;")
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Add header
        header = QLabel("Import Settings Panel")
        header.setStyleSheet("font-size: 20px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(header)
        
        # Import settings panel
        self.import_settings = ImportSettingsPanel()
        layout.addWidget(self.import_settings)
        
        # Status information
        status_layout = QHBoxLayout()
        status_layout.setContentsMargins(0, 10, 0, 0)
        
        self.status_label = QLabel("Settings will appear here when changed")
        self.status_label.setStyleSheet("color: #aaa; padding: 5px; background-color: #333; border-radius: 3px;")
        status_layout.addWidget(self.status_label)
        
        # Add test button to dump settings
        test_button = QPushButton("Show Current Settings")
        test_button.setStyleSheet("""
            QPushButton {
                background-color: #0078d7;
                color: white;
                border: none;
                border-radius: 3px;
                padding: 8px 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1c84de;
            }
        """)
        test_button.clicked.connect(self.display_settings)
        status_layout.addWidget(test_button)
        
        layout.addLayout(status_layout)
        
        # Connect signals
        self.import_settings.settings_changed.connect(self.handle_settings_changed)
    
    def handle_settings_changed(self):
        """Handler for settings changed signal."""
        self.display_settings()
    
    def display_settings(self):
        """Display the current settings."""
        dest_folder = self.import_settings.get_destination_folder() or "Not set"
        org_method = "By Date" if self.import_settings.get_organization_method() == self.import_settings.ORG_BY_DATE else "Custom"
        date_format = self.import_settings.get_date_format()
        custom_format = self.import_settings.get_custom_format() or "Not set"
        extract_exif = "Yes" if self.import_settings.get_extract_exif() else "No"
        
        settings_text = (
            f"Destination: {dest_folder}\n"
            f"Organization: {org_method}\n"
            f"Date Format: {date_format}\n"
            f"Custom Format: {custom_format}\n"
            f"Extract EXIF: {extract_exif}"
        )
        
        self.status_label.setText(settings_text)
        print(settings_text)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TestWindow()
    window.show()
    sys.exit(app.exec()) 