from PyQt6.QtWidgets import QFrame, QHBoxLayout, QPushButton, QLabel
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap, QFont
from ..styles.dark_theme import (
    TOP_BAR_STYLE,
    VERSION_LABEL_STYLE,
    WINDOW_CONTROLS_BUTTON_STYLE,
    CLOSE_BUTTON_STYLE
)

class TitleBar(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setup_ui()
        
    def setup_ui(self):
        """Set up the title bar UI"""
        self.setFixedHeight(30)
        self.setStyleSheet(TOP_BAR_STYLE)
        
        # Create layout
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 0, 0, 0)
        layout.setSpacing(6)  # Add some spacing between elements
        
        # Add logo
        logo_label = QLabel()
        try:
            logo_pixmap = QPixmap("icons:imsdly_logo.png")
            logo_pixmap = logo_pixmap.scaledToHeight(20, Qt.TransformationMode.SmoothTransformation)
            logo_label.setPixmap(logo_pixmap)
            logo_label.setFixedSize(20, 20)
        except:
            # Fallback if logo can't be loaded
            logo_label.setText("📷")
            logo_label.setStyleSheet("color: #007bff; font-size: 16px;")
        
        layout.addWidget(logo_label)
        
        # Add brand name
        brand_label = QLabel("Imsdly")
        brand_font = QFont()
        brand_font.setBold(True)
        brand_font.setPointSize(10)
        brand_label.setFont(brand_font)
        brand_label.setStyleSheet("color: #ffffff;")
        layout.addWidget(brand_label)
        
        # Add some spacing between brand and version
        layout.addSpacing(4)
        
        # Version label
        version_label = QLabel("v1.0.0")
        version_label.setStyleSheet(VERSION_LABEL_STYLE)
        layout.addWidget(version_label)
        
        layout.addStretch()
        
        # Window controls
        window_controls = QFrame()
        controls_layout = QHBoxLayout(window_controls)
        controls_layout.setContentsMargins(0, 0, 0, 0)
        controls_layout.setSpacing(0)
        
        # Create window control buttons
        min_btn = QPushButton("−")
        max_btn = QPushButton("□")
        close_btn = QPushButton("×")
        
        for btn in [min_btn, max_btn]:
            btn.setFixedSize(45, 30)
            btn.setStyleSheet(WINDOW_CONTROLS_BUTTON_STYLE)
            controls_layout.addWidget(btn)
        
        close_btn.setFixedSize(45, 30)
        close_btn.setStyleSheet(CLOSE_BUTTON_STYLE)
        controls_layout.addWidget(close_btn)
        
        layout.addWidget(window_controls)
        
        # Connect buttons
        min_btn.clicked.connect(self.parent.showMinimized)
        max_btn.clicked.connect(self.parent.toggle_maximize)
        close_btn.clicked.connect(self.parent.close)
        
        # Enable window dragging
        self.mousePressEvent = self.parent.mousePressEvent
        self.mouseMoveEvent = self.parent.mouseMoveEvent 