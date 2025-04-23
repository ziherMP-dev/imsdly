from PyQt6.QtWidgets import QSplitter
from PyQt6.QtCore import Qt, QTimer
from .custom_splitter_handle import CustomSplitterHandle


class CustomSplitter(QSplitter):
    """
    Custom splitter with improved handle appearance.
    """
    
    def __init__(self, orientation=Qt.Orientation.Horizontal, parent=None):
        """Initialize the custom splitter."""
        super().__init__(orientation, parent)
        
        # Set handle properties
        self.setHandleWidth(4)
        self.setChildrenCollapsible(False)
        
        # Optimize drawing during resize
        self.setOpaqueResize(True)
        
        # Store original sizes for restoration
        self._original_sizes = None
        
        # Create a timer for delayed size setting to improve resize performance
        self._resize_timer = QTimer(self)
        self._resize_timer.setSingleShot(True)
        self._resize_timer.setInterval(250)  # 250ms delay
    
    def createHandle(self):
        """Create and return a custom splitter handle."""
        return CustomSplitterHandle(self.orientation(), self)
    
    def setSizes(self, sizes):
        """Override setSizes to store original values for restoration."""
        super().setSizes(sizes)
        if self._original_sizes is None:
            self._original_sizes = sizes
    
    def setMinimumSizes(self):
        """Set minimum sizes for the widgets to prevent too small sizes."""
        # For horizontal splitter, first widget is usually a sidebar with a minimum width
        if self.orientation() == Qt.Orientation.Horizontal and self.count() > 0:
            widget = self.widget(0)
            if widget:
                widget.setMinimumWidth(150)  # Minimum sidebar width
                
    def addWidget(self, widget):
        """Override addWidget to set minimum sizes after adding widgets."""
        result = super().addWidget(widget)
        self.setMinimumSizes()
        return result
    
    def resetSizes(self):
        """Reset to the original sizes if available."""
        if self._original_sizes is not None:
            self.setSizes(self._original_sizes) 