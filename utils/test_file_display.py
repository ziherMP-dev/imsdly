"""
Test utility to display files from a directory using the FileSystemModel and FileListWidget.
Run this directly to test the file display functionality.
"""

import sys
import os
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QFileDialog
from PyQt6.QtCore import Qt

# Add parent directory to path to import from other modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.file_system import FileSystemModel
from ui.widgets.sd_card.file_list import FileListWidget

class TestFileDisplay(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("File Display Test")
        self.setGeometry(100, 100, 800, 600)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Create layout
        layout = QVBoxLayout(central_widget)
        
        # Add button to select directory
        self.select_dir_button = QPushButton("Select Directory")
        self.select_dir_button.clicked.connect(self.select_directory)
        layout.addWidget(self.select_dir_button)
        
        # Add file list widget
        self.file_list = FileListWidget()
        layout.addWidget(self.file_list)
        
        # Set dark theme
        self.setStyleSheet("""
            QMainWindow, QWidget {
                background-color: #1e1e1e;
                color: white;
            }
            QPushButton {
                background-color: #333;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #444;
            }
        """)
    
    def select_directory(self):
        """Open file dialog to select a directory."""
        directory = QFileDialog.getExistingDirectory(
            self, "Select Directory", os.path.expanduser("~")
        )
        
        if directory:
            print(f"Selected directory: {directory}")
            # Create file system model for the selected directory
            model = FileSystemModel(directory)
            model.scan_directory()
            
            # Set the model to the file list widget
            self.file_list.set_file_model(model)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TestFileDisplay()
    window.show()
    sys.exit(app.exec()) 