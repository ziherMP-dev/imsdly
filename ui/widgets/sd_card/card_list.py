from typing import List, Dict, Any, Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QScrollArea, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QIcon, QFont
import logging

from handlers.sd_card.detector import SDCardDetector

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class SDCardListItem(QFrame):
    """Widget representing a single SD card in the list."""
    
    clicked = pyqtSignal(dict)  # Signal emitted when item is clicked
    
    def __init__(self, card_info: Dict[str, Any], parent=None):
        """
        Initialize the SD card list item widget.
        
        Args:
            card_info: Dictionary containing SD card information
            parent: Parent widget
        """
        super().__init__(parent)
        self.card_info = card_info
        self._setup_ui()
        logger.debug(f"Created SDCardListItem for {card_info.get('name', 'Unknown Card')}")
        
    def _setup_ui(self) -> None:
        """Set up the UI components."""
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setLineWidth(0)
        
        layout = QHBoxLayout()
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(8)
        
        # Icon
        icon_label = QLabel()
        icon_label.setText("💾")
        icon_label.setFixedSize(16, 16)
        icon_label.setStyleSheet("""
            QLabel {
                color: #4a9eff;
                font-size: 14px;
            }
        """)
        layout.addWidget(icon_label)
        
        # Card info
        info_layout = QVBoxLayout()
        info_layout.setContentsMargins(0, 0, 0, 0)
        info_layout.setSpacing(2)
        
        # Card name
        name_label = QLabel(self.card_info.get("name", "Unknown Card"))
        font = name_label.font()
        font.setBold(True)
        font.setPointSize(10)
        name_label.setFont(font)
        name_label.setStyleSheet("color: #ffffff;")
        info_layout.addWidget(name_label)
        
        # Card details
        details_text = f"{self._format_size(self.card_info.get('free_space', 0))}" \
                      f" free of {self._format_size(self.card_info.get('total_space', 0))}" \
                      f" • {self.card_info.get('filesystem', '')}"
        details_label = QLabel(details_text)
        details_label.setStyleSheet("color: #888; font-size: 9pt;")
        info_layout.addWidget(details_label)
        
        layout.addLayout(info_layout)
        layout.addStretch()
        
        self.setLayout(layout)
        self.setFixedHeight(30)
        
        # Set the widget to accept mouse events
        self.setAttribute(Qt.WidgetAttribute.WA_Hover)
        self.setMouseTracking(True)
        
        # Set the base style
        self.setStyleSheet("""
            QFrame {
                background: transparent;
                border: none;
                border-radius: 4px;
            }
            QFrame:hover {
                background: #2a2a2a;
            }
            QLabel {
                background: transparent;
            }
        """)
        
    def enterEvent(self, event):
        """Handle mouse enter event."""
        logger.debug("Mouse entered SDCardListItem")
        self.setStyleSheet("""
            QFrame {
                background: #2a2a2a;
                border: none;
                border-radius: 4px;
            }
            QLabel {
                background: transparent;
            }
        """)
        
    def leaveEvent(self, event):
        """Handle mouse leave event."""
        logger.debug("Mouse left SDCardListItem")
        self.setStyleSheet("""
            QFrame {
                background: transparent;
                border: none;
                border-radius: 4px;
            }
            QLabel {
                background: transparent;
            }
        """)
        
    def mousePressEvent(self, event):
        """Handle mouse press events."""
        logger.debug("Mouse pressed on SDCardListItem")
        self.clicked.emit(self.card_info)
        
    @staticmethod
    def _format_size(size_bytes: Optional[int]) -> str:
        """
        Format size in bytes to human-readable format.
        
        Args:
            size_bytes: Size in bytes
            
        Returns:
            str: Formatted size string
        """
        if size_bytes is None:
            return "Unknown"
            
        # Convert to appropriate unit
        units = ["B", "KB", "MB", "GB", "TB"]
        size = float(size_bytes)
        unit_index = 0
        
        while size >= 1024 and unit_index < len(units) - 1:
            size /= 1024
            unit_index += 1
            
        return f"{size:.1f} {units[unit_index]}"


class SDCardListWidget(QWidget):
    """Widget for displaying the list of available SD cards."""
    
    card_selected = pyqtSignal(dict)  # Emitted when a card is selected
    
    def __init__(self, parent=None):
        """
        Initialize the SD card list widget.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self.sd_detector = SDCardDetector()
        self.selected_card = None
        
        self._setup_ui()
        self._connect_signals()
        
        # Initialize with current cards
        self.refresh_cards()
        
    def _setup_ui(self) -> None:
        """Set up the UI components."""
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Create a scroll area
        scroll_area = QScrollArea()
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background: #1e1e1e;
                border-radius: 6px;
            }
            QScrollArea > QWidget > QWidget {
                background: #1e1e1e;
            }
            QScrollBar:vertical {
                width: 6px;
                background: transparent;
                margin: 2px 0;
            }
            QScrollBar::handle:vertical {
                background: #444;
                min-height: 20px;
                border-radius: 3px;
            }
            QScrollBar::handle:vertical:hover {
                background: #555;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)
        
        # Create container widget for cards
        self.cards_container = QWidget()
        self.cards_layout = QVBoxLayout(self.cards_container)
        self.cards_layout.setContentsMargins(4, 4, 4, 4)
        self.cards_layout.setSpacing(2)
        
        scroll_area.setWidget(self.cards_container)
        layout.addWidget(scroll_area)
        
        # No cards message
        self.no_cards_label = QLabel("No SD cards detected")
        self.no_cards_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.no_cards_label.setStyleSheet("""
            color: #666;
            padding: 0;
            margin: 0;
            font-size: 10pt;
            font-style: italic;
        """)
        self.no_cards_label.setFixedHeight(30)
        layout.addWidget(self.no_cards_label)
        self.no_cards_label.hide()
        
        # Set fixed size for the widget
        self.setFixedHeight(60)
        self.setLayout(layout)
        
    def _connect_signals(self) -> None:
        """Connect signals to slots."""
        # Connect detector signals
        self.sd_detector.cards_updated.connect(self.update_card_list)
        
        # Start the detector
        self.sd_detector.start()
        
    def refresh_cards(self) -> None:
        """Manually refresh the card list."""
        # Get current cards and update the list
        cards = self.sd_detector.get_current_cards()
        self.update_card_list(cards)
        
    def update_card_list(self, cards: List[Dict[str, Any]]) -> None:
        """
        Update the displayed list of SD cards.
        
        Args:
            cards: List of SD card information dictionaries
        """
        logger.debug(f"Updating card list with {len(cards)} cards")
        # Clear existing widgets
        while self.cards_layout.count():
            item = self.cards_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        if not cards:
            scroll_area = self.findChild(QScrollArea)
            if scroll_area:
                scroll_area.hide()
            self.no_cards_label.show()
            return
            
        scroll_area = self.findChild(QScrollArea)
        if scroll_area:
            scroll_area.show()
        self.no_cards_label.hide()
        
        for card in cards:
            item = SDCardListItem(card)
            item.clicked.connect(self._handle_item_click)
            self.cards_layout.addWidget(item)
            logger.debug(f"Added card item: {card.get('name', 'Unknown Card')}")
            
    def _handle_item_click(self, card_info: Dict[str, Any]) -> None:
        """
        Handle a click on a card item.
        
        Args:
            card_info: Information about the clicked card
        """
        logger.debug(f"Card clicked: {card_info.get('name', 'Unknown Card')}")
        self.selected_card = card_info
        self.card_selected.emit(card_info)
        
    def get_selected_card(self) -> Optional[Dict[str, Any]]:
        """
        Get the currently selected SD card.
        
        Returns:
            Optional[Dict[str, Any]]: Information about the selected card, or None if no card is selected
        """
        return self.selected_card

    def get_cards(self):
        """Get a list of all currently detected SD cards.
        
        Returns:
            list: List of card info dictionaries
        """
        cards = []
        for i in range(self.cards_layout.count()):
            item = self.cards_layout.itemAt(i)
            widget = item.widget()
            if widget and hasattr(widget, 'card_info'):
                cards.append(widget.card_info)
        return cards 