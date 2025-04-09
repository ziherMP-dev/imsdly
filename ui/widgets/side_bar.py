from PyQt6.QtWidgets import QFrame, QVBoxLayout, QPushButton, QStyle, QWidget
from PyQt6.QtCore import QSize
from ..styles.dark_theme import SIDEBAR_STYLE
from .sd_card.card_list import SDCardListWidget
from handlers.sd_card.detector import SDCardDetector
import logging

# Set up logging
logger = logging.getLogger(__name__)

class SideBar(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setup_ui()
        
    def setup_ui(self):
        """Set up the sidebar UI"""
        self.setStyleSheet(SIDEBAR_STYLE)
        
        # Create layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)  # Remove spacing between widgets
        
        # Log initial layout properties
        logger.debug(f"SideBar layout margins: {layout.contentsMargins()}")
        logger.debug(f"SideBar layout spacing: {layout.spacing()}")
        
        # Define buttons
        buttons = [
            ("SD Card", self.parent.handle_sd_card, "SP_DriveHDIcon"),
            ("Import Settings", self.parent.handle_import_settings, "SP_ArrowRight"),
            ("Browse Files", self.parent.handle_browse_files, "SP_FileDialogContentsView"),
        ]
        
        # Add main buttons
        for button_text, handler, icon_name in buttons:
            btn = QPushButton(button_text)
            icon = self.style().standardIcon(getattr(QStyle.StandardPixmap, icon_name))
            btn.setIcon(icon)
            # Make buttons 3x bigger vertically and 2x wider
            btn.setIconSize(QSize(48, 48))  # 3x bigger icon
            btn.setMinimumHeight(72)  # 3x bigger height
            btn.setMinimumWidth(200)  # 2x wider
            btn.setStyleSheet("""
                QPushButton {
                    font-size: 16px;
                    padding: 12px;
                    text-align: left;
                    border: none;
                    border-bottom: 1px solid #333;
                    margin: 0;
                }
            """)
            btn.clicked.connect(handler)
            layout.addWidget(btn)
            
            # Add SD card list under the SD Card button
            if button_text == "SD Card":
                self.sd_card_list = SDCardListWidget()
                # Connect to the detector's cards_updated signal
                self.sd_card_list.sd_detector.cards_updated.connect(self._handle_cards_updated)
                # Add list widget with no spacing
                layout.addWidget(self.sd_card_list)
                
                # Log button and list sizes
                logger.debug(f"SD Card button size: {btn.size()}")
                logger.debug(f"SD Card list size: {self.sd_card_list.size()}")
                
                # Check initial state of SD cards
                initial_cards = self.sd_card_list.sd_detector.get_current_cards()
                self.sd_card_list.setVisible(len(initial_cards) > 0)
        
        # Add stretch to push bottom buttons down
        layout.addStretch()
        
        # Add exit button at the bottom
        exit_btn = QPushButton("Exit")
        exit_icon = self.style().standardIcon(QStyle.StandardPixmap.SP_DialogCloseButton)
        exit_btn.setIcon(exit_icon)
        exit_btn.setIconSize(QSize(48, 48))  # 3x bigger icon
        exit_btn.setMinimumHeight(72)  # 3x bigger height
        exit_btn.setMinimumWidth(200)  # 2x wider
        exit_btn.setStyleSheet("""
            QPushButton {
                font-size: 16px;
                padding: 12px;
                text-align: left;
                border: none;
                margin: 0;
            }
        """)
        exit_btn.clicked.connect(self.parent.close)
        layout.addWidget(exit_btn)
        
        # Log final layout properties
        logger.debug(f"SideBar final size: {self.size()}")
        
    def _handle_cards_updated(self, cards):
        """Handle when the SD card list is updated"""
        if hasattr(self, 'sd_card_list'):
            # Show the list if there are cards, hide if empty
            self.sd_card_list.setVisible(len(cards) > 0)
            # Log sizes after update
            logger.debug(f"SD Card list size after update: {self.sd_card_list.size()}")
            logger.debug(f"SideBar size after update: {self.size()}") 