from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QLineEdit, QFileDialog, QGroupBox, QFormLayout, QComboBox,
    QCheckBox, QRadioButton, QButtonGroup, QScrollArea, QFrame,
    QSizePolicy, QTreeWidget, QTreeWidgetItem, QSpacerItem
)
from PyQt6.QtCore import Qt, pyqtSignal, QSettings, QSize
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
        self.setup_ui()
        self.load_settings()
        self.update_ui_states()
    
    def setup_ui(self):
        """Set up the UI components."""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(10)
        
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
        
        # Date format options
        date_format_layout = QFormLayout()
        date_format_layout.setContentsMargins(20, 5, 0, 10)
        
        self.date_format_combo = QComboBox()
        for date_format in self.DATE_FORMATS:
            self.date_format_combo.addItem(date_format["display"], date_format["id"])
        
        date_format_layout.addRow("Date Format:", self.date_format_combo)
        organization_layout.addLayout(date_format_layout)
        
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
        
        # Preview button
        preview_button = QPushButton("Update Preview")
        preview_button.clicked.connect(self.update_preview)
        preview_layout.addWidget(preview_button)
        
        scroll_layout.addWidget(preview_group)
        
        # Finalize scroll area
        scroll_area.setWidget(scroll_content)
        main_layout.addWidget(scroll_area)
        
        # Connect signals for live updates
        self.org_by_date.toggled.connect(self.update_ui_states)
        self.org_by_custom.toggled.connect(self.update_ui_states)
        self.date_format_combo.currentIndexChanged.connect(self.handle_settings_changed)
        self.custom_format_input.textChanged.connect(self.handle_settings_changed)
        self.extract_exif.toggled.connect(self.handle_settings_changed)
        
        # Apply dark theme
        self.apply_styles()
    
    def apply_styles(self):
        """Apply dark theme styling to all components."""
        self.setStyleSheet("""
            QWidget {
                background-color: #1e1e1e;
                color: #e1e1e1;
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
        """)
    
    def update_ui_states(self):
        """Update UI components based on current selections."""
        # Enable/disable date format based on organization method
        date_format_enabled = self.org_by_date.isChecked()
        self.date_format_combo.setEnabled(date_format_enabled)
        
        # Enable/disable custom format based on organization method
        custom_format_enabled = self.org_by_custom.isChecked()
        self.custom_format_input.setEnabled(custom_format_enabled)
        
        # Update preview
        self.update_preview()
    
    def update_preview(self):
        """Update the folder structure preview."""
        self.preview_tree.clear()
        
        # Start with destination folder
        dest_folder = self.destination_path.text() or "Destination"
        root_item = QTreeWidgetItem(self.preview_tree, [dest_folder])
        root_item.setIcon(0, QIcon.fromTheme("folder"))
        
        # Generate example structure based on current settings
        if self.org_by_date.isChecked():
            # Get selected date format
            date_format_id = self.date_format_combo.currentData()
            
            # Create example structure based on date format
            if date_format_id == "yyyy-mm-dd":
                self._add_folder_path(root_item, ["2023-04-15", "example_image.jpg"])
                self._add_folder_path(root_item, ["2023-04-15", "example_video.mp4"])
                self._add_folder_path(root_item, ["2023-04-16", "another_image.jpg"])
            elif date_format_id == "yyyy/mm/dd":
                self._add_folder_path(root_item, ["2023", "04", "15", "example_image.jpg"])
                self._add_folder_path(root_item, ["2023", "04", "15", "example_video.mp4"])
                self._add_folder_path(root_item, ["2023", "04", "16", "another_image.jpg"])
            elif date_format_id == "yyyy-mm":
                self._add_folder_path(root_item, ["2023-04", "example_image.jpg"])
                self._add_folder_path(root_item, ["2023-04", "example_video.mp4"])
                self._add_folder_path(root_item, ["2023-05", "another_image.jpg"])
            elif date_format_id == "yyyy/mm":
                self._add_folder_path(root_item, ["2023", "04", "example_image.jpg"])
                self._add_folder_path(root_item, ["2023", "04", "example_video.mp4"])
                self._add_folder_path(root_item, ["2023", "05", "another_image.jpg"])
            elif date_format_id == "yyyy":
                self._add_folder_path(root_item, ["2023", "example_image.jpg"])
                self._add_folder_path(root_item, ["2023", "example_video.mp4"])
                self._add_folder_path(root_item, ["2022", "another_image.jpg"])
            elif date_format_id == "yyyy/mm/dd/hh":
                self._add_folder_path(root_item, ["2023", "04", "15", "10", "example_image.jpg"])
                self._add_folder_path(root_item, ["2023", "04", "15", "11", "example_video.mp4"])
                self._add_folder_path(root_item, ["2023", "04", "16", "09", "another_image.jpg"])
        else:
            # Custom format
            custom_format = self.custom_format_input.text()
            if not custom_format:
                custom_format = "{YYYY}/{MM}/{DD}/{type}"
            
            # Replace placeholders with example values
            example1 = custom_format.replace("{YYYY}", "2023").replace("{MM}", "04").replace("{DD}", "15")
            example1 = example1.replace("{hh}", "10").replace("{mm}", "30")
            example1 = example1.replace("{camera}", "Canon EOS R5").replace("{type}", "image")
            
            example2 = custom_format.replace("{YYYY}", "2023").replace("{MM}", "04").replace("{DD}", "15")
            example2 = example2.replace("{hh}", "11").replace("{mm}", "45")
            example2 = example2.replace("{camera}", "Canon EOS R5").replace("{type}", "video")
            
            example3 = custom_format.replace("{YYYY}", "2023").replace("{MM}", "04").replace("{DD}", "16")
            example3 = example3.replace("{hh}", "09").replace("{mm}", "15")
            example3 = example3.replace("{camera}", "Sony A7IV").replace("{type}", "image")
            
            # Add examples to preview
            self._add_custom_path(root_item, example1, "example_image.jpg")
            self._add_custom_path(root_item, example2, "example_video.mp4")
            self._add_custom_path(root_item, example3, "another_image.jpg")
        
        # Expand all items
        self.preview_tree.expandAll()
    
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
        parts = path_string.split("/")
        parts.append(filename)
        return self._add_folder_path(parent, parts)
    
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
        self.save_settings()
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
        """Load settings from QSettings."""
        settings = QSettings("Imsdly", "SDCardImporter")
        
        # Load destination folder
        destination = settings.value("import/destination_folder", "")
        if destination:
            self.destination_path.setText(destination)
        
        # Load organization method
        org_method = settings.value("import/organization_method", self.ORG_BY_DATE)
        self.org_by_date.setChecked(org_method == self.ORG_BY_DATE)
        self.org_by_custom.setChecked(org_method == self.ORG_BY_CUSTOM)
        
        # Load date format
        date_format = settings.value("import/date_format", "yyyy-mm-dd")
        for i in range(self.date_format_combo.count()):
            if self.date_format_combo.itemData(i) == date_format:
                self.date_format_combo.setCurrentIndex(i)
                break
        
        # Load custom format
        custom_format = settings.value("import/custom_format", "{YYYY}/{MM}/{DD}/{type}")
        self.custom_format_input.setText(custom_format)
        
        # Load EXIF options
        extract_exif = settings.value("import/extract_exif", True, type=bool)
        self.extract_exif.setChecked(extract_exif)
    
    def save_settings(self):
        """Save settings to QSettings."""
        settings = QSettings("Imsdly", "SDCardImporter")
        
        # Save destination folder
        settings.setValue("import/destination_folder", self.destination_path.text())
        
        # Save organization method
        settings.setValue("import/organization_method", self.get_organization_method())
        
        # Save date format
        settings.setValue("import/date_format", self.date_format_combo.currentData())
        
        # Save custom format
        settings.setValue("import/custom_format", self.custom_format_input.text())
        
        # Save EXIF options
        settings.setValue("import/extract_exif", self.extract_exif.isChecked()) 