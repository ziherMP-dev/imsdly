from PyQt6.QtWidgets import QSplitterHandle, QSplitter
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QPainter, QColor, QLinearGradient


class CustomSplitterHandle(QSplitterHandle):
    """
    Custom splitter handle with improved appearance and hover effect.
    Provides a visual separator between sidebar and main content area.
    """
    
    def __init__(self, orientation: Qt.Orientation, parent: QSplitter):
        """Initialize the custom splitter handle."""
        super().__init__(orientation, parent)
        self.setCursor(Qt.CursorShape.SplitHCursor if orientation == Qt.Orientation.Horizontal else Qt.CursorShape.SplitVCursor)
        self.setMouseTracking(True)
        self.is_hovered = False
        self.is_pressed = False
        
        # Set tooltip to help users understand the splitter functionality
        self.setToolTip("Drag to resize panels\nDouble-click to reset to default size")
    
    def sizeHint(self) -> QSize:
        """Return the size hint for the handle."""
        if self.orientation() == Qt.Orientation.Horizontal:
            return QSize(4, self.height())
        else:
            return QSize(self.width(), 4)
    
    def enterEvent(self, event):
        """Handle the mouse enter event for hover effect."""
        self.is_hovered = True
        self.update()
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        """Handle the mouse leave event for hover effect."""
        self.is_hovered = False
        self.update()
        super().leaveEvent(event)
    
    def mousePressEvent(self, event):
        """Handle mouse press events."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_pressed = True
            self.update()
        super().mousePressEvent(event)
    
    def mouseReleaseEvent(self, event):
        """Handle mouse release events."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_pressed = False
            self.update()
        super().mouseReleaseEvent(event)
    
    def mouseDoubleClickEvent(self, event):
        """Handle double-click to reset splitter to default sizes."""
        if event.button() == Qt.MouseButton.LeftButton:
            # Call the parent splitter's resetSizes method
            if hasattr(self.splitter(), 'resetSizes'):
                self.splitter().resetSizes()
        super().mouseDoubleClickEvent(event)
    
    def paintEvent(self, event):
        """Custom paint event for the splitter handle."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Define colors
        if self.is_pressed:
            # When pressed, use a brighter blue
            main_color = QColor("#0d8bf2")
        elif self.is_hovered:
            # When hovered, use a blue accent
            main_color = QColor("#007bff")
        else:
            # Default state, dark gray line with subtle gradient
            main_color = QColor("#333333")
        
        if self.orientation() == Qt.Orientation.Horizontal:
            # Create a gradient for a nicer look
            gradient = QLinearGradient(0, 0, 0, self.height())
            gradient.setColorAt(0, main_color.lighter(110))
            gradient.setColorAt(0.5, main_color)
            gradient.setColorAt(1, main_color.darker(110))
            
            # Draw the handle with the gradient
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(gradient)
            painter.drawRect(0, 0, self.width(), self.height())
            
            # Draw grip dots for better visibility
            if self.is_hovered or self.is_pressed:
                dot_color = QColor("#ffffff")  # White dots
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(dot_color)
                
                # Draw 3 dots in the center
                center_y = self.height() // 2
                for i in range(3):
                    y_offset = (i - 1) * 6
                    dot_x = self.width() // 2 - 1
                    dot_y = center_y + y_offset
                    # Create slightly larger dots
                    if self.is_pressed:
                        # Pressed dots are brighter and bigger
                        painter.drawEllipse(dot_x - 1, dot_y - 1, 3, 3)
                    else:
                        painter.drawEllipse(dot_x, dot_y, 2, 2)
        else:
            # For vertical orientation
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(main_color)
            painter.drawRect(0, 0, self.width(), self.height()) 