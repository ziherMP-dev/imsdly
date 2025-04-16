from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QLineEdit, QFileDialog, QGroupBox, QFormLayout, QComboBox,
    QCheckBox, QRadioButton, QButtonGroup, QScrollArea, QFrame,
    QSizePolicy, QTreeWidget, QTreeWidgetItem, QSpacerItem,
    QTabWidget, QTableWidget, QTableWidgetItem, QHeaderView, QSpinBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QSettings, QSize, QEvent
from PyQt6.QtGui import QIcon, QFont

class ImportSettingsPanel(QWidget):
    """Panel for configuring import settings, including destination folder."""
    
    # Signal emitted when settings change
    settings_changed = pyqtSignal()
    
    # Organization methods
    ORG_BY_DATE = "date"
    ORG_BY_CUSTOM = "custom"
    
    # Date formats
    DATE_FORMATS = [
        {"id": "yyyy-mm-dd", "display": "YYYY-MM-DD (e.g., 2023-04-15)"},
        {"id": "yyyy/mm/dd", "display": "YYYY/MM/DD (e.g., 2023/04/15)"},
        {"id": "yyyy-mm", "display": "YYYY-MM (e.g., 2023-04)"},
        {"id": "yyyy/mm", "display": "YYYY/MM (e.g., 2023/04)"},
        {"id": "yyyy", "display": "YYYY (e.g., 2023)"},
        {"id": "yyyy/mm/dd/hh", "display": "YYYY/MM/DD/HH (e.g., 2023/04/15/10)"}
    ]
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.settings_file_path = self._get_settings_file_path()
        self.setup_ui()
        
        # Don't connect signals until UI is fully initialized
        self._connect_signals()
        
        # Load settings after UI is fully set up
        self.load_settings()
        self.update_ui_states()
    
    def _get_settings_file_path(self):
        """Get the path to the settings file."""
        import os
        # Get app data directory
        if os.name == 'nt':  # Windows
            app_data = os.getenv('APPDATA')
            if not app_data:
                app_data = os.path.expanduser('~')
        else:  # macOS/Linux
            app_data = os.path.expanduser('~/.config')
            
        # Create Imsdly directory if it doesn't exist
        imsdly_dir = os.path.join(app_data, 'Imsdly')
        os.makedirs(imsdly_dir, exist_ok=True)
        
        # Return settings file path
        return os.path.join(imsdly_dir, 'import_settings.ini')
        
    def _connect_signals(self):
        """Connect UI signals after UI is fully initialized."""
        # Connect signals for live updates
        self.org_by_date.toggled.connect(self._handle_org_method_changed)
        self.org_by_custom.toggled.connect(self._handle_org_method_changed)
        self.date_format_combo.currentIndexChanged.connect(self.handle_settings_changed)
        self.custom_format_input.textChanged.connect(self._handle_custom_format_changed)
        self.extract_exif.toggled.connect(self.handle_settings_changed)
        
        # Connect batch renaming signals
        if hasattr(self, 'keep_original'):
            self.keep_original.stateChanged.connect(self._handle_keep_original_changed)
            
            # Basic settings signals
            if hasattr(self, 'basic_filename'):
                self.basic_filename.textChanged.connect(self.handle_settings_changed)
                
            # Advanced settings signals
            if hasattr(self, 'advanced_group'):
                self.advanced_group.toggled.connect(self._handle_advanced_mode_toggled)
                
            # Advanced options signals
            self.pattern_input.textChanged.connect(self.handle_settings_changed)
            self.seq_start.valueChanged.connect(self.handle_settings_changed)
            self.seq_digits.valueChanged.connect(self.handle_settings_changed)
            self.reset_by_folder.toggled.connect(self.handle_settings_changed)
            self.reset_by_date.toggled.connect(self.handle_settings_changed)
    
    def setup_ui(self):
        """Set up the UI components."""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(10)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        
        # Create the folder settings tab
        folder_settings_tab = self.create_folder_settings_tab()
        
        # Create the batch rename tab
        batch_rename_tab = self.create_batch_rename_tab()
        
        # Add tabs to the tab widget
        self.tab_widget.addTab(folder_settings_tab, "Folder Settings")
        self.tab_widget.addTab(batch_rename_tab, "Batch Rename")
        
        # Add tab widget to main layout
        main_layout.addWidget(self.tab_widget)
        
        # Apply dark theme
        self.apply_styles()
    
    def create_folder_settings_tab(self):
        """Create the folder settings tab with existing settings UI."""
        tab = QWidget()
        
        # Create a scroll area to handle overflow
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        
        # Create content widget for scroll area
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(0, 0, 0, 0)
        scroll_layout.setSpacing(15)
        
        # --- Destination Folder Group ---
        destination_group = QGroupBox("Destination Folder")
        destination_layout = QVBoxLayout(destination_group)
        
        # Description label
        description_label = QLabel("Select where your files will be imported:")
        description_label.setWordWrap(True)
        destination_layout.addWidget(description_label)
        
        # Folder selection controls
        folder_layout = QHBoxLayout()
        
        self.destination_path = QLineEdit()
        self.destination_path.setReadOnly(True)
        self.destination_path.setPlaceholderText("No folder selected")
        
        browse_button = QPushButton("Browse...")
        browse_button.setFixedWidth(100)
        browse_button.clicked.connect(self.handle_browse_clicked)
        
        folder_layout.addWidget(self.destination_path)
        folder_layout.addWidget(browse_button)
        destination_layout.addLayout(folder_layout)
        
        scroll_layout.addWidget(destination_group)
        
        # --- Organization Method Group ---
        organization_group = QGroupBox("Organization Method")
        organization_layout = QVBoxLayout(organization_group)
        
        # Organization method options
        self.org_method_group = QButtonGroup(self)
        
        # By date option
        self.org_by_date = QRadioButton("Organize by Date")
        self.org_by_date.setChecked(True)  # Default
        self.org_method_group.addButton(self.org_by_date)
        organization_layout.addWidget(self.org_by_date)
        
        # Date format options - simplified layout
        date_format_container = QHBoxLayout()
        date_format_container.setContentsMargins(20, 5, 0, 10)
        
        # Create date format label
        date_format_label = QLabel("Date Format:")
        date_format_container.addWidget(date_format_label)
        
        # Create the combobox
        self.date_format_combo = QComboBox()
        self.date_format_combo.setStyleSheet("""
            QComboBox {
                background-color: #2d2d2d;
                border: 1px solid #444;
                border-radius: 3px;
                padding: 5px;
                color: #e1e1e1;
                min-width: 200px;
            }
        """)
        
        # Add items to combobox
        for date_format in self.DATE_FORMATS:
            self.date_format_combo.addItem(date_format["display"], date_format["id"])
        
        date_format_container.addWidget(self.date_format_combo)
        
        # Create a dropdown button (like in SD card panel)
        dropdown_button = QPushButton("↓")
        dropdown_button.setFixedWidth(24)
        dropdown_button.setToolTip("Show date format options")
        dropdown_button.setStyleSheet("""
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
        date_format_container.addWidget(dropdown_button)
        
        # Connect the dropdown button to open the combo box popup
        dropdown_button.clicked.connect(lambda: self.date_format_combo.showPopup())
        
        # Add to main layout
        organization_layout.addLayout(date_format_container)
        
        # Custom structure option
        self.org_by_custom = QRadioButton("Custom Folder Structure")
        self.org_method_group.addButton(self.org_by_custom)
        organization_layout.addWidget(self.org_by_custom)
        
        # Custom structure editor
        custom_format_layout = QVBoxLayout()
        custom_format_layout.setContentsMargins(20, 5, 0, 0)
        
        custom_format_help = QLabel(
            "Define a custom folder structure using the following variables:"
            "<ul>"
            "<li><b>{YYYY}</b> - Year (4 digits)</li>"
            "<li><b>{MM}</b> - Month (2 digits)</li>"
            "<li><b>{DD}</b> - Day (2 digits)</li>"
            "<li><b>{hh}</b> - Hour (2 digits)</li>"
            "<li><b>{mm}</b> - Minute (2 digits)</li>"
            "<li><b>{camera}</b> - Camera model from EXIF</li>"
            "<li><b>{type}</b> - File type (image/video)</li>"
            "</ul>"
            "Example: <i>{YYYY}/{MM}/{DD}/{type}</i> → 2023/04/15/image/"
        )
        custom_format_help.setWordWrap(True)
        custom_format_layout.addWidget(custom_format_help)
        
        self.custom_format_input = QLineEdit()
        self.custom_format_input.setPlaceholderText("{YYYY}/{MM}/{DD}/{type}")
        custom_format_layout.addWidget(self.custom_format_input)
        
        organization_layout.addLayout(custom_format_layout)
        
        scroll_layout.addWidget(organization_group)
        
        # --- EXIF Options Group ---
        exif_group = QGroupBox("EXIF Options")
        exif_layout = QVBoxLayout(exif_group)
        
        self.extract_exif = QCheckBox("Extract and save EXIF metadata")
        self.extract_exif.setChecked(True)
        exif_layout.addWidget(self.extract_exif)
        
        exif_description = QLabel(
            "When enabled, EXIF data (camera info, settings, GPS, etc.) will be "
            "extracted from image files and preserved alongside the images."
        )
        exif_description.setWordWrap(True)
        exif_description.setStyleSheet("color: #999; font-size: 11px;")
        exif_layout.addWidget(exif_description)
        
        scroll_layout.addWidget(exif_group)
        
        # --- Preview Group ---
        preview_group = QGroupBox("Structure Preview")
        preview_layout = QVBoxLayout(preview_group)
        
        self.preview_tree = QTreeWidget()
        self.preview_tree.setHeaderHidden(True)
        self.preview_tree.setMinimumHeight(150)
        self.preview_tree.setStyleSheet("""
            QTreeWidget {
                background-color: #2d2d2d;
                border: 1px solid #444;
                color: #e1e1e1;
            }
            QTreeWidget::item {
                padding: 4px;
            }
            QTreeWidget::item:selected {
                background-color: #0078d7;
            }
        """)
        preview_layout.addWidget(self.preview_tree)
        
        scroll_layout.addWidget(preview_group)
        
        # Finalize scroll area
        scroll_area.setWidget(scroll_content)
        
        # Create tab layout and add scroll area
        tab_layout = QVBoxLayout(tab)
        tab_layout.setContentsMargins(0, 0, 0, 0)
        tab_layout.addWidget(scroll_area)
        
        return tab
    
    def create_batch_rename_tab(self):
        """Create the batch rename tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Create a scroll area for batch rename content
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        
        # Create content widget for scroll area
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(0, 0, 0, 0)
        scroll_layout.setSpacing(15)
        
        # Add option to keep original filenames (disable batch renaming)
        keep_original_layout = QHBoxLayout()
        self.keep_original = QCheckBox("Keep original filenames (disable batch renaming)")
        self.keep_original.setStyleSheet("font-weight: bold;")
        keep_original_layout.addWidget(self.keep_original)
        keep_original_layout.addStretch()
        scroll_layout.addLayout(keep_original_layout)
        
        # Add a separator line
        separator1 = QFrame()
        separator1.setFrameShape(QFrame.Shape.HLine)
        separator1.setFrameShadow(QFrame.Shadow.Sunken)
        separator1.setStyleSheet("background-color: #444;")
        scroll_layout.addWidget(separator1)
        
        # --- Basic Settings Group ---
        basic_group = QGroupBox("Basic Settings")
        basic_layout = QVBoxLayout(basic_group)
        
        # Simple filename pattern with automatic sequence
        filename_layout = QHBoxLayout()
        filename_layout.addWidget(QLabel("Filename:"))
        
        self.basic_filename = QLineEdit()
        self.basic_filename.setPlaceholderText("e.g., IMG_{seq} (will add sequence number automatically)")
        filename_layout.addWidget(self.basic_filename)
        
        basic_layout.addLayout(filename_layout)
        
        # Help text
        basic_help = QLabel("A sequence number with padding of 3 digits will be added automatically (e.g., '001', '002', etc.)")
        basic_help.setStyleSheet("color: #999; font-size: 11px;")
        basic_layout.addWidget(basic_help)
        
        scroll_layout.addWidget(basic_group)
        self.basic_group = basic_group
        
        # Add a separator line
        separator2 = QFrame()
        separator2.setFrameShape(QFrame.Shape.HLine)
        separator2.setFrameShadow(QFrame.Shadow.Sunken)
        separator2.setStyleSheet("background-color: #444;")
        scroll_layout.addWidget(separator2)
        
        # --- Advanced Settings Group ---
        advanced_group = QGroupBox("Advanced Settings")
        advanced_group.setCheckable(True)
        advanced_group.setChecked(False)  # Initially collapsed
        advanced_layout = QVBoxLayout(advanced_group)
        
        # Rename Pattern Group (moved into advanced settings)
        pattern_group = QGroupBox("Rename Pattern")
        pattern_layout = QVBoxLayout(pattern_group)
        
        # Custom pattern input
        pattern_layout.addWidget(QLabel("Pattern Format:"))
        self.pattern_input = QLineEdit()
        self.pattern_input.setPlaceholderText="{date}_{seq}"
        pattern_layout.addWidget(self.pattern_input)
        
        # Pattern help text
        help_text = QLabel(
            "Available variables:\n"
            "• {date} - Capture date (YYYYMMDD)\n"
            "• {time} - Capture time (HHMMSS)\n"
            "• {seq} - Sequence number\n"
            "• {cam} - Camera model\n"
            "• {orig} - Original filename\n"
            "• {type} - File type (image/video)"
        )
        help_text.setStyleSheet("color: #999; font-size: 11px;")
        pattern_layout.addWidget(help_text)
        
        # Add pattern group to advanced layout
        advanced_layout.addWidget(pattern_group)
        self.pattern_group = pattern_group
        
        # Sequence Number Options Group
        sequence_group = QGroupBox("Sequence Number Options")
        sequence_layout = QVBoxLayout(sequence_group)
        
        # Start number and digits - side by side
        seq_number_layout = QHBoxLayout()
        
        # Start number
        start_layout = QHBoxLayout()
        start_layout.addWidget(QLabel("Start:"))
        self.seq_start = QSpinBox()
        self.seq_start.setRange(1, 9999)
        self.seq_start.setValue(1)
        start_layout.addWidget(self.seq_start)
        seq_number_layout.addLayout(start_layout)
        
        # Add some spacing
        seq_number_layout.addSpacing(20)
        
        # Padding digits
        padding_layout = QHBoxLayout()
        padding_layout.addWidget(QLabel("Padding:"))
        self.seq_digits = QSpinBox()
        self.seq_digits.setRange(1, 6)
        self.seq_digits.setValue(3)
        padding_layout.addWidget(self.seq_digits)
        seq_number_layout.addLayout(padding_layout)
        
        # Add stretch to push everything to the left
        seq_number_layout.addStretch()
        
        sequence_layout.addLayout(seq_number_layout)
        
        # Reset sequence options
        reset_options_layout = QVBoxLayout()
        self.reset_by_folder = QCheckBox("Reset sequence for each folder")
        self.reset_by_folder.setChecked(True)
        reset_options_layout.addWidget(self.reset_by_folder)
        
        self.reset_by_date = QCheckBox("Reset sequence for each date")
        reset_options_layout.addWidget(self.reset_by_date)
        
        sequence_layout.addLayout(reset_options_layout)
        
        # Add sequence group to advanced layout
        advanced_layout.addWidget(sequence_group)
        self.sequence_group = sequence_group
        
        # Add advanced group to main layout
        scroll_layout.addWidget(advanced_group)
        self.advanced_group = advanced_group
        
        # Preview Group
        preview_group = QGroupBox("Preview")
        preview_layout = QVBoxLayout(preview_group)
        
        # Create a table for preview
        self.rename_preview_table = QTableWidget(0, 2)
        self.rename_preview_table.setHorizontalHeaderLabels(["Original Filename", "New Filename"])
        self.rename_preview_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.rename_preview_table.setStyleSheet("""
            QTableWidget {
                background-color: #2d2d2d;
                border: 1px solid #444;
                color: #e1e1e1;
            }
            QTableWidget::item {
                padding: 4px;
            }
            QTableWidget::item:selected {
                background-color: #0078d7;
            }
            QHeaderView::section {
                background-color: #333;
                color: #e1e1e1;
                padding: 4px;
                border: 1px solid #444;
            }
        """)
        
        # Add some example data for the preview
        self.rename_preview_table.setRowCount(5)
        example_files = [
            ("IMG_0001.JPG", "20230415_001.jpg"),
            ("IMG_0002.JPG", "20230415_002.jpg"),
            ("IMG_0003.JPG", "20230415_003.jpg"),
            ("MOV_0001.MP4", "20230415_004.mp4"),
            ("IMG_0004.JPG", "20230416_001.jpg")
        ]
        
        for row, (orig, new) in enumerate(example_files):
            self.rename_preview_table.setItem(row, 0, QTableWidgetItem(orig))
            self.rename_preview_table.setItem(row, 1, QTableWidgetItem(new))
        
        preview_layout.addWidget(self.rename_preview_table)
        
        # Add preview group to main layout
        scroll_layout.addWidget(preview_group)
        self.preview_group = preview_group
        
        # Finalize scroll area
        scroll_area.setWidget(scroll_content)
        layout.addWidget(scroll_area)
        
        # Connect signals specific to this view
        self.advanced_group.toggled.connect(self._handle_advanced_mode_toggled)
        self.basic_filename.textChanged.connect(self.handle_settings_changed)
        
        # Install event filters for toggling between basic and advanced settings
        self._install_event_filters()
        
        return tab
    
    def _handle_keep_original_changed(self, state):
        """Handle the checkbox state change to enable/disable renaming options"""
        enabled = not bool(state)
        
        # Enable/disable basic settings
        if hasattr(self, 'basic_group'):
            self.basic_group.setEnabled(enabled)
            
        # Enable/disable advanced settings
        if hasattr(self, 'advanced_group'):
            self.advanced_group.setEnabled(enabled)
        
        # Enable/disable all advanced option groups
        if hasattr(self, 'pattern_group'):
            self.pattern_group.setEnabled(enabled)
        if hasattr(self, 'sequence_group'):
            self.sequence_group.setEnabled(enabled)
        
        # Update preview table if "Keep original" is checked
        self.update_rename_preview()
        
        # Save settings
        self.handle_settings_changed()
    
    def _handle_advanced_mode_toggled(self, is_checked):
        """Handle toggling of the advanced settings group."""
        # Update the preview to reflect the change in rename mode
        self.update_rename_preview()
        self.handle_settings_changed()
        
        # Enable/disable basic settings based on advanced mode
        if hasattr(self, 'basic_group'):
            self.basic_group.setEnabled(not is_checked)
            
            # Apply visual highlight based on which mode is active
            if is_checked:
                self.advanced_group.setStyleSheet("QGroupBox { border: 2px solid #0078d7; }")
                self.basic_group.setStyleSheet("")
            else:
                self.basic_group.setStyleSheet("QGroupBox { border: 2px solid #0078d7; }")
                self.advanced_group.setStyleSheet("")

    def update_rename_preview(self):
        """Update the rename preview table based on current settings."""
        if not hasattr(self, 'rename_preview_table'):
            return
            
        # Example file data for preview
        example_files = [
            {"filename": "IMG_0001.JPG", "date": "20230415", "camera": "Canon EOS R5"},
            {"filename": "IMG_0002.JPG", "date": "20230415", "camera": "Canon EOS R5"},
            {"filename": "IMG_0003.JPG", "date": "20230415", "camera": "Canon EOS R5"},
            {"filename": "MOV_0001.MP4", "date": "20230415", "camera": "Canon EOS R5"},
            {"filename": "IMG_0004.JPG", "date": "20230416", "camera": "Canon EOS R5"}
        ]
        
        # Clear the table
        self.rename_preview_table.setRowCount(len(example_files))
        
        # If keep original is checked, show original filenames
        if hasattr(self, 'keep_original') and self.keep_original.isChecked():
            for row, file_data in enumerate(example_files):
                orig = file_data["filename"]
                self.rename_preview_table.setItem(row, 0, QTableWidgetItem(orig))
                self.rename_preview_table.setItem(row, 1, QTableWidgetItem(orig))
            return
            
        # Check if we're using basic mode (advanced settings off)
        using_basic_mode = hasattr(self, 'advanced_group') and not self.advanced_group.isChecked()
        
        if using_basic_mode and hasattr(self, 'basic_filename'):
            # Basic mode - use the basic filename pattern with automatic sequencing
            base_filename = self.basic_filename.text()
            if not base_filename:
                base_filename = "IMG"  # Default if nothing entered
                
            # Setup sequence numbers (in basic mode, always start from 1 with padding 3)
            seq_start = 1
            seq_digits = 3
            current_seq = seq_start
                
            for row, file_data in enumerate(example_files):
                orig_filename = file_data["filename"]
                ext = self._get_extension(orig_filename)
                
                # Generate new filename with fixed sequence format
                new_filename = f"{base_filename}_{current_seq:0{seq_digits}d}{ext}"
                
                # Set table items
                self.rename_preview_table.setItem(row, 0, QTableWidgetItem(orig_filename))
                self.rename_preview_table.setItem(row, 1, QTableWidgetItem(new_filename))
                
                # Increment sequence counter
                current_seq += 1
            
            return
        
        # Advanced mode - use custom pattern
        
        # Setup sequence numbers
        seq_start = self.seq_start.value() if hasattr(self, 'seq_start') else 1
        seq_digits = self.seq_digits.value() if hasattr(self, 'seq_digits') else 3
        
        # Track current sequence number
        current_seq = seq_start
        current_date = None
        
        for row, file_data in enumerate(example_files):
            orig_filename = file_data["filename"]
            date = file_data["date"]
            camera = file_data["camera"]
            
            # Reset sequence if needed
            if hasattr(self, 'reset_by_date') and self.reset_by_date.isChecked() and current_date != date:
                current_seq = seq_start
                current_date = date
            
            # Use custom pattern for all advanced mode renaming
            pattern = self.pattern_input.text() if hasattr(self, 'pattern_input') else "{date}_{seq}"
            new_filename = self._apply_custom_pattern(pattern, file_data, current_seq, seq_digits)
            
            # Set table items
            self.rename_preview_table.setItem(row, 0, QTableWidgetItem(orig_filename))
            self.rename_preview_table.setItem(row, 1, QTableWidgetItem(new_filename))
            
            # Increment sequence counter
            current_seq += 1
    
    def _apply_custom_pattern(self, pattern, file_data, seq_num, seq_digits):
        """Apply a custom pattern to generate a filename."""
        filename = file_data["filename"]
        date = file_data["date"]
        camera = file_data["camera"]
        
        # Get file extension
        ext = self._get_extension(filename)
        
        # Get file type
        file_type = "video" if ext.lower() in [".mp4", ".mov", ".avi"] else "image"
        
        # Format the sequence number with the specified padding
        padded_seq = f"{seq_num:0{seq_digits}d}"
        
        # Replace variables in pattern
        result = pattern.replace("{date}", date)
        result = result.replace("{time}", "120000")  # Example time
        result = result.replace("{seq}", padded_seq)
        result = result.replace("{cam}", camera.replace(" ", ""))
        result = result.replace("{orig}", self._remove_extension(filename))
        result = result.replace("{type}", file_type)
        
        # Add extension if not in pattern
        if not result.endswith(ext):
            result += ext
            
        return result
    
    def _get_extension(self, filename):
        """Get the file extension with dot."""
        import os
        _, ext = os.path.splitext(filename)
        return ext.lower()
    
    def _remove_extension(self, filename):
        """Remove the extension from a filename."""
        import os
        base, _ = os.path.splitext(filename)
        return base
        
    def update_ui_states(self):
        """Update UI states based on current selection."""
        # Handle organization method selection
        date_selected = self.org_by_date.isChecked()
        custom_selected = self.org_by_custom.isChecked()
        
        # Enable date format options only if "By date" is selected
        self.date_format_combo.setEnabled(date_selected)
        
        # Enable custom format options only if "Custom structure" is selected
        self.custom_format_input.setEnabled(custom_selected)
        
        # Update preview
        self.update_preview()
    
    def update_preview(self):
        """Update the folder structure preview based on current settings."""
        # Clear the preview tree
        self.preview_tree.clear()
        
        # Add root item for destination folder
        destination = self.destination_path.text() or "Destination"
        root = QTreeWidgetItem(self.preview_tree, [destination])
        root.setIcon(0, QIcon.fromTheme("folder"))
        
        # Add example files with different organization methods
        example_files = [
            {"filename": "IMG_0001.JPG", "date": "2023-04-15", "time": "10:30:00"},
            {"filename": "IMG_0002.JPG", "date": "2023-04-15", "time": "10:35:00"},
            {"filename": "MOV_0001.MP4", "date": "2023-04-15", "time": "11:00:00"},
            {"filename": "IMG_0003.JPG", "date": "2023-04-16", "time": "09:15:00"}
        ]
        
        for file_info in example_files:
            if self.org_by_date.isChecked():
                # Get the date format
                date_format = self.date_format_combo.currentData()
                
                # Format the date based on selected format
                date_str = self._format_date(file_info["date"], date_format)
                
                # Check if the date format contains slashes and needs to be split
                if "/" in date_str:
                    # Split into individual parts for folder hierarchy
                    date_parts = date_str.split("/")
                    # Add date-organized folder structure with separate parts
                    self._add_folder_path(root, date_parts + [file_info["filename"]])
                else:
                    # Add date-organized folder structure
                    self._add_folder_path(root, [date_str, file_info["filename"]])
                
            elif self.org_by_custom.isChecked():
                # Get the custom format
                custom_format = self.custom_format_input.text()
                
                # Parse custom format and add to tree
                if custom_format:
                    # Format the custom path
                    formatted_path = self._format_custom_path(
                        custom_format, file_info["date"], file_info["time"],
                        "Camera Model", file_info["filename"]
                    )
                    
                    # Add to tree
                    self._add_custom_path(root, formatted_path, file_info["filename"])
                else:
                    # If no custom format, just add files at root
                    self._add_folder_path(root, [file_info["filename"]])
        
        # Expand the root item
        self.preview_tree.expandAll()
        
        # Also update rename preview if available
        if hasattr(self, 'update_rename_preview'):
            self.update_rename_preview()
    
    def _add_folder_path(self, parent, path_parts):
        """Add a folder path to the preview tree."""
        if not path_parts:
            return parent
        
        current = path_parts[0]
        
        # Find if folder already exists
        folder_item = None
        for i in range(parent.childCount()):
            if parent.child(i).text(0) == current:
                folder_item = parent.child(i)
                break
        
        # Create new folder item if not found
        if not folder_item:
            folder_item = QTreeWidgetItem(parent, [current])
            if "." in current:  # This is a file
                folder_item.setIcon(0, QIcon.fromTheme("text-x-generic"))
            else:
                folder_item.setIcon(0, QIcon.fromTheme("folder"))
        
        # Process remaining path parts
        if len(path_parts) > 1:
            return self._add_folder_path(folder_item, path_parts[1:])
        
        return folder_item
    
    def _add_custom_path(self, parent, path_string, filename):
        """Add a custom path structure to the preview tree."""
        # Split path by / and filter out empty parts
        parts = [part for part in path_string.split("/") if part]
        
        # If there are no parts, just add the filename directly
        if not parts:
            return self._add_folder_path(parent, [filename])
            
        # Add the filename to the end
        return self._add_folder_path(parent, parts + [filename])
    
    def handle_browse_clicked(self):
        """Handle the browse button click to select a destination folder."""
        folder_path = QFileDialog.getExistingDirectory(
            self,
            "Select Destination Folder",
            self.destination_path.text() or "",
            QFileDialog.Option.ShowDirsOnly
        )
        
        if folder_path:
            self.destination_path.setText(folder_path)
            self.save_settings()
            self.settings_changed.emit()
            self.update_preview()
    
    def handle_settings_changed(self):
        """Handle when any setting is changed."""
        # Save settings
        self.save_settings()
        
        # Update the preview to reflect changes
        self.update_preview()
        
        # Emit settings changed signal
        self.settings_changed.emit()
    
    def get_destination_folder(self):
        """Get the currently selected destination folder."""
        return self.destination_path.text()
    
    def set_destination_folder(self, folder_path):
        """Set the destination folder path."""
        self.destination_path.setText(folder_path)
        self.save_settings()
    
    def get_organization_method(self):
        """Get the selected organization method."""
        if self.org_by_date.isChecked():
            return self.ORG_BY_DATE
        else:
            return self.ORG_BY_CUSTOM
    
    def get_date_format(self):
        """Get the selected date format."""
        return self.date_format_combo.currentData()
    
    def get_custom_format(self):
        """Get the custom folder structure format."""
        return self.custom_format_input.text()
    
    def get_extract_exif(self):
        """Get whether to extract EXIF data."""
        return self.extract_exif.isChecked()
    
    def load_settings(self):
        """Load settings from file."""
        import configparser
        import os
        
        # Create default settings
        settings = {
            'destination_folder': '',
            'organization_method': self.ORG_BY_DATE,
            'date_format': 'yyyy-mm-dd',
            'custom_format': '{YYYY}/{MM}/{DD}/{type}',
            'extract_exif': 'True',
            # Batch rename settings
            'keep_original_filenames': 'False',
            'basic_filename': 'IMG',
            'advanced_mode': 'False',
            'rename_pattern_custom': '{date}_{seq}',
            'sequence_start': '1',
            'sequence_digits': '3',
            'reset_by_folder': 'True',
            'reset_by_date': 'False',
        }
        
        # Load existing settings if file exists
        if os.path.exists(self.settings_file_path):
            config = configparser.ConfigParser()
            config.read(self.settings_file_path)
            
            if 'Import' in config:
                for key in settings:
                    if key in config['Import']:
                        settings[key] = config['Import'][key]
        
        # Apply settings to UI - do this with signals disabled
        self.blockSignals(True)
        
        # Destination folder
        if settings['destination_folder']:
            self.destination_path.setText(settings['destination_folder'])
        
        # Organization method
        org_method = settings['organization_method']
        self.org_by_date.setChecked(org_method == self.ORG_BY_DATE)
        self.org_by_custom.setChecked(org_method == self.ORG_BY_CUSTOM)
        
        # Date format
        date_format = settings['date_format']
        for i in range(self.date_format_combo.count()):
            if self.date_format_combo.itemData(i) == date_format:
                self.date_format_combo.setCurrentIndex(i)
                break
        
        # Custom format
        custom_format = settings['custom_format']
        self.custom_format_input.setText(custom_format)
        
        # EXIF options
        extract_exif = settings['extract_exif'].lower() == 'true'
        self.extract_exif.setChecked(extract_exif)
        
        # Load batch rename settings if the UI elements exist
        if hasattr(self, 'keep_original'):
            # Keep original filenames
            keep_original = settings['keep_original_filenames'].lower() == 'true'
            self.keep_original.setChecked(keep_original)
            
            # Basic filename
            if hasattr(self, 'basic_filename'):
                self.basic_filename.setText(settings['basic_filename'])
                
            # Advanced mode
            if hasattr(self, 'advanced_group'):
                advanced_mode = settings['advanced_mode'].lower() == 'true'
                self.advanced_group.setChecked(advanced_mode)
                
                # Also disable basic settings if advanced mode is active
                if hasattr(self, 'basic_group'):
                    self.basic_group.setEnabled(not advanced_mode)
                    
                    # Apply visual highlight based on which mode is active
                    if advanced_mode:
                        self.advanced_group.setStyleSheet("QGroupBox { border: 2px solid #0078d7; }")
                        self.basic_group.setStyleSheet("")
                    else:
                        self.basic_group.setStyleSheet("QGroupBox { border: 2px solid #0078d7; }")
                        self.advanced_group.setStyleSheet("")
            
            # Custom pattern
            self.pattern_input.setText(settings['rename_pattern_custom'])
            
            # Sequence settings
            self.seq_start.setValue(int(settings['sequence_start']))
            self.seq_digits.setValue(int(settings['sequence_digits']))
            
            # Reset options
            self.reset_by_folder.setChecked(settings['reset_by_folder'].lower() == 'true')
            self.reset_by_date.setChecked(settings['reset_by_date'].lower() == 'true')
        
        self.blockSignals(False)
    
    def save_settings(self):
        """Save settings to file."""
        import configparser
        
        # Create config parser
        config = configparser.ConfigParser()
        
        # Basic import settings
        settings = {
            'destination_folder': self.destination_path.text(),
            'organization_method': self.get_organization_method(),
            'date_format': self.date_format_combo.currentData(),
            'custom_format': self.custom_format_input.text(),
            'extract_exif': str(self.extract_exif.isChecked())
        }
        
        # Add batch rename settings if UI elements exist
        if hasattr(self, 'keep_original'):
            # Add batch rename settings
            settings.update({
                'keep_original_filenames': str(self.keep_original.isChecked()),
                'sequence_start': str(self.seq_start.value()),
                'sequence_digits': str(self.seq_digits.value()),
                'reset_by_folder': str(self.reset_by_folder.isChecked()),
                'reset_by_date': str(self.reset_by_date.isChecked())
            })
            
            # Basic and advanced settings
            if hasattr(self, 'basic_filename'):
                settings['basic_filename'] = self.basic_filename.text()
                
            if hasattr(self, 'advanced_group'):
                settings['advanced_mode'] = str(self.advanced_group.isChecked())
            
            # Advanced pattern settings
            settings['rename_pattern_custom'] = self.pattern_input.text()
        
        # Add settings to config
        config['Import'] = settings
        
        # Write to file
        with open(self.settings_file_path, 'w') as f:
            config.write(f)
            
    def _handle_org_method_changed(self):
        """Handle when organization method radio buttons are toggled."""
        # First update UI states
        self.update_ui_states()
        
        # Then save settings
        self.save_settings()
        self.settings_changed.emit()
    
    def _handle_custom_format_changed(self, text):
        """Handle when custom format input changes."""
        # Force save settings immediately
        self.save_settings()
        
        # Update preview if custom format is currently selected
        if self.org_by_custom.isChecked():
            self.update_preview()
            
        # Emit settings changed signal
        self.settings_changed.emit()
    
    def apply_styles(self):
        """Apply dark theme styling to all components."""
        self.setStyleSheet("""
            QWidget {
                background-color: #1e1e1e;
                color: #e1e1e1;
            }
            QTabWidget::pane {
                border: 1px solid #444;
                background-color: #1e1e1e;
            }
            QTabBar::tab {
                background-color: #2d2d2d;
                color: #e1e1e1;
                border: 1px solid #444;
                padding: 6px 12px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                border-bottom: none;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background-color: #3a3a3a;
                border-bottom: 1px solid #3a3a3a;
            }
            QTabBar::tab:hover:!selected {
                background-color: #333;
            }
            QGroupBox {
                border: 1px solid #444;
                border-radius: 4px;
                margin-top: 1.5ex;
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 5px;
                color: #e1e1e1;
            }
            QLineEdit {
                background-color: #2d2d2d;
                border: 1px solid #444;
                border-radius: 3px;
                padding: 5px;
                color: #e1e1e1;
            }
            QPushButton {
                background-color: #0078d7;
                color: white;
                border: none;
                border-radius: 3px;
                padding: 5px 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1c84de;
            }
            QPushButton:pressed {
                background-color: #00559d;
            }
            QComboBox {
                background-color: #2d2d2d;
                border: 1px solid #444;
                border-radius: 3px;
                padding: 5px;
                color: #e1e1e1;
                min-width: 200px;
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 20px;
                border-left: 1px solid #444;
            }
            QComboBox QAbstractItemView {
                background-color: #2d2d2d;
                border: 1px solid #444;
                color: #e1e1e1;
                selection-background-color: #0078d7;
            }
            QRadioButton, QCheckBox {
                color: #e1e1e1;
                spacing: 5px;
            }
            QRadioButton::indicator, QCheckBox::indicator {
                width: 15px;
                height: 15px;
            }
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                background: #1e1e1e;
                width: 8px;
                margin: 0;
            }
            QScrollBar::handle:vertical {
                background: #444;
                min-height: 20px;
                border-radius: 4px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QSpinBox {
                background-color: #2d2d2d;
                border: 1px solid #444;
                border-radius: 3px;
                padding: 5px;
                color: #e1e1e1;
            }
            QSpinBox::up-button, QSpinBox::down-button {
                background-color: #333;
                width: 16px;
                border-radius: 2px;
            }
            QSpinBox::up-button:hover, QSpinBox::down-button:hover {
                background-color: #444;
            }
            QTableWidget {
                background-color: #2d2d2d;
                border: 1px solid #444;
                color: #e1e1e1;
            }
            QTableWidget::item {
                padding: 4px;
            }
            QTableWidget::item:selected {
                background-color: #0078d7;
            }
            QHeaderView::section {
                background-color: #333;
                color: #e1e1e1;
                padding: 4px;
                border: 1px solid #444;
            }
            QGroupBox:disabled {
                color: #888;
            }
            QRadioButton:disabled, QCheckBox:disabled, QLabel:disabled {
                color: #888;
            }
            QLineEdit:disabled, QSpinBox:disabled, QComboBox:disabled {
                background-color: #252525;
                color: #888;
            }
        """) 

    def _format_date(self, date_str, format_id):
        """Format a date string according to the selected format."""
        import datetime
        
        # Try to parse the date string (assuming YYYY-MM-DD format)
        try:
            date_obj = datetime.datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            # If parsing fails, just return the original date string
            return date_str
        
        # Format according to the selected format
        if format_id == "yyyy-mm-dd":
            return date_obj.strftime("%Y-%m-%d")
        elif format_id == "yyyy/mm/dd":
            return date_obj.strftime("%Y/%m/%d")
        elif format_id == "yyyy-mm":
            return date_obj.strftime("%Y-%m")
        elif format_id == "yyyy/mm":
            return date_obj.strftime("%Y/%m")
        elif format_id == "yyyy":
            return date_obj.strftime("%Y")
        elif format_id == "yyyy/mm/dd/hh":
            return date_obj.strftime("%Y/%m/%d/%H")
        else:
            # Default to yyyy-mm-dd
            return date_obj.strftime("%Y-%m-%d")
            
    def _format_custom_path(self, format_str, date_str, time_str, camera_model, filename):
        """Format a custom path string with variables replaced by values."""
        import datetime
        import os
        
        # Try to parse the date and time
        try:
            date_obj = datetime.datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M:%S")
        except ValueError:
            # Use current date/time if parsing fails
            date_obj = datetime.datetime.now()
        
        # Get file type based on extension
        file_ext = os.path.splitext(filename)[1].lower()
        file_type = "video" if file_ext in ['.mp4', '.mov', '.avi'] else "image"
        
        # Replace variables in format string
        result = format_str
        result = result.replace("{YYYY}", date_obj.strftime("%Y"))
        result = result.replace("{MM}", date_obj.strftime("%m"))
        result = result.replace("{DD}", date_obj.strftime("%d"))
        result = result.replace("{hh}", date_obj.strftime("%H"))
        result = result.replace("{mm}", date_obj.strftime("%M"))
        result = result.replace("{camera}", camera_model.replace(" ", "_"))
        result = result.replace("{type}", file_type)
        
        return result
    
    def eventFilter(self, obj, event):
        """Event filter to handle clicks on settings groups"""
        # Check if it's a mouse press event
        if event.type() == QEvent.Type.MouseButtonPress:
            # Check if click was in basic settings area
            if self._is_in_group(obj, self.basic_group):
                # Only toggle if advanced is currently active
                if self.advanced_group.isChecked():
                    self.advanced_group.setChecked(False)
                return False  # Allow event to propagate
                
            # Check if click was in advanced settings area
            elif self._is_in_group(obj, self.advanced_group):
                # Only toggle if advanced is currently not active
                if not self.advanced_group.isChecked():
                    self.advanced_group.setChecked(True)
                return False  # Allow event to propagate
                
        # For other events, just pass them through
        return super().eventFilter(obj, event)
    
    def _is_in_group(self, obj, group):
        """Check if obj is group or a child widget of group"""
        if obj == group:
            return True
        
        # Check if obj is a child of group
        parent = obj
        while parent is not None:
            if parent == group:
                return True
            # Move up to next parent
            parent = parent.parent()
        
        return False
        
    def _install_event_filters(self):
        """Install event filters on settings groups and their children"""
        # Install on basic group
        self.basic_group.installEventFilter(self)
        for child in self.basic_group.findChildren(QWidget):
            child.installEventFilter(self)
            
        # Install on advanced group
        self.advanced_group.installEventFilter(self)
        for child in self.advanced_group.findChildren(QWidget):
            child.installEventFilter(self) 