import logging
import os
from typing import List, Dict, Any, Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QStatusBar, QFrame, QButtonGroup
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from models.file_system import FileSystemModel
from ui.widgets.sd_card.file_list import FileListWidget

# Set up logging
logger = logging.getLogger(__name__)

class SDCardPanel(QWidget):
    """Panel for displaying SD card contents and providing file operations."""
    
    def __init__(self, parent=None):
        """Initialize the SD card panel.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        logger.debug("Initializing SDCardPanel")
        self.selected_card = None
        self.file_model: Optional[FileSystemModel] = None
        self.card_info: Optional[Dict] = None
        self._setup_ui()
        self._connect_signals()
        
    def _setup_ui(self) -> None:
        """Set up the UI components."""
        logger.debug("Setting up SDCardPanel UI")
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Header with card name
        self.content_header = QLabel("No SD Card Selected")
        self.content_header.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        self.content_header.setStyleSheet("color: white;")
        layout.addWidget(self.content_header)
        
        # Control bar
        control_bar = QHBoxLayout()
        
        # Scan button
        self.scan_button = QPushButton("Scan Files")
        self.scan_button.setEnabled(False)
        self.scan_button.setStyleSheet("""
            QPushButton {
                background-color: #333;
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #0b5ed7;
            }
            QPushButton:disabled {
                background-color: #1a1a3d;
                color: #dee2e6;
            }
        """)
        control_bar.addWidget(self.scan_button)
        
        # Filter buttons
        filter_layout = QHBoxLayout()
        filter_layout.setSpacing(0)
        
        # Create button group for filter buttons (non-exclusive)
        self.filter_group = QButtonGroup()
        self.filter_group.setExclusive(False)
        
        # Photos button
        self.photos_button = QPushButton("Photos")
        self.photos_button.setCheckable(True)
        self.photos_button.setChecked(True)  # Set as default
        self.photos_button.setStyleSheet("""
            QPushButton {
                background-color: #333;
                color: white;
                border: none;
                padding: 6px 12px;
                border-top-left-radius: 4px;
                border-bottom-left-radius: 4px;
            }
            QPushButton:checked {
                background-color: #0d6efd;
            }
            QPushButton:hover:!checked {
                background-color: #444;
            }
        """)
        self.filter_group.addButton(self.photos_button)
        filter_layout.addWidget(self.photos_button)
        
        # Videos button
        self.videos_button = QPushButton("Videos")
        self.videos_button.setCheckable(True)
        self.videos_button.setChecked(True)  # Set as default
        self.videos_button.setStyleSheet("""
            QPushButton {
                background-color: #333;
                color: white;
                border: none;
                padding: 6px 12px;
                border-top-right-radius: 4px;
                border-bottom-right-radius: 4px;
            }
            QPushButton:checked {
                background-color: #0d6efd;
            }
            QPushButton:hover:!checked {
                background-color: #444;
            }
        """)
        self.filter_group.addButton(self.videos_button)
        filter_layout.addWidget(self.videos_button)
        
        control_bar.addLayout(filter_layout)
        
        # Filter status label
        self.filter_status_label = QLabel("Showing: All Media Files")
        self.filter_status_label.setStyleSheet("color: #888;")
        control_bar.addWidget(self.filter_status_label)
        
        # Spacer
        control_bar.addStretch()
        
        layout.addLayout(control_bar)
        
        # Add separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        separator.setStyleSheet("background-color: #444;")
        layout.addWidget(separator)
        
        # Status bar
        status_bar = QStatusBar()
        self.status_label = QLabel("No SD card selected")
        status_bar.addWidget(self.status_label)
        status_bar.setStyleSheet("""
            QStatusBar {
                background-color: #333;
                color: #ccc;
            }
        """)
        
        layout.addWidget(status_bar)
        
        # Create file list widget
        self.file_list = FileListWidget()
        layout.addWidget(self.file_list)
        
        self.setLayout(layout)
        
        # Set dark background
        self.setStyleSheet("background-color: #1e1e1e;")
        
    def _connect_signals(self) -> None:
        """Connect UI signals to slots."""
        self.scan_button.clicked.connect(self._handle_scan_clicked)
        self.filter_group.buttonClicked.connect(self._handle_filter_changed)
        
    def _handle_filter_changed(self, button: QPushButton) -> None:
        """Handle filter button click.
        
        Args:
            button: The clicked filter button
        """
        logger.debug(f"Filter changed: {button.text()}")
        
        # Update filter status label
        active_filters = []
        if self.photos_button.isChecked():
            active_filters.append("Photos")
        if self.videos_button.isChecked():
            active_filters.append("Videos")
            
        if not active_filters:
            self.filter_status_label.setText("Showing: All Files")
        elif len(active_filters) == 2:
            self.filter_status_label.setText("Showing: All Media Files")
        else:
            self.filter_status_label.setText(f"Showing: {' and '.join(active_filters)}")
        
        if self.file_model and self.selected_card:
            # Get current filter settings
            file_types = []
            if self.photos_button.isChecked():
                file_types.append('image')
            if self.videos_button.isChecked():
                file_types.append('video')
                
            # Update status with what we're scanning for
            scan_types = []
            if 'image' in file_types:
                scan_types.append("photos")
            if 'video' in file_types:
                scan_types.append("videos")
                
            if not file_types:
                self.status_label.setText("Scanning all files...")
                self.file_model.scan_directory()
            else:
                self.status_label.setText(f"Scanning {' and '.join(scan_types)}...")
                self.file_model.scan_directory(file_types=file_types)
            
            # Update the file list with the scan results
            self.file_list.set_file_model(self.file_model, file_types=file_types)
            
            # Update status with scan results
            files = self.file_model.get_files()
            if file_types:
                files = [f for f in files if f['type'] in file_types]
            
            type_counts = {}
            for file in files:
                file_type = file['type']
                type_counts[file_type] = type_counts.get(file_type, 0) + 1
                
            status_parts = []
            if 'image' in type_counts:
                status_parts.append(f"{type_counts['image']} photos")
            if 'video' in type_counts:
                status_parts.append(f"{type_counts['video']} videos")
                
            self.status_label.setText(f"Found {len(files)} files ({', '.join(status_parts)})")
        
    def _handle_card_selected(self, card_info: Dict[str, Any]) -> None:
        """Handle SD card selection.
        
        Args:
            card_info: Dictionary containing information about the selected card
        """
        logger.debug(f"SDCardPanel._handle_card_selected: {card_info}")
        self.selected_card = card_info
        self.content_header.setText(f"Content of {card_info.get('name', 'SD Card')}")
        self.status_label.setText(f"Selected: {card_info.get('name', 'SD Card')} ({card_info.get('path', '')})")
        self.scan_button.setEnabled(True)
        
        # Set the card information and update the view
        self.set_card_info(card_info)
        
    def _handle_scan_clicked(self) -> None:
        """Handle scan button click."""
        if self.selected_card:
            self.status_label.setText(f"Scanning {self.selected_card.get('name', 'SD Card')}...")
            
            # Get current filter settings
            file_types = []
            if self.photos_button.isChecked():
                file_types.append('image')
            if self.videos_button.isChecked():
                file_types.append('video')
                
            # If no filters are selected, scan for all files
            if not file_types:
                self.status_label.setText("Scanning all files...")
                self.file_model.scan_directory()
            else:
                # Update status with what we're scanning for
                scan_types = []
                if 'image' in file_types:
                    scan_types.append("photos")
                if 'video' in file_types:
                    scan_types.append("videos")
                self.status_label.setText(f"Scanning {' and '.join(scan_types)}...")
                self.file_model.scan_directory(file_types=file_types)
            
            # Update the file list with the scan results
            self.file_list.set_file_model(self.file_model, file_types=file_types)
            
            # Update status with scan results
            files = self.file_model.get_files()
            if file_types:
                files = [f for f in files if f['type'] in file_types]
            
            type_counts = {}
            for file in files:
                file_type = file['type']
                type_counts[file_type] = type_counts.get(file_type, 0) + 1
                
            status_parts = []
            if 'image' in type_counts:
                status_parts.append(f"{type_counts['image']} photos")
            if 'video' in type_counts:
                status_parts.append(f"{type_counts['video']} videos")
                
            self.status_label.setText(f"Found {len(files)} files ({', '.join(status_parts)})")
        
    def set_card_info(self, card_info: dict):
        """Set the card information and update the view.
        
        Args:
            card_info: Dictionary containing card information
        """
        logger.debug(f"SDCardPanel.set_card_info: {card_info}")
        self.card_info = card_info
        
        # Check if the card has a valid path
        if 'path' not in card_info or not card_info['path']:
            logger.warning("Card info missing path")
            return
        
        path = card_info['path']
        # Verify the path exists
        if not os.path.exists(path):
            logger.warning(f"Card path does not exist: {path}")
            return
            
        # Create file system model and scan for files
        logger.debug(f"Creating FileSystemModel with path: {path}")
        self.file_model = FileSystemModel(path)
        self.file_model.scan_directory()
        
        # Get file count for debugging
        file_count = len(self.file_model.get_files())
        logger.debug(f"Found {file_count} files in {path}")
        
        # Update file list widget with model, defaulting to media files
        logger.debug("Updating file list widget with model")
        self.file_list.set_file_model(self.file_model, file_types=['image', 'video'])
        
        # Log the file list state
        logger.debug(f"File list visible: {self.file_list.isVisible()}")
        logger.debug(f"File list widget count: {self.file_list.list_widget.count()}") 