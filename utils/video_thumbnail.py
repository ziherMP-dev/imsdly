import os
import sys
import logging
from typing import Optional
from pathlib import Path
import time

from PyQt6.QtCore import QSize, Qt, QRect, QPoint
from PyQt6.QtGui import QPixmap, QPainter, QColor, QFont, QPen, QBrush, QImage, QPolygon
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel

logger = logging.getLogger(__name__)

# Check if OpenCV is available
try:
    import cv2
    OPENCV_AVAILABLE = True
    logger.info("OpenCV is available for video thumbnail generation")
except ImportError:
    OPENCV_AVAILABLE = False
    logger.warning("OpenCV not available. Install with: pip install opencv-python")

def generate_video_thumbnail(file_path: str, size: QSize, frame_time: float = 1.0) -> Optional[QPixmap]:
    """Generate a thumbnail for a video file.
    
    Args:
        file_path: Path to the video file
        size: Desired thumbnail size
        frame_time: Time in seconds to extract the frame from
        
    Returns:
        QPixmap containing the thumbnail or None if failed
    """
    if not OPENCV_AVAILABLE:
        logger.error("OpenCV is not available for video thumbnail generation.")
        return create_fallback_thumbnail(file_path, size)
    
    try:
        start_time = time.time()  # Add start_time variable for logging
        logger.debug(f"Generating video thumbnail for {file_path} at time {frame_time}s with size {size.width()}x{size.height()}")
        
        # Check memory cache first
        cache_key = f"{file_path}_{size.width()}x{size.height()}_{frame_time}"
        if hasattr(generate_video_thumbnail, "cache") and cache_key in generate_video_thumbnail.cache:
            logger.debug(f"Memory cache hit for {file_path}")
            return generate_video_thumbnail.cache[cache_key]
        
        # Open the video file
        video = cv2.VideoCapture(file_path)
        
        if not video.isOpened():
            logger.error(f"Could not open video file: {file_path}")
            return create_fallback_thumbnail(file_path, size)
        
        # Get video info
        fps = video.get(cv2.CAP_PROP_FPS)
        total_frames = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
        
        if fps <= 0 or total_frames <= 0:
            logger.error(f"Invalid video properties: fps={fps}, frames={total_frames}")
            video.release()
            return create_fallback_thumbnail(file_path, size)
        
        # Calculate frame number
        frame_number = int(frame_time * fps)
        frame_number = min(max(0, frame_number), total_frames - 1)
        
        # Set position to the desired frame
        video.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
        
        # Read the frame
        success, frame = video.read()
        video.release()
        
        if not success or frame is None:
            logger.error(f"Failed to extract frame from {file_path}")
            return create_fallback_thumbnail(file_path, size)
        
        # Convert BGR to RGB (OpenCV uses BGR format)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Resize while maintaining aspect ratio
        h, w, _ = rgb_frame.shape
        
        target_w, target_h = size.width(), size.height()
        aspect_ratio = w / h
        
        if w > h:
            # Landscape
            new_w = target_w
            new_h = int(new_w / aspect_ratio)
            if new_h > target_h:
                new_h = target_h
                new_w = int(new_h * aspect_ratio)
        else:
            # Portrait
            new_h = target_h
            new_w = int(new_h * aspect_ratio)
            if new_w > target_w:
                new_w = target_w
                new_h = int(new_w / aspect_ratio)
        
        # Resize frame
        resized_frame = cv2.resize(rgb_frame, (new_w, new_h), interpolation=cv2.INTER_AREA)
        logger.debug(f"Resized frame from {w}x{h} to {new_w}x{new_h}")
        
        # Create QImage from numpy array
        h, w, channels = resized_frame.shape
        bytes_per_line = channels * w
        q_img = QImage(resized_frame.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
        
        # Create QPixmap and center it on a transparent background of the target size
        pixmap = QPixmap.fromImage(q_img)
        
        # Create a target pixmap of the desired size
        target_pixmap = QPixmap(target_w, target_h)
        target_pixmap.fill(QColor(25, 25, 25))  # Dark background
        
        # Center the frame on the target pixmap
        painter = QPainter(target_pixmap)
        painter.drawPixmap((target_w - pixmap.width()) // 2, 
                         (target_h - pixmap.height()) // 2, 
                         pixmap)
        painter.end()
        
        # Add filmstrip overlay
        pixmap_with_overlay = add_filmstrip_overlay(target_pixmap)
        
        # Add duration indicator if available
        duration = get_video_duration(file_path)
        if duration and duration > 0:
            pixmap_with_overlay = add_duration_indicator(pixmap_with_overlay, duration)
        
        # Cache the result
        if not hasattr(generate_video_thumbnail, "cache"):
            generate_video_thumbnail.cache = {}
        
        generate_video_thumbnail.cache[cache_key] = pixmap_with_overlay
        
        # Keep cache size reasonable (max 50 items)
        if len(generate_video_thumbnail.cache) > 50:
            # Remove the oldest item
            oldest_key = next(iter(generate_video_thumbnail.cache))
            del generate_video_thumbnail.cache[oldest_key]
        
        logger.debug(f"Successfully generated thumbnail for {file_path} in {time.time() - start_time:.3f}s")
        return pixmap_with_overlay
        
    except Exception as e:
        logger.error(f"Error generating video thumbnail: {str(e)}")
        return create_fallback_thumbnail(file_path, size)

def add_play_button_overlay(pixmap: QPixmap) -> QPixmap:
    """Add a play button overlay to the thumbnail."""
    # Create a copy of the pixmap to draw on
    result = QPixmap(pixmap)
    
    painter = QPainter(result)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    
    # Semi-transparent dark circle background for play button
    width, height = pixmap.width(), pixmap.height()
    center_x, center_y = width // 2, height // 2
    circle_radius = min(width, height) // 6  # Size proportional to thumbnail
    
    # Draw circle
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QBrush(QColor(0, 0, 0, 150)))
    painter.drawEllipse(center_x - circle_radius, center_y - circle_radius, 
                       circle_radius * 2, circle_radius * 2)
    
    # Draw play triangle
    play_size = circle_radius * 0.8
    painter.setBrush(QBrush(QColor(255, 255, 255, 220)))
    
    # Create a right-facing triangle centered in the circle
    # Make sure all values are integers for QPoint
    triangle = QPolygon([
        QPoint(int(center_x - play_size//2), int(center_y - play_size)),
        QPoint(int(center_x + play_size), int(center_y)),
        QPoint(int(center_x - play_size//2), int(center_y + play_size))
    ])
    
    painter.drawPolygon(triangle)
    painter.end()
    
    return result

def add_duration_indicator(pixmap: QPixmap, duration: float) -> QPixmap:
    """Add a duration indicator to the thumbnail."""
    result = QPixmap(pixmap)
    
    painter = QPainter(result)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    
    # Format duration as MM:SS
    minutes = int(duration // 60)
    seconds = int(duration % 60)
    duration_text = f"{minutes:02d}:{seconds:02d}"
    
    # Calculate text size
    width, height = pixmap.width(), pixmap.height()
    font = QFont("Arial", height // 15)
    font.setBold(True)
    painter.setFont(font)
    
    # Semi-transparent background
    text_rect_height = height // 6
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QBrush(QColor(0, 0, 0, 180)))
    painter.drawRect(0, height - text_rect_height, width, text_rect_height)
    
    # Draw text
    painter.setPen(QColor(255, 255, 255))
    painter.drawText(0, height - text_rect_height, width, text_rect_height, 
                    Qt.AlignmentFlag.AlignCenter, duration_text)
    
    painter.end()
    
    return result

def create_fallback_thumbnail(file_path: str, size: QSize) -> QPixmap:
    """Create a fallback thumbnail for video files when video processing fails."""
    pixmap = QPixmap(size)
    pixmap.fill(QColor(30, 30, 30))
    
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    
    # Background with rounded corners
    width, height = size.width(), size.height()
    painter.setPen(QPen(QColor(40, 40, 40)))
    painter.setBrush(QBrush(QColor(40, 40, 40)))
    painter.drawRoundedRect(0, 0, width, height, 8, 8)
    
    # Calculate filmstrip properties
    strip_width = max(width // 12, 6)  # Width of the filmstrip, at least 6px
    hole_height = height // 8  # Height of each sprocket hole
    hole_spacing = height // 6  # Space between holes
    hole_width = int(strip_width * 0.6)  # Width of each hole, ensure it's an integer
    
    # Draw left filmstrip
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QBrush(QColor(0, 0, 0, 255)))  # Full opacity (was 180)
    painter.drawRect(0, 0, strip_width, height)
    
    # Draw right filmstrip
    painter.drawRect(width - strip_width, 0, strip_width, height)
    
    # Draw sprocket holes
    painter.setBrush(QBrush(QColor(60, 60, 60, 255)))  # Full opacity (was 220)
    
    # Calculate number of holes based on spacing
    hole_count = height // (hole_height + hole_spacing)
    if hole_count < 3:
        hole_count = 3  # Ensure at least 3 holes
    
    # Calculate vertical offset to center the holes
    total_holes_height = hole_count * hole_height + (hole_count - 1) * hole_spacing
    y_offset = (height - total_holes_height) // 2
    
    # Draw holes on left side
    for i in range(hole_count):
        y_pos = y_offset + i * (hole_height + hole_spacing)
        hole_x = (strip_width - hole_width) // 2
        painter.drawRoundedRect(
            int(hole_x), int(y_pos), 
            hole_width, hole_height, 
            2, 2
        )
    
    # Draw holes on right side
    for i in range(hole_count):
        y_pos = y_offset + i * (hole_height + hole_spacing)
        hole_x = width - strip_width + (strip_width - hole_width) // 2
        painter.drawRoundedRect(
            int(hole_x), int(y_pos), 
            hole_width, hole_height, 
            2, 2
        )
    
    # Add "VIDEO" text in the center
    painter.setPen(QColor(255, 255, 255))
    font = QFont("Arial", height // 8)
    font.setBold(True)
    painter.setFont(font)
    painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, "VIDEO")
    
    # Add file extension at the bottom
    ext = os.path.splitext(file_path)[1].upper()
    if ext.startswith('.'):
        ext = ext[1:]
    
    # Bottom overlay rectangle for extension
    painter.setBrush(QBrush(QColor(0, 0, 0, 180)))
    painter.setPen(Qt.PenStyle.NoPen)
    rect = QRect(0, height - height // 5, width, height // 5)
    painter.drawRect(rect)
    
    # File extension text
    painter.setPen(QPen(QColor(255, 255, 255)))
    font = QFont("Arial", height // 15)
    font.setBold(True)
    painter.setFont(font)
    painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, ext)
    
    painter.end()
    return pixmap

def get_video_duration(file_path: str) -> Optional[float]:
    """Get the duration of a video file in seconds."""
    if not OPENCV_AVAILABLE:
        return None
    
    try:
        # Open the video file
        video = cv2.VideoCapture(file_path)
        
        if not video.isOpened():
            logger.error(f"Could not open video file: {file_path}")
            return None
        
        # Get video info
        fps = video.get(cv2.CAP_PROP_FPS)
        total_frames = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
        
        # Release the video capture object
        video.release()
        
        if fps <= 0 or total_frames <= 0:
            logger.error(f"Invalid video properties: fps={fps}, frames={total_frames}")
            return None
        
        # Calculate duration in seconds
        duration = total_frames / fps
        
        return duration
    except Exception as e:
        logger.error(f"Error getting video duration: {str(e)}")
        return None

def add_filmstrip_overlay(pixmap: QPixmap) -> QPixmap:
    """Add filmstrip borders to the left and right sides of the thumbnail."""
    # Create a copy of the pixmap to draw on
    result = QPixmap(pixmap)
    
    painter = QPainter(result)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    
    width, height = pixmap.width(), pixmap.height()
    
    # Calculate filmstrip properties
    strip_width = max(width // 12, 6)  # Width of the filmstrip, at least 6px
    hole_height = height // 8  # Height of each sprocket hole
    hole_spacing = height // 6  # Space between holes
    hole_width = int(strip_width * 0.6)  # Width of each hole, ensure it's an integer
    
    # Draw left filmstrip
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QBrush(QColor(0, 0, 0, 255)))
    painter.drawRect(0, 0, strip_width, height)
    
    # Draw right filmstrip
    painter.drawRect(width - strip_width, 0, strip_width, height)
    
    # Draw sprocket holes (left side)
    painter.setBrush(QBrush(QColor(40, 40, 40, 255)))
    
    # Calculate number of holes based on spacing
    hole_count = height // (hole_height + hole_spacing)
    if hole_count < 3:
        hole_count = 3  # Ensure at least 3 holes
    
    # Calculate vertical offset to center the holes
    total_holes_height = hole_count * hole_height + (hole_count - 1) * hole_spacing
    y_offset = (height - total_holes_height) // 2
    
    # Draw holes on left side
    for i in range(hole_count):
        y_pos = y_offset + i * (hole_height + hole_spacing)
        hole_x = (strip_width - hole_width) // 2
        painter.drawRoundedRect(
            int(hole_x), int(y_pos), 
            hole_width, hole_height, 
            2, 2
        )
    
    # Draw holes on right side
    for i in range(hole_count):
        y_pos = y_offset + i * (hole_height + hole_spacing)
        hole_x = width - strip_width + (strip_width - hole_width) // 2
        painter.drawRoundedRect(
            int(hole_x), int(y_pos), 
            hole_width, hole_height, 
            2, 2
        )
    
    painter.end()
    return result 