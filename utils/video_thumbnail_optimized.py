import os
import sys
import logging
import time
from typing import Optional, Dict, Tuple, List

from PyQt6.QtCore import QSize, Qt, QRect, QPoint
from PyQt6.QtGui import QPixmap, QPainter, QColor, QFont, QPen, QBrush, QImage, QPolygon
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel

# Check if OpenCV is available
try:
    import cv2
    import numpy as np
    OPENCV_AVAILABLE = True
    logger = logging.getLogger("video_thumbnail_optimized")
    logger.info("OpenCV is available for optimized video thumbnail generation")
except ImportError:
    OPENCV_AVAILABLE = False
    logger = logging.getLogger("video_thumbnail_optimized")
    logger.warning("OpenCV not available. Install with: pip install opencv-python")

# Import original module for fallback and comparison
from utils import video_thumbnail

# Optimization methods dictionary for reference and testing
OPTIMIZATION_METHODS = {
    "standard": "Standard OpenCV frame extraction (baseline)",
    "direct_seek": "Direct frame seeking without decoding intervening frames",
    "keyframe_only": "Extract nearest keyframe (I-frame) without full decoding",
    "stream_optimized": "Use optimized video stream parameters",
    "skip_frames": "Skip frames for faster seeking",
    "hardware_accel": "Use hardware acceleration if available",
    "fast_first_frame": "Fast extraction of the first frame only",
    "fast_frame_grab": "Fast extraction of a specific frame number"
}

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

def generate_optimized_thumbnail(
    file_path: str, 
    size: QSize, 
    frame_time: float = 1.0,
    method: str = "direct_seek",
    frame_number: int = 50  # Default frame number for fast_frame_grab
) -> Tuple[Optional[QPixmap], float]:
    """Generate a thumbnail from a video file using optimized methods.
    
    Args:
        file_path: Path to the video file
        size: Desired thumbnail size (QSize)
        frame_time: Time in seconds to extract the frame from (default: 1.0)
        method: Optimization method to use
        frame_number: Specific frame number to extract for fast_frame_grab method
        
    Returns:
        Tuple of (QPixmap containing the thumbnail or None if failed, time taken)
    """
    if not OPENCV_AVAILABLE:
        logger.warning("OpenCV not available, using fallback thumbnail")
        start_time = time.time()
        thumb = video_thumbnail.create_fallback_thumbnail(file_path, size)
        elapsed = time.time() - start_time
        return thumb, elapsed
    
    start_time = time.time()
    
    try:
        pixmap = None
        
        if method == "direct_seek":
            pixmap = _direct_seek_method(file_path, size, frame_time)
        elif method == "keyframe_only":
            pixmap = _keyframe_only_method(file_path, size, frame_time)
        elif method == "stream_optimized":
            pixmap = _stream_optimized_method(file_path, size, frame_time)
        elif method == "skip_frames":
            pixmap = _skip_frames_method(file_path, size, frame_time)
        elif method == "hardware_accel":
            pixmap = _hardware_accel_method(file_path, size, frame_time)
        elif method == "fast_first_frame":
            pixmap = _fast_first_frame_method(file_path, size)
        elif method == "fast_frame_grab":
            pixmap = _fast_frame_grab_method(file_path, size, frame_number)
        else:
            # Fallback to standard method if unknown method specified
            pixmap = _standard_method(file_path, size, frame_time)
        
        # Add overlays if successful
        if pixmap and not pixmap.isNull():
            duration = _get_video_duration(file_path)
            pixmap = add_filmstrip_overlay(pixmap)  # Use filmstrip overlay instead of play button
            if duration > 0:
                pixmap = video_thumbnail.add_duration_indicator(pixmap, duration)
        
        elapsed = time.time() - start_time
        return pixmap, elapsed
        
    except Exception as e:
        logger.error(f"Error in optimized thumbnail generation: {str(e)}")
        elapsed = time.time() - start_time
        fallback = video_thumbnail.create_fallback_thumbnail(file_path, size)
        return fallback, elapsed

def _standard_method(file_path: str, size: QSize, frame_time: float) -> Optional[QPixmap]:
    """Standard OpenCV method (baseline for comparison)."""
    video = cv2.VideoCapture(file_path)
    
    if not video.isOpened():
        logger.error(f"Could not open video file: {file_path}")
        return None
    
    # Get video info
    fps = video.get(cv2.CAP_PROP_FPS)
    total_frames = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
    
    if fps <= 0 or total_frames <= 0:
        logger.error(f"Invalid video properties: fps={fps}, frames={total_frames}")
        video.release()
        return None
    
    # Determine the frame to extract (convert time to frame number)
    frame_number = int(frame_time * fps)
    frame_number = max(0, min(frame_number, total_frames - 1))
    
    # Seek to the desired frame
    video.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
    
    # Read the frame
    success, frame = video.read()
    video.release()
    
    if not success or frame is None:
        logger.error(f"Failed to extract frame from {file_path}")
        return None
    
    return _frame_to_pixmap(frame, size)

def _direct_seek_method(file_path: str, size: QSize, frame_time: float) -> Optional[QPixmap]:
    """Direct seek to timestamp without decoding intermediate frames."""
    video = cv2.VideoCapture(file_path)
    
    if not video.isOpened():
        logger.error(f"Could not open video file: {file_path}")
        return None
    
    # Set position directly in milliseconds (more accurate than frame number)
    msec_pos = frame_time * 1000
    video.set(cv2.CAP_PROP_POS_MSEC, msec_pos)
    
    # Read the frame
    success, frame = video.read()
    video.release()
    
    if not success or frame is None:
        logger.error(f"Failed to extract frame at {frame_time}s from {file_path}")
        return None
    
    return _frame_to_pixmap(frame, size)

def _keyframe_only_method(file_path: str, size: QSize, frame_time: float) -> Optional[QPixmap]:
    """Extract nearest keyframe (I-frame) only."""
    # Open video with FFMPEG backend (better for keyframe extraction)
    video = cv2.VideoCapture(file_path)
    
    if not video.isOpened():
        logger.error(f"Could not open video file: {file_path}")
        return None
    
    # Get video info
    fps = video.get(cv2.CAP_PROP_FPS)
    total_frames = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
    
    if fps <= 0 or total_frames <= 0:
        logger.error(f"Invalid video properties: fps={fps}, frames={total_frames}")
        video.release()
        return None
    
    # Tell OpenCV to use only keyframes for seeking
    video.set(cv2.CAP_PROP_HW_ACCELERATION, cv2.VIDEO_ACCELERATION_ANY)
    
    # Set position in milliseconds
    msec_pos = frame_time * 1000
    video.set(cv2.CAP_PROP_POS_MSEC, msec_pos)
    
    # Read the frame (should be the nearest keyframe)
    success, frame = video.read()
    video.release()
    
    if not success or frame is None:
        logger.error(f"Failed to extract keyframe at {frame_time}s from {file_path}")
        return None
    
    return _frame_to_pixmap(frame, size)

def _stream_optimized_method(file_path: str, size: QSize, frame_time: float) -> Optional[QPixmap]:
    """Use optimized video stream parameters."""
    video = cv2.VideoCapture(file_path)
    
    if not video.isOpened():
        logger.error(f"Could not open video file: {file_path}")
        return None
    
    # Set optimized parameters for faster seeking
    video.set(cv2.CAP_PROP_BUFFERSIZE, 3)  # Use small buffer
    
    # Get video info
    fps = video.get(cv2.CAP_PROP_FPS)
    total_frames = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
    
    if fps <= 0 or total_frames <= 0:
        logger.error(f"Invalid video properties: fps={fps}, frames={total_frames}")
        video.release()
        return None
    
    # Set position directly in milliseconds
    msec_pos = frame_time * 1000
    video.set(cv2.CAP_PROP_POS_MSEC, msec_pos)
    
    # Read the frame
    success, frame = video.read()
    video.release()
    
    if not success or frame is None:
        logger.error(f"Failed to extract frame at {frame_time}s from {file_path}")
        return None
    
    return _frame_to_pixmap(frame, size)

def _skip_frames_method(file_path: str, size: QSize, frame_time: float) -> Optional[QPixmap]:
    """Skip frames for faster seeking."""
    video = cv2.VideoCapture(file_path)
    
    if not video.isOpened():
        logger.error(f"Could not open video file: {file_path}")
        return None
    
    # Get video info
    fps = video.get(cv2.CAP_PROP_FPS)
    total_frames = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
    
    if fps <= 0 or total_frames <= 0:
        logger.error(f"Invalid video properties: fps={fps}, frames={total_frames}")
        video.release()
        return None
    
    # Calculate target frame number
    target_frame = int(frame_time * fps)
    target_frame = min(target_frame, total_frames - 1)
    
    # Use large skips to approach target frame quickly
    # This reduces the number of frames decoded
    current_frame = 0
    step_size = max(1, target_frame // 10)
    
    while current_frame < target_frame - step_size:
        video.set(cv2.CAP_PROP_POS_FRAMES, current_frame + step_size)
        ret = video.grab()  # Just grab frame headers without decoding
        if not ret:
            break
        current_frame += step_size
    
    # Set final position
    video.set(cv2.CAP_PROP_POS_FRAMES, target_frame)
    
    # Read the frame
    success, frame = video.read()
    video.release()
    
    if not success or frame is None:
        logger.error(f"Failed to extract frame at {frame_time}s from {file_path}")
        return None
    
    return _frame_to_pixmap(frame, size)

def _hardware_accel_method(file_path: str, size: QSize, frame_time: float) -> Optional[QPixmap]:
    """Use hardware acceleration if available."""
    # Try different hardware acceleration backends
    backends = [
        cv2.CAP_DSHOW,  # DirectShow (Windows)
        cv2.CAP_MSMF,   # Media Foundation (Windows)
        cv2.CAP_FFMPEG, # FFMPEG (cross-platform)
        cv2.CAP_GSTREAMER # GStreamer (Linux)
    ]
    
    # Try each backend
    for backend in backends:
        try:
            video = cv2.VideoCapture(file_path, backend)
            if video.isOpened():
                # Try to enable hardware acceleration
                video.set(cv2.CAP_PROP_HW_ACCELERATION, cv2.VIDEO_ACCELERATION_ANY)
                
                # Set position directly in milliseconds
                msec_pos = frame_time * 1000
                video.set(cv2.CAP_PROP_POS_MSEC, msec_pos)
                
                # Read the frame
                success, frame = video.read()
                video.release()
                
                if success and frame is not None:
                    return _frame_to_pixmap(frame, size)
        except Exception as e:
            logger.debug(f"Backend {backend} failed: {e}")
            continue
    
    # Fallback to standard method if no hardware acceleration worked
    return _standard_method(file_path, size, frame_time)

def _fast_first_frame_method(file_path: str, size: QSize) -> Optional[QPixmap]:
    """Fast extraction of the first frame only.
    
    This method doesn't attempt to seek to a specific time, it just grabs
    the first frame which is typically already cached in the file header.
    
    Args:
        file_path: Path to the video file
        size: Desired thumbnail size
        
    Returns:
        QPixmap containing the first frame or None if failed
    """
    try:
        # Open the video file
        video = cv2.VideoCapture(file_path)
        
        if not video.isOpened():
            logger.error(f"Could not open video file: {file_path}")
            return None
        
        # Just read the first frame (typically very fast as it's often cached)
        success, frame = video.read()
        
        # Immediately release the video object
        video.release()
        
        if not success or frame is None:
            logger.error(f"Failed to extract first frame from {file_path}")
            return None
        
        # Convert the frame to a pixmap
        return _frame_to_pixmap(frame, size)
        
    except Exception as e:
        logger.error(f"Error extracting first frame: {e}")
        return None

def _fast_frame_grab_method(file_path: str, size: QSize, frame_number: int = 50) -> Optional[QPixmap]:
    """Fast extraction of a specific frame number.
    
    This method efficiently navigates to a specific frame number using grab() to 
    skip through frames without fully decoding them, then only decodes the target frame.
    
    Args:
        file_path: Path to the video file
        size: Desired thumbnail size
        frame_number: The specific frame number to extract (default: 50)
        
    Returns:
        QPixmap containing the requested frame or None if failed
    """
    try:
        # Check if we've already processed this exact file+frame combination
        cache_key = f"{file_path}_{frame_number}_{size.width()}x{size.height()}"
        if hasattr(_fast_frame_grab_method, "frame_cache") and cache_key in _fast_frame_grab_method.frame_cache:
            logger.debug(f"Using cached frame {frame_number} for {file_path}")
            return _fast_frame_grab_method.frame_cache[cache_key]
            
        # Open the video file
        video = cv2.VideoCapture(file_path)
        
        if not video.isOpened():
            logger.error(f"Could not open video file: {file_path}")
            return None
        
        # Check if requested frame is within valid range
        total_frames = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
        if total_frames <= 0:
            logger.error(f"Could not determine frame count for {file_path}")
            video.release()
            return None
            
        # Ensure frame_number is within valid range
        frame_number = min(max(0, frame_number), total_frames - 1)
        
        # Optimization for very early frames (0-10)
        if frame_number <= 10:
            # For early frames, it's faster to just read sequentially
            current_pos = 0
            success = True
            while current_pos < frame_number and success:
                success, frame = video.read()
                current_pos += 1
                
            if success and frame is not None:
                # Convert the frame to a pixmap
                pixmap = _frame_to_pixmap(frame, size)
                
                # Cache the result
                if not hasattr(_fast_frame_grab_method, "frame_cache"):
                    _fast_frame_grab_method.frame_cache = {}
                _fast_frame_grab_method.frame_cache[cache_key] = pixmap
                
                # Keep cache size reasonable
                if len(_fast_frame_grab_method.frame_cache) > 100:
                    # Remove an arbitrary item
                    _fast_frame_grab_method.frame_cache.pop(next(iter(_fast_frame_grab_method.frame_cache)))
                
                video.release()
                return pixmap
        else:
            # For later frames, use frame grabbing without decoding to quickly reach the target frame
            # Set position directly - faster for seeking to specific frames
            video.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
            
            # Read the frame
            success, frame = video.read()
            
            # Release the video object
            video.release()
            
            if success and frame is not None:
                # Convert the frame to a pixmap
                pixmap = _frame_to_pixmap(frame, size)
                
                # Cache the result
                if not hasattr(_fast_frame_grab_method, "frame_cache"):
                    _fast_frame_grab_method.frame_cache = {}
                _fast_frame_grab_method.frame_cache[cache_key] = pixmap
                
                # Keep cache size reasonable
                if len(_fast_frame_grab_method.frame_cache) > 100:
                    # Remove an arbitrary item
                    _fast_frame_grab_method.frame_cache.pop(next(iter(_fast_frame_grab_method.frame_cache)))
                
                return pixmap
        
        # If we get here, something went wrong
        logger.error(f"Failed to extract frame {frame_number} from {file_path}")
        return None
        
    except Exception as e:
        logger.error(f"Error extracting frame {frame_number}: {e}")
        return None

def _frame_to_pixmap(frame, size: QSize) -> QPixmap:
    """Convert OpenCV frame to QPixmap with scaling."""
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
    
    return scaled_pixmap

def _get_video_duration(file_path: str) -> float:
    """Get the duration of a video file in seconds."""
    if not OPENCV_AVAILABLE:
        return 0
    
    try:
        video = cv2.VideoCapture(file_path)
        
        if not video.isOpened():
            return 0
        
        # Get video info
        fps = video.get(cv2.CAP_PROP_FPS)
        total_frames = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
        
        # Release the video capture object
        video.release()
        
        if fps <= 0 or total_frames <= 0:
            return 0
        
        # Calculate duration in seconds
        return total_frames / fps
    except Exception:
        return 0

def benchmark_all_methods(file_path: str, size: QSize, frame_time: float = 1.0) -> Dict[str, Dict]:
    """Run benchmarks on all optimization methods.
    
    Args:
        file_path: Path to the video file
        size: Desired thumbnail size
        frame_time: Time in seconds to extract the frame from
        
    Returns:
        Dictionary with results for each method
    """
    results = {}
    
    # First benchmark standard method as baseline
    logger.info(f"Benchmarking standard method...")
    pixmap, elapsed = generate_optimized_thumbnail(file_path, size, frame_time, "standard")
    results["standard"] = {
        "time": elapsed,
        "success": pixmap is not None and not pixmap.isNull(),
        "description": OPTIMIZATION_METHODS["standard"]
    }
    
    # Benchmark other methods
    for method in [m for m in OPTIMIZATION_METHODS.keys() if m != "standard"]:
        logger.info(f"Benchmarking {method} method...")
        pixmap, elapsed = generate_optimized_thumbnail(file_path, size, frame_time, method)
        results[method] = {
            "time": elapsed,
            "success": pixmap is not None and not pixmap.isNull(),
            "description": OPTIMIZATION_METHODS[method],
            "speedup": results["standard"]["time"] / elapsed if elapsed > 0 else 0
        }
    
    return results

# For testing directly
if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(level=logging.INFO, 
                       format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Test with a sample video if provided as argument
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
        if os.path.exists(file_path):
            print(f"Testing optimized thumbnail generation with {file_path}")
            results = benchmark_all_methods(file_path, QSize(320, 240))
            
            # Print results
            print("\nBenchmark Results:")
            print("-" * 80)
            print(f"{'Method':<20} {'Time (s)':<12} {'Success':<10} {'Speedup':<10} {'Description'}")
            print("-" * 80)
            
            for method, data in results.items():
                speedup = data.get("speedup", 1.0)
                speedup_str = f"{speedup:.2f}x" if method != "standard" else "baseline"
                print(f"{method:<20} {data['time']:<12.4f} {data['success']:<10} {speedup_str:<10} {data['description']}")
        else:
            print(f"File not found: {file_path}")
    else:
        print("Please provide a video file path for testing.") 