"""
File List Widget for SD Card Manager.

Handles displaying files from SD cards in different view modes (list, icons, thumbnails)
with asynchronous thumbnail generation for images, videos, and other file types.

Video thumbnail optimizations:
- Uses OpenCV for frame extraction via the video_thumbnail module
- Supports optimized methods through video_thumbnail_optimized, which offers several
  optimization techniques:
  - fast_first_frame: Extracts only the first frame (fastest method)
  - fast_frame_grab: Efficiently extracts a specific frame number (good quality/speed balance)
  - direct_seek: Direct timestamp seeking without decoding intervening frames
  - keyframe_only: Extract nearest keyframe for faster processing
  - stream_optimized: Uses optimized video stream parameters
  - skip_frames: Skips frames for faster seeking
  - hardware_accel: Attempts to use hardware acceleration
- Configuration options are available in VIDEO_THUMBNAIL_CONFIG

For benchmarking video thumbnail performance, use:
  test_video_thumbnail(path_to_video_file)
"""

import os
import time
import json
import logging
import shutil
import subprocess
import math
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Set, Callable
from queue import Queue, Empty
from threading import Thread
import sys

# Configure logging
logger = logging.getLogger("FileList")

from PyQt6.QtCore import (
    Qt, QSize, QTimer, QRect, QPoint, QEvent, QThread, QThreadPool, 
    QRunnable, QObject, pyqtSignal, pyqtSlot, QMutex, QRunnable, QCoreApplication
)
from PyQt6.QtGui import (
    QPixmap, QImage, QPainter, QColor, QIcon, QPen, QBrush, QFont, QAction, 
    QKeySequence, QDrag, QCursor, QShortcut, QPainterPath, QStandardItem,
    QStandardItemModel, QPainter, QPolygon, QLinearGradient
)
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QListWidget, QListView, QListWidgetItem, QMenu, QFrame, QDialog,
    QMessageBox, QAbstractItemView, QFileDialog, QSizePolicy, QToolButton,
    QToolTip, QScrollArea, QGridLayout, QSplitter, QProgressBar, QCheckBox,
    QComboBox, QInputDialog, QLineEdit, QStyle
)

# Initialize video thumbnail availability flags
VIDEO_THUMBNAIL_AVAILABLE = False
OPTIMIZED_THUMBNAIL_AVAILABLE = False

# Video thumbnail configuration
VIDEO_THUMBNAIL_CONFIG = {
    "use_optimized": True,        # Whether to use the optimized version when available
    "preferred_method": "fast_frame_grab",  # Use fast_frame_grab as it provides better content than fast_first_frame
    "frame_number": 5,            # Frame number for thumbnail generation (changed from 50)
    "frame_time": 2.0,            # Time in seconds for standard method (only used as fallback)
    "fallback_to_standard": True  # Fallback to standard method if optimized fails
}

# Import video thumbnail module if available
try:
    from utils import video_thumbnail
    
    # Check if OpenCV is available
    if not hasattr(video_thumbnail, 'OPENCV_AVAILABLE') or not video_thumbnail.OPENCV_AVAILABLE:
        logger.warning("OpenCV is not available in video_thumbnail module")
    else:
        logger.info("OpenCV is available through video_thumbnail module")
        VIDEO_THUMBNAIL_AVAILABLE = True
        
        # Try to import the optimized version
        try:
            from utils import video_thumbnail_optimized
            OPTIMIZED_THUMBNAIL_AVAILABLE = True
            logger.info("Optimized video thumbnail module is available")
        except ImportError as e:
            logger.warning(f"Optimized video thumbnail module not available: {e}")
    
except ImportError as e:
    logger.warning(f"Failed to import video_thumbnail module: {e}")
except Exception as e:
    logger.error(f"Unexpected error importing video_thumbnail: {e}", exc_info=True)

# Import other modules
try:
    import rawpy
    import io
    import traceback
    import numpy as np
    logger.info("RawPy successfully imported. RAW thumbnails will be available.")
    RAWPY_AVAILABLE = True
except ImportError:
    logger.warning("RawPy not found. RAW thumbnails will not be available.")
    logger.info("Install with: pip install rawpy")
    RAWPY_AVAILABLE = False

# Global thumbnail cache (memory)
THUMBNAIL_CACHE = {}

# Disk-based cache settings
CACHE_DIR = os.path.join(os.path.expanduser('~'), '.imsdly', 'thumbnail_cache')
MAX_CACHE_SIZE_MB = 500  # Maximum cache size in MB
CACHE_INDEX_FILE = os.path.join(CACHE_DIR, 'cache_index.json')

# Create cache directory if it doesn't exist
os.makedirs(CACHE_DIR, exist_ok=True)

# Define a thumbnail cache to avoid regenerating thumbnails
class ThumbnailCache:
    """Cache for file thumbnails to avoid regenerating them"""
    
    def __init__(self):
        """Initialize the cache"""
        # Cache of pixmaps
        self.cache = {}
        # Set of keys currently being loaded
        self.loading = set()
        # Map of key -> callbacks
        self.callbacks = {}
        # Queue for worker thread
        self.queue = Queue()
        # Use multiple worker threads for better performance
        self.worker_threads = []
        
        # The number of worker threads to use (more threads = faster processing but higher CPU load)
        num_workers = 2
        
        # Start the worker threads
        for _ in range(num_workers):
            thread = Thread(target=self._worker, daemon=True)
            thread.start()
            self.worker_threads.append(thread)

    def get(self, file_path: str, size: QSize = QSize(64, 64)) -> Optional[QPixmap]:
        """Get a thumbnail from the cache or generate it"""
        key = f"{file_path}_{size.width()}x{size.height()}"
        if key in self.cache:
            return self.cache[key]
        return None

    def get_async(self, file_path: str, size: QSize, callback: Callable[[str, QPixmap], None]) -> None:
        """Get a thumbnail asynchronously, calling the callback when done"""
        key = f"{file_path}_{size.width()}x{size.height()}"
        
        # If already in cache, call the callback immediately
        if key in self.cache:
            callback(file_path, self.cache[key])
            return
            
        # If loading, add to callback list
        if key in self.loading:
            if key not in self.callbacks:
                self.callbacks[key] = []
            self.callbacks[key].append(callback)
            return
            
        # Add to loading set and callback list
        self.loading.add(key)
        if key not in self.callbacks:
            self.callbacks[key] = []
        self.callbacks[key].append(callback)
        
        # Add to queue for processing
        self.queue.put((file_path, size, key))

    def _worker(self) -> None:
        """Worker thread to generate thumbnails in the background"""
        while True:
            try:
                # Process up to 5 files at once from the queue to improve batch efficiency
                files_to_process = []
                for _ in range(5):  # Process up to 5 items in one batch
                    try:
                        # Get with a short timeout to avoid blocking indefinitely
                        file_path, size, key = self.queue.get(timeout=0.1)
                        files_to_process.append((file_path, size, key))
                    except Empty:
                        break
                
                if not files_to_process:
                    # If no files to process, sleep briefly
                    time.sleep(0.2)
                    continue
                    
                # Process the batch of files
                for file_path, size, key in files_to_process:
                    try:
                        # Skip if file doesn't exist
                        if not os.path.exists(file_path):
                            logging.warning(f"File does not exist: {file_path}")
                            self.loading.discard(key)
                            continue
                        
                        # Check if already in cache (another worker might have processed it)
                        if key in self.cache:
                            if key in self.callbacks:
                                for callback in self.callbacks[key]:
                                    try:
                                        callback(file_path, self.cache[key])
                                    except Exception as e:
                                        logging.error(f"Error in thumbnail callback: {e}")
                                del self.callbacks[key]
                            self.loading.discard(key)
                            continue
                        
                        file_type = self._get_file_type(file_path)
                        
                        # Prioritize video files for more efficient processing
                        if file_type == 'video':
                            logging.info(f"Generating thumbnail for video file: {file_path}")
                        
                        pixmap = self._generate_thumbnail(file_path, size, file_type)
                        
                        if pixmap:
                            self.cache[key] = pixmap
                            
                            # Call all callbacks
                            if key in self.callbacks:
                                for callback in self.callbacks[key]:
                                    try:
                                        callback(file_path, pixmap)
                                    except Exception as e:
                                        logging.error(f"Error in thumbnail callback: {e}")
                                del self.callbacks[key]
                                
                        self.loading.discard(key)
                    except Exception as e:
                        logging.error(f"Error generating thumbnail for {file_path}: {e}")
                        self.loading.discard(key)
            except Exception as e:
                logging.error(f"Error in thumbnail worker: {e}")

    def put(self, file_path: str, pixmap: QPixmap, size: QSize = QSize(64, 64)) -> None:
        """Put a thumbnail in the cache"""
        key = f"{file_path}_{size.width()}x{size.height()}"
        self.cache[key] = pixmap

    def clear(self) -> None:
        """Clear the cache"""
        self.cache.clear()
        self.loading.clear()
        self.callbacks.clear()
        # Clear the queue
        while not self.queue.empty():
            try:
                self.queue.get_nowait()
            except Empty:
                break

    def _get_file_type(self, file_path: str) -> str:
        """Get the file type based on extension"""
        ext = os.path.splitext(file_path)[1].lower()
        
        # Image files
        if ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp', '.svg']:
            return 'image'
        
        # RAW image files
        if ext in ['.raw', '.cr2', '.nef', '.arf', '.sr2', '.crw', '.dng', '.orf', '.pef', '.arw']:
            return 'raw'
            
        # Video files
        if ext in ['.mp4', '.mov', '.avi', '.mkv', '.mpg', '.mpeg', '.3gp', '.wmv', '.flv', '.webm']:
            return 'video'
            
        # Document files
        if ext in ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.txt', '.rtf']:
            return 'document'
            
        return 'other'

    def _generate_thumbnail(self, file_path: str, size: QSize, file_type: str) -> Optional[QPixmap]:
        """Generate a thumbnail for a file"""
        try:
            if file_type == 'image':
                return self._generate_image_thumbnail(file_path, size)
            elif file_type == 'raw' and RAWPY_AVAILABLE:
                return self._generate_raw_thumbnail(file_path, size)
            elif file_type == 'video':
                return self._generate_video_thumbnail(file_path, size)
            elif file_type == 'document':
                return self._generate_document_thumbnail(file_path, size)
            else:
                return self._generate_generic_thumbnail(file_path, size)
        except Exception as e:
            logging.error(f"Error generating thumbnail for {file_path}: {e}")
            return None

    def _generate_image_thumbnail(self, file_path: str, size: QSize) -> Optional[QPixmap]:
        """Generate a thumbnail for an image file"""
        try:
            pixmap = QPixmap(file_path)
            if pixmap.isNull():
                return self._generate_generic_thumbnail(file_path, size)
            return pixmap.scaled(size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        except Exception as e:
            logging.error(f"Error generating image thumbnail: {e}")
            return self._generate_generic_thumbnail(file_path, size)

    def _generate_raw_thumbnail(self, file_path: str, size: QSize) -> Optional[QPixmap]:
        """Generate a thumbnail for a RAW image file using rawpy"""
        try:
            if not RAWPY_AVAILABLE:
                return self._generate_generic_thumbnail(file_path, size)
                
            with rawpy.imread(file_path) as raw:
                try:
                    # Try to get embedded thumbnail first
                    thumb = raw.extract_thumb()
                    if thumb.format == rawpy.ThumbFormat.JPEG:
                        pixmap = QPixmap()
                        pixmap.loadFromData(thumb.data)
                        return pixmap.scaled(size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                except:
                    pass
                    
                # If no embedded thumbnail, process the raw file
                rgb = raw.postprocess(use_camera_wb=True, half_size=True, no_auto_bright=True)
                height, width, channels = rgb.shape
                
                # Create QImage from numpy array
                from PyQt6.QtGui import QImage
                import numpy as np
                
                # Convert to RGB888 format for QImage
                rgb_image = QImage(rgb.data, width, height, width * 3, QImage.Format.Format_RGB888)
                pixmap = QPixmap.fromImage(rgb_image)
                return pixmap.scaled(size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        except Exception as e:
            logging.error(f"Error generating RAW thumbnail: {e}")
            return self._generate_generic_thumbnail(file_path, size)

    def _generate_video_thumbnail(self, file_path: str, size: QSize) -> QPixmap:
        """Generate a thumbnail for a video file"""
        # Use the optimized module if available (fast_frame_grab method for best quality/speed balance)
        if VIDEO_THUMBNAIL_AVAILABLE:
            logging.info(f"Attempting to generate video thumbnail for {file_path}")
            try:
                # First try the optimized module if available and configured
                if OPTIMIZED_THUMBNAIL_AVAILABLE and VIDEO_THUMBNAIL_CONFIG["use_optimized"]:
                    try:
                        method = VIDEO_THUMBNAIL_CONFIG["preferred_method"]
                        frame_number = VIDEO_THUMBNAIL_CONFIG["frame_number"]
                        logging.info(f"Using optimized thumbnail generator with {method} method (frame {frame_number})")
                        
                        # Different parameters based on method
                        kwargs = {}
                        if method == "fast_frame_grab":
                            kwargs["frame_number"] = frame_number
                        elif method not in ["fast_first_frame", "standard"]:
                            # For other methods, use frame number converted to time
                            # This is an approximation assuming 30fps
                            kwargs["frame_time"] = frame_number / 30.0
                        
                        pixmap, _ = video_thumbnail_optimized.generate_optimized_thumbnail(
                            file_path,
                            size,
                            method=method,
                            **kwargs
                        )
                        if pixmap and not pixmap.isNull():
                            logging.info(f"Successfully generated optimized video thumbnail for {file_path}")
                            return pixmap
                    except Exception as e:
                        logging.warning(f"Optimized thumbnail generation failed: {e}")
                        if not VIDEO_THUMBNAIL_CONFIG["fallback_to_standard"]:
                            raise
                        logging.warning("Falling back to standard method")
                
                # Fall back to standard method if optimized fails or is not available/configured
                logging.info(f"Using standard video thumbnail method with frame {VIDEO_THUMBNAIL_CONFIG['frame_number']}")
                # Standard method uses time, so convert frame number to time (assuming 30fps)
                approx_time = VIDEO_THUMBNAIL_CONFIG["frame_number"] / 30.0
                video_pixmap = video_thumbnail.generate_video_thumbnail(
                    file_path, 
                    size, 
                    frame_time=approx_time  # Convert frame number to approximate time
                )
                if video_pixmap and not video_pixmap.isNull():
                    logging.info(f"Successfully generated video thumbnail for {file_path}")
                    return video_pixmap
                else:
                    logging.warning(f"video_thumbnail.generate_video_thumbnail returned null/empty pixmap for {file_path}")
            except Exception as e:
                logging.error(f"Error using video_thumbnail module: {e}", exc_info=True)
        else:
            logging.warning("VIDEO_THUMBNAIL_AVAILABLE is False, using fallback")
                
        # Fall back to generic thumbnail if module not available or fails
        logging.info(f"Using fallback thumbnail for {file_path}")
        return self._generate_generic_thumbnail(file_path, size, is_video=True)

    def _generate_document_thumbnail(self, file_path: str, size: QSize) -> QPixmap:
        """Generate a thumbnail for a document file"""
        # Return a generic document icon
        return self._generate_generic_thumbnail(file_path, size, is_document=True)

    def _generate_generic_thumbnail(self, file_path: str, size: QSize, 
                                   is_video: bool = False, 
                                   is_document: bool = False) -> QPixmap:
        """Generate a generic thumbnail with icon for file"""
        pixmap = QPixmap(size)
        pixmap.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(pixmap)
        
        # File extension for overlay
        ext = os.path.splitext(file_path)[1].lower()
        if ext.startswith('.'):
            ext = ext[1:]
        
        # Background with rounded corners
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(QBrush(QColor("#303030")))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(0, 0, size.width(), size.height(), 4, 4)
        
        # Icon type based on file type
        icon_color = QColor("#4a9eff")  # Blue for most files
        icon_name = "📄"  # Default file icon
        
        if is_video:
            icon_color = QColor("#ff4a4a")  # Red for video
            icon_name = "🎬"
        elif is_document:
            icon_color = QColor("#4aff7f")  # Green for documents
            icon_name = "📝"
        elif ext in ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'tiff', 'webp', 'svg']:
            icon_color = QColor("#ff9e4a")  # Orange for images
            icon_name = "🖼️"
        elif ext in ['raw', 'cr2', 'nef', 'arf', 'sr2', 'crw', 'dng', 'orf', 'pef', 'arw']:
            icon_color = QColor("#ff9e4a")  # Orange for RAW images
            icon_name = "📸"
        
        # Draw icon
        font = QFont()
        font.setPointSize(size.height() // 2)
        painter.setFont(font)
        painter.setPen(icon_color)
        painter.drawText(QRect(0, 0, size.width(), size.height()), Qt.AlignmentFlag.AlignCenter, icon_name)
        
        # Draw overlay with file extension for non-standard files
        if ext and not is_video and not is_document and ext not in ['jpg', 'jpeg', 'png', 'gif', 'bmp']:
            # Bottom overlay rectangle
            painter.setBrush(QBrush(QColor(0, 0, 0, 180)))
            painter.setPen(Qt.PenStyle.NoPen)
            rect = QRect(0, size.height() - size.height() // 4, size.width(), size.height() // 4)
            painter.drawRect(rect)
            
            # File extension text
            painter.setPen(QPen(QColor(255, 255, 255)))
            font = QFont()
            font.setPointSize(size.height() // 6)
            painter.setFont(font)
            painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, ext.upper())
        
        painter.end()
        return pixmap

# Initialize the thumbnail cache
THUMBNAIL_MANAGER = ThumbnailCache()


class ThumbnailWorker(QRunnable):
    """Worker for generating thumbnails asynchronously."""
    
    def __init__(self, cache_key: str, file_path: str, file_info: Dict, 
                 thumb_width: int, thumb_height: int, callback: Callable = None):
        super().__init__()
        self.cache_key = cache_key
        self.file_path = file_path
        self.file_info = file_info
        self.thumb_width = thumb_width
        self.thumb_height = thumb_height
        self.signals = ThumbnailSignals()
        self.callback = callback
        
        # Connect the finished signal to the callback if provided
        if callback:
            self.signals.finished.connect(callback)
        
    @pyqtSlot()
    def run(self):
        """Main worker method that runs in a separate thread."""
        try:
            start_time = time.time()
            pixmap = self._generate_thumbnail()
            if pixmap:
                # Emit the signal with the result
                self.signals.finished.emit(self.cache_key, pixmap)
                logger.debug(f"Thumbnail generated for {self.file_path} in {time.time() - start_time:.2f}s")
        except Exception as e:
            logger.error(f"Error in thumbnail worker: {e}")
    
    def _generate_thumbnail(self) -> Optional[QPixmap]:
        """Generate thumbnail based on file type."""
        try:
            # Get file extension
            ext = os.path.splitext(self.file_path)[1].lower()
            file_type = self.file_info.get('type', '')
            
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
            
            # Handle RAW files
            if ext in raw_formats and RAWPY_AVAILABLE:
                return self._generate_raw_thumbnail()
            
            # Handle special formats
            if ext in special_formats:
                pixmap = QPixmap(self.file_path)
                if not pixmap.isNull():
                    # Scale it
                    return self._scale_and_center_pixmap(pixmap)
                else:
                    # Create format indicator
                    return self._create_format_indicator(ext, False)
            
            # Standard image formats
            if file_type == 'image':
                pixmap = QPixmap(self.file_path)
                if not pixmap.isNull():
                    return self._scale_and_center_pixmap(pixmap)
            
            # Video thumbnails - use the video_thumbnail module
            if file_type == 'video':
                # First check if the module is available
                if VIDEO_THUMBNAIL_AVAILABLE:
                    try:
                        # Use the optimized module if available and configured
                        thumbnail_size = QSize(self.thumb_width, self.thumb_height)
                        logger.info(f"ThumbnailWorker: Generating video thumbnail for {self.file_path}")
                        
                        if OPTIMIZED_THUMBNAIL_AVAILABLE and VIDEO_THUMBNAIL_CONFIG["use_optimized"]:
                            try:
                                logger.info(f"ThumbnailWorker: Using optimized thumbnail generator")
                                
                                method = VIDEO_THUMBNAIL_CONFIG["preferred_method"]
                                frame_number = VIDEO_THUMBNAIL_CONFIG["frame_number"]
                                
                                # Different parameters based on method
                                kwargs = {}
                                if method == "fast_frame_grab":
                                    kwargs["frame_number"] = frame_number
                                elif method not in ["fast_first_frame", "standard"]:
                                    # For other methods, use frame number converted to time
                                    # This is an approximation assuming 30fps
                                    kwargs["frame_time"] = frame_number / 30.0
                                
                                # Use the already imported module from the top-level import
                                video_pixmap, _ = video_thumbnail_optimized.generate_optimized_thumbnail(
                                    self.file_path,
                                    thumbnail_size,
                                    method=method,
                                    **kwargs
                                )
                                if video_pixmap and not video_pixmap.isNull():
                                    logger.info(f"ThumbnailWorker: Successfully generated optimized video thumbnail")
                                    return video_pixmap
                            except Exception as e:
                                logger.warning(f"ThumbnailWorker: Optimized method failed: {e}")
                                if not VIDEO_THUMBNAIL_CONFIG["fallback_to_standard"]:
                                    raise
                                logger.warning("ThumbnailWorker: Falling back to standard method")
                        
                        # Fall back to standard method
                        logger.info(f"ThumbnailWorker: Using standard video thumbnail method with frame {VIDEO_THUMBNAIL_CONFIG['frame_number']}")
                        # Standard method uses time, so convert frame number to time (assuming 30fps)
                        approx_time = VIDEO_THUMBNAIL_CONFIG["frame_number"] / 30.0
                        video_pixmap = video_thumbnail.generate_video_thumbnail(
                            self.file_path, 
                            thumbnail_size, 
                            frame_time=approx_time  # Convert frame number to approximate time
                        )
                        if video_pixmap and not video_pixmap.isNull():
                            logger.info(f"ThumbnailWorker: Successfully generated video thumbnail for {self.file_path}")
                            return video_pixmap
                        else:
                            logger.warning(f"ThumbnailWorker: Video thumbnail generation returned null/empty pixmap for {self.file_path}")
                    except Exception as e:
                        logger.error(f"ThumbnailWorker: Error using video_thumbnail module: {str(e)}", exc_info=True)
                else:
                    logger.warning("ThumbnailWorker: VIDEO_THUMBNAIL_AVAILABLE is False, using fallback")
                    
                # If video_thumbnail module failed or not available, use fallback
                logger.info(f"ThumbnailWorker: Using fallback thumbnail for {self.file_path}")
                return self._create_video_thumbnail()
            
            # Generic file thumbnail
            return self._create_generic_thumbnail()
            
        except Exception as e:
            logger.error(f"Error generating thumbnail: {e}")
            return None
    
    def _generate_raw_thumbnail(self) -> Optional[QPixmap]:
        """Generate thumbnail for RAW image files."""
        try:
            if not RAWPY_AVAILABLE:
                return self._create_format_indicator(
                    os.path.splitext(self.file_path)[1].lower(), True
                )
                
            with rawpy.imread(self.file_path) as raw:
                # First try embedded thumbnail
                try:
                    thumb_data = raw.extract_thumb()
                    if thumb_data and thumb_data.format == 'jpeg':
                        q_data = QByteArray(thumb_data.data)
                        pixmap = QPixmap()
                        pixmap.loadFromData(q_data)
                        
                        if not pixmap.isNull():
                            return self._scale_and_center_pixmap(pixmap)
                except (AttributeError, ValueError, RuntimeError):
                    pass
                
                # Fall back to processing the RAW data
                try:
                    rgb = raw.postprocess(use_camera_wb=True, half_size=True, output_bps=8)
                    
                    height, width, channels = rgb.shape
                    bytes_per_line = channels * width
                    
                    # Convert from RGB to BGR which is what QImage expects
                    rgb_swapped = rgb[...,::-1].copy()
                    
                    q_img = QImage(rgb_swapped.data, width, height, bytes_per_line, QImage.Format.Format_RGB888)
                    pixmap = QPixmap.fromImage(q_img)
                    
                    if not pixmap.isNull():
                        return self._scale_and_center_pixmap(pixmap)
                except Exception as e:
                    logger.error(f"Error processing RAW data: {e}")
                    
            # If all attempts failed, create format indicator
            return self._create_format_indicator(
                os.path.splitext(self.file_path)[1].lower(), True
            )
                
        except Exception as e:
            logger.error(f"Error generating RAW thumbnail: {e}")
            return self._create_format_indicator(
                os.path.splitext(self.file_path)[1].lower(), True
            )
    
    def _scale_and_center_pixmap(self, pixmap: QPixmap) -> QPixmap:
        """Scale pixmap to thumbnail size and center it."""
        # Scale the pixmap
        pixmap = pixmap.scaled(
            self.thumb_width, self.thumb_height, 
            Qt.AspectRatioMode.KeepAspectRatio, 
            Qt.TransformationMode.SmoothTransformation
        )
        
        # Center if needed
        if pixmap.width() < self.thumb_width or pixmap.height() < self.thumb_height:
            final_pixmap = QPixmap(self.thumb_width, self.thumb_height)
            final_pixmap.fill(QColor(25, 25, 25))
            
            painter = QPainter(final_pixmap)
            x = (self.thumb_width - pixmap.width()) // 2
            y = (self.thumb_height - pixmap.height()) // 2
            painter.drawPixmap(x, y, pixmap)
            painter.end()
            
            return final_pixmap
        
        return pixmap
    
    def _create_format_indicator(self, ext: str, is_raw: bool = False) -> QPixmap:
        """Create a formatted indicator for special file formats."""
        final_pixmap = QPixmap(self.thumb_width, self.thumb_height)
        final_pixmap.fill(QColor(25, 25, 25))
        
        painter = QPainter(final_pixmap)
        
        # Draw a styled box with format name
        painter.setPen(Qt.PenStyle.NoPen)
        if is_raw:
            # RAW format - blue gradient
            gradient = QLinearGradient(0, 0, self.thumb_width, self.thumb_height)
            gradient.setColorAt(0, QColor(41, 128, 185, 180))  # Darker blue
            gradient.setColorAt(1, QColor(52, 152, 219, 180))  # Lighter blue
            painter.setBrush(gradient)
        else:
            # Special format - purple gradient
            gradient = QLinearGradient(0, 0, self.thumb_width, self.thumb_height)
            gradient.setColorAt(0, QColor(142, 68, 173, 180))  # Darker purple
            gradient.setColorAt(1, QColor(155, 89, 182, 180))  # Lighter purple
            painter.setBrush(gradient)
        
        # Draw rounded rectangle
        painter.drawRoundedRect(0, 0, self.thumb_width, self.thumb_height, 8, 8)
        
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
    
    def _create_video_thumbnail(self) -> QPixmap:
        """Create a video thumbnail with play icon."""
        final_pixmap = QPixmap(self.thumb_width, self.thumb_height)
        final_pixmap.fill(QColor(25, 25, 25))
        
        painter = QPainter(final_pixmap)
        
        # Add a play triangle overlay
        play_triangle = QPolygon([
            QPoint(self.thumb_width // 2 - 25, self.thumb_height // 2 - 25),
            QPoint(self.thumb_width // 2 + 25, self.thumb_height // 2),
            QPoint(self.thumb_width // 2 - 25, self.thumb_height // 2 + 25)
        ])
        painter.setBrush(QColor(231, 76, 60, 180))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawPolygon(play_triangle)
        
        # Add video text
        painter.setPen(QColor(255, 255, 255))
        painter.setFont(QFont("Arial", 9, QFont.Weight.Bold))
        painter.drawText(final_pixmap.rect().adjusted(0, 30, 0, 0), 
                        Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignBottom, 
                        "VIDEO")
        
        painter.end()
        return final_pixmap
    
    def _create_generic_thumbnail(self) -> QPixmap:
        """Create a generic file thumbnail."""
        final_pixmap = QPixmap(self.thumb_width, self.thumb_height)
        final_pixmap.fill(QColor(25, 25, 25))
        
        painter = QPainter(final_pixmap)
        
        # Draw icon for generic file
        icon = QIcon.fromTheme("text-x-generic")
        if icon.isNull():
            # Draw simple file icon
            painter.setPen(QColor(149, 165, 166))
            painter.setBrush(QColor(149, 165, 166, 100))
            painter.drawRect(self.thumb_width // 2 - 15, self.thumb_height // 2 - 20, 30, 40)
        else:
            pixmap = icon.pixmap(48, 48)
            painter.drawPixmap(
                (self.thumb_width - pixmap.width()) // 2,
                (self.thumb_height - pixmap.height()) // 2,
                pixmap
            )
        
        # Add file extension text
        ext = os.path.splitext(self.file_path)[1].upper()
        if ext:
            painter.setPen(QColor(255, 255, 255))
            painter.setFont(QFont("Arial", 12, QFont.Weight.Bold))
            painter.drawText(final_pixmap.rect(), Qt.AlignmentFlag.AlignCenter, ext[1:])
        
        painter.end()
        return final_pixmap


class FileIconItem(QWidget):
    """Widget for displaying a file item in the icon view."""
    
    # Thumbnail dimensions
    THUMB_WIDTH = 120
    THUMB_HEIGHT = 90
    
    def __init__(self, file_info: Dict, parent=None):
        super().__init__(parent)
        self.file_info = file_info
        self.cache_key = self._get_cache_key(file_info['path'])
        self.thumbnail_loaded = False
        self.setup_ui()
        
    def setup_ui(self):
        """Set up the UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Create thumbnail container
        self.icon_label = QLabel()
        self.icon_label.setFixedSize(self.THUMB_WIDTH, self.THUMB_HEIGHT)
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.icon_label.setStyleSheet("""
            QLabel {
                background-color: #2a2a2a;
                border-radius: 4px;
            }
        """)
        
        # Set an immediate default icon based on file type
        self._set_default_icon()
        
        # Request the thumbnail asynchronously
        self._request_thumbnail()
        
        layout.addWidget(self.icon_label)
        
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
        self.setFixedSize(self.THUMB_WIDTH + 20, self.THUMB_HEIGHT + 40)
        
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
    
    def _set_default_icon(self):
        """Set a default icon based on file type."""
        # Create a background for the icon
        pixmap = QPixmap(self.THUMB_WIDTH, self.THUMB_HEIGHT)
        pixmap.fill(QColor(34, 34, 34))  # Slightly darker than the background
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        file_type = self.file_info['type']
        filename = self.file_info['name']
        ext = os.path.splitext(filename)[1].lower()
        
        # Draw a rounded rectangle background
        painter.setPen(QPen(QColor(50, 50, 50), 1))
        painter.setBrush(QBrush(QColor(40, 40, 40)))
        painter.drawRoundedRect(0, 0, self.THUMB_WIDTH, self.THUMB_HEIGHT, 6, 6)
        
        if file_type == 'image':
            # For image files
            gradient = QLinearGradient(0, 0, self.THUMB_WIDTH, self.THUMB_HEIGHT)
            gradient.setColorAt(0, QColor(30, 30, 40))
            gradient.setColorAt(1, QColor(34, 34, 44))
            painter.fillRect(2, 2, self.THUMB_WIDTH-4, self.THUMB_HEIGHT-4, gradient)
            
            # Create "image placeholder" icon with frame
            painter.setPen(QPen(QColor(80, 80, 100), 1))
            painter.setBrush(QBrush(QColor(52, 152, 219, 40)))  # Light blue with transparency
            
            # Convert floats to integers for the rect
            frame_x = int(self.THUMB_WIDTH/4)
            frame_y = int(self.THUMB_HEIGHT/4)
            frame_width = int(self.THUMB_WIDTH/2)
            frame_height = int(self.THUMB_HEIGHT/2)
            painter.drawRoundedRect(frame_x, frame_y, frame_width, frame_height, 4, 4)
            
            # Add mountain icon for photos
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(QColor(52, 152, 219)))
            
            # Draw a stylized mountain
            mountains = QPolygon([
                QPoint(int(self.THUMB_WIDTH/4), int(self.THUMB_HEIGHT*3/4)),
                QPoint(int(self.THUMB_WIDTH*3/8), int(self.THUMB_HEIGHT*2/4)),
                QPoint(int(self.THUMB_WIDTH/2), int(self.THUMB_HEIGHT*2.5/4)),
                QPoint(int(self.THUMB_WIDTH*5/8), int(self.THUMB_HEIGHT*1.5/4)),
                QPoint(int(self.THUMB_WIDTH*3/4), int(self.THUMB_HEIGHT*2/4)),
                QPoint(int(self.THUMB_WIDTH*3/4), int(self.THUMB_HEIGHT*3/4)),
            ])
            painter.drawPolygon(mountains)
            
            # Draw a sun
            sun_x = int(self.THUMB_WIDTH*5/8)
            sun_y = int(self.THUMB_HEIGHT/4)
            sun_size = int(self.THUMB_WIDTH/8)
            painter.setBrush(QBrush(QColor(241, 196, 15)))
            painter.drawEllipse(sun_x, sun_y, sun_size, sun_size)
            
            # Draw format badge for all image files
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(QColor(41, 128, 185, 220)))
            badge_x = self.THUMB_WIDTH - 40
            badge_y = 10  # At top to avoid overlap with filename
            painter.drawRoundedRect(badge_x, badge_y, 36, 16, 8, 8)
            
            painter.setPen(QColor(255, 255, 255))
            painter.setFont(QFont("Arial", 8, QFont.Weight.Bold))
            badge_rect = QRect(badge_x, badge_y, 36, 16)
            # Display extension without leading dot, uppercase
            ext_text = ext[1:].upper() if ext.startswith('.') else ext.upper()
            painter.drawText(badge_rect, Qt.AlignmentFlag.AlignCenter, ext_text)
            
        elif file_type == 'video':
            # For video files
            gradient = QLinearGradient(0, 0, self.THUMB_WIDTH, self.THUMB_HEIGHT)
            gradient.setColorAt(0, QColor(40, 30, 30))
            gradient.setColorAt(1, QColor(44, 34, 34))
            painter.fillRect(2, 2, self.THUMB_WIDTH-4, self.THUMB_HEIGHT-4, gradient)
            
            # Draw film strip borders
            painter.setPen(QPen(QColor(231, 76, 60), 1))
            for y in range(5, self.THUMB_HEIGHT-5, 12):
                # Draw film strip holes
                painter.drawRect(5, y, 8, 6)
                painter.drawRect(self.THUMB_WIDTH-13, y, 8, 6)
            
            # Draw play triangle
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(231, 76, 60, 200))
            
            # Define center coordinates and play button size
            center_x = self.THUMB_WIDTH // 2
            center_y = self.THUMB_HEIGHT // 2
            play_size = min(self.THUMB_WIDTH, self.THUMB_HEIGHT) // 3
            
            # Create play button triangle
            play_triangle = QPolygon([
                QPoint(self.THUMB_WIDTH // 2 - 15, self.THUMB_HEIGHT // 2 - 15),
                QPoint(self.THUMB_WIDTH // 2 + 15, self.THUMB_HEIGHT // 2),
                QPoint(self.THUMB_WIDTH // 2 - 15, self.THUMB_HEIGHT // 2 + 15)
            ])
            painter.drawPolygon(play_triangle)
            
            # Add circular border around play button
            painter.setPen(QPen(QColor(231, 76, 60, 150), 2))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawEllipse(center_x - play_size*2//3, center_y - play_size*2//3, 
                                play_size*4//3, play_size*4//3)
                                
            # Add film strip at bottom
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(QColor(231, 76, 60, 100)))
            strip_y = self.THUMB_HEIGHT - 15
            strip_height = 10
            painter.drawRect(5, strip_y, self.THUMB_WIDTH - 10, strip_height)
            
            # Add film holes
            painter.setBrush(QBrush(QColor(40, 30, 30)))
            hole_width = 6
            for x in range(10, self.THUMB_WIDTH - 10, 20):
                painter.drawRect(x, strip_y + 2, hole_width, strip_height - 4)
            
            # Move format badge to top-right corner instead of bottom to avoid overlap with filename
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(QColor(192, 57, 43, 220)))
            badge_x = self.THUMB_WIDTH - 40
            badge_y = 10  # Moved to top instead of bottom
            painter.drawRoundedRect(badge_x, badge_y, 36, 16, 8, 8)
            
            painter.setPen(QColor(255, 255, 255))
            painter.setFont(QFont("Arial", 8, QFont.Weight.Bold))
            badge_rect = QRect(badge_x, badge_y, 36, 16)
            
            # Show extension in badge
            ext_text = ext[1:].upper() if ext.startswith('.') else ext.upper()
            painter.drawText(badge_rect, Qt.AlignmentFlag.AlignCenter, ext_text)
        else:
            # For other files
            gradient = QLinearGradient(0, 0, self.THUMB_WIDTH, self.THUMB_HEIGHT)
            gradient.setColorAt(0, QColor(30, 35, 30))
            gradient.setColorAt(1, QColor(34, 39, 34))
            painter.fillRect(2, 2, self.THUMB_WIDTH-4, self.THUMB_HEIGHT-4, gradient)
            
            # Draw document icon
            painter.setPen(QPen(QColor(100, 100, 100), 1))
            painter.setBrush(QBrush(QColor(60, 60, 60)))
            
            # Document shape
            doc_x = self.THUMB_WIDTH//2 - 20
            doc_y = self.THUMB_HEIGHT//2 - 25
            doc_rect = QRect(doc_x, doc_y, 40, 50)
            painter.drawRect(doc_rect)
            
            # Document lines
            painter.setPen(QPen(QColor(120, 120, 120), 1))
            for y_offset in range(10, 40, 8):
                painter.drawLine(
                    doc_rect.left() + 5, 
                    doc_rect.top() + y_offset,
                    doc_rect.right() - 5, 
                    doc_rect.top() + y_offset
                )
            
            # Draw extension badge for all other files (not just those with extensions)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(QColor(80, 80, 80, 180)))
            badge_x = self.THUMB_WIDTH - 40
            badge_y = 10  # Move to top for consistency
            painter.drawRoundedRect(badge_x, badge_y, 32, 16, 4, 4)
            
            painter.setPen(QColor(255, 255, 255))
            painter.setFont(QFont("Arial", 8, QFont.Weight.Bold))
            badge_rect = QRect(badge_x, badge_y, 32, 16)
            ext_text = ext[1:].upper() if ext.startswith('.') else ext.upper()
            if not ext:
                ext_text = "FILE"
            painter.drawText(badge_rect, Qt.AlignmentFlag.AlignCenter, ext_text)
            
            # Draw secondary format indicator in the document
            if ext:
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(QBrush(QColor(80, 80, 80, 180)))
                badge_x = self.THUMB_WIDTH//2 - 16
                badge_y = self.THUMB_HEIGHT//2 + 12
                painter.drawRoundedRect(badge_x, badge_y, 32, 16, 4, 4)
                    
                painter.setPen(QColor(255, 255, 255))
                painter.setFont(QFont("Arial", 8, QFont.Weight.Bold))
                badge_rect = QRect(badge_x, badge_y, 32, 16)
                painter.drawText(badge_rect, Qt.AlignmentFlag.AlignCenter, ext_text)
        
        # Add subtle "loading" indicator at bottom
        painter.setPen(QPen(QColor(255, 255, 255, 100), 1))
        painter.setFont(QFont("Arial", 7))
        loading_rect = QRect(0, self.THUMB_HEIGHT - 15, self.THUMB_WIDTH, 10)
        painter.drawText(loading_rect, Qt.AlignmentFlag.AlignCenter, "Loading thumbnail...")
        
        painter.end()
        
        # Set the pixmap
        self.icon_label.setPixmap(pixmap)
    
    def _request_thumbnail(self):
        """Request thumbnail generation for the file."""
        # Avoid duplicate thumbnail requests
        if hasattr(self, '_thumbnail_requested') and self._thumbnail_requested:
            return
        
        self._thumbnail_requested = True
        
        # First check cache
        cache_key = self._get_cache_key(self.file_info['path'])
        pixmap = THUMBNAIL_MANAGER.get(self.file_info['path'], QSize(self.THUMB_WIDTH, self.THUMB_HEIGHT))
        
        if pixmap and not pixmap.isNull():
            # Cache hit - use it directly
            self.icon_label.setPixmap(pixmap)
            self.thumbnail_loaded = True
            return
        
        # For video files, add loading indicator right away
        if self.file_info['type'] == 'video':
            self._show_loading_indicator()
        
        # Request asynchronous thumbnail generation
        def update_thumbnail(key, pixmap):
            if pixmap and not pixmap.isNull():
                self.icon_label.setPixmap(pixmap)
                self.thumbnail_loaded = True
        
        THUMBNAIL_MANAGER.get_async(
            self.file_info['path'], 
            QSize(self.THUMB_WIDTH, self.THUMB_HEIGHT),
            update_thumbnail
        )
    
    def _show_loading_indicator(self):
        """Show a loading indicator if thumbnail is taking time to load."""
        if self.thumbnail_loaded:
            return
            
        # Only add loading indicator for video files
        if self.file_info['type'] != 'video':
            return
            
        # Create loading text overlay
        pixmap = self.icon_label.pixmap()
        if pixmap and not pixmap.isNull():
            painter = QPainter(pixmap)
            painter.setPen(QColor(255, 255, 255))
            painter.setFont(QFont("Arial", 8))
            painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, "Loading video...")
            painter.end()
            self.icon_label.setPixmap(pixmap)
            
            # Set a timer to retry in 4 seconds if still not loaded (increased from 2 seconds)
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(4000, self._handle_thumbnail_timeout)
            
    def _handle_thumbnail_timeout(self):
        """Handle case when thumbnail takes too long to generate."""
        # Don't do anything if thumbnail is already loaded
        if self.thumbnail_loaded:
            return
        
        # Only for video files
        if self.file_info['type'] != 'video':
            return
    
        # Check if there's a thumbnail in the cache before trying direct generation
        cache_key = self._get_cache_key(self.file_info['path'])
        existing_thumbnail = THUMBNAIL_MANAGER.get(self.file_info['path'], QSize(self.THUMB_WIDTH, self.THUMB_HEIGHT))
    
        # If thumbnail exists in cache now, use it
        if existing_thumbnail and not existing_thumbnail.isNull():
            self.icon_label.setPixmap(existing_thumbnail)
            self.thumbnail_loaded = True
            logging.info(f"Found cached thumbnail for {self.file_info['path']} after timeout")
            return
    
        logging.warning(f"Thumbnail generation timeout for video: {self.file_info['path']}")
    
        # Try using test_video_thumbnail to directly generate
        try:
            from PyQt6.QtCore import QTimer
            logging.info("Attempting direct thumbnail generation after timeout")
            # Schedule a direct thumbnail test - with a bit more delay to allow async to complete if it's almost done
            QTimer.singleShot(200, lambda: self._try_direct_thumbnail())
        except Exception as e:
            logging.error(f"Error setting up direct thumbnail generation: {e}")
    
    def _try_direct_thumbnail(self):
        """Try to directly generate a video thumbnail using the test function."""
        if self.thumbnail_loaded:
            return
            
        try:
            from utils import video_thumbnail
            
            logging.info(f"Direct thumbnail generation for {self.file_info['path']}")
            thumbnail_size = QSize(self.THUMB_WIDTH, self.THUMB_HEIGHT)
            
            # Use the frame number from configuration
            frame_number = VIDEO_THUMBNAIL_CONFIG["frame_number"]
            # Convert frame number to approximate time (assuming 30fps)
            approx_time = frame_number / 30.0
            
            # Check if already loaded before we start the expensive operation
            if self.thumbnail_loaded:
                logging.info(f"Thumbnail already loaded for {self.file_info['path']}, skipping direct generation")
                return
                
            pixmap = video_thumbnail.generate_video_thumbnail(
                self.file_info['path'],
                thumbnail_size,
                frame_time=approx_time  # Use the same frame as the optimized method
            )
            
            # Check again if it's already loaded (async worker might have completed)
            if self.thumbnail_loaded:
                logging.info(f"Thumbnail already loaded for {self.file_info['path']} while direct generation was running")
                return
                
            if pixmap and not pixmap.isNull():
                self.icon_label.setPixmap(pixmap)
                self.thumbnail_loaded = True
                logging.info(f"Direct thumbnail generation successful for {self.file_info['path']}")
            else:
                logging.error(f"Direct thumbnail generation failed for {self.file_info['path']}")
        except Exception as e:
            logging.error(f"Error in direct thumbnail generation: {e}")
            # If all else fails, show a better fallback
            self._create_better_fallback()
    
    def _get_cache_key(self, file_path: str) -> str:
        """Generate a unique cache key for a file based on path and modification time."""
        try:
            # Get file modification time to ensure cache is invalidated when file changes
            mod_time = os.path.getmtime(file_path)
            key_string = f"{file_path}_{mod_time}"
            return hashlib.md5(key_string.encode()).hexdigest()
        except Exception:
            # If there's any error, just use the file path
            return hashlib.md5(file_path.encode()).hexdigest()
    
    def _create_better_fallback(self):
        """Create an improved fallback thumbnail for video files when all else fails."""
        try:
            # Create an attractive fallback with video format badge and play button
            pixmap = QPixmap(self.THUMB_WIDTH, self.THUMB_HEIGHT)
            pixmap.fill(QColor(40, 40, 40))
            
            painter = QPainter(pixmap)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            
            # Get file extension 
            filename = self.file_info['name']
            ext = os.path.splitext(filename)[1].lower()
            
            # Background gradient
            gradient = QLinearGradient(0, 0, self.THUMB_WIDTH, self.THUMB_HEIGHT)
            gradient.setColorAt(0, QColor(40, 30, 30))
            gradient.setColorAt(1, QColor(50, 40, 40))
            painter.fillRect(0, 0, self.THUMB_WIDTH, self.THUMB_HEIGHT, gradient)
            
            # Create play button
            play_size = min(self.THUMB_WIDTH, self.THUMB_HEIGHT) // 3
            center_x = self.THUMB_WIDTH // 2
            center_y = self.THUMB_HEIGHT // 2
            
            # Semitransparent dark circle
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(QColor(0, 0, 0, 150)))
            painter.drawEllipse(center_x - play_size//2, center_y - play_size//2, 
                              play_size, play_size)
            
            # Play triangle
            painter.setBrush(QBrush(QColor(231, 76, 60)))
            triangle = QPolygon([
                QPoint(center_x - play_size//4, center_y - play_size//3),
                QPoint(center_x + play_size//3, center_y),
                QPoint(center_x - play_size//4, center_y + play_size//3)
            ])
            painter.drawPolygon(triangle)
            
            # Add video text at the bottom
            painter.setPen(QColor(255, 255, 255))
            painter.setFont(QFont("Arial", 8, QFont.Weight.Bold))
            text_rect = QRect(0, self.THUMB_HEIGHT - 20, self.THUMB_WIDTH, 20)
            painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, "VIDEO PREVIEW")
            
            # Add format badge in top-right
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(QColor(231, 76, 60, 200)))
            badge_width = 36
            badge_height = 18
            badge_x = self.THUMB_WIDTH - badge_width - 5
            badge_y = 5
            painter.drawRoundedRect(badge_x, badge_y, badge_width, badge_height, 4, 4)
            
            painter.setPen(QColor(255, 255, 255))
            painter.setFont(QFont("Arial", 8, QFont.Weight.Bold))
            badge_rect = QRect(badge_x, badge_y, badge_width, badge_height)
            
            # Show extension in badge
            ext_text = ext[1:].upper() if ext.startswith('.') else ext.upper()
            painter.drawText(badge_rect, Qt.AlignmentFlag.AlignCenter, ext_text)
            
            painter.end()
            
            # Set the pixmap
            self.icon_label.setPixmap(pixmap)
            
        except Exception as e:
            logging.error(f"Error creating better fallback: {e}")
            # If all else fails, do nothing - keep the default icon


class FileListItem(QWidget):
    """Widget for displaying a file item in the list view."""
    
    def __init__(self, file_info: Dict, parent=None):
        super().__init__(parent)
        self.file_info = file_info
        self.cache_key = self._get_cache_key(file_info['path'])
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
        
    def _get_cache_key(self, file_path: str) -> str:
        """Generate a unique cache key for a file based on path and modification time."""
        try:
            # Get file modification time to ensure cache is invalidated when file changes
            mod_time = os.path.getmtime(file_path)
            key_string = f"{file_path}_{mod_time}"
            return hashlib.md5(key_string.encode()).hexdigest()
        except Exception:
            # If there's any error, just use the file path
            return hashlib.md5(file_path.encode()).hexdigest()


class FileIconsItem(QWidget):
    """Widget for displaying a file item in the icons view (without thumbnails)."""
    
    # Icon dimensions
    ICON_WIDTH = 120
    ICON_HEIGHT = 90
    
    def __init__(self, file_info: Dict, parent=None):
        super().__init__(parent)
        self.file_info = file_info
        self.setup_ui()
        
    def setup_ui(self):
        """Set up the UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Create icon container
        self.icon_label = QLabel()
        self.icon_label.setFixedSize(self.ICON_WIDTH, self.ICON_HEIGHT)
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.icon_label.setStyleSheet("""
            QLabel {
                background-color: #2a2a2a;
                border-radius: 4px;
            }
        """)
        
        # Set icon based on file type
        self._set_icon()
        
        layout.addWidget(self.icon_label)
        
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
        self.setFixedSize(self.ICON_WIDTH + 20, self.ICON_HEIGHT + 40)
        
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
    
    def _set_icon(self):
        """Set an icon based on file type."""
        # Create a background for the icon
        pixmap = QPixmap(self.ICON_WIDTH, self.ICON_HEIGHT)
        pixmap.fill(QColor(34, 34, 34))  # Slightly darker than the background
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        file_type = self.file_info['type']
        filename = self.file_info['name']
        ext = os.path.splitext(filename)[1].lower()
        
        # Draw a rounded rectangle background
        painter.setPen(QPen(QColor(50, 50, 50), 1))
        painter.setBrush(QBrush(QColor(40, 40, 40)))
        painter.drawRoundedRect(0, 0, self.ICON_WIDTH, self.ICON_HEIGHT, 6, 6)
        
        if file_type == 'image':
            # For image files
            gradient = QLinearGradient(0, 0, self.ICON_WIDTH, self.ICON_HEIGHT)
            gradient.setColorAt(0, QColor(30, 30, 40))
            gradient.setColorAt(1, QColor(34, 34, 44))
            painter.fillRect(2, 2, self.ICON_WIDTH-4, self.ICON_HEIGHT-4, gradient)
            
            # Create "image placeholder" icon with frame
            painter.setPen(QPen(QColor(80, 80, 100), 1))
            painter.setBrush(QBrush(QColor(52, 152, 219, 40)))  # Light blue with transparency
            
            # Convert floats to integers for the rect
            frame_x = int(self.ICON_WIDTH/4)
            frame_y = int(self.ICON_HEIGHT/4)
            frame_width = int(self.ICON_WIDTH/2)
            frame_height = int(self.ICON_HEIGHT/2)
            painter.drawRoundedRect(frame_x, frame_y, frame_width, frame_height, 4, 4)
            
            # Add mountain icon for photos
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(QColor(52, 152, 219)))
            
            # Draw a stylized mountain
            mountains = QPolygon([
                QPoint(int(self.ICON_WIDTH/4), int(self.ICON_HEIGHT*3/4)),
                QPoint(int(self.ICON_WIDTH*3/8), int(self.ICON_HEIGHT*2/4)),
                QPoint(int(self.ICON_WIDTH/2), int(self.ICON_HEIGHT*2.5/4)),
                QPoint(int(self.ICON_WIDTH*5/8), int(self.ICON_HEIGHT*1.5/4)),
                QPoint(int(self.ICON_WIDTH*3/4), int(self.ICON_HEIGHT*2/4)),
                QPoint(int(self.ICON_WIDTH*3/4), int(self.ICON_HEIGHT*3/4)),
            ])
            painter.drawPolygon(mountains)
            
            # Draw a sun
            sun_x = int(self.ICON_WIDTH*5/8)
            sun_y = int(self.ICON_HEIGHT/4)
            sun_size = int(self.ICON_WIDTH/8)
            painter.setBrush(QBrush(QColor(241, 196, 15)))
            painter.drawEllipse(sun_x, sun_y, sun_size, sun_size)
            
            # Draw format badge for all image files
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(QColor(41, 128, 185, 220)))
            badge_x = self.ICON_WIDTH - 40
            badge_y = 10  # At top to avoid overlap with filename
            painter.drawRoundedRect(badge_x, badge_y, 36, 16, 8, 8)
            
            painter.setPen(QColor(255, 255, 255))
            painter.setFont(QFont("Arial", 8, QFont.Weight.Bold))
            badge_rect = QRect(badge_x, badge_y, 36, 16)
            # Display extension without leading dot, uppercase
            ext_text = ext[1:].upper() if ext.startswith('.') else ext.upper()
            painter.drawText(badge_rect, Qt.AlignmentFlag.AlignCenter, ext_text)
            
        elif file_type == 'video':
            # For video files
            gradient = QLinearGradient(0, 0, self.ICON_WIDTH, self.ICON_HEIGHT)
            gradient.setColorAt(0, QColor(40, 30, 30))
            gradient.setColorAt(1, QColor(44, 34, 34))
            painter.fillRect(2, 2, self.ICON_WIDTH-4, self.ICON_HEIGHT-4, gradient)
            
            # Create "video placeholder" icon
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(QColor(231, 76, 60, 200)))  # Red with transparency
            
            # Draw play button
            center_x = self.ICON_WIDTH // 2
            center_y = self.ICON_HEIGHT // 2
            play_size = min(self.ICON_WIDTH, self.ICON_HEIGHT) // 3
            
            # Triangle play icon
            play_triangle = QPolygon([
                QPoint(center_x - play_size//2, center_y - play_size//2),
                QPoint(center_x + play_size//2, center_y),
                QPoint(center_x - play_size//2, center_y + play_size//2)
            ])
            painter.drawPolygon(play_triangle)
            
            # Add circular border around play button
            painter.setPen(QPen(QColor(231, 76, 60, 150), 2))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawEllipse(center_x - play_size*2//3, center_y - play_size*2//3, 
                                play_size*4//3, play_size*4//3)
                                
            # Add film strip at bottom
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(QColor(231, 76, 60, 100)))
            strip_y = self.ICON_HEIGHT - 15
            strip_height = 10
            painter.drawRect(5, strip_y, self.ICON_WIDTH - 10, strip_height)
            
            # Add film holes
            painter.setBrush(QBrush(QColor(40, 30, 30)))
            hole_width = 6
            for x in range(10, self.ICON_WIDTH - 10, 20):
                painter.drawRect(x, strip_y + 2, hole_width, strip_height - 4)
            
            # Move format badge to top-right corner instead of bottom to avoid overlap with filename
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(QColor(192, 57, 43, 220)))
            badge_x = self.ICON_WIDTH - 40
            badge_y = 10  # Moved to top instead of bottom
            painter.drawRoundedRect(badge_x, badge_y, 36, 16, 8, 8)
            
            painter.setPen(QColor(255, 255, 255))
            painter.setFont(QFont("Arial", 8, QFont.Weight.Bold))
            badge_rect = QRect(badge_x, badge_y, 36, 16)
            
            # Show extension in badge
            ext_text = ext[1:].upper() if ext.startswith('.') else ext.upper()
            painter.drawText(badge_rect, Qt.AlignmentFlag.AlignCenter, ext_text)
        else:
            # For other files
            gradient = QLinearGradient(0, 0, self.ICON_WIDTH, self.ICON_HEIGHT)
            gradient.setColorAt(0, QColor(30, 35, 30))
            gradient.setColorAt(1, QColor(34, 39, 34))
            painter.fillRect(2, 2, self.ICON_WIDTH-4, self.ICON_HEIGHT-4, gradient)
            
            # Draw document icon
            painter.setPen(QPen(QColor(100, 100, 100), 1))
            painter.setBrush(QBrush(QColor(60, 60, 60)))
            
            # Document shape
            doc_x = self.ICON_WIDTH//2 - 20
            doc_y = self.ICON_HEIGHT//2 - 25
            doc_rect = QRect(doc_x, doc_y, 40, 50)
            painter.drawRect(doc_rect)
            
            # Document lines
            painter.setPen(QPen(QColor(120, 120, 120), 1))
            for y_offset in range(10, 40, 8):
                painter.drawLine(
                    doc_rect.left() + 5, 
                    doc_rect.top() + y_offset,
                    doc_rect.right() - 5, 
                    doc_rect.top() + y_offset
                )
            
            # Draw extension badge for all other files (not just those with extensions)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(QColor(80, 80, 80, 180)))
            badge_x = self.ICON_WIDTH - 40
            badge_y = 10  # Move to top for consistency
            painter.drawRoundedRect(badge_x, badge_y, 32, 16, 4, 4)
            
            painter.setPen(QColor(255, 255, 255))
            painter.setFont(QFont("Arial", 8, QFont.Weight.Bold))
            badge_rect = QRect(badge_x, badge_y, 32, 16)
            ext_text = ext[1:].upper() if ext.startswith('.') else ext.upper()
            if not ext:
                ext_text = "FILE"
            painter.drawText(badge_rect, Qt.AlignmentFlag.AlignCenter, ext_text)
            
            # Draw secondary format indicator in the document
            if ext:
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(QBrush(QColor(80, 80, 80, 180)))
                badge_x = self.ICON_WIDTH//2 - 16
                badge_y = self.ICON_HEIGHT//2 + 12
                painter.drawRoundedRect(badge_x, badge_y, 32, 16, 4, 4)
                    
                painter.setPen(QColor(255, 255, 255))
                painter.setFont(QFont("Arial", 8, QFont.Weight.Bold))
                badge_rect = QRect(badge_x, badge_y, 32, 16)
                painter.drawText(badge_rect, Qt.AlignmentFlag.AlignCenter, ext_text)
                
        painter.end()
        
        # Set the pixmap
        self.icon_label.setPixmap(pixmap)


class FileListWidget(QWidget):
    """Widget for displaying a list of files."""
    
    file_selected = pyqtSignal(dict)
    files_selected = pyqtSignal(list)  # New signal for multi-selection
    
    # View modes
    LIST_VIEW = 0
    ICONS_VIEW = 1
    THUMBNAIL_VIEW = 2
    
    # Thumbnail size for icon view
    ICON_SIZE = QSize(120, 90)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.file_model = None
        self.current_file_types = None
        self.view_mode = self.LIST_VIEW  # Default to list view
        self.is_loading = False  # Flag to track if thumbnail loading is in progress
        self.pending_thumbnails = 0  # Counter for pending thumbnail generations
        self.loaded_thumbnails = 0   # Counter for loaded thumbnails
        self.visible_items = []      # List to track currently visible items
        self.scroll_timer = QTimer()  # Timer to delay thumbnail loading during scrolling
        self.scroll_timer.setSingleShot(True)
        self.scroll_timer.timeout.connect(self._load_visible_thumbnails)
        
    def setup_ui(self):
        """Set up the UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Top bar with status and controls
        top_bar = QHBoxLayout()
        top_bar.setContentsMargins(8, 8, 8, 0)
        
        # Status label (No files, file count, etc.)
        self.status_label = QLabel("No files found")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.status_label.setStyleSheet("color: white; padding: 5px;")
        top_bar.addWidget(self.status_label)
        
        # Add stretch to push loading status to the right
        top_bar.addStretch()
        
        # Loading progress indicator
        self.loading_label = QLabel()
        self.loading_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.loading_label.setStyleSheet("color: #1e1e1e; font-size: 10px;")
        self.loading_label.hide()  # Hidden by default
        top_bar.addWidget(self.loading_label)
        
        layout.addLayout(top_bar)
        
        # File list widget with multi-selection support
        self.list_widget = QListWidget()
        self.list_widget.setFrameShape(self.list_widget.Shape.NoFrame)
        self.list_widget.setVerticalScrollMode(QListWidget.ScrollMode.ScrollPerPixel)
        self.list_widget.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)  # Enable multi-selection
        self.list_widget.itemClicked.connect(self._handle_item_clicked)
        self.list_widget.itemSelectionChanged.connect(self._handle_selection_changed)  # Handle selection changes
        
        # Connect scroll events to prioritize visible thumbnails
        self.list_widget.verticalScrollBar().valueChanged.connect(self._handle_scroll)
        
        layout.addWidget(self.list_widget)
        
        # Selection indicator (shows count of selected items)
        self.selection_indicator = QLabel()
        self.selection_indicator.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.selection_indicator.setStyleSheet("color: #aaa; background-color: #2a2a2a; padding: 5px; border-top: 1px solid #333;")
        self.selection_indicator.hide()  # Hidden by default
        layout.addWidget(self.selection_indicator)
        
        # Install event filter for keyboard shortcuts
        self.list_widget.installEventFilter(self)
        
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
    
    def eventFilter(self, obj, event):
        """Handle keyboard shortcuts."""
        if obj == self.list_widget and event.type() == QEvent.Type.KeyPress:
            # Handle Ctrl+A (select all)
            if event.key() == Qt.Key.Key_A and event.modifiers() == Qt.KeyboardModifier.ControlModifier:
                self.list_widget.selectAll()
                return True
        return super().eventFilter(obj, event)
    
    def _handle_selection_changed(self):
        """Handle selection changes."""
        selected_items = self.list_widget.selectedItems()
        selected_count = len(selected_items)
        
        # Update selection indicator
        if selected_count > 0:
            self.selection_indicator.setText(f"{selected_count} item{'s' if selected_count > 1 else ''} selected")
            self.selection_indicator.show()
        else:
            self.selection_indicator.hide()
        
        # Process single selection for backward compatibility
        if selected_count == 1:
            widget = self.list_widget.itemWidget(selected_items[0])
            if widget and hasattr(widget, 'file_info'):
                self.file_selected.emit(widget.file_info)
        
        # Collect selected file info for multi-select signal
        selected_files = []
        for item in selected_items:
            widget = self.list_widget.itemWidget(item)
            if widget and hasattr(widget, 'file_info'):
                selected_files.append(widget.file_info)
        
        # Emit the multi-select signal
        self.files_selected.emit(selected_files)
    
    def _handle_scroll(self):
        """Handle scroll events to prioritize visible thumbnails."""
        # Reset the timer to prevent multiple calls during continuous scrolling
        self.scroll_timer.stop()
        self.scroll_timer.start(150)  # 150ms delay
        
    def _load_visible_thumbnails(self):
        """Prioritize loading thumbnails for currently visible items."""
        if self.view_mode != self.THUMBNAIL_VIEW:
            return
            
        # Get visible items
        visible_rect = self.list_widget.viewport().rect()
        self.visible_items = []
        pending_items = []
        
        # First pass: find all visible items
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            item_rect = self.list_widget.visualItemRect(item)
            
            # Check if item is visible
            if visible_rect.intersects(item_rect):
                widget = self.list_widget.itemWidget(item)
                if widget and isinstance(widget, FileIconItem) and not widget.thumbnail_loaded:
                    self.visible_items.append(widget)
                    pending_items.append((widget, item_rect))
        
        # Sort items by distance from center of viewport for better user experience
        center_y = visible_rect.center().y()
        pending_items.sort(key=lambda x: abs(x[1].center().y() - center_y))
        
        # Second pass: request thumbnails in batches with a slight delay between batches
        # to keep the UI responsive
        batch_size = 5  # Process 5 items at a time
        for batch_index, batch in enumerate(
            [pending_items[i:i+batch_size] for i in range(0, len(pending_items), batch_size)]
        ):
            # For the first batch, load immediately
            delay = 0 if batch_index == 0 else batch_index * 50  # 50ms delay between batches
            
            # Use a lambda that captures the current batch
            def load_batch(items_to_load=batch):
                for widget, _ in items_to_load:
                    if not widget.thumbnail_loaded:
                        # Request thumbnail with high priority
                        THUMBNAIL_MANAGER.get_async(
                            widget.file_info['path'],
                            QSize(widget.THUMB_WIDTH, widget.THUMB_HEIGHT),
                            lambda key, pixmap, w=widget: self._handle_thumbnail_loaded(key, pixmap, w)
                        )
            
            # Schedule this batch
            QTimer.singleShot(delay, load_batch)
            
        # If there are no visible items needing thumbnails, check the next screen worth of items
        if not self.visible_items:
            # Find the first item below the viewport and request its thumbnail
            found_below = False
            for i in range(self.list_widget.count()):
                item = self.list_widget.item(i)
                item_rect = self.list_widget.visualItemRect(item)
                
                # Check if item is below the visible area
                if item_rect.top() > visible_rect.bottom():
                    widget = self.list_widget.itemWidget(item)
                    if widget and isinstance(widget, FileIconItem) and not widget.thumbnail_loaded:
                        # Request this thumbnail to prepare for scrolling down
                        THUMBNAIL_MANAGER.get_async(
                            widget.file_info['path'],
                            QSize(widget.THUMB_WIDTH, widget.THUMB_HEIGHT),
                            lambda key, pixmap, w=widget: self._handle_thumbnail_loaded(key, pixmap, w)
                        )
                        found_below = True
                        break
            
            # If we didn't find any below, check for ones above (for scrolling up)
            if not found_below:
                for i in range(self.list_widget.count()-1, -1, -1):
                    item = self.list_widget.item(i)
                    item_rect = self.list_widget.visualItemRect(item)
                    
                    # Check if item is above the visible area
                    if item_rect.bottom() < visible_rect.top():
                        widget = self.list_widget.itemWidget(item)
                        if widget and isinstance(widget, FileIconItem) and not widget.thumbnail_loaded:
                            # Request this thumbnail to prepare for scrolling up
                            THUMBNAIL_MANAGER.get_async(
                                widget.file_info['path'],
                                QSize(widget.THUMB_WIDTH, widget.THUMB_HEIGHT),
                                lambda key, pixmap, w=widget: self._handle_thumbnail_loaded(key, pixmap, w)
                            )
                            break
    
    def _handle_thumbnail_loaded(self, key, pixmap, widget):
        """Handle when a thumbnail is loaded."""
        if widget.thumbnail_loaded:
            return
            
        # Update the widget
        widget.icon_label.setPixmap(pixmap)
        widget.thumbnail_loaded = True
        
        # Update loading progress
        self._handle_thumbnail_status_changed(key, pixmap)
    
    def _handle_thumbnail_status_changed(self, key, pixmap):
        """Track thumbnail loading status."""
        self.loaded_thumbnails += 1
        
        # Update loading status
        if self.pending_thumbnails > 0:
            progress = (self.loaded_thumbnails / self.pending_thumbnails) * 100
            self.loading_label.setText(f"Loading thumbnails... {int(progress)}% ({self.loaded_thumbnails}/{self.pending_thumbnails})")
            
            # Hide when complete
            if self.loaded_thumbnails >= self.pending_thumbnails:
                self.loading_label.setText("All thumbnails loaded")
                # Hide after a brief delay
                QTimer.singleShot(2000, self.loading_label.hide)
                self.is_loading = False

    def set_view_mode(self, mode: int):
        """Set the view mode.
        
        Args:
            mode: The view mode (LIST_VIEW, ICONS_VIEW, or THUMBNAIL_VIEW)
        """
        if mode not in [self.LIST_VIEW, self.ICONS_VIEW, self.THUMBNAIL_VIEW]:
            return
            
        # Store current view mode for comparison
        old_mode = self.view_mode
        self.view_mode = mode
        
        # If switching to thumbnail view, show a brief loading message
        if mode == self.THUMBNAIL_VIEW and old_mode != self.THUMBNAIL_VIEW:
            self.loading_label.setText("Switching to thumbnail view...")
            self.loading_label.show()
            
        # Force immediate processing of events to update UI
        QApplication.processEvents()
        
        # Update the list widget view mode
        if mode == self.LIST_VIEW:
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
        else:  # ICONS_VIEW or THUMBNAIL_VIEW
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
        
        # Force immediate processing of events to update styling
        QApplication.processEvents()
            
        # Refresh the view if we have a model
        if self.file_model:
            # If we've already populated the view, clear only when switching modes
            # to avoid flickering when toggling between the same mode
            if old_mode != mode:
                self.update_view()
            
        # Load visible thumbnails if in thumbnail view - do this immediately but with a low delay
        if mode == self.THUMBNAIL_VIEW:
            QTimer.singleShot(50, self._load_visible_thumbnails)
    
    def clear_thumbnail_cache(self):
        """Clear the thumbnail cache."""
        THUMBNAIL_MANAGER.clear()
        logger.info("Thumbnail cache cleared")
        
        # Refresh view to regenerate thumbnails
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
        
        # Reset thumbnail counters
        self.pending_thumbnails = len(files) if self.view_mode == self.THUMBNAIL_VIEW else 0
        self.loaded_thumbnails = 0
        
        # Show loading indicator only for thumbnail view
        if self.pending_thumbnails > 0:
            self.loading_label.setText(f"Loading thumbnails... 0% (0/{self.pending_thumbnails})")
            self.loading_label.show()
            self.is_loading = True
        else:
            self.loading_label.hide()
            self.is_loading = False
        
        # Add files to the list widget based on the current view mode
        for file_info in files:
            item = QListWidgetItem(self.list_widget)
            
            if self.view_mode == self.THUMBNAIL_VIEW:
                widget = FileIconItem(file_info)
                # Don't automatically request thumbnails for all items
                # They will be requested based on visibility
                item.setSizeHint(widget.sizeHint())
            elif self.view_mode == self.ICONS_VIEW:
                # For icons view, use the FileIconsItem class that displays icons without thumbnails
                widget = FileIconsItem(file_info)
                item.setSizeHint(widget.sizeHint())
            else:
                widget = FileListItem(file_info)
                item.setSizeHint(widget.sizeHint())
            
            self.list_widget.setItemWidget(item, widget)
            
            # Force UI update periodically to show progress
            if self.list_widget.count() % 20 == 0:  # Update every 20 items
                QApplication.processEvents()
        
        # If no pending thumbnails, consider loading complete
        if self.pending_thumbnails == 0:
            self.is_loading = False
            self.loading_label.hide()
        
        # Force a final UI update to show all items before starting thumbnail loading
        QApplication.processEvents()
        
        # Load visible thumbnails immediately for a better user experience
        if self.view_mode == self.THUMBNAIL_VIEW:
            # Load immediately, but in a non-blocking way
            QTimer.singleShot(10, self._load_visible_thumbnails)
            
    def _handle_item_clicked(self, item):
        """Handle item click event.
        
        Args:
            item: The clicked QListWidgetItem
        """
        widget = self.list_widget.itemWidget(item)
        if widget and hasattr(widget, 'file_info'):
            self.file_selected.emit(widget.file_info) 

# Add a helper function at the bottom of the file
def test_video_thumbnail(file_path):
    """Test function to directly generate a video thumbnail and verify it works.
    Can be called from a debugger or command line to test the video thumbnailing.
    
    Args:
        file_path: Path to a video file to test
        
    Returns:
        True if thumbnail generation succeeded, False otherwise
    """
    try:
        from PyQt6.QtCore import QSize
        from utils import video_thumbnail
        
        logger = logging.getLogger('VideoThumbnailTest')
        logger.setLevel(logging.DEBUG)
        
        # Check if OpenCV is available
        if not video_thumbnail.OPENCV_AVAILABLE:
            logger.error("OpenCV is not available")
            return False
            
        logger.info(f"Testing video thumbnail generation for {file_path}")
        logger.info(f"Current configuration: {VIDEO_THUMBNAIL_CONFIG}")
        
        # Test standard method
        frame_number = VIDEO_THUMBNAIL_CONFIG["frame_number"]
        # Convert frame number to approximate time (assuming 30fps)
        approx_time = frame_number / 30.0
        
        logger.info(f"Testing standard method with frame {frame_number} (approx time: {approx_time:.2f}s)")
        start_time = time.time()
        pixmap = video_thumbnail.generate_video_thumbnail(
            file_path,
            QSize(200, 150),
            frame_time=approx_time  # Convert frame number to approximate time
        )
        standard_time = time.time() - start_time
        standard_success = pixmap and not pixmap.isNull()
        
        logger.info(f"Standard method completed in {standard_time:.4f}s - Success: {standard_success}")
        
        # Test optimized methods if available
        optimized_methods = {}
        try:
            from utils import video_thumbnail_optimized
            logger.info(f"Testing optimized methods with frame {frame_number}")
            
            # Test each available method
            for method in video_thumbnail_optimized.OPTIMIZATION_METHODS:
                start_time = time.time()
                
                # Set appropriate parameters based on method
                kwargs = {}
                if method == "fast_frame_grab":
                    kwargs["frame_number"] = frame_number
                elif method not in ["fast_first_frame", "standard"]:
                    # For other methods, convert frame number to time
                    kwargs["frame_time"] = approx_time
                
                try:
                    pixmap, _ = video_thumbnail_optimized.generate_optimized_thumbnail(
                        file_path,
                        QSize(200, 150),
                        method=method,
                        **kwargs
                    )
                    
                    method_time = time.time() - start_time
                    method_success = pixmap and not pixmap.isNull()
                    
                    # Store results
                    optimized_methods[method] = {
                        "time": method_time,
                        "success": method_success,
                        "speedup": standard_time / method_time if method_time > 0 else 0
                    }
                    
                    logger.info(f"{method} method: {method_time:.4f}s, Success: {method_success}, " 
                               f"Speedup: {standard_time / method_time:.2f}x")
                except Exception as e:
                    logger.error(f"Error testing {method} method: {e}")
                    optimized_methods[method] = {
                        "time": 0,
                        "success": False,
                        "error": str(e)
                    }
            
            # Find the fastest successful method
            successful_methods = {m: data for m, data in optimized_methods.items() 
                                if data.get("success", False)}
            
            if successful_methods:
                fastest_method = min(successful_methods.items(), 
                                   key=lambda x: x[1]["time"])
                
                best_quality_method = "fast_frame_grab" if "fast_frame_grab" in successful_methods else fastest_method[0]
                
                logger.info(f"RECOMMENDATION:")
                logger.info(f"  Fastest method: {fastest_method[0]} ({fastest_method[1]['time']:.4f}s)")
                logger.info(f"  Best quality/speed: {best_quality_method}")
                logger.info(f"  Current setting: {VIDEO_THUMBNAIL_CONFIG['preferred_method']}")
                
                # Suggest updating configuration if significantly faster option available
                current_method = VIDEO_THUMBNAIL_CONFIG["preferred_method"]
                if current_method in successful_methods:
                    current_time = successful_methods[current_method]["time"]
                    fastest_time = fastest_method[1]["time"]
                    
                    if current_time > fastest_time * 1.5:  # If current is 50% slower than fastest
                        logger.info(f"SUGGESTION: Consider changing preferred_method to {fastest_method[0]} "
                                  f"for {current_time/fastest_time:.1f}x speed improvement")
            
        except ImportError:
            logger.warning("Optimized thumbnail module not available")
        except Exception as e:
            logger.error(f"Error testing optimized methods: {e}")
        
        return standard_success
    except Exception as e:
        logger.exception(f"Error testing video thumbnail: {e}")
        return False