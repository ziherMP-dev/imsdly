from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QFrame, QStatusBar, QSizeGrip, QStackedWidget, QLabel
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
        
        # Placeholder panel for Import Files
        self.import_files_panel = QWidget()
        import_layout = QVBoxLayout(self.import_files_panel)
        import_layout.addWidget(QLabel("Import Files Panel - To be implemented"))
        self.stacked_widget.addWidget(self.import_files_panel)
        
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
        
        # Show SD card panel by default
        self.stacked_widget.setCurrentWidget(self.sd_card_panel)
        
        # Connect SD card list signals
        if hasattr(self.sidebar, 'sd_card_list'):
            self.sidebar.sd_card_list.card_selected.connect(self._handle_card_selected)
    
    def _handle_card_selected(self, card_info: dict) -> None:
        """
        Handle SD card selection.
        
        Args:
            card_info: Dictionary containing information about the selected card
        """
        # Switch to SD card panel
        self.stacked_widget.setCurrentWidget(self.sd_card_panel)
        # Update status bar
        self.statusBar().showMessage(f"Selected SD card: {card_info.get('name', 'Unknown Card')}", 2000)

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

    def handle_import_files(self):
        """Handle Import Files button click"""
        self.stacked_widget.setCurrentWidget(self.import_files_panel)
        self.statusBar().showMessage("Import Files view activated", 2000)

    def handle_sd_card(self):
        """Handle SD Card button click"""
        self.stacked_widget.setCurrentWidget(self.sd_card_panel)
        self.statusBar().showMessage("SD Card view activated", 2000)

    def handle_browse_files(self):
        """Handle Browse Files button click"""
        self.stacked_widget.setCurrentWidget(self.browse_files_panel)
        self.statusBar().showMessage("Browse Files view activated", 2000) 