"""
Test utility to display different icon options for image files.
Run this directly to test the icon options.
"""

import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QWidget,
    QLabel, QHBoxLayout, QPushButton, QStyle
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QPainter, QPixmap

class IconTestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Icon Options Test")
        self.setGeometry(100, 100, 400, 600)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Create layout
        layout = QVBoxLayout(central_widget)
        layout.setSpacing(10)
        
        # Icon options to test
        icon_options = [
            ("1. SP_FileDialogInfoView", QStyle.StandardPixmap.SP_FileDialogInfoView),
            ("2. SP_FileDialogDetailedView", QStyle.StandardPixmap.SP_FileDialogDetailedView),
            ("3. SP_FileDialogContentsView", QStyle.StandardPixmap.SP_FileDialogContentsView),
            ("4. SP_FileDialogListView", QStyle.StandardPixmap.SP_FileDialogListView),
            ("5. SP_FileIcon", QStyle.StandardPixmap.SP_FileIcon),
            ("6. SP_DialogOpenButton", QStyle.StandardPixmap.SP_DialogOpenButton),
            ("7. SP_DialogSaveButton", QStyle.StandardPixmap.SP_DialogSaveButton),
            ("8. SP_DialogApplyButton", QStyle.StandardPixmap.SP_DialogApplyButton),
            ("9. SP_ArrowUp", QStyle.StandardPixmap.SP_ArrowUp),
            ("10. SP_ArrowDown", QStyle.StandardPixmap.SP_ArrowDown),
            # New photo/image related icons
            ("11. SP_DialogOpenButton", QStyle.StandardPixmap.SP_DialogOpenButton),
            ("12. SP_DialogSaveButton", QStyle.StandardPixmap.SP_DialogSaveButton),
            ("13. SP_DialogApplyButton", QStyle.StandardPixmap.SP_DialogApplyButton),
            ("14. SP_ArrowUp", QStyle.StandardPixmap.SP_ArrowUp),
            ("15. SP_ArrowDown", QStyle.StandardPixmap.SP_ArrowDown),
            ("16. SP_FileLinkIcon", QStyle.StandardPixmap.SP_FileLinkIcon),
            ("17. SP_FileDialogStart", QStyle.StandardPixmap.SP_FileDialogStart),
            ("18. SP_FileDialogEnd", QStyle.StandardPixmap.SP_FileDialogEnd),
            ("19. SP_FileDialogToParent", QStyle.StandardPixmap.SP_FileDialogToParent),
            ("20. SP_FileDialogNewFolder", QStyle.StandardPixmap.SP_FileDialogNewFolder)
        ]
        
        # Add each icon option
        for name, icon_type in icon_options:
            # Create row layout
            row = QHBoxLayout()
            
            # Add label with number and name
            label = QLabel(name)
            label.setStyleSheet("color: white;")
            row.addWidget(label)
            
            # Add icon
            icon = self.style().standardIcon(icon_type)
            pixmap = icon.pixmap(16, 16)
            
            # Apply blue tint
            result = pixmap.copy()
            painter = QPainter(result)
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
            painter.fillRect(result.rect(), QColor(52, 152, 219))  # Blue color
            painter.end()
            
            icon_label = QLabel()
            icon_label.setPixmap(result)
            row.addWidget(icon_label)
            
            # Add stretch to push icon to the right
            row.addStretch()
            
            layout.addLayout(row)
        
        # Add stretch to push all items to the top
        layout.addStretch()
        
        # Set dark theme
        self.setStyleSheet("""
            QMainWindow, QWidget {
                background-color: #1e1e1e;
                color: white;
            }
        """)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = IconTestWindow()
    window.show()
    sys.exit(app.exec()) 