import os
from typing import List, Dict, Any, Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QButtonGroup, QComboBox
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
        
        # View mode buttons
        view_buttons_layout = QHBoxLayout()
        view_buttons_layout.setSpacing(0)
        
        # Create button group for view mode buttons
        self.view_mode_group = QButtonGroup()
        self.view_mode_group.setExclusive(True)
        
        # List view button
        self.list_view_button = QPushButton("List")
        self.list_view_button.setCheckable(True)
        self.list_view_button.setChecked(True)  # Default to list view
        self.list_view_button.setStyleSheet("""
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
        self.view_mode_group.addButton(self.list_view_button)
        view_buttons_layout.addWidget(self.list_view_button)
        
        # Icon view button
        self.icon_view_button = QPushButton("Thumbnails")
        self.icon_view_button.setCheckable(True)
        self.icon_view_button.setStyleSheet("""
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
        self.view_mode_group.addButton(self.icon_view_button)
        view_buttons_layout.addWidget(self.icon_view_button)
        
        control_bar.addLayout(view_buttons_layout)
        
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
        
        # Create file list widget
        self.file_list = FileListWidget()
        self.file_list.file_selected.connect(self._handle_file_selected)
        layout.addWidget(self.file_list)
        
        self.setLayout(layout)
        
        # Set dark background
        self.setStyleSheet("background-color: #1e1e1e;")
        
        # Track current view mode - matching the default button state (list view)
        self.current_view_mode = self.file_list.LIST_VIEW
        
        # Initialize file model as None until a card is selected
        self.file_model = None
        
        # Set up initial state
        self.selected_card = None
        self._update_filter_buttons()
        
    def _connect_signals(self) -> None:
        """Connect UI signals to slots."""
        self.scan_button.clicked.connect(self._handle_scan_clicked)
        self.filter_group.buttonClicked.connect(self._handle_filter_changed)
        
        # Connect sort controls
        self.sort_combo.currentTextChanged.connect(self._handle_sort_changed)
        self.sort_order_button.clicked.connect(self._handle_sort_order_changed)
        
        # Connect view mode buttons
        self.list_view_button.clicked.connect(lambda: self._handle_view_mode_changed(self.file_list.LIST_VIEW))
        self.icon_view_button.clicked.connect(lambda: self._handle_view_mode_changed(self.file_list.ICON_VIEW))
        
    def _handle_view_mode_changed(self, mode: int) -> None:
        """Handle view mode change.
        
        Args:
            mode: The view mode to change to
        """
        # Update the current view mode
        self.current_view_mode = mode
        
        # Update button states
        self.list_view_button.setChecked(mode == self.file_list.LIST_VIEW)
        self.icon_view_button.setChecked(mode == self.file_list.ICON_VIEW)
        
        # Update the file list view mode
        self.file_list.set_view_mode(mode)
        
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
                
            # Update the file list with the current filters
            self.file_list.set_file_model(self.file_model, file_types=file_types if file_types else None)
        
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
        
        # Update filter buttons
        self._update_filter_buttons()
        
    def _update_filter_buttons(self) -> None:
        """Update the filter buttons based on the current file model."""
        if self.file_model:
            self.photos_button.setEnabled(True)
            self.videos_button.setEnabled(True)
        else:
            self.photos_button.setEnabled(False)
            self.videos_button.setEnabled(False)
        
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
        
        # Update file list with current filters
        file_types = []
        if self.photos_button.isChecked():
            file_types.append('image')
        if self.videos_button.isChecked():
            file_types.append('video')
            
        self.file_list.set_file_model(self.file_model, file_types=file_types if file_types else None)
        
    def _handle_file_selected(self, file_info: Dict[str, Any]) -> None:
        """Handle file selection.
        
        Args:
            file_info: Dictionary containing information about the selected file
        """
        # Handle file selection
        print(f"Selected file: {file_info['name']}") 