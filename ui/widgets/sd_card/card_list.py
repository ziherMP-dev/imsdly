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
        self._is_selected = False
        self._setup_ui()
        logger.debug(f"Created SDCardListItem for {card_info.get('name', 'Unknown Card')}")
        
    def _setup_ui(self) -> None:
        """Set up the UI components."""
        # Create main layout with selection indicator
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Blue selection indicator (visible only when selected)
        self.selection_indicator = QFrame(self)
        self.selection_indicator.setFixedWidth(3)
        self.selection_indicator.setStyleSheet("background-color: #007bff;")
        self.selection_indicator.hide()  # Hidden by default
        main_layout.addWidget(self.selection_indicator)
        
        # Content container with some spacing from the indicator
        content = QWidget()
        layout = QHBoxLayout(content)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(8)
        
        # Icon
        icon_label = QLabel()
        icon_label.setText("💾")
        icon_label.setFixedSize(16, 16)
        icon_label.setStyleSheet("color: #4a9eff; font-size: 14px;")
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
        
        main_layout.addWidget(content)
        
        # Set fixed height for consistent sizing
        self.setFixedHeight(36)
        
        # Setup for hover
        self.setAttribute(Qt.WidgetAttribute.WA_Hover)
        self.setMouseTracking(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        # Apply initial style
        self._update_style()
        
    def set_selected(self, selected: bool) -> None:
        """Set whether this item is selected."""
        if self._is_selected == selected:
            return
        
        self._is_selected = selected
        logger.debug(f"Setting card {self.card_info.get('name')} selection to {selected}")
        
        # Show/hide selection indicator
        self.selection_indicator.setVisible(selected)
        
        # Update the style
        self._update_style()
    
    def _update_style(self) -> None:
        """Update the widget style based on selection state."""
        if self._is_selected:
            # Selected style - darker background but NO blue border
            self.setStyleSheet("""
                QFrame {
                    background-color: #404040;
                    border: none;
                    border-radius: 4px;
                }
                QLabel {
                    background: transparent;
                }
            """)
        else:
            # Normal style with hover effect
            self.setStyleSheet("""
                QFrame {
                    background-color: transparent;
                    border: none;
                    border-radius: 4px;
                }
                QFrame:hover {
                    background-color: #2a2a2a;
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
        
        # Set minimum height initially - will be dynamically updated
        self.setMinimumHeight(60)
        self.setLayout(layout)
        
    def _connect_signals(self) -> None:
        """Connect signals to slots."""
        # Connect detector signals
        self.sd_detector.cards_updated.connect(self.update_card_list)
        
        # Start the detector
        self.sd_detector.start()
        
    def refresh_cards(self) -> None:
        """Manually refresh the card list."""
        # Get current cards
        cards = self.sd_detector.get_current_cards()
        
        # Debug what cards we got
        logger.debug(f"Refreshing SD card list, found {len(cards)} cards:")
        for i, card in enumerate(cards):
            card_id = card.get("id") or card.get("path")
            logger.debug(f"  Card {i+1}: {card.get('name')} (ID: {card_id})")
        
        # Update the list with these cards
        self.update_card_list(cards)
        
    def update_card_list(self, cards: List[Dict[str, Any]]) -> None:
        """
        Update the list of SD cards displayed in the widget.
        
        Args:
            cards: List of dictionaries containing SD card information
        """
        # Remember the currently selected card path
        selected_path = None
        if self.selected_card:
            selected_path = self.selected_card.get('path')
        
        # Clear existing widgets first
        self._clear_layout()
        self.items = []
        
        # Add card items
        if not cards:
            self._show_no_cards_message()
            return
            
        for card_info in cards:
            item = SDCardListItem(card_info)
            item.clicked.connect(self._handle_item_click)
            self.cards_layout.addWidget(item)
            self.items.append(item)
            
            # Restore selection if this is the previously selected card
            if selected_path and card_info.get('path') == selected_path:
                item.set_selected(True)
                self.selected_card = card_info
        
        # Dynamically resize based on number of cards
        card_count = len(cards)
        card_height = 38  # Each card is 36px tall + 2px spacing
        total_padding = 8  # Top and bottom padding of the container
        
        if card_count <= 4:
            # For 1-4 cards, show all cards without scrolling
            new_height = card_count * card_height + total_padding
            self.setFixedHeight(new_height)
            logger.debug(f"Showing all {card_count} cards, height: {new_height}px")
        else:
            # For more than 4 cards, show 4 cards and enable scrolling
            max_height = 4 * card_height + total_padding
            self.setFixedHeight(max_height)
            logger.debug(f"Showing 4 of {card_count} cards with scrolling, height: {max_height}px")
            
    def _clear_layout(self) -> None:
        """Clear all items from the cards layout."""
        while self.cards_layout.count():
            item = self.cards_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Hide the no cards message
        self.no_cards_label.hide()
        
    def _show_no_cards_message(self) -> None:
        """Show a message when no cards are available."""
        self.no_cards_label.show()
        # Set a fixed height when empty
        self.setFixedHeight(60)
        
    def _handle_item_click(self, card_info: Dict[str, Any]) -> None:
        """Handle when a card item is clicked."""
        logger.debug(f"Card clicked: {card_info.get('name')}")
        
        # Deselect all items first
        for item in self.findChildren(SDCardListItem):
            item.set_selected(False)
        
        # Find and select the clicked item
        sender = self.sender()
        if isinstance(sender, SDCardListItem):
            sender.set_selected(True)
            self.selected_card = card_info
            self.card_selected.emit(card_info)
        
    def get_selected_card(self) -> Optional[Dict[str, Any]]:
        """
        Get the currently selected SD card.
        
        Returns:
            Optional[Dict[str, Any]]: Information about the selected card, or None if no card is selected
        """
        return self.selected_card 