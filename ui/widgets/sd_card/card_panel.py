from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout, QPushButton
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from typing import Optional
import logging
import os

from models.file_system import FileSystemModel
from .file_list import FileListWidget

# Set up logging
logger = logging.getLogger(__name__)

class SDCardPanel(QWidget):
    """Panel for displaying SD card contents."""
    
    file_selected = pyqtSignal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.file_model: Optional[FileSystemModel] = None
        self.setup_ui()
        
    def setup_ui(self):
        """Set up the UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(8)
        
        # Header with card info
        header_layout = QHBoxLayout()
        
        self.card_name_label = QLabel("SD Card")
        self.card_name_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        self.card_name_label.setStyleSheet("color: white;")
        header_layout.addWidget(self.card_name_label)
        
        header_layout.addStretch()
        
        # Refresh button
        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.clicked.connect(self.handle_refresh)
        header_layout.addWidget(self.refresh_button)
        
        layout.addLayout(header_layout)
        
        # Card path
        self.path_label = QLabel()
        self.path_label.setFont(QFont("Arial", 9))
        self.path_label.setStyleSheet("color: #aaa;")
        layout.addWidget(self.path_label)
        
        # Create file list widget
        self.file_list = FileListWidget()
        self.file_list.file_selected.connect(self._handle_file_selected)
        layout.addWidget(self.file_list)
        
        # Set background color
        self.setStyleSheet("background-color: #1e1e1e;")
        
    def set_card_info(self, card_info: dict):
        """Set the SD card information and update the view.
        
        Args:
            card_info: Dictionary containing card information
        """
        logger.info(f"Setting card info: {card_info}")
        
        if 'name' in card_info:
            self.card_name_label.setText(card_info['name'])
        if 'path' in card_info:
            self.path_label.setText(card_info['path'])
            self.set_card_path(card_info['path'])
        
    def set_card_path(self, path: str):
        """Set the SD card path and update the view.
        
        Args:
            path: Path to the SD card
        """
        if not path:
            logger.warning("Empty path provided to set_card_path")
            return
            
        logger.info(f"Setting card path: {path}")
        
        # Verify the path exists
        if not os.path.exists(path):
            logger.warning(f"Path does not exist: {path}")
            self.path_label.setText(f"Path not found: {path}")
            return
            
        # Create file system model with the path
        self.file_model = FileSystemModel(path)
        
        # Scan for files
        self.file_model.scan_directory()
        
        # Update file list widget with the model
        self.file_list.set_file_model(self.file_model)
        
    def handle_refresh(self):
        """Handle refresh button click."""
        logger.info("Refreshing file list")
        if self.file_model:
            self.file_model.scan_directory()
            self.file_list.update_view()
        else:
            logger.warning("Cannot refresh: File model not initialized")
            
    def _handle_file_selected(self, file_info: dict):
        """Handle file selection event.
        
        Args:
            file_info: Dictionary containing file information
        """
        logger.info(f"File selected: {file_info.get('name', 'Unknown')}")
        self.file_selected.emit(file_info) 