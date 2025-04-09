"""
Test utility to check SD card access and file loading.
Run this directly to test if your SD card is accessible and can be read.
"""

import sys
import os
import logging
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QLabel, QTextEdit, QFileDialog
from PyQt6.QtCore import Qt

# Add parent directory to path to import from other modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.file_system import FileSystemModel
from handlers.sd_card.detector import SDCardDetector

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class TestSDCardAccess(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SD Card Access Test")
        self.setGeometry(100, 100, 800, 600)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Create layout
        layout = QVBoxLayout(central_widget)
        
        # Add button to detect SD cards
        self.detect_button = QPushButton("Detect SD Cards")
        self.detect_button.clicked.connect(self.detect_sd_cards)
        layout.addWidget(self.detect_button)
        
        # Add button to select directory manually
        self.select_dir_button = QPushButton("Select Directory")
        self.select_dir_button.clicked.connect(self.select_directory)
        layout.addWidget(self.select_dir_button)
        
        # Add text area for logs
        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        layout.addWidget(self.log_area)
        
        # Create SD card detector
        self.sd_detector = SDCardDetector()
        self.sd_detector.start()
        
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
            QTextEdit {
                background-color: #252525;
                color: #ddd;
                border: 1px solid #555;
            }
        """)
        
        # Set up custom handler for logging to text area
        self.log_handler = TextEditHandler(self.log_area)
        logger.addHandler(self.log_handler)
        
        # Initial card detection
        self.detect_sd_cards()
    
    def detect_sd_cards(self):
        """Detect SD cards and check file access."""
        self.log_area.clear()
        logger.info("Checking for SD cards...")
        
        cards = self.sd_detector.get_current_cards()
        logger.info(f"Found {len(cards)} cards")
        
        for card in cards:
            logger.info(f"Card: {card.get('name', 'Unknown')} at {card.get('path', 'Unknown path')}")
            
            # Check if path exists
            path = card.get('path', '')
            if os.path.exists(path):
                logger.info(f"Path exists: {path}")
                
                # Try to list directory contents
                try:
                    files = os.listdir(path)
                    logger.info(f"Successfully listed directory. Found {len(files)} items")
                    
                    # Show some files
                    if files:
                        logger.info("Sample files:")
                        for i, file in enumerate(files[:5]):
                            logger.info(f"  - {file}")
                        if len(files) > 5:
                            logger.info(f"  - ... and {len(files) - 5} more")
                    
                    # Try to scan with FileSystemModel
                    logger.info("Trying to scan with FileSystemModel...")
                    model = FileSystemModel(path)
                    model.scan_directory()
                    model_files = model.get_files()
                    logger.info(f"FileSystemModel found {len(model_files)} files")
                    
                except Exception as e:
                    logger.error(f"Error accessing directory: {e}")
            else:
                logger.error(f"Path does not exist: {path}")
    
    def select_directory(self):
        """Open file dialog to select a directory."""
        directory = QFileDialog.getExistingDirectory(
            self, "Select Directory", os.path.expanduser("~")
        )
        
        if directory:
            logger.info(f"Selected directory: {directory}")
            
            # Check if path exists
            if os.path.exists(directory):
                logger.info(f"Path exists: {directory}")
                
                # Try to list directory contents
                try:
                    files = os.listdir(directory)
                    logger.info(f"Successfully listed directory. Found {len(files)} items")
                    
                    # Try to scan with FileSystemModel
                    logger.info("Trying to scan with FileSystemModel...")
                    model = FileSystemModel(directory)
                    model.scan_directory()
                    model_files = model.get_files()
                    logger.info(f"FileSystemModel found {len(model_files)} files")
                    
                except Exception as e:
                    logger.error(f"Error accessing directory: {e}")
            else:
                logger.error(f"Path does not exist: {directory}")

class TextEditHandler(logging.Handler):
    """Logging handler that writes to a QTextEdit."""
    
    def __init__(self, text_edit):
        super().__init__()
        self.text_edit = text_edit
        self.setLevel(logging.INFO)
        self.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    
    def emit(self, record):
        msg = self.format(record)
        self.text_edit.append(msg)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TestSDCardAccess()
    window.show()
    sys.exit(app.exec()) 