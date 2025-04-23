from PyQt6.QtWidgets import QFrame, QVBoxLayout, QPushButton, QStyle, QWidget, QLabel, QHBoxLayout
from PyQt6.QtCore import QSize, Qt, pyqtSignal
from PyQt6.QtGui import QPixmap, QFont
from ..styles.dark_theme import SIDEBAR_STYLE
from .sd_card.card_list import SDCardListWidget
from handlers.sd_card.detector import SDCardDetector
import logging

# Set up logging
logger = logging.getLogger(__name__)

class SideBarButton(QPushButton):
    """Custom sidebar button that can display an active indicator"""
    
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self._active = False
        self.setCheckable(True)  # Make button checkable but don't use built-in checked state visuals
        
    @property
    def active(self):
        return self._active
        
    @active.setter
    def active(self, value):
        if self._active != value:
            self._active = value
            self.setChecked(value)  # Sync Qt's checked state with our active state
            self.update()  # Force repaint when active state changes

    def paintEvent(self, event):
        """Override paint event to draw the active indicator"""
        super().paintEvent(event)
        
        # Draw active indicator if this button is active
        if self._active:
            from PyQt6.QtGui import QPainter, QColor
            painter = QPainter(self)
            painter.setPen(Qt.PenStyle.NoPen)
            # Use a bright blue color for the indicator
            painter.setBrush(QColor("#007bff"))  # Bootstrap blue color
            # Draw a vertical strip on the left side (5px wide)
            painter.drawRect(0, 0, 5, self.height())
            painter.end()

class SideBar(QFrame):
    # Add signal to notify main window when the active panel changes
    active_panel_changed = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.active_panel = None  # Track which panel is active
        self.buttons = {}  # Store references to buttons
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
        
        # Add brand header
        brand_container = QFrame()
        brand_container.setStyleSheet("""
            background-color: #1a1a1a;
            border-bottom: 1px solid #333;
        """)
        brand_container.setFixedHeight(60)
        brand_layout = QHBoxLayout(brand_container)
        brand_layout.setContentsMargins(16, 8, 16, 8)
        
        # Add logo
        logo_label = QLabel()
        try:
            logo_pixmap = QPixmap("icons:imsdly_logo.png")
            logo_pixmap = logo_pixmap.scaledToHeight(32, Qt.TransformationMode.SmoothTransformation)
            logo_label.setPixmap(logo_pixmap)
        except:
            # Fallback if logo can't be loaded
            logo_label.setText("📷")
            logo_label.setStyleSheet("color: #007bff; font-size: 24px;")
        
        brand_layout.addWidget(logo_label)
        
        # Add brand name
        brand_label = QLabel("Imsdly")
        brand_font = QFont()
        brand_font.setBold(True)
        brand_font.setPointSize(14)
        brand_label.setFont(brand_font)
        brand_label.setStyleSheet("color: #ffffff;")
        brand_layout.addWidget(brand_label)
        
        brand_layout.addStretch(1)
        
        # Add to main layout
        layout.addWidget(brand_container)
        
        # Define buttons
        button_defs = [
            ("SD Card", self.parent.handle_sd_card, "SP_DriveHDIcon"),
            ("Import Settings", self.parent.handle_import_settings, "SP_ArrowRight"),
            ("Browse Files", self.parent.handle_browse_files, "SP_FileDialogContentsView"),
        ]
        
        # Add main buttons
        for button_text, handler, icon_name in button_defs:
            # Use custom SideBarButton instead of QPushButton
            btn = SideBarButton(button_text)
            self.buttons[button_text] = btn  # Store reference to button
            
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
                    padding-left: 16px;  /* Extra padding to account for the indicator */
                    text-align: left;
                    border: none;
                    border-bottom: 1px solid #333;
                    margin: 0;
                }
            """)
            
            # Capture the button name in a local variable
            button_name = button_text
            btn.clicked.connect(lambda checked, name=button_name: self.set_active_panel(name))
            # Connect to original handler too
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
        exit_btn = SideBarButton("Exit")
        self.buttons["Exit"] = exit_btn
        exit_icon = self.style().standardIcon(QStyle.StandardPixmap.SP_DialogCloseButton)
        exit_btn.setIcon(exit_icon)
        exit_btn.setIconSize(QSize(48, 48))  # 3x bigger icon
        exit_btn.setMinimumHeight(72)  # 3x bigger height
        exit_btn.setMinimumWidth(200)  # 2x wider
        exit_btn.setStyleSheet("""
            QPushButton {
                font-size: 16px;
                padding: 12px;
                padding-left: 16px;  /* Extra padding to account for the indicator */
                text-align: left;
                border: none;
                margin: 0;
            }
        """)
        exit_btn.clicked.connect(self.parent.close)
        layout.addWidget(exit_btn)
        
        # Log final layout properties
        logger.debug(f"SideBar final size: {self.size()}")
        
        # Set SD Card as active by default
        self.set_active_panel("SD Card")
        
    def set_active_panel(self, panel_name):
        """Set the active panel and update indicators."""
        if panel_name == self.active_panel:
            return  # Already active
            
        # Deactivate the previous active button
        if self.active_panel and self.active_panel in self.buttons:
            self.buttons[self.active_panel].active = False
            self.buttons[self.active_panel].setChecked(False)  # Ensure the checked state is reset
            
        # Activate the new button
        self.active_panel = panel_name
        if panel_name in self.buttons:
            self.buttons[panel_name].active = True
            self.buttons[panel_name].setChecked(True)  # Ensure the checked state is set
            
        # Emit signal to inform main window
        self.active_panel_changed.emit(panel_name)
        
        logger.debug(f"Active panel set to: {panel_name}")
        
    def _handle_cards_updated(self, cards):
        """Handle when the SD card list is updated"""
        if hasattr(self, 'sd_card_list'):
            # Show the list if there are cards, hide if empty
            self.sd_card_list.setVisible(len(cards) > 0)
            # Log sizes after update
            logger.debug(f"SD Card list size after update: {self.sd_card_list.size()}")
            logger.debug(f"SideBar size after update: {self.size()}")

    def start_monitoring(self):
        """Start monitoring SD cards"""
        if hasattr(self, 'sd_card_list'):
            self.sd_card_list.sd_detector.start_monitoring() 