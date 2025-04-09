import os
from typing import List, Dict, Any, Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QStatusBar, QFrame, QButtonGroup, QComboBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QIcon

from models.file_system import FileSystemModel
from ui.widgets.sd_card.file_list import FileListWidget

class SDCardPanel(QWidget):
    """Panel for displaying SD card contents and providing file operations."""
    
    def __init__(self, parent=None):
        """Initialize the SD card panel."""
        super().__init__(parent)
        self.selected_card = None
        self.file_model: Optional[FileSystemModel] = None
        self.card_info: Optional[Dict] = None
        self._setup_ui()
        self._connect_signals()
        
    def _setup_ui(self) -> None:
        """Set up the UI components."""
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
        
        # View mode toggle button
        self.view_mode_button = QPushButton("Icon View")
        self.view_mode_button.setStyleSheet("""
            QPushButton {
                background-color: #333;
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #444;
            }
        """)
        control_bar.addWidget(self.view_mode_button)
        
        # Sort controls
        sort_label = QLabel("Sort by:")
        sort_label.setStyleSheet("color: #888;")
        control_bar.addWidget(sort_label)
        
        # Sort combobox
        self.sort_combo = QComboBox()
        self.sort_combo.addItems(["Name", "Size", "Type"])
        self.sort_combo.setStyleSheet("""
            QComboBox {
                background-color: #333;
                color: white;
                border: none;
                padding: 4px 8px;
                border-radius: 4px;
                min-width: 80px;
            }
            QComboBox:hover {
                background-color: #444;
            }
            QComboBox QAbstractItemView {
                background-color: #333;
                color: white;
                border: 1px solid #555;
                selection-background-color: #0d6efd;
            }
        """)
        control_bar.addWidget(self.sort_combo)
        
        # Sort order button
        self.sort_order_button = QPushButton("↑")
        self.sort_order_button.setToolTip("Sort ascending")
        self.sort_order_button.setStyleSheet("""
            QPushButton {
                background-color: #333;
                color: white;
                border: none;
                padding: 4px 8px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #444;
            }
        """)
        control_bar.addWidget(self.sort_order_button)
        
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
        
        # Track current view mode
        self.current_view_mode = self.file_list.LIST_VIEW
        
    def _connect_signals(self) -> None:
        """Connect UI signals to slots."""
        self.scan_button.clicked.connect(self._handle_scan_clicked)
        self.filter_group.buttonClicked.connect(self._handle_filter_changed)
        
        # Connect sort controls
        self.sort_combo.currentTextChanged.connect(self._handle_sort_changed)
        self.sort_order_button.clicked.connect(self._handle_sort_order_changed)
        
        # Connect view mode toggle button
        self.view_mode_button.clicked.connect(self._handle_view_mode_toggle)
        
    def _handle_view_mode_toggle(self) -> None:
        """Toggle between list view and icon view."""
        if self.current_view_mode == self.file_list.LIST_VIEW:
            # Switch to icon view
            self.current_view_mode = self.file_list.ICON_VIEW
            self.view_mode_button.setText("List View")
        else:
            # Switch to list view
            self.current_view_mode = self.file_list.LIST_VIEW
            self.view_mode_button.setText("Icon View")
            
        # Update the file list view mode
        self.file_list.set_view_mode(self.current_view_mode)
        
        # Print debug info
        try:
            import rawpy
            print("\n--- RAW SUPPORT INFO ---")
            print(f"rawpy version: {rawpy.__version__}")
            print("RawPy is available and should support common RAW formats")
            # List some common formats that should be supported
            print("Commonly supported formats include: CR2, NEF, ARW, DNG, etc.")
            print("------------------------\n")
        except Exception as e:
            print(f"Error getting RAW support info: {str(e)}")
            print("Make sure rawpy is installed: pip install rawpy")
        
    def _handle_filter_changed(self, button: QPushButton) -> None:
        """Handle filter button click.
        
        Args:
            button: The clicked filter button
        """
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
        
    def _handle_sort_changed(self, sort_text: str) -> None:
        """Handle sort selection change.
        
        Args:
            sort_text: The selected sort option text
        """
        if not self.file_model:
            return
            
        # Map UI text to model sort key
        sort_map = {
            "Name": "name",
            "Size": "size",
            "Type": "type"
        }
        
        # Get sort order from button
        sort_order = "desc" if self.sort_order_button.text() == "↓" else "asc"
        
        # Apply sorting
        self.file_model.sort_files(sort_map[sort_text], sort_order)
        
        # Update file list with current filters
        file_types = []
        if self.photos_button.isChecked():
            file_types.append('image')
        if self.videos_button.isChecked():
            file_types.append('video')
            
        self.file_list.set_file_model(self.file_model, file_types=file_types if file_types else None)
            
    def _handle_sort_order_changed(self) -> None:
        """Toggle sort direction between ascending and descending."""
        if not self.file_model:
            return
            
        # Toggle button text
        is_ascending = self.sort_order_button.text() == "↑"
        if is_ascending:
            self.sort_order_button.setText("↓")
            self.sort_order_button.setToolTip("Sort descending")
            sort_order = "desc"
        else:
            self.sort_order_button.setText("↑")
            self.sort_order_button.setToolTip("Sort ascending")
            sort_order = "asc"
            
        # Get current sort key from combo box
        sort_map = {
            "Name": "name",
            "Size": "size",
            "Type": "type"
        }
        sort_key = sort_map[self.sort_combo.currentText()]
        
        # Apply sorting
        self.file_model.sort_files(sort_key, sort_order)
        
        # Update file list with current filters
        file_types = []
        if self.photos_button.isChecked():
            file_types.append('image')
        if self.videos_button.isChecked():
            file_types.append('video')
            
        self.file_list.set_file_model(self.file_model, file_types=file_types if file_types else None)
        
    def _handle_card_selected(self, card_info: Dict[str, Any]) -> None:
        """Handle SD card selection.
        
        Args:
            card_info: Dictionary containing information about the selected card
        """
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
        self.card_info = card_info
        
        # Check if the card has a valid path
        if 'path' not in card_info or not card_info['path']:
            return
        
        path = card_info['path']
        # Verify the path exists
        if not os.path.exists(path):
            return
            
        # Create file system model and scan for files
        self.file_model = FileSystemModel(path)
        self.file_model.scan_directory()
        
        # Get file count for debugging
        file_count = len(self.file_model.get_files())
        
        # Update file list widget with model, defaulting to media files
        self.file_list.set_file_model(self.file_model, file_types=['image', 'video']) 