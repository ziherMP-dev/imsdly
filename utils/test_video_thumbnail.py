#!/usr/bin/env python3
"""
Test script for video thumbnail generation using OpenCV.
"""

import sys
import os
import logging
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel, QPushButton, QFileDialog, QHBoxLayout
from PyQt6.QtCore import QSize, Qt
from PyQt6.QtGui import QPixmap, QColor

# Configure logging
logging.basicConfig(level=logging.DEBUG, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import our video thumbnail module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import video_thumbnail

class VideoThumbnailTester(QMainWindow):
    """Test application for video thumbnailing using OpenCV."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Video Thumbnail Tester (OpenCV)")
        self.setMinimumSize(600, 500)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Create layout
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Status label
        self.status_label = QLabel("OpenCV Status: Checking...")
        self.status_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(self.status_label)
        
        # Check OpenCV status
        if video_thumbnail.OPENCV_AVAILABLE:
            self.status_label.setText("✅ OpenCV is available")
            self.status_label.setStyleSheet("font-weight: bold; font-size: 14px; color: green;")
        else:
            self.status_label.setText("❌ OpenCV not available. Install with: pip install opencv-python")
            self.status_label.setStyleSheet("font-weight: bold; font-size: 14px; color: red;")
        
        # Open video button
        button_layout = QHBoxLayout()
        
        self.open_button = QPushButton("Open Video File")
        self.open_button.clicked.connect(self.handle_open_file)
        self.open_button.setMinimumHeight(36)
        button_layout.addWidget(self.open_button)
        
        # Capture Frame button - lets user specify time
        self.capture_frame_button = QPushButton("Capture Frame at Time (sec)")
        self.capture_frame_button.clicked.connect(self.handle_capture_at_time)
        self.capture_frame_button.setMinimumHeight(36)
        button_layout.addWidget(self.capture_frame_button)
        
        layout.addLayout(button_layout)
        
        # Thumbnail display
        self.thumbnail_label = QLabel("No thumbnail generated yet")
        self.thumbnail_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.thumbnail_label.setMinimumSize(480, 360)
        self.thumbnail_label.setStyleSheet("background-color: #222; border-radius: 8px;")
        layout.addWidget(self.thumbnail_label)
        
        # File info and status label
        self.file_info_label = QLabel("")
        self.file_info_label.setStyleSheet("color: #aaa;")
        layout.addWidget(self.file_info_label)
        
        # Store current video path
        self.current_video_path = None
        
    def handle_open_file(self):
        """Handle open file button click."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Video File",
            "",
            "Video Files (*.mp4 *.mov *.avi *.mkv *.wmv *.flv *.webm);;All Files (*)"
        )
        
        if not file_path:
            return
            
        self.current_video_path = file_path
        self.file_info_label.setText(f"File: {os.path.basename(file_path)}")
        
        # Generate thumbnail
        self.generate_thumbnail(file_path, 1.0)
        
    def handle_capture_at_time(self):
        """Capture a frame at a specific time."""
        if not self.current_video_path:
            self.file_info_label.setText("Please open a video file first")
            return
            
        # Simple dialog for time input
        time_str, ok = QFileDialog.getSaveFileName(
            self, "Enter time in seconds", "", "Seconds (e.g. 5)"
        )
        
        if not ok or not time_str:
            return
            
        try:
            time_sec = float(time_str)
            self.generate_thumbnail(self.current_video_path, time_sec)
        except ValueError:
            self.file_info_label.setText(f"Invalid time format: {time_str}. Please enter a number in seconds.")
            
    def generate_thumbnail(self, file_path: str, time_sec: float):
        """Generate a thumbnail from the video file at the specified time."""
        self.thumbnail_label.setText("Generating thumbnail...\nPlease wait.")
        QApplication.processEvents()  # Force UI update
        
        try:
            # Get video duration
            duration = video_thumbnail.get_video_duration(file_path)
            if duration:
                self.file_info_label.setText(
                    f"File: {os.path.basename(file_path)}\n"
                    f"Duration: {int(duration // 60):02d}:{int(duration % 60):02d} • "
                    f"Frame time: {time_sec:.1f}s"
                )
            
            # Generate thumbnail
            thumbnail = video_thumbnail.generate_video_thumbnail(
                file_path,
                QSize(480, 360),
                frame_time=time_sec
            )
            
            if thumbnail and not thumbnail.isNull():
                self.thumbnail_label.setPixmap(thumbnail)
                self.thumbnail_label.setText("")
            else:
                self.thumbnail_label.setText("Failed to generate thumbnail")
                
        except Exception as e:
            self.thumbnail_label.setText("Error generating thumbnail")
            self.file_info_label.setText(f"Error: {str(e)}")
            logger.exception("Error generating thumbnail")

def main():
    """Main entry point for the test application."""
    app = QApplication(sys.argv)
    app.setStyle("Fusion")  # Use Fusion style for consistent appearance
    
    # Set dark palette
    palette = app.palette()
    palette.setColor(palette.ColorRole.Window, QColor(53, 53, 53))
    palette.setColor(palette.ColorRole.WindowText, Qt.GlobalColor.white)
    palette.setColor(palette.ColorRole.Base, QColor(25, 25, 25))
    palette.setColor(palette.ColorRole.AlternateBase, QColor(53, 53, 53))
    palette.setColor(palette.ColorRole.ToolTipBase, Qt.GlobalColor.white)
    palette.setColor(palette.ColorRole.ToolTipText, Qt.GlobalColor.white)
    palette.setColor(palette.ColorRole.Text, Qt.GlobalColor.white)
    palette.setColor(palette.ColorRole.Button, QColor(53, 53, 53))
    palette.setColor(palette.ColorRole.ButtonText, Qt.GlobalColor.white)
    palette.setColor(palette.ColorRole.BrightText, Qt.GlobalColor.red)
    palette.setColor(palette.ColorRole.Link, QColor(42, 130, 218))
    palette.setColor(palette.ColorRole.Highlight, QColor(42, 130, 218))
    palette.setColor(palette.ColorRole.HighlightedText, Qt.GlobalColor.black)
    app.setPalette(palette)
    
    window = VideoThumbnailTester()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main() 