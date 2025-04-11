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
        # Track sorting preferences
        self.current_sort_key = "name"
        self.current_sort_order = "asc"
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
        
        # Create a fixed container for scan button and filter toggles
        left_controls = QWidget()
        left_controls.setFixedWidth(300)  # Fixed width to prevent expanding
        left_layout = QHBoxLayout(left_controls)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(0)
        
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
        left_layout.addWidget(self.scan_button)
        
        # Filter buttons
        filter_layout = QHBoxLayout()
        filter_layout.setSpacing(0)
        filter_layout.setContentsMargins(10, 0, 0, 0)  # Add left margin for spacing from scan button
        
        # Create button group for filter buttons (non-exclusive)
        self.filter_group = QButtonGroup()
        self.filter_group.setExclusive(False)
        
        # Photos button with small toggle
        self.photos_button = QPushButton()
        self.photos_button.setCheckable(True)
        self.photos_button.setChecked(True)  # Set as default
        
        photos_layout = QHBoxLayout()
        photos_layout.setContentsMargins(8, 0, 8, 0)
        photos_layout.setSpacing(6)
        
        # Create toggle switch widget
        photos_toggle = QFrame()
        photos_toggle.setFixedSize(28, 16)
        photos_toggle.setStyleSheet("""
            QFrame {
                background-color: #0d6efd;
                border-radius: 8px;
                border: 1px solid #0d6efd;
            }
        """)
        
        # Create toggle handle
        photos_handle = QFrame(photos_toggle)
        photos_handle.setFixedSize(14, 14)
        photos_handle.move(12, 1)
        photos_handle.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 7px;
            }
        """)
        
        photos_layout.addWidget(photos_toggle)
        
        # Add label text
        photos_label = QLabel("Photos")
        photos_label.setStyleSheet("color: white;")
        photos_layout.addWidget(photos_label)
        
        # Set custom widget as layout for button
        photos_widget = QWidget()
        photos_widget.setLayout(photos_layout)
        
        self.photos_toggle = photos_toggle
        self.photos_handle = photos_handle
        self.photos_label = photos_label
        
        # Create container widget with similar styling to previous buttons
        photos_container = QFrame()
        photos_container.setStyleSheet("""
            QFrame {
                background-color: transparent;
                border: none;
            }
        """)
        
        photos_container_layout = QHBoxLayout(photos_container)
        photos_container_layout.setContentsMargins(6, 6, 6, 6)
        photos_container_layout.addWidget(photos_widget)
        photos_container_layout.addStretch()
        
        # Add to filter layout
        filter_layout.addWidget(photos_container)
        
        # Videos button with small toggle
        self.videos_button = QPushButton()
        self.videos_button.setCheckable(True)
        self.videos_button.setChecked(True)  # Set as default
        
        videos_layout = QHBoxLayout()
        videos_layout.setContentsMargins(8, 0, 8, 0)
        videos_layout.setSpacing(6)
        
        # Create toggle switch widget
        videos_toggle = QFrame()
        videos_toggle.setFixedSize(28, 16)
        videos_toggle.setStyleSheet("""
            QFrame {
                background-color: #0d6efd;
                border-radius: 8px;
                border: 1px solid #0d6efd;
            }
        """)
        
        # Create toggle handle
        videos_handle = QFrame(videos_toggle)
        videos_handle.setFixedSize(14, 14)
        videos_handle.move(12, 1)
        videos_handle.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 7px;
            }
        """)
        
        videos_layout.addWidget(videos_toggle)
        
        # Add label text
        videos_label = QLabel("Videos")
        videos_label.setStyleSheet("color: white;")
        videos_layout.addWidget(videos_label)
        
        # Set custom widget as layout for button
        videos_widget = QWidget()
        videos_widget.setLayout(videos_layout)
        
        self.videos_toggle = videos_toggle
        self.videos_handle = videos_handle
        self.videos_label = videos_label
        
        # Create container widget with similar styling to previous buttons
        videos_container = QFrame()
        videos_container.setStyleSheet("""
            QFrame {
                background-color: transparent;
                border: none;
            }
        """)
        
        videos_container_layout = QHBoxLayout(videos_container)
        videos_container_layout.setContentsMargins(6, 6, 6, 6)
        videos_container_layout.addWidget(videos_widget)
        videos_container_layout.addStretch()
        
        # Add to filter layout
        filter_layout.addWidget(videos_container)
        
        # Setup filter buttons
        self.photos_container = photos_container
        self.videos_container = videos_container
        
        # Connect mouse events for toggle switches
        photos_container.mousePressEvent = lambda e: self._toggle_photos()
        videos_container.mousePressEvent = lambda e: self._toggle_videos()
        
        # Add filter layout to left controls
        left_layout.addLayout(filter_layout)
        
        # Add fixed left controls to main control bar
        control_bar.addWidget(left_controls)
        
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
                background-color: #222;
                color: #fff;
                border: 1px solid #444;
                padding: 5px 11px 5px 11px;
                border-right: 2px solid #444;
                border-bottom: 2px solid #444;
            }
            QPushButton:hover:!checked {
                background-color: #444;
            }
        """)
        self.view_mode_group.addButton(self.list_view_button)
        view_buttons_layout.addWidget(self.list_view_button)
        
        # Icons view button (without thumbnails)
        self.icons_view_button = QPushButton("Icons")
        self.icons_view_button.setCheckable(True)
        self.icons_view_button.setStyleSheet("""
            QPushButton {
                background-color: #333;
                color: white;
                border: none;
                padding: 6px 12px;
            }
            QPushButton:checked {
                background-color: #222;
                color: #fff;
                border: 1px solid #444;
                padding: 5px 11px 5px 11px;
                border-right: 2px solid #444;
                border-bottom: 2px solid #444;
            }
            QPushButton:hover:!checked {
                background-color: #444;
            }
        """)
        self.view_mode_group.addButton(self.icons_view_button)
        view_buttons_layout.addWidget(self.icons_view_button)
        
        # Thumbnails view button
        self.thumbnail_view_button = QPushButton("Thumbnails")
        self.thumbnail_view_button.setCheckable(True)
        self.thumbnail_view_button.setStyleSheet("""
            QPushButton {
                background-color: #333;
                color: white;
                border: none;
                padding: 6px 12px;
                border-top-right-radius: 4px;
                border-bottom-right-radius: 4px;
            }
            QPushButton:checked {
                background-color: #222;
                color: #fff;
                border: 1px solid #444;
                padding: 5px 11px 5px 11px;
                border-right: 2px solid #444;
                border-bottom: 2px solid #444;
            }
            QPushButton:hover:!checked {
                background-color: #444;
            }
        """)
        self.view_mode_group.addButton(self.thumbnail_view_button)
        view_buttons_layout.addWidget(self.thumbnail_view_button)
        
        control_bar.addLayout(view_buttons_layout)
        
        # Sort controls
        sort_label = QLabel("Sort by:")
        sort_label.setStyleSheet("color: #888;")
        control_bar.addWidget(sort_label)
        
        # Sort combobox
        self.sort_combo = QComboBox()
        self.sort_combo.addItems(["Name", "Date", "Size", "Type"])
        self.sort_combo.setItemData(1, "Sort by modification date", Qt.ItemDataRole.ToolTipRole)
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
        self.file_list.files_selected.connect(self._handle_files_selected)
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
        self.icons_view_button.clicked.connect(lambda: self._handle_view_mode_changed(self.file_list.ICONS_VIEW))
        self.thumbnail_view_button.clicked.connect(lambda: self._handle_view_mode_changed(self.file_list.THUMBNAIL_VIEW))
        
        # Connect selection signals
        self.file_list.files_selected.connect(self._handle_files_selected)
        
    def _handle_view_mode_changed(self, mode: int) -> None:
        """Handle view mode change.
        
        Args:
            mode: The view mode to change to
        """
        # Update the current view mode
        self.current_view_mode = mode
        
        # Update button states
        self.list_view_button.setChecked(mode == self.file_list.LIST_VIEW)
        self.icons_view_button.setChecked(mode == self.file_list.ICONS_VIEW)
        self.thumbnail_view_button.setChecked(mode == self.file_list.THUMBNAIL_VIEW)
        
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
        
    def _toggle_photos(self):
        """Toggle photos filter on/off."""
        is_checked = not self.photos_button.isChecked()
        self.photos_button.setChecked(is_checked)
        
        # Update toggle appearance
        if is_checked:
            self.photos_toggle.setStyleSheet("""
                QFrame {
                    background-color: #0d6efd;
                    border-radius: 8px;
                    border: 1px solid #0d6efd;
                }
            """)
            self.photos_handle.move(12, 1)
        else:
            self.photos_toggle.setStyleSheet("""
                QFrame {
                    background-color: #444;
                    border-radius: 8px;
                    border: 1px solid #555;
                }
            """)
            self.photos_handle.move(2, 1)
        
        # Trigger the filter changed handler
        self._handle_filter_changed(self.photos_button)
    
    def _toggle_videos(self):
        """Toggle videos filter on/off."""
        is_checked = not self.videos_button.isChecked()
        self.videos_button.setChecked(is_checked)
        
        # Update toggle appearance
        if is_checked:
            self.videos_toggle.setStyleSheet("""
                QFrame {
                    background-color: #0d6efd;
                    border-radius: 8px;
                    border: 1px solid #0d6efd;
                }
            """)
            self.videos_handle.move(12, 1)
        else:
            self.videos_toggle.setStyleSheet("""
                QFrame {
                    background-color: #444;
                    border-radius: 8px;
                    border: 1px solid #555;
                }
            """)
            self.videos_handle.move(2, 1)
        
        # Trigger the filter changed handler
        self._handle_filter_changed(self.videos_button)

    def _handle_filter_changed(self, button: QPushButton) -> None:
        """Handle filter button click.
        
        Args:
            button: The clicked filter button
        """
        # Update filter status label - only show "All Files" when both filters are OFF
        if not self.photos_button.isChecked() and not self.videos_button.isChecked():
            self.filter_status_label.setText("Showing: All Files")
        else:
            self.filter_status_label.setText("")
        
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
            "Date": "date",
            "Size": "size",
            "Type": "type"
        }
        
        # Update current sort settings
        self.current_sort_key = sort_map[sort_text]
        
        # Apply sorting
        self.file_model.sort_files(self.current_sort_key, self.current_sort_order)
        
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
            
        # Toggle button text and update current sort order
        is_ascending = self.sort_order_button.text() == "↑"
        if is_ascending:
            self.sort_order_button.setText("↓")
            self.sort_order_button.setToolTip("Sort descending")
            self.current_sort_order = "desc"
        else:
            self.sort_order_button.setText("↑")
            self.sort_order_button.setToolTip("Sort ascending")
            self.current_sort_order = "asc"
            
        # Apply sorting
        self.file_model.sort_files(self.current_sort_key, self.current_sort_order)
        
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
            # Get current filter settings
            file_types = []
            if self.photos_button.isChecked():
                file_types.append('image')
            if self.videos_button.isChecked():
                file_types.append('video')
                
            # If no filters are selected, scan for all files
            if not file_types:
                self.file_model.scan_directory()
            else:
                self.file_model.scan_directory(file_types=file_types)
            
            # Update the file list with the scan results
            self.file_list.set_file_model(self.file_model, file_types=file_types)
        
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
        
        # Apply current sorting settings
        self.file_model.sort_files(self.current_sort_key, self.current_sort_order)
        
        # Update file list widget with model, defaulting to media files
        self.file_list.set_file_model(self.file_model, file_types=['image', 'video'])
        
        # Update toggle states to reflect current button states
        self._update_toggle_states()
        
        # Update filter buttons
        self._update_filter_buttons()
        
        # Update sort UI to match current settings
        sort_map_reverse = {
            "name": "Name",
            "date": "Date",
            "size": "Size",
            "type": "Type"
        }
        self.sort_combo.setCurrentText(sort_map_reverse[self.current_sort_key])
        self.sort_order_button.setText("↓" if self.current_sort_order == "desc" else "↑")
        self.sort_order_button.setToolTip(f"Sort {'descending' if self.current_sort_order == 'desc' else 'ascending'}")
        
    def _update_toggle_states(self):
        """Update the toggle switch appearances based on current button states."""
        # Update photos toggle
        if self.photos_button.isChecked():
            self.photos_toggle.setStyleSheet("""
                QFrame {
                    background-color: #0d6efd;
                    border-radius: 8px;
                    border: 1px solid #0d6efd;
                }
            """)
            self.photos_handle.move(12, 1)
        else:
            self.photos_toggle.setStyleSheet("""
                QFrame {
                    background-color: #444;
                    border-radius: 8px;
                    border: 1px solid #555;
                }
            """)
            self.photos_handle.move(2, 1)
            
        # Update videos toggle
        if self.videos_button.isChecked():
            self.videos_toggle.setStyleSheet("""
                QFrame {
                    background-color: #0d6efd;
                    border-radius: 8px;
                    border: 1px solid #0d6efd;
                }
            """)
            self.videos_handle.move(12, 1)
        else:
            self.videos_toggle.setStyleSheet("""
                QFrame {
                    background-color: #444;
                    border-radius: 8px;
                    border: 1px solid #555;
                }
            """)
            self.videos_handle.move(2, 1)
        
    def _update_filter_buttons(self) -> None:
        """Update the filter buttons based on the current file model."""
        if self.file_model:
            self.photos_button.setEnabled(True)
            self.videos_button.setEnabled(True)
        else:
            self.photos_button.setEnabled(False)
            self.videos_button.setEnabled(False)
        
        # Update filter status label - only show "All Files" when both filters are OFF
        if not self.photos_button.isChecked() and not self.videos_button.isChecked():
            self.filter_status_label.setText("Showing: All Files")
        else:
            self.filter_status_label.setText("")
        
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
        # Handle single file selection
        print(f"Selected file: {file_info['name']}")
        
    def _handle_files_selected(self, files: List[Dict[str, Any]]) -> None:
        """Handle multiple files selected.
        
        Args:
            files: List of file info dictionaries for selected files
        """
        # Report selected files count
        if files:
            count = len(files)
            print(f"Selected {count} file{'s' if count > 1 else ''}")
        else:
            print("No files selected") 