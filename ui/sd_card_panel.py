from typing import List, Dict, Any, Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QFrame
)
from PyQt6.QtCore import Qt

class SDCardPanel(QWidget):
    """
    Panel for displaying SD card information and content.
    """
    
    def __init__(self, parent=None):
        """
        Initialize the SD card panel.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self.selected_card = None
        self._setup_ui()
        self._connect_signals()
        
    def _setup_ui(self) -> None:
        """Set up the UI components."""
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Header
        self.content_header = QLabel("SD Card Content")
        font = self.content_header.font()
        font.setBold(True)
        self.content_header.setFont(font)
        layout.addWidget(self.content_header)
        
        # Placeholder for file listing
        self.placeholder = QLabel("Select an SD card to view its content")
        self.placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.placeholder.setStyleSheet("color: #999; padding: 50px;")
        layout.addWidget(self.placeholder)
        
        # Status bar
        status_bar = QFrame()
        status_bar.setFrameShape(QFrame.Shape.StyledPanel)
        status_bar_layout = QHBoxLayout(status_bar)
        status_bar_layout.setContentsMargins(10, 5, 10, 5)
        
        self.status_label = QLabel("No SD card selected")
        status_bar_layout.addWidget(self.status_label)
        
        # Add scan button
        self.scan_button = QPushButton("Scan for Media")
        self.scan_button.setEnabled(False)  # Disabled until a card is selected
        status_bar_layout.addWidget(self.scan_button)
        
        layout.addWidget(status_bar)
        
        self.setLayout(layout)
        
    def _connect_signals(self) -> None:
        """Connect signals to slots."""
        # Connect to the sidebar's SD card list selection
        if hasattr(self.parent(), 'sidebar'):
            self.parent().sidebar.sd_card_list.card_selected.connect(self._handle_card_selected)
        self.scan_button.clicked.connect(self._handle_scan_clicked)
        
    def _handle_card_selected(self, card_info: Dict[str, Any]) -> None:
        """
        Handle selection of an SD card.
        
        Args:
            card_info: Dictionary containing information about the selected card
        """
        self.selected_card = card_info
        self.content_header.setText(f"Content of {card_info.get('name', 'SD Card')}")
        self.status_label.setText(f"Selected: {card_info.get('name', 'SD Card')} ({card_info.get('path', '')})")
        self.scan_button.setEnabled(True)
        
    def _handle_scan_clicked(self) -> None:
        """Handle scan button click."""
        if self.selected_card:
            # Placeholder for actual scanning functionality
            self.status_label.setText(f"Scanning {self.selected_card.get('name', 'SD Card')}...")
            # In a real implementation, this would trigger file scanning 