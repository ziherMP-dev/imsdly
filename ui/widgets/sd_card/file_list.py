from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QListWidget, QListWidgetItem,
    QHBoxLayout, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QIcon, QFont, QPixmap, QColor
from typing import Dict, Optional, List
import logging

# Set up logging
logger = logging.getLogger(__name__)

class FileListItem(QWidget):
    """Widget for displaying a file item in the list."""
    
    def __init__(self, file_info: Dict, parent=None):
        super().__init__(parent)
        self.file_info = file_info
        logger.debug(f"Creating FileListItem for: {file_info.get('name', 'unknown')}")
        self.setup_ui()
        
    def setup_ui(self):
        """Set up the UI components."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        
        # Create icon based on file type
        icon_label = QLabel()
        icon_label.setFixedSize(16, 16)
        
        # Create colored rectangle for icon
        pixmap = QPixmap(16, 16)
        
        if self.file_info['type'] == 'image':
            pixmap.fill(QColor(52, 152, 219))  # Blue
        elif self.file_info['type'] == 'video':
            pixmap.fill(QColor(231, 76, 60))   # Red
        else:
            pixmap.fill(QColor(149, 165, 166)) # Gray
            
        icon_label.setPixmap(pixmap)
        layout.addWidget(icon_label)
        
        # File name
        name_label = QLabel(self.file_info['name'])
        name_label.setFont(QFont("Arial", 10))
        name_label.setStyleSheet("color: white;")
        layout.addWidget(name_label)
        
        # Set tooltip with file details
        size_kb = self.file_info['size'] / 1024
        size_mb = size_kb / 1024
        size_text = f"{size_mb:.2f} MB" if size_mb >= 1 else f"{size_kb:.2f} KB"
        
        tooltip_text = (
            f"Name: {self.file_info['name']}\n"
            f"Size: {size_text}\n"
            f"Created: {self.file_info['created'].strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"Modified: {self.file_info['modified'].strftime('%Y-%m-%d %H:%M:%S')}"
        )
        self.setToolTip(tooltip_text)
        
        # Set fixed height for consistent list appearance
        self.setFixedHeight(30)
        
        # Styling
        self.setStyleSheet("""
            QWidget {
                background-color: transparent;
            }
            QWidget:hover {
                background-color: #2a2a2a;
                border-radius: 3px;
            }
        """)


class FileListWidget(QWidget):
    """Widget for displaying a list of files."""
    
    file_selected = pyqtSignal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        logger.debug("Initializing FileListWidget")
        self.setup_ui()
        self.file_model = None
        self.current_file_types = None
        
    def setup_ui(self):
        """Set up the UI components."""
        logger.debug("Setting up FileListWidget UI")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Status label (No files, file count, etc.)
        self.status_label = QLabel("No files found")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("color: white; padding: 5px;")
        layout.addWidget(self.status_label)
        
        # File list widget
        self.list_widget = QListWidget()
        self.list_widget.setFrameShape(self.list_widget.Shape.NoFrame)
        self.list_widget.setVerticalScrollMode(QListWidget.ScrollMode.ScrollPerPixel)
        self.list_widget.itemClicked.connect(self._handle_item_clicked)
        layout.addWidget(self.list_widget)
        
        # Styling
        self.list_widget.setStyleSheet("""
            QListWidget {
                background-color: #1e1e1e;
                border: none;
                outline: none;
            }
            QListWidget::item {
                border-bottom: 1px solid #333;
                padding: 0;
                margin: 0;
            }
            QListWidget::item:selected {
                background: #3a3a3a;
            }
            QScrollBar:vertical {
                background: #1e1e1e;
                width: 6px;
                border-radius: 3px;
            }
            QScrollBar::handle:vertical {
                background: #444;
                border-radius: 3px;
            }
            QScrollBar::handle:vertical:hover {
                background: #555;
            }
        """)
        
    def set_file_model(self, model, file_types: Optional[List[str]] = None):
        """Set the file model and update the view.
        
        Args:
            model: The FileSystemModel
            file_types: List of file types to show (e.g., ['image', 'video'])
        """
        logger.debug(f"Setting file model in FileListWidget with file types: {file_types}")
        self.file_model = model
        self.current_file_types = file_types
        self.update_view()
        
    def update_view(self):
        """Update the view with the current files."""
        logger.debug("Updating view in FileListWidget")
        self.list_widget.clear()
        
        if not self.file_model:
            logger.warning("No file model set")
            self.status_label.setText("No files found")
            return
            
        files = self.file_model.get_files()
        
        if not files:
            logger.warning("No files found in model")
            self.status_label.setText("No files found on the SD card")
            return
            
        # Filter files based on file types if specified
        if self.current_file_types:
            files = [f for f in files if f['type'] in self.current_file_types]
            
        # Update status label with file type information
        if not self.current_file_types:
            self.status_label.setText(f"{len(files)} files found")
        else:
            type_counts = {}
            for file in files:
                file_type = file['type']
                type_counts[file_type] = type_counts.get(file_type, 0) + 1
                
            status_parts = []
            if 'image' in type_counts:
                status_parts.append(f"{type_counts['image']} photos")
            if 'video' in type_counts:
                status_parts.append(f"{type_counts['video']} videos")
                
            self.status_label.setText(f"{len(files)} files found ({', '.join(status_parts)})")
        
        for file_info in files:
            item = QListWidgetItem(self.list_widget)
            widget = FileListItem(file_info)
            item.setSizeHint(widget.sizeHint())
            self.list_widget.setItemWidget(item, widget)
        
        logger.debug(f"List widget updated with {self.list_widget.count()} items")
            
    def _handle_item_clicked(self, item):
        """Handle item click event.
        
        Args:
            item: The clicked QListWidgetItem
        """
        widget = self.list_widget.itemWidget(item)
        if widget and hasattr(widget, 'file_info'):
            logger.debug(f"Item clicked: {widget.file_info.get('name', 'unknown')}")
            self.file_selected.emit(widget.file_info) 