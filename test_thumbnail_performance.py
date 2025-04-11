#!/usr/bin/env python
"""
Video Thumbnail Performance Test Launcher
----------------------------------------
This script launches the video thumbnail performance testing tool
which helps measure and optimize video thumbnail generation speed.

It includes multiple optimization techniques for extracting frames:
- Fast First-Frame: Extract only the first frame for maximum speed
- Fast Frame Grab (NEW): Extract a specific frame (e.g., #50) without decoding intermediate frames
- Direct seeking to frame time without decoding intermediate frames
- Keyframe-only extraction for faster processing
- Frame skipping and stream optimization
- Hardware acceleration where available
"""

import sys
import os
import argparse
import logging

# Ensure that the current directory is in the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import and run the test app
from utils.test_video_thumbnail import VideoThumbnailTester
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer

def main():
    """Launch the video thumbnail performance test application."""
    # Configure argument parser
    parser = argparse.ArgumentParser(description="Test video thumbnail generation performance")
    parser.add_argument("--video", type=str, help="Path to video file to test")
    parser.add_argument("--benchmark-all", action="store_true", help="Automatically run all benchmark tests")
    parser.add_argument("--test-fast-first", action="store_true", help="Test only the fast first frame method")
    parser.add_argument("--test-frame-grab", action="store_true", help="Test the fast frame grab method")
    parser.add_argument("--frame-number", type=int, default=50, help="Frame number for fast frame grab (default: 50)")
    parser.add_argument("--frame-time", type=float, default=1.0, help="Frame time in seconds (default: 1.0)")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    args = parser.parse_args()
    
    # Configure logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Start the Qt application
    app = QApplication(sys.argv)
    app.setStyle("Fusion")  # Consistent style across platforms
    
    # Create and show the main window
    window = VideoThumbnailTester()
    
    # Set frame time if specified
    if args.frame_time != 1.0:
        window.frame_time_spin.setValue(args.frame_time)
        
    # Set frame number if specified
    if args.frame_number != 50:
        window.frame_number_spin.setValue(args.frame_number)
    
    # If a video file was specified, load it
    if args.video and os.path.exists(args.video):
        window.video_path = args.video
        window.file_path_label.setText(os.path.basename(args.video))
        window.status_label.setText("Ready to generate thumbnail")
        window.generate_btn.setEnabled(True)
        window.benchmark_current_btn.setEnabled(True)
        
        # Check if optimized methods are available
        try:
            from utils import video_thumbnail_optimized
            window.benchmark_all_btn.setEnabled(True)
            
            # Process testing flags (fast-first has precedence if both are specified)
            if args.test_fast_first:
                # Find the index of the fast_first_frame method
                for i in range(window.method_combo.count()):
                    if window.method_combo.itemData(i) == "fast_first_frame":
                        window.method_combo.setCurrentIndex(i)
                        # Generate thumbnail immediately
                        QTimer.singleShot(100, window.generate_thumbnail)
                        break
            elif args.test_frame_grab:
                # Find the index of the fast_frame_grab method
                for i in range(window.method_combo.count()):
                    if window.method_combo.itemData(i) == "fast_frame_grab":
                        window.method_combo.setCurrentIndex(i)
                        # Generate thumbnail immediately
                        QTimer.singleShot(100, window.generate_thumbnail)
                        break
            # Run benchmark if requested
            elif args.benchmark_all:
                # Use QTimer to run after window is shown
                QTimer.singleShot(100, lambda: window.run_benchmarks(True))
        except ImportError:
            logging.warning("Optimized thumbnail methods not available")
    
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main() 