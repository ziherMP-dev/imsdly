import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                           QHBoxLayout, QPushButton, QLabel, QFrame)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Imsdly")
        self.setMinimumSize(1000, 600)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        
        # Create main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Top bar
        top_bar = QFrame()
        top_bar.setFixedHeight(30)
        top_bar.setStyleSheet("""
            QFrame {
                background-color: #2c313c;
                border: none;
            }
        """)
        top_bar_layout = QHBoxLayout(top_bar)
        top_bar_layout.setContentsMargins(10, 0, 0, 0)
        top_bar_layout.setSpacing(0)
        
        # Add version label to top bar
        version_label = QLabel("v1.0.0")
        version_label.setStyleSheet("color: #ffffff;")
        top_bar_layout.addWidget(version_label)
        
        top_bar_layout.addStretch()
        
        # Window controls
        window_controls = QFrame()
        window_controls_layout = QHBoxLayout(window_controls)
        window_controls_layout.setContentsMargins(0, 0, 0, 0)
        window_controls_layout.setSpacing(0)
        
        min_btn = QPushButton("−")
        max_btn = QPushButton("□")
        close_btn = QPushButton("×")
        
        for btn in [min_btn, max_btn, close_btn]:
            btn.setFixedSize(45, 30)
            btn.setStyleSheet("""
                QPushButton {
                    color: #ffffff;
                    border: none;
                    font-size: 16px;
                }
                QPushButton:hover {
                    background-color: #3c4454;
                }
            """)
            window_controls_layout.addWidget(btn)
        
        close_btn.setStyleSheet("""
            QPushButton {
                color: #ffffff;
                border: none;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: #ff5555;
            }
        """)
        
        top_bar_layout.addWidget(window_controls)
        main_layout.addWidget(top_bar)
        
        # Content area with sidebar and main content
        content_widget = QWidget()
        content_layout = QHBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        
        # Left sidebar
        sidebar = QFrame()
        sidebar.setStyleSheet("""
            QFrame {
                background-color: #2c313c;
                border: none;
            }
            QPushButton {
                color: #ffffff;
                text-align: left;
                padding: 10px;
                border: none;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #3c4454;
            }
        """)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(0)
        
        # Add sidebar buttons with their respective handlers
        sidebar_buttons = [
            ("Import Files", self.handle_import_files),
            ("SD Card", self.handle_sd_card),
            ("Browse Files", self.handle_browse_files),
            ("Exit", self.close)
        ]
        
        for button_text, handler in sidebar_buttons:
            btn = QPushButton(button_text)
            btn.clicked.connect(handler)
            sidebar_layout.addWidget(btn)
        
        sidebar_layout.addStretch()
        content_layout.addWidget(sidebar, stretch=0)
        
        # Main content area
        self.center_content = QFrame()
        self.center_content.setStyleSheet("""
            QFrame {
                background-color: #1b1e23;
                border: none;
            }
        """)
        content_layout.addWidget(self.center_content, stretch=1)
        
        main_layout.addWidget(content_widget)
        
        # Connect window control buttons
        close_btn.clicked.connect(self.close)
        min_btn.clicked.connect(self.showMinimized)
        max_btn.clicked.connect(self.toggle_maximize)
        
        # Set application-wide style
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1b1e23;
            }
        """)

    def toggle_maximize(self):
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()

    def handle_import_files(self):
        """Handle Import Files button click"""
        self.statusBar().showMessage("Import Files clicked", 2000)

    def handle_sd_card(self):
        """Handle SD Card button click"""
        self.statusBar().showMessage("SD Card clicked", 2000)

    def handle_browse_files(self):
        """Handle Browse Files button click"""
        self.statusBar().showMessage("Browse Files clicked", 2000)

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
