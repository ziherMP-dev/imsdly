from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QListWidget, QListWidgetItem,
    QHBoxLayout, QSizePolicy, QStyle, QAbstractItemView
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize, QPoint, QByteArray
from PyQt6.QtGui import QIcon, QFont, QPixmap, QColor, QPainter, QPolygon, QLinearGradient, QImage
from typing import Dict, Optional, List
import os

# Add this at the top to handle the case when rawpy is not installed
try:
    import rawpy
    import io
    import traceback
    import numpy as np
    print("RawPy successfully imported. RAW thumbnails will be available.")
    RAWPY_AVAILABLE = True
except ImportError:
    print("RawPy not found. RAW thumbnails will not be available.")
    print("Install with: pip install rawpy")
    RAWPY_AVAILABLE = False


class FileIconItem(QWidget):
    """Widget for displaying a file item in the icon view."""
    
    def __init__(self, file_info: Dict, parent=None):
        super().__init__(parent)
        self.file_info = file_info
        self.setup_ui()
        
    def setup_ui(self):
        """Set up the UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Create thumbnail container
        icon_label = QLabel()
        icon_label.setFixedSize(120, 90)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label.setStyleSheet("""
            QLabel {
                background-color: #2a2a2a;
                border-radius: 4px;
            }
        """)
        
        # Generate thumbnail based on file type
        if self.file_info['type'] == 'image':
            # For image files, load the actual image as thumbnail
            pixmap = self._generate_image_thumbnail(self.file_info['path'])
            if pixmap:
                icon_label.setPixmap(pixmap)
            else:
                # Fallback to generic icon if thumbnail generation fails
                icon = self.style().standardIcon(QStyle.StandardPixmap.SP_FileIcon)
                pixmap = icon.pixmap(48, 48)
                pixmap = self._apply_color_tint(pixmap, QColor(52, 152, 219))
                icon_label.setPixmap(pixmap)
        elif self.file_info['type'] == 'video':
            # For videos, use a better video icon
            icon = self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPlay)
            pixmap = icon.pixmap(48, 48)
            pixmap = self._apply_color_tint(pixmap, QColor(231, 76, 60))
            
            # Create a video thumbnail appearance
            final_pixmap = QPixmap(120, 90)
            final_pixmap.fill(QColor(25, 25, 25))
            
            painter = QPainter(final_pixmap)
            # Draw video icon in center
            painter.drawPixmap((120 - pixmap.width()) // 2, (90 - pixmap.height()) // 2, pixmap)
            
            # Add a play triangle overlay
            play_triangle = QPolygon([
                QPoint(50, 30),
                QPoint(75, 45),
                QPoint(50, 60)
            ])
            painter.setBrush(QColor(231, 76, 60, 180))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawPolygon(play_triangle)
            painter.end()
            
            icon_label.setPixmap(final_pixmap)
        else:
            # Generic file icon for other files
            icon = self.style().standardIcon(QStyle.StandardPixmap.SP_FileIcon)
            pixmap = icon.pixmap(48, 48)
            pixmap = self._apply_color_tint(pixmap, QColor(149, 165, 166))
            
            # Center the icon in the thumbnail area
            final_pixmap = QPixmap(120, 90)
            final_pixmap.fill(QColor(25, 25, 25))
            
            painter = QPainter(final_pixmap)
            painter.drawPixmap((120 - pixmap.width()) // 2, (90 - pixmap.height()) // 2, pixmap)
            painter.end()
            
            icon_label.setPixmap(final_pixmap)
            
        layout.addWidget(icon_label)
        
        # File name (truncated if too long)
        name = self.file_info['name']
        if len(name) > 20:
            # Truncate with ellipsis
            ext = os.path.splitext(name)[1]
            base = os.path.splitext(name)[0]
            if len(base) > 17:
                name = base[:17] + "..." + ext
        
        name_label = QLabel(name)
        name_label.setFont(QFont("Arial", 9))
        name_label.setStyleSheet("color: white;")
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name_label.setWordWrap(True)
        layout.addWidget(name_label)
        
        # Add file size beneath the name
        size_kb = self.file_info['size'] / 1024
        size_mb = size_kb / 1024
        size_text = f"{size_mb:.1f} MB" if size_mb >= 1 else f"{size_kb:.1f} KB"
        
        size_label = QLabel(size_text)
        size_label.setFont(QFont("Arial", 8))
        size_label.setStyleSheet("color: #aaa;")
        size_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(size_label)
        
        # Set fixed size for consistent grid appearance
        self.setFixedSize(140, 140)
        
        # Show full details in tooltip
        details_text = (
            f"Name: {self.file_info['name']}\n"
            f"Size: {size_text}\n"
            f"Created: {self.file_info['created'].strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"Modified: {self.file_info['modified'].strftime('%Y-%m-%d %H:%M:%S')}"
        )
        self.setToolTip(details_text)
        
        # Styling
        self.setStyleSheet("""
            QWidget {
                background-color: transparent;
                border-radius: 6px;
            }
            QWidget:hover {
                background-color: #2a2a2a;
            }
        """)
        
    def _generate_image_thumbnail(self, image_path: str) -> Optional[QPixmap]:
        """Generate thumbnail for an image file.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Scaled pixmap or None if generation fails
        """
        try:
            # Check for RAW file types and other special formats
            ext = os.path.splitext(image_path)[1].lower()
            
            # Comprehensive list of RAW formats
            raw_formats = [
                # Canon
                '.cr2', '.cr3',
                # Nikon
                '.nef', '.nrw',
                # Sony
                '.arw', '.srf', '.sr2',
                # Fujifilm
                '.raf',
                # Olympus
                '.orf',
                # Panasonic
                '.rw2',
                # Pentax
                '.pef', '.dng',
                # Leica
                '.raw', '.rwl',
                # Phase One
                '.iiq',
                # Hasselblad
                '.3fr',
                # Sigma
                '.x3f',
                # Kodak
                '.kdc', '.dcr',
                # Samsung
                '.srw',
                # Epson
                '.erf',
                # Generic
                '.raw'
            ]
            
            special_formats = ['.heic', '.heif', '.webp', '.tiff', '.tif']
            
            # Print the file extension to verify it's detected correctly
            print(f"Processing file with extension: {ext}")
            
            # For RAW files, try to extract embedded thumbnail
            if ext in raw_formats and RAWPY_AVAILABLE:
                try:
                    print(f"Attempting to process RAW file: {image_path}")
                    # Open the RAW file
                    with rawpy.imread(image_path) as raw:
                        # First try to extract embedded thumbnail if available
                        try:
                            print("Attempting to extract thumbnail")
                            # Some RAW files have embedded thumbnails we can extract
                            thumb_data = raw.extract_thumb()
                            
                            if thumb_data is not None:
                                print(f"Extracted thumbnail format: {thumb_data.format}")
                                
                                # Convert thumb data to QPixmap
                                if thumb_data.format == 'jpeg':
                                    q_data = QByteArray(thumb_data.data)
                                    pixmap = QPixmap()
                                    pixmap.loadFromData(q_data)
                                    
                                    if not pixmap.isNull():
                                        print("Successfully loaded thumbnail from RAW")
                                        # Scale and center if needed
                                        pixmap = pixmap.scaled(
                                            120, 90, 
                                            Qt.AspectRatioMode.KeepAspectRatio, 
                                            Qt.TransformationMode.SmoothTransformation
                                        )
                                        
                                        # Center the thumbnail if needed
                                        if pixmap.width() < 120 or pixmap.height() < 90:
                                            final_pixmap = QPixmap(120, 90)
                                            final_pixmap.fill(QColor(25, 25, 25))
                                            
                                            painter = QPainter(final_pixmap)
                                            x = (120 - pixmap.width()) // 2
                                            y = (90 - pixmap.height()) // 2
                                            painter.drawPixmap(x, y, pixmap)
                                            painter.end()
                                            
                                            return final_pixmap
                                        
                                        return pixmap
                        except (AttributeError, ValueError, RuntimeError) as e:
                            print(f"No embedded thumbnail available: {str(e)}")
                        
                        # If no thumbnail available or extraction failed, try to render the RAW
                        try:
                            print("Attempting to postprocess RAW data (may be slow)")
                            # Process the RAW data to RGB (this can be slow)
                            rgb = raw.postprocess(use_camera_wb=True, half_size=True, output_bps=8)
                            
                            # Convert numpy array to QImage
                            height, width, channels = rgb.shape
                            bytes_per_line = channels * width
                            
                            # Convert from RGB to BGR which is what QImage expects
                            rgb_swapped = rgb[...,::-1].copy()
                            
                            # Create QImage and convert to QPixmap
                            q_img = QImage(rgb_swapped.data, width, height, bytes_per_line, QImage.Format.Format_RGB888)
                            pixmap = QPixmap.fromImage(q_img)
                            
                            if not pixmap.isNull():
                                print("Successfully created thumbnail from RAW processing")
                                # Scale and center
                                pixmap = pixmap.scaled(
                                    120, 90, 
                                    Qt.AspectRatioMode.KeepAspectRatio, 
                                    Qt.TransformationMode.SmoothTransformation
                                )
                                
                                # Center the thumbnail if needed
                                if pixmap.width() < 120 or pixmap.height() < 90:
                                    final_pixmap = QPixmap(120, 90)
                                    final_pixmap.fill(QColor(25, 25, 25))
                                    
                                    painter = QPainter(final_pixmap)
                                    x = (120 - pixmap.width()) // 2
                                    y = (90 - pixmap.height()) // 2
                                    painter.drawPixmap(x, y, pixmap)
                                    painter.end()
                                    
                                    return final_pixmap
                                
                                return pixmap
                        except Exception as e:
                            print(f"Error processing RAW data: {str(e)}")
                            print(traceback.format_exc())
                except Exception as e:
                    print(f"Error opening RAW file: {str(e)}")
                    print(traceback.format_exc())
                
                # Fallback to format indicator if all RAW processing failed
                print(f"Falling back to format indicator for RAW file: {image_path}")
                return self._create_format_indicator(ext, True)
            
            # For special formats that might not load properly in Qt
            if ext in special_formats:
                # Try to load it first
                pixmap = QPixmap(image_path)
                if not pixmap.isNull():
                    # Standard processing for successful loads
                    pixmap = pixmap.scaled(
                        120, 90, 
                        Qt.AspectRatioMode.KeepAspectRatio, 
                        Qt.TransformationMode.SmoothTransformation
                    )
                    
                    # Center if needed
                    if pixmap.width() < 120 or pixmap.height() < 90:
                        final_pixmap = QPixmap(120, 90)
                        final_pixmap.fill(QColor(25, 25, 25))
                        
                        painter = QPainter(final_pixmap)
                        x = (120 - pixmap.width()) // 2
                        y = (90 - pixmap.height()) // 2
                        painter.drawPixmap(x, y, pixmap)
                        painter.end()
                        
                        return final_pixmap
                    
                    return pixmap
                else:
                    # Fallback to format indicator
                    return self._create_format_indicator(ext, False)
            
            # For standard formats, try to load the actual image
            pixmap = QPixmap(image_path)
            if pixmap.isNull():
                return None
                
            # Scale the image to fit within the thumbnail size while maintaining aspect ratio
            pixmap = pixmap.scaled(
                120, 90, 
                Qt.AspectRatioMode.KeepAspectRatio, 
                Qt.TransformationMode.SmoothTransformation
            )
            
            # If the pixmap is smaller than the thumbnail size, center it
            if pixmap.width() < 120 or pixmap.height() < 90:
                final_pixmap = QPixmap(120, 90)
                final_pixmap.fill(QColor(25, 25, 25))
                
                painter = QPainter(final_pixmap)
                # Draw pixmap centered
                x = (120 - pixmap.width()) // 2
                y = (90 - pixmap.height()) // 2
                painter.drawPixmap(x, y, pixmap)
                painter.end()
                
                return final_pixmap
            
            return pixmap
        except Exception:
            return None
    
    def _create_format_indicator(self, ext: str, is_raw: bool = False) -> QPixmap:
        """Create a formatted indicator for special file formats.
        
        Args:
            ext: File extension
            is_raw: Whether this is a RAW format
            
        Returns:
            Formatted pixmap indicator
        """
        final_pixmap = QPixmap(120, 90)
        final_pixmap.fill(QColor(25, 25, 25))
        
        painter = QPainter(final_pixmap)
        
        # Draw a styled box with format name
        painter.setPen(Qt.PenStyle.NoPen)
        if is_raw:
            # RAW format - blue gradient
            gradient = QLinearGradient(0, 0, 120, 90)
            gradient.setColorAt(0, QColor(41, 128, 185, 180))  # Darker blue
            gradient.setColorAt(1, QColor(52, 152, 219, 180))  # Lighter blue
            painter.setBrush(gradient)
        else:
            # Special format - purple gradient
            gradient = QLinearGradient(0, 0, 120, 90)
            gradient.setColorAt(0, QColor(142, 68, 173, 180))  # Darker purple
            gradient.setColorAt(1, QColor(155, 89, 182, 180))  # Lighter purple
            painter.setBrush(gradient)
        
        # Draw rounded rectangle
        painter.drawRoundedRect(0, 0, 120, 90, 8, 8)
        
        # Draw format name
        painter.setPen(QColor(255, 255, 255))
        painter.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        
        # Display the format name
        format_name = ext[1:].upper()
        painter.drawText(final_pixmap.rect(), Qt.AlignmentFlag.AlignCenter, format_name)
        
        # For RAW, add "RAW" text
        if is_raw:
            painter.setFont(QFont("Arial", 9))
            painter.drawText(final_pixmap.rect().adjusted(0, 30, 0, 0), 
                            Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop, 
                            "RAW FORMAT")
        
        painter.end()
        return final_pixmap
            
    def _apply_color_tint(self, pixmap, color):
        """Apply a color tint to a pixmap while preserving transparency."""
        result = pixmap.copy()
        painter = QPainter(result)
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
        painter.fillRect(result.rect(), color)
        painter.end()
        return result


class FileListItem(QWidget):
    """Widget for displaying a file item in the list view."""
    
    def __init__(self, file_info: Dict, parent=None):
        super().__init__(parent)
        self.file_info = file_info
        self.setup_ui()
        
    def setup_ui(self):
        """Set up the UI components."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        
        # Create icon based on file type
        icon_label = QLabel()
        icon_label.setFixedSize(16, 16)
        
        # Get appropriate icon based on file type
        if self.file_info['type'] == 'image':
            icon = self.style().standardIcon(QStyle.StandardPixmap.SP_FileIcon)
        elif self.file_info['type'] == 'video':
            icon = self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPlay)
        else:
            icon = self.style().standardIcon(QStyle.StandardPixmap.SP_FileIcon)
            
        # Create pixmap with icon
        pixmap = icon.pixmap(16, 16)
        
        # Apply color tint based on file type
        if self.file_info['type'] == 'image':
            # Blue tint for images
            pixmap = self._apply_color_tint(pixmap, QColor(52, 152, 219))
        elif self.file_info['type'] == 'video':
            # Red tint for videos
            pixmap = self._apply_color_tint(pixmap, QColor(231, 76, 60))
        else:
            # Gray tint for other files
            pixmap = self._apply_color_tint(pixmap, QColor(149, 165, 166))
            
        icon_label.setPixmap(pixmap)
        layout.addWidget(icon_label)
        
        # File name
        name_label = QLabel(self.file_info['name'])
        name_label.setFont(QFont("Arial", 10))
        name_label.setStyleSheet("color: white;")
        layout.addWidget(name_label)
        
        # Add stretch to push details to the right
        layout.addStretch()
        
        # Add file details
        size_kb = self.file_info['size'] / 1024
        size_mb = size_kb / 1024
        size_text = f"{size_mb:.2f} MB" if size_mb >= 1 else f"{size_kb:.2f} KB"
        
        details_text = (
            f"Size: {size_text} | "
            f"Created: {self.file_info['created'].strftime('%Y-%m-%d')} | "
            f"Modified: {self.file_info['modified'].strftime('%Y-%m-%d')}"
        )
        
        details_label = QLabel(details_text)
        details_label.setFont(QFont("Arial", 8))
        details_label.setStyleSheet("color: #aaa;")
        layout.addWidget(details_label)
        
        # Set fixed height for consistent list appearance
        self.setFixedHeight(30)
        
        # Styling
        self.setStyleSheet("""
            QWidget {
                background-color: transparent;
            }
            QWidget:hover {
                background-color: #2a2a2a;
                border-radius: 3px;
            }
        """)
        
    def _apply_color_tint(self, pixmap, color):
        """Apply a color tint to a pixmap while preserving transparency."""
        result = pixmap.copy()
        painter = QPainter(result)
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
        painter.fillRect(result.rect(), color)
        painter.end()
        return result


class FileListWidget(QWidget):
    """Widget for displaying a list of files."""
    
    file_selected = pyqtSignal(dict)
    
    # View modes
    LIST_VIEW = 0
    ICON_VIEW = 1
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.file_model = None
        self.current_file_types = None
        self.view_mode = self.LIST_VIEW  # Default to list view
        
    def setup_ui(self):
        """Set up the UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Status label (No files, file count, etc.)
        self.status_label = QLabel("No files found")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("color: white; padding: 5px;")
        layout.addWidget(self.status_label)
        
        # File list widget
        self.list_widget = QListWidget()
        self.list_widget.setFrameShape(self.list_widget.Shape.NoFrame)
        self.list_widget.setVerticalScrollMode(QListWidget.ScrollMode.ScrollPerPixel)
        self.list_widget.itemClicked.connect(self._handle_item_clicked)
        layout.addWidget(self.list_widget)
        
        # Styling
        self.list_widget.setStyleSheet("""
            QListWidget {
                background-color: #1e1e1e;
                border: none;
                outline: none;
            }
            QListWidget::item {
                border-bottom: 1px solid #333;
                padding: 0;
                margin: 0;
            }
            QListWidget::item:selected {
                background: #3a3a3a;
            }
            QScrollBar:vertical {
                background: #1e1e1e;
                width: 6px;
                border-radius: 3px;
            }
            QScrollBar::handle:vertical {
                background: #444;
                border-radius: 3px;
            }
            QScrollBar::handle:vertical:hover {
                background: #555;
            }
        """)
        
    def set_view_mode(self, mode: int):
        """Set the view mode.
        
        Args:
            mode: The view mode (LIST_VIEW or ICON_VIEW)
        """
        if mode not in [self.LIST_VIEW, self.ICON_VIEW]:
            return
            
        self.view_mode = mode
        
        # Update the list widget view mode
        if mode == self.ICON_VIEW:
            self.list_widget.setViewMode(QListWidget.ViewMode.IconMode)
            self.list_widget.setResizeMode(QListWidget.ResizeMode.Adjust)
            self.list_widget.setGridSize(QSize(160, 160))
            self.list_widget.setSpacing(10)
            self.list_widget.setWordWrap(True)
            self.list_widget.setUniformItemSizes(True)
            
            # Change the list widget styling for icon view
            self.list_widget.setStyleSheet("""
                QListWidget {
                    background-color: #1e1e1e;
                    border: none;
                    outline: none;
                }
                QListWidget::item {
                    padding: 5px;
                    border-radius: 6px;
                }
                QListWidget::item:selected {
                    background: #3a3a3a;
                }
                QScrollBar:vertical {
                    background: #1e1e1e;
                    width: 6px;
                    border-radius: 3px;
                }
                QScrollBar::handle:vertical {
                    background: #444;
                    border-radius: 3px;
                }
                QScrollBar::handle:vertical:hover {
                    background: #555;
                }
            """)
        else:
            self.list_widget.setViewMode(QListWidget.ViewMode.ListMode)
            self.list_widget.setResizeMode(QListWidget.ResizeMode.Fixed)
            self.list_widget.setGridSize(QSize())
            self.list_widget.setSpacing(0)
            self.list_widget.setWordWrap(False)
            self.list_widget.setUniformItemSizes(False)
            
            # Restore the original list mode styling
            self.list_widget.setStyleSheet("""
                QListWidget {
                    background-color: #1e1e1e;
                    border: none;
                    outline: none;
                }
                QListWidget::item {
                    border-bottom: 1px solid #333;
                    padding: 0;
                    margin: 0;
                }
                QListWidget::item:selected {
                    background: #3a3a3a;
                }
                QScrollBar:vertical {
                    background: #1e1e1e;
                    width: 6px;
                    border-radius: 3px;
                }
                QScrollBar::handle:vertical {
                    background: #444;
                    border-radius: 3px;
                }
                QScrollBar::handle:vertical:hover {
                    background: #555;
                }
            """)
            
        # Refresh the view if we have a model
        if self.file_model:
            self.update_view()
        
    def set_file_model(self, model, file_types: Optional[List[str]] = None):
        """Set the file model and update the view.
        
        Args:
            model: The FileSystemModel
            file_types: List of file types to show (e.g., ['image', 'video'])
        """
        self.file_model = model
        self.current_file_types = file_types
        self.update_view()
        
    def update_view(self):
        """Update the view with the current files."""
        self.list_widget.clear()
        
        if not self.file_model:
            self.status_label.setText("No files found")
            return
            
        files = self.file_model.get_files()
        
        if not files:
            self.status_label.setText("No files found on the SD card")
            return
            
        # Filter files based on file types if specified
        if self.current_file_types:
            files = [f for f in files if f['type'] in self.current_file_types]
            
        # Update status label with file type information
        if not self.current_file_types:
            self.status_label.setText(f"{len(files)} files found")
        else:
            type_counts = {}
            for file in files:
                file_type = file['type']
                type_counts[file_type] = type_counts.get(file_type, 0) + 1
                
            status_parts = []
            if 'image' in type_counts:
                status_parts.append(f"{type_counts['image']} photos")
            if 'video' in type_counts:
                status_parts.append(f"{type_counts['video']} videos")
                
            self.status_label.setText(f"{len(files)} files found ({', '.join(status_parts)})")
        
        # Add files to the list widget based on the current view mode
        for file_info in files:
            item = QListWidgetItem(self.list_widget)
            
            if self.view_mode == self.ICON_VIEW:
                widget = FileIconItem(file_info)
                item.setSizeHint(widget.sizeHint())
            else:
                widget = FileListItem(file_info)
                item.setSizeHint(widget.sizeHint())
                
            self.list_widget.setItemWidget(item, widget)
            
    def _handle_item_clicked(self, item):
        """Handle item click event.
        
        Args:
            item: The clicked QListWidgetItem
        """
        widget = self.list_widget.itemWidget(item)
        if widget and hasattr(widget, 'file_info'):
            self.file_selected.emit(widget.file_info) 