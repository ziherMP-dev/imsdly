from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QLineEdit, QFileDialog, QGroupBox, QFormLayout
)
from PyQt6.QtCore import Qt, pyqtSignal, QSettings

class ImportSettingsPanel(QWidget):
    """Panel for configuring import settings, including destination folder."""
    
    # Signal emitted when settings change
    settings_changed = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.load_settings()
    
    def setup_ui(self):
        """Set up the UI components."""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(10)
        
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
        
        main_layout.addWidget(destination_group)
        
        # Add a stretch to push everything to the top
        main_layout.addStretch()
        
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
        """)
    
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
    
    def get_destination_folder(self):
        """Get the currently selected destination folder."""
        return self.destination_path.text()
    
    def set_destination_folder(self, folder_path):
        """Set the destination folder path."""
        self.destination_path.setText(folder_path)
        self.save_settings()
    
    def load_settings(self):
        """Load settings from QSettings."""
        settings = QSettings("Imsdly", "SDCardImporter")
        destination = settings.value("import/destination_folder", "")
        if destination:
            self.destination_path.setText(destination)
    
    def save_settings(self):
        """Save settings to QSettings."""
        settings = QSettings("Imsdly", "SDCardImporter")
        settings.setValue("import/destination_folder", self.destination_path.text()) 