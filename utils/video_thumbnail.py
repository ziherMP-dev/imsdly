import os
import sys
import logging
from typing import Optional
from pathlib import Path

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
    """Generate a thumbnail from a video file.
    
    Args:
        file_path: Path to the video file
        size: Desired thumbnail size (QSize)
        frame_time: Time in seconds to extract the frame from (default: 1.0)
        
    Returns:
        QPixmap containing the thumbnail or None if generation failed
    """
    logger.debug(f"Generating video thumbnail for {file_path} at time {frame_time}s with size {size.width()}x{size.height()}")
    
    if not OPENCV_AVAILABLE:
        logger.warning("OpenCV not available, using fallback thumbnail")
        return create_fallback_thumbnail(file_path, size)
    
    try:
        # Open the video file
        video = cv2.VideoCapture(file_path)
        
        if not video.isOpened():
            logger.error(f"Could not open video file: {file_path}")
            return create_fallback_thumbnail(file_path, size)
        
        # Get video info
        fps = video.get(cv2.CAP_PROP_FPS)
        total_frames = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = total_frames / fps if fps > 0 else 0
        
        if fps <= 0 or total_frames <= 0:
            logger.error(f"Invalid video properties: fps={fps}, frames={total_frames}")
            return create_fallback_thumbnail(file_path, size)
        
        # Determine the frame to extract (convert time to frame number)
        frame_number = int(frame_time * fps)
        
        # Make sure frame_number is within valid range
        frame_number = max(0, min(frame_number, total_frames - 1))
        
        # Seek to the desired frame
        video.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
        
        # Read the frame
        success, frame = video.read()
        
        # Release the video capture object
        video.release()
        
        if not success or frame is None:
            logger.error(f"Failed to extract frame from {file_path}")
            return create_fallback_thumbnail(file_path, size)
        
        # Convert BGR to RGB (OpenCV uses BGR format)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Create QImage from numpy array
        height, width, channels = rgb_frame.shape
        bytes_per_line = channels * width
        image = QImage(rgb_frame.data, width, height, bytes_per_line, QImage.Format.Format_RGB888)
        
        # Convert to pixmap and scale to requested size
        pixmap = QPixmap.fromImage(image)
        scaled_pixmap = pixmap.scaled(
            size, 
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        
        # Add play button overlay
        pixmap_with_play = add_play_button_overlay(scaled_pixmap)
        
        # Add duration indicator if available
        if duration > 0:
            pixmap_with_play = add_duration_indicator(pixmap_with_play, duration)
        
        logger.debug(f"Successfully generated thumbnail for {file_path}")
        return pixmap_with_play
        
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
    painter.setPen(QPen(QColor(40, 40, 40)))
    painter.setBrush(QBrush(QColor(40, 40, 40)))
    painter.drawRoundedRect(0, 0, size.width(), size.height(), 8, 8)
    
    # Add a play triangle overlay
    width, height = size.width(), size.height()
    play_triangle = QPolygon([
        QPoint(width // 2 - 25, height // 2 - 25),
        QPoint(width // 2 + 25, height // 2),
        QPoint(width // 2 - 25, height // 2 + 25)
    ])
    painter.setBrush(QColor(231, 76, 60, 180))
    painter.setPen(Qt.PenStyle.NoPen)
    painter.drawPolygon(play_triangle)
    
    # Add video text
    painter.setPen(QColor(255, 255, 255))
    painter.setFont(QFont("Arial", 9, QFont.Weight.Bold))
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