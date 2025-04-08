from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QFrame, QStatusBar, QSizeGrip, QStackedWidget, QLabel, QPushButton
from PyQt6.QtCore import Qt, QPoint
from .widgets.title_bar import TitleBar
from .widgets.side_bar import SideBar
from .styles.dark_theme import MAIN_WINDOW_STYLE, CONTENT_AREA_STYLE
from .sd_card_panel import SDCardPanel

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.dragPos = None
        self.setup_ui()
        
    def setup_ui(self):
        """Set up the main window UI"""
        self.setWindowTitle("Imsdly")
        self.setMinimumSize(1000, 600)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setStyleSheet(MAIN_WINDOW_STYLE)
        
        # Create main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Add title bar
        self.title_bar = TitleBar(self)
        main_layout.addWidget(self.title_bar)
        
        # Content area with sidebar and main content
        content_widget = QWidget()
        content_layout = QHBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        
        # Add sidebar
        self.sidebar = SideBar(self)
        content_layout.addWidget(self.sidebar, stretch=0)
        
        # Main content area
        self.center_content = QFrame()
        self.center_content.setStyleSheet(CONTENT_AREA_STYLE)
        content_layout.addWidget(self.center_content, stretch=1)
        
        # Create stacked widget for content pages
        self.stacked_widget = QStackedWidget()
        center_layout = QVBoxLayout(self.center_content)
        center_layout.setContentsMargins(0, 0, 0, 0)
        center_layout.addWidget(self.stacked_widget)
        
        # Create and add panels
        self.sd_card_panel = SDCardPanel()
        self.stacked_widget.addWidget(self.sd_card_panel)
        
        # Create a "No SD Card" placeholder panel
        self.no_sd_card_panel = QWidget()
        no_card_layout = QVBoxLayout(self.no_sd_card_panel)
        no_card_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        no_card_message = QLabel("No SD Card Detected")
        no_card_message.setStyleSheet("""
            font-size: 24px;
            color: #cccccc;
            margin-bottom: 20px;
        """)
        
        instruction_message = QLabel("Please insert an SD card or click Refresh if you've already inserted one.")
        instruction_message.setStyleSheet("""
            font-size: 16px;
            color: #999999;
            margin-bottom: 30px;
        """)
        
        refresh_button = QPushButton("Refresh")
        refresh_button.setStyleSheet("""
            QPushButton {
                background-color: #0d6efd;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 10px 20px;
                font-size: 16px;
                min-width: 150px;
            }
            QPushButton:hover {
                background-color: #0b5ed7;
            }
            QPushButton:pressed {
                background-color: #0a58ca;
            }
        """)
        refresh_button.clicked.connect(self.handle_refresh)
        
        no_card_layout.addWidget(no_card_message)
        no_card_layout.addWidget(instruction_message)
        no_card_layout.addWidget(refresh_button)
        
        self.stacked_widget.addWidget(self.no_sd_card_panel)
        
        # Placeholder panel for Import Settings
        self.import_settings_panel = QWidget()
        import_layout = QVBoxLayout(self.import_settings_panel)
        import_layout.addWidget(QLabel("Import Settings Panel - To be implemented"))
        self.stacked_widget.addWidget(self.import_settings_panel)
        
        # Placeholder panel for Browse Files
        self.browse_files_panel = QWidget()
        browse_layout = QVBoxLayout(self.browse_files_panel)
        browse_layout.addWidget(QLabel("Browse Files Panel - To be implemented"))
        self.stacked_widget.addWidget(self.browse_files_panel)
        
        main_layout.addWidget(content_widget)

        # Set up status bar
        status_bar = QStatusBar()
        status_bar.setStyleSheet("""
            QStatusBar {
                background-color: #0d1117;
                color: #ffffff;
                border: none;
                font-family: 'Segoe UI', 'Arial', sans-serif;
                font-size: 12px;
            }
        """)
        self.setStatusBar(status_bar)

        # Add size grip to status bar
        size_grip = QSizeGrip(status_bar)
        size_grip.setStyleSheet("""
            QSizeGrip {
                background-color: #0d1117;
                width: 16px;
                height: 16px;
            }
        """)
        status_bar.addPermanentWidget(size_grip)
        
        # Show initial status
        self.statusBar().showMessage("Ready")
        
        # Show SD card panel by default only if cards are available, otherwise show no card panel
        if hasattr(self.sidebar, 'sd_card_list'):
            cards = self.sidebar.sd_card_list.sd_detector.get_current_cards()
            if len(cards) > 0:
                self.stacked_widget.setCurrentWidget(self.sd_card_panel)
            else:
                self.stacked_widget.setCurrentWidget(self.no_sd_card_panel)
        else:
            self.stacked_widget.setCurrentWidget(self.no_sd_card_panel)
        
        # Connect SD card list signals
        if hasattr(self.sidebar, 'sd_card_list'):
            self.sidebar.sd_card_list.card_selected.connect(self._handle_card_selected)
            # Connect to card_inserted signal to automatically select newly inserted cards
            self.sidebar.sd_card_list.sd_detector.card_inserted.connect(self._handle_card_inserted)
            # Connect to card_removed signal to switch to no card view when needed
            self.sidebar.sd_card_list.sd_detector.card_removed.connect(self._handle_card_removed)
    
    def _handle_card_selected(self, card_info: dict) -> None:
        """
        Handle SD card selection.
        
        Args:
            card_info: Dictionary containing information about the selected card
        """
        # Switch to SD card panel since a card is now selected
        self.stacked_widget.setCurrentWidget(self.sd_card_panel)
        # Update status bar
        self.statusBar().showMessage(f"Selected SD card: {card_info.get('name', 'Unknown Card')}", 2000)

    def _handle_card_inserted(self, card_info: dict) -> None:
        """
        Handle SD card insertion - automatically select the card and switch to SD card view.
        
        Args:
            card_info: Dictionary containing information about the inserted card
        """
        # Update SD card panel with the card information
        self.sd_card_panel._handle_card_selected(card_info)
        
        # Switch to SD card panel
        self.stacked_widget.setCurrentWidget(self.sd_card_panel)
        
        # Update status bar
        self.statusBar().showMessage(f"SD card detected: {card_info.get('name', 'Unknown Card')}", 3000)
        
        # Store as selected card in the list widget
        if hasattr(self.sidebar, 'sd_card_list'):
            self.sidebar.sd_card_list.selected_card = card_info

    def _handle_card_removed(self, card_info: dict) -> None:
        """
        Handle SD card removal - switch to no card view if no cards are left.
        
        Args:
            card_info: Dictionary containing information about the removed card
        """
        # Check if any cards are still available
        if hasattr(self.sidebar, 'sd_card_list'):
            remaining_cards = self.sidebar.sd_card_list.sd_detector.get_current_cards()
            
            if not remaining_cards:
                # No cards left, switch to the no card panel
                self.stacked_widget.setCurrentWidget(self.no_sd_card_panel)
                
                # Update status bar
                self.statusBar().showMessage(f"SD card removed: {card_info.get('name', 'Unknown Card')}", 3000)

    def mousePressEvent(self, event):
        """Handle mouse press events for window dragging"""
        if event.button() == Qt.MouseButton.LeftButton and not self.isMaximized():
            self.dragPos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        """Handle mouse move events for window dragging"""
        if event.buttons() == Qt.MouseButton.LeftButton and self.dragPos is not None and not self.isMaximized():
            newPos = event.globalPosition().toPoint()
            diff = newPos - self.dragPos
            self.move(self.pos() + diff)
            self.dragPos = newPos

    def mouseReleaseEvent(self, event):
        """Handle mouse release events for window dragging"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragPos = None

    def toggle_maximize(self):
        """Toggle window maximize/restore"""
        if self.isMaximized():
            self.showNormal()
            # Enable title bar dragging when window is not maximized
            self.title_bar.setCursor(Qt.CursorShape.ArrowCursor)
        else:
            self.showMaximized()
            # Disable title bar dragging when window is maximized
            self.title_bar.setCursor(Qt.CursorShape.ArrowCursor)
            self.dragPos = None  # Clear drag position when maximized

    def handle_import_settings(self):
        """Handle Import Settings button click"""
        self.stacked_widget.setCurrentWidget(self.import_settings_panel)
        self.statusBar().showMessage("Import Settings view activated", 2000)

    def handle_refresh(self):
        """Handle refresh button click on no SD card panel"""
        if hasattr(self.sidebar, 'sd_card_list'):
            self.sidebar.sd_card_list.refresh_cards()
            
            # Check if there are any cards after refresh
            cards = self.sidebar.sd_card_list.sd_detector.get_current_cards()
            if len(cards) > 0:
                # Switch to SD card panel if cards are available
                self.stacked_widget.setCurrentWidget(self.sd_card_panel)
            else:
                # Stay on no SD card panel if no cards are available
                self.stacked_widget.setCurrentWidget(self.no_sd_card_panel)
        
        self.statusBar().showMessage("Refreshed SD card list", 2000)

    def handle_sd_card(self):
        """Handle SD Card button click"""
        # Check if there are any SD cards available
        if hasattr(self.sidebar, 'sd_card_list'):
            cards = self.sidebar.sd_card_list.sd_detector.get_current_cards()
            if len(cards) > 0:
                self.stacked_widget.setCurrentWidget(self.sd_card_panel)
            else:
                self.stacked_widget.setCurrentWidget(self.no_sd_card_panel)
        else:
            self.stacked_widget.setCurrentWidget(self.no_sd_card_panel)
            
        self.statusBar().showMessage("SD Card view activated", 2000)

    def handle_browse_files(self):
        """Handle Browse Files button click"""
        self.stacked_widget.setCurrentWidget(self.browse_files_panel)
        self.statusBar().showMessage("Browse Files view activated", 2000) 