import sys
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QTabWidget, QLabel, QPushButton, 
    QLineEdit, QGroupBox, QFormLayout, QComboBox, QCheckBox, QRadioButton, 
    QTreeWidget, QTreeWidgetItem, QHBoxLayout, QFrame, QSpinBox, QTableWidget,
    QTableWidgetItem, QHeaderView, QMainWindow
)
from PyQt6.QtCore import Qt, QSize, QTimer
from PyQt6.QtGui import QIcon, QFont, QScreen

class ImportSettingsTestApp(QMainWindow):
    """Test application for import settings with tabbed interface."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Import Settings Test")
        self.resize(800, 600)
        
        # Create central widget and layout
        central_widget = QWidget()
        main_layout = QVBoxLayout(central_widget)
        self.setCentralWidget(central_widget)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        
        # Create the folder settings tab (simplified version of current panel)
        folder_settings_tab = QWidget()
        folder_layout = QVBoxLayout(folder_settings_tab)
        
        # Add placeholder content for folder settings (simplified)
        folder_label = QLabel("This tab would contain all the existing folder settings:")
        folder_label.setStyleSheet("font-weight: bold;")
        folder_layout.addWidget(folder_label)
        
        placeholder_list = QLabel(
            "• Destination folder selection\n"
            "• Organization method (by date or custom)\n"
            "• Date format options\n"
            "• Custom folder structure\n"
            "• EXIF options\n"
            "• Structure preview"
        )
        folder_layout.addWidget(placeholder_list)
        
        # Create the batch renaming tab
        batch_rename_tab = self.create_batch_rename_tab()
        
        # Add tabs to the tab widget
        self.tab_widget.addTab(folder_settings_tab, "Folder Settings")
        self.tab_widget.addTab(batch_rename_tab, "Batch Rename")
        
        # Start on batch rename tab for screenshot
        self.tab_widget.setCurrentIndex(1)
        
        # Add tab widget to main layout
        main_layout.addWidget(self.tab_widget)
        
        # Apply dark theme 
        self.apply_styles()
        
        # Set up a timer to take a screenshot
        QTimer.singleShot(500, self.take_screenshot)
    
    def create_batch_rename_tab(self):
        """Create the batch rename tab content."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Add option to keep original filenames (disable batch renaming)
        keep_original_layout = QHBoxLayout()
        self.keep_original = QCheckBox("Keep original filenames (disable batch renaming)")
        self.keep_original.setStyleSheet("font-weight: bold;")
        keep_original_layout.addWidget(self.keep_original)
        keep_original_layout.addStretch()
        layout.addLayout(keep_original_layout)
        
        # Add a separator line
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        separator.setStyleSheet("background-color: #444;")
        layout.addWidget(separator)
        
        # Connect the checkbox to enable/disable the renaming options
        self.keep_original.stateChanged.connect(self.handle_keep_original_changed)
        
        # Rename Pattern Group
        pattern_group = QGroupBox("Rename Pattern")
        pattern_layout = QVBoxLayout(pattern_group)
        
        # Pattern selection
        pattern_form = QFormLayout()
        
        # Pattern type selection
        self.pattern_type = QComboBox()
        self.pattern_type.addItems([
            "Date + Sequence Number", 
            "Custom Pattern",
            "Camera Model + Sequence",
            "Original Filename + Suffix"
        ])
        
        # Create a dropdown button (like in SD card panel)
        pattern_layout_h = QHBoxLayout()
        pattern_layout_h.addWidget(QLabel("Pattern Type:"))
        pattern_layout_h.addWidget(self.pattern_type)
        
        dropdown_button = QPushButton("↓")
        dropdown_button.setFixedWidth(24)
        dropdown_button.setToolTip("Show pattern options")
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
        pattern_layout_h.addWidget(dropdown_button)
        dropdown_button.clicked.connect(lambda: self.pattern_type.showPopup())
        
        pattern_layout.addLayout(pattern_layout_h)
        
        # Custom pattern input
        pattern_layout.addWidget(QLabel("Pattern Format:"))
        self.pattern_input = QLineEdit()
        self.pattern_input.setPlaceholderText("{date}_{seq}")
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
        
        # Add group to layout
        layout.addWidget(pattern_group)
        self.pattern_group = pattern_group
        
        # Sequence Number Options Group
        sequence_group = QGroupBox("Sequence Number Options")
        sequence_layout = QVBoxLayout(sequence_group)
        
        # Start number and digits
        seq_form = QFormLayout()
        
        self.seq_start = QSpinBox()
        self.seq_start.setRange(1, 9999)
        self.seq_start.setValue(1)
        seq_form.addRow("Start Number:", self.seq_start)
        
        self.seq_digits = QSpinBox()
        self.seq_digits.setRange(1, 6)
        self.seq_digits.setValue(3)
        seq_form.addRow("Padding Digits:", self.seq_digits)
        
        sequence_layout.addLayout(seq_form)
        
        # Reset sequence options
        reset_options_layout = QVBoxLayout()
        self.reset_by_folder = QCheckBox("Reset sequence for each folder")
        self.reset_by_folder.setChecked(True)
        reset_options_layout.addWidget(self.reset_by_folder)
        
        self.reset_by_date = QCheckBox("Reset sequence for each date")
        reset_options_layout.addWidget(self.reset_by_date)
        
        sequence_layout.addLayout(reset_options_layout)
        
        # Add group to layout
        layout.addWidget(sequence_group)
        self.sequence_group = sequence_group
        
        # Case Options
        case_group = QGroupBox("Case Options")
        case_layout = QHBoxLayout(case_group)
        
        self.case_original = QRadioButton("Original")
        self.case_original.setChecked(True)
        case_layout.addWidget(self.case_original)
        
        self.case_lower = QRadioButton("lowercase")
        case_layout.addWidget(self.case_lower)
        
        self.case_upper = QRadioButton("UPPERCASE")
        case_layout.addWidget(self.case_upper)
        
        # Add group to layout
        layout.addWidget(case_group)
        self.case_group = case_group
        
        # Preview Group
        preview_group = QGroupBox("Preview")
        preview_layout = QVBoxLayout(preview_group)
        
        # Create a table for preview
        self.preview_table = QTableWidget(0, 2)
        self.preview_table.setHorizontalHeaderLabels(["Original Filename", "New Filename"])
        self.preview_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.preview_table.setStyleSheet("""
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
        
        # Add some example data
        self.preview_table.setRowCount(5)
        example_files = [
            ("IMG_0001.JPG", "20230415_001.jpg"),
            ("IMG_0002.JPG", "20230415_002.jpg"),
            ("IMG_0003.JPG", "20230415_003.jpg"),
            ("MOV_0001.MP4", "20230415_004.mp4"),
            ("IMG_0004.JPG", "20230416_001.jpg")
        ]
        
        for row, (orig, new) in enumerate(example_files):
            self.preview_table.setItem(row, 0, QTableWidgetItem(orig))
            self.preview_table.setItem(row, 1, QTableWidgetItem(new))
        
        preview_layout.addWidget(self.preview_table)
        
        # Update preview button
        update_button = QPushButton("Update Preview")
        update_button.setStyleSheet("""
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
        """)
        preview_layout.addWidget(update_button)
        
        # Add group to layout
        layout.addWidget(preview_group)
        self.preview_group = preview_group
        
        return tab
    
    def handle_keep_original_changed(self, state):
        """Handle the checkbox state change to enable/disable renaming options"""
        enabled = not bool(state)
        
        # Enable/disable all renaming option groups
        self.pattern_group.setEnabled(enabled)
        self.sequence_group.setEnabled(enabled)
        self.case_group.setEnabled(enabled)
        
        # Update preview table if "Keep original" is checked
        if state:
            # Show original filenames in both columns
            for row in range(self.preview_table.rowCount()):
                original = self.preview_table.item(row, 0).text()
                self.preview_table.setItem(row, 1, QTableWidgetItem(original))
        else:
            # Restore the renamed versions
            example_files = [
                ("IMG_0001.JPG", "20230415_001.jpg"),
                ("IMG_0002.JPG", "20230415_002.jpg"),
                ("IMG_0003.JPG", "20230415_003.jpg"),
                ("MOV_0001.MP4", "20230415_004.mp4"),
                ("IMG_0004.JPG", "20230416_001.jpg")
            ]
            for row, (orig, new) in enumerate(example_files):
                self.preview_table.setItem(row, 1, QTableWidgetItem(new))
    
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
            QLineEdit, QSpinBox {
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
    
    def take_screenshot(self):
        """Take a screenshot of the window and save it"""
        screen = QApplication.primaryScreen()
        screenshot = screen.grabWindow(self.winId())
        screenshot.save("batch_rename_tab_screenshot.png")
        print("Screenshot saved as batch_rename_tab_screenshot.png")
        # Quit after taking screenshot
        QApplication.quit()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ImportSettingsTestApp()
    window.show()
    sys.exit(app.exec()) 