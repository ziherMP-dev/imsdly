#!/usr/bin/env python3
"""
Test script for video thumbnail generation using OpenCV.
"""

import sys
import os
import time
import logging
from pathlib import Path
from typing import Optional

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QPushButton, QVBoxLayout, QHBoxLayout, 
    QLabel, QFileDialog, QWidget, QSpinBox, QCheckBox, QGroupBox,
    QSlider, QSizePolicy, QComboBox, QTableWidget, QTableWidgetItem,
    QHeaderView
)
from PyQt6.QtCore import Qt, QSize, QTimer
from PyQt6.QtGui import QPixmap

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('VideoThumbnailTest')

# Import the thumbnail modules
from utils import video_thumbnail
try:
    from utils import video_thumbnail_optimized
    OPTIMIZED_AVAILABLE = True
    # Get the optimization methods
    OPTIMIZATION_METHODS = video_thumbnail_optimized.OPTIMIZATION_METHODS
except ImportError:
    logger.warning("Optimized video thumbnail module not available")
    OPTIMIZED_AVAILABLE = False
    OPTIMIZATION_METHODS = {"standard": "Standard method"}


class VideoThumbnailTester(QMainWindow):
    """Test application for video thumbnail generation performance."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Video Thumbnail Performance Test")
        self.resize(1000, 700)  # Make window larger to fit comparison table
        
        # Initialize variables
        self.video_path = None
        self.generation_times = {}  # Dictionary to store times by method
        self.current_thumbnail = None
        self.current_method = "standard"
        
        # Setup UI
        self.setup_ui()
        
        # Check OpenCV availability
        self.check_opencv()
    
    def setup_ui(self):
        """Set up the user interface."""
        # Main container
        container = QWidget()
        main_layout = QVBoxLayout(container)
        
        # Status display
        self.status_label = QLabel("Select a video file to start testing")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("font-weight: bold; color: #333;")
        main_layout.addWidget(self.status_label)
        
        # File selection
        file_layout = QHBoxLayout()
        self.file_path_label = QLabel("No file selected")
        self.file_path_label.setStyleSheet("background-color: #f0f0f0; padding: 8px; border-radius: 4px;")
        self.file_path_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        
        select_file_btn = QPushButton("Select Video")
        select_file_btn.clicked.connect(self.select_video_file)
        
        file_layout.addWidget(self.file_path_label)
        file_layout.addWidget(select_file_btn)
        main_layout.addLayout(file_layout)
        
        # Settings group
        settings_group = QGroupBox("Generation Settings")
        settings_layout = QVBoxLayout(settings_group)
        
        # Method selection
        method_layout = QHBoxLayout()
        method_layout.addWidget(QLabel("Optimization Method:"))
        self.method_combo = QComboBox()
        
        # Add methods with special highlighting for recommended methods
        self.method_combo.addItem("Standard (baseline)", "standard")
        
        # Add optimized methods if available
        if OPTIMIZED_AVAILABLE:
            # Highlight the recommended methods
            self.method_combo.addItem("⭐ Fast First Frame - Fastest method (uses first frame)", "fast_first_frame")
            self.method_combo.addItem("⭐ Fast Frame Grab - Fast specific frame extraction", "fast_frame_grab")
            
            # Add other methods
            for method, description in OPTIMIZATION_METHODS.items():
                if method not in ["standard", "fast_first_frame", "fast_frame_grab"]:
                    self.method_combo.addItem(f"{method} - {description}", method)
        
        self.method_combo.currentIndexChanged.connect(self.method_changed)
        method_layout.addWidget(self.method_combo)
        settings_layout.addLayout(method_layout)
        
        # Frame number selection (for fast_frame_grab)
        self.frame_number_layout = QHBoxLayout()
        self.frame_number_layout.addWidget(QLabel("Frame Number:"))
        self.frame_number_spin = QSpinBox()
        self.frame_number_spin.setRange(1, 9999)
        self.frame_number_spin.setValue(50)
        self.frame_number_spin.setEnabled(False)  # Disabled by default
        self.frame_number_layout.addWidget(self.frame_number_spin)
        
        # Add explanation text
        frame_number_info = QLabel("📌 Frame 50 often shows more content than frame 1")
        frame_number_info.setStyleSheet("color: #666; font-size: 10px;")
        
        # Create a container layout for frame number settings
        frame_number_container = QVBoxLayout()
        frame_number_container.addLayout(self.frame_number_layout)
        frame_number_container.addWidget(frame_number_info)
        
        settings_layout.addLayout(frame_number_container)
        
        # Frame time settings with guidance
        frame_time_layout = QVBoxLayout()
        frame_time_header = QHBoxLayout()
        frame_time_header.addWidget(QLabel("Frame Time (seconds):"))
        
        # Add a help label about frame time
        help_label = QLabel("📌 Note: First frame (0s) is fastest but 1-2s often shows better content")
        help_label.setStyleSheet("color: #666; font-size: 10px;")
        
        self.frame_time_spin = QSpinBox()
        self.frame_time_spin.setRange(0, 3600)
        self.frame_time_spin.setValue(1)
        frame_time_header.addWidget(self.frame_time_spin)
        frame_time_layout.addLayout(frame_time_header)
        frame_time_layout.addWidget(help_label)
        settings_layout.addLayout(frame_time_layout)
        
        # Thumbnail size settings
        size_layout = QHBoxLayout()
        size_layout.addWidget(QLabel("Thumbnail Width:"))
        self.width_spin = QSpinBox()
        self.width_spin.setRange(50, 800)
        self.width_spin.setValue(320)
        size_layout.addWidget(self.width_spin)
        
        size_layout.addWidget(QLabel("Height:"))
        self.height_spin = QSpinBox()
        self.height_spin.setRange(50, 800)
        self.height_spin.setValue(240)
        size_layout.addWidget(self.height_spin)
        settings_layout.addLayout(size_layout)
        
        main_layout.addWidget(settings_group)
        
        # Split layout for thumbnail preview and results table
        split_layout = QHBoxLayout()
        
        # Thumbnail preview
        preview_group = QGroupBox("Thumbnail Preview")
        preview_layout = QVBoxLayout(preview_group)
        
        self.thumbnail_label = QLabel("No thumbnail generated")
        self.thumbnail_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.thumbnail_label.setStyleSheet("background-color: #222; color: white; padding: 10px;")
        self.thumbnail_label.setMinimumHeight(250)
        preview_layout.addWidget(self.thumbnail_label)
        
        split_layout.addWidget(preview_group)
        
        # Results table
        results_group = QGroupBox("Performance Comparison")
        results_layout = QVBoxLayout(results_group)
        
        self.results_table = QTableWidget(0, 4)
        self.results_table.setHorizontalHeaderLabels(["Method", "Time (s)", "Speedup", "Status"])
        self.results_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        results_layout.addWidget(self.results_table)
        
        # Add a tips section below the table
        tips_label = QLabel("💡 Tips: For production use, consider 'fast_first_frame' for maximum speed or "
                           "'fast_frame_grab' with frame=50 for a good balance of speed and content quality.")
        tips_label.setWordWrap(True)
        tips_label.setStyleSheet("color: #666; padding: 5px;")
        results_layout.addWidget(tips_label)
        
        split_layout.addWidget(results_group)
        
        main_layout.addLayout(split_layout)
        
        # Performance metrics
        metrics_group = QGroupBox("Current Method Performance")
        metrics_layout = QVBoxLayout(metrics_group)
        
        self.current_method_label = QLabel("Current method: Standard")
        metrics_layout.addWidget(self.current_method_label)
        
        self.last_time_label = QLabel("Last generation time: N/A")
        metrics_layout.addWidget(self.last_time_label)
        
        self.avg_time_label = QLabel("Average generation time: N/A")
        metrics_layout.addWidget(self.avg_time_label)
        
        main_layout.addWidget(metrics_group)
        
        # Action buttons
        button_layout = QHBoxLayout()
        
        self.generate_btn = QPushButton("Generate Thumbnail")
        self.generate_btn.clicked.connect(self.generate_thumbnail)
        self.generate_btn.setEnabled(False)
        self.generate_btn.setStyleSheet("font-weight: bold;")
        button_layout.addWidget(self.generate_btn)
        
        self.benchmark_current_btn = QPushButton("Benchmark Current Method")
        self.benchmark_current_btn.clicked.connect(lambda: self.run_benchmarks(False))
        self.benchmark_current_btn.setEnabled(False)
        button_layout.addWidget(self.benchmark_current_btn)
        
        self.benchmark_all_btn = QPushButton("Benchmark All Methods")
        self.benchmark_all_btn.clicked.connect(lambda: self.run_benchmarks(True))
        self.benchmark_all_btn.setEnabled(False)
        button_layout.addWidget(self.benchmark_all_btn)
        
        self.reset_btn = QPushButton("Reset Metrics")
        self.reset_btn.clicked.connect(self.reset_metrics)
        self.reset_btn.setEnabled(False)
        button_layout.addWidget(self.reset_btn)
        
        main_layout.addLayout(button_layout)
        
        # Set the central widget
        self.setCentralWidget(container)
    
    def check_opencv(self):
        """Check if OpenCV is available and update UI accordingly."""
        if not video_thumbnail.OPENCV_AVAILABLE:
            self.status_label.setText("ERROR: OpenCV is not available. Please install it with: pip install opencv-python")
            self.status_label.setStyleSheet("font-weight: bold; color: red;")
    
    def method_changed(self):
        """Handle method selection change."""
        method_data = self.method_combo.currentData()
        if method_data:
            self.current_method = method_data
            self.current_method_label.setText(f"Current method: {self.current_method}")
            
            # Enable/disable frame number spinner based on method
            if self.current_method == "fast_frame_grab":
                self.frame_number_spin.setEnabled(True)
                self.frame_time_spin.setEnabled(False)
            else:
                self.frame_number_spin.setEnabled(False)
                self.frame_time_spin.setEnabled(True)
                
            self.update_metrics()
    
    def select_video_file(self):
        """Open file dialog to select a video file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Video File", "", 
            "Video Files (*.mp4 *.mov *.avi *.mkv *.wmv *.flv *.webm);;All Files (*)"
        )
        
        if file_path:
            self.video_path = file_path
            self.file_path_label.setText(os.path.basename(file_path))
            self.status_label.setText("Ready to generate thumbnail")
            self.generate_btn.setEnabled(True)
            self.benchmark_current_btn.setEnabled(True)
            self.benchmark_all_btn.setEnabled(OPTIMIZED_AVAILABLE)
    
    def generate_thumbnail(self):
        """Generate a thumbnail from the selected video file and measure time."""
        if not self.video_path:
            return
            
        self.status_label.setText(f"Generating thumbnail using {self.current_method} method...")
        
        # Get generation parameters
        frame_time = self.frame_time_spin.value()
        thumb_size = QSize(self.width_spin.value(), self.height_spin.value())
        frame_number = self.frame_number_spin.value()
        
        # Measure generation time
        start_time = time.time()
        
        # Generate thumbnail based on selected method
        pixmap = None
        if self.current_method == "standard" or not OPTIMIZED_AVAILABLE:
            pixmap = video_thumbnail.generate_video_thumbnail(
                self.video_path,
                thumb_size,
                frame_time=frame_time
            )
            elapsed_time = time.time() - start_time
        else:
            # Use optimized methods
            pixmap, elapsed_time = video_thumbnail_optimized.generate_optimized_thumbnail(
                self.video_path,
                thumb_size,
                frame_time=frame_time,
                method=self.current_method,
                frame_number=frame_number
            )
        
        # Update UI
        if pixmap and not pixmap.isNull():
            self.current_thumbnail = pixmap
            self.thumbnail_label.setPixmap(pixmap)
            self.status_label.setText(f"Thumbnail generated in {elapsed_time:.4f} seconds")
        else:
            self.thumbnail_label.setText("Failed to generate thumbnail")
            self.status_label.setText("Error generating thumbnail")
        
        # Store the time for this method
        if self.current_method not in self.generation_times:
            self.generation_times[self.current_method] = []
        self.generation_times[self.current_method].append(elapsed_time)
        
        # Update metrics
        self.update_metrics()
        self.update_results_table()
        self.reset_btn.setEnabled(True)
    
    def run_benchmarks(self, all_methods=False):
        """Run multiple benchmark tests."""
        if not self.video_path:
            return
            
        # Get parameters
        iterations = 5
        frame_time = self.frame_time_spin.value()
        thumb_size = QSize(self.width_spin.value(), self.height_spin.value())
        frame_number = self.frame_number_spin.value()
        
        # Determine which methods to benchmark
        methods_to_test = []
        if all_methods and OPTIMIZED_AVAILABLE:
            methods_to_test = list(OPTIMIZATION_METHODS.keys())
        else:
            methods_to_test = [self.current_method]
            
        self.status_label.setText(f"Running {iterations} benchmarks on {len(methods_to_test)} methods...")
        
        # Disable buttons during benchmarking
        self.benchmark_current_btn.setEnabled(False)
        self.benchmark_all_btn.setEnabled(False)
        self.generate_btn.setEnabled(False)
        self.reset_btn.setEnabled(False)
        
        # Create a function to handle benchmark iterations
        def run_benchmark_iteration(method_idx=0, iteration=0):
            if method_idx >= len(methods_to_test):
                # All methods completed
                self.benchmark_current_btn.setEnabled(True)
                self.benchmark_all_btn.setEnabled(OPTIMIZED_AVAILABLE)
                self.generate_btn.setEnabled(True)
                self.reset_btn.setEnabled(True)
                self.status_label.setText(f"Completed benchmarks for {len(methods_to_test)} methods")
                self.update_results_table()
                return
                
            method = methods_to_test[method_idx]
            
            if iteration == 0:
                # First iteration for this method, update status
                self.status_label.setText(f"Benchmarking method: {method} (1/{iterations})")
                
                # Initialize if this is first time testing this method
                if method not in self.generation_times:
                    self.generation_times[method] = []
            else:
                # Update status for subsequent iterations
                self.status_label.setText(f"Benchmarking method: {method} ({iteration+1}/{iterations})")
            
            # Generate thumbnail and measure time
            start_time = time.time()
            pixmap = None
            
            try:
                if method == "standard" or not OPTIMIZED_AVAILABLE:
                    pixmap = video_thumbnail.generate_video_thumbnail(
                        self.video_path,
                        thumb_size,
                        frame_time=frame_time
                    )
                    elapsed_time = time.time() - start_time
                else:
                    # Use optimized methods
                    pixmap, elapsed_time = video_thumbnail_optimized.generate_optimized_thumbnail(
                        self.video_path,
                        thumb_size,
                        frame_time=frame_time,
                        method=method,
                        frame_number=frame_number
                    )
                
                # Update thumbnail display with the latest one
                if pixmap and not pixmap.isNull():
                    self.current_thumbnail = pixmap
                    self.thumbnail_label.setPixmap(pixmap)
                
                # Record the time
                self.generation_times[method].append(elapsed_time)
                
                # If this is current method, update the metrics
                if method == self.current_method:
                    self.update_metrics()
                
            except Exception as e:
                logger.error(f"Error benchmarking {method}: {e}")
                if method not in self.generation_times:
                    self.generation_times[method] = []
                
            # Determine next step
            if iteration + 1 < iterations:
                # Schedule next iteration for same method
                QTimer.singleShot(100, lambda: run_benchmark_iteration(method_idx, iteration + 1))
            else:
                # Done with this method, update table and move to next
                self.update_results_table()
                QTimer.singleShot(100, lambda: run_benchmark_iteration(method_idx + 1, 0))
        
        # Start the first iteration of the first method
        run_benchmark_iteration(0, 0)
    
    def update_metrics(self):
        """Update the performance metrics display for current method."""
        if self.current_method not in self.generation_times or not self.generation_times[self.current_method]:
            return
            
        # Calculate metrics for current method
        times = self.generation_times[self.current_method]
        last_time = times[-1]
        avg_time = sum(times) / len(times)
        
        # Update labels
        self.last_time_label.setText(f"Last generation time: {last_time:.4f} seconds")
        self.avg_time_label.setText(f"Average generation time: {avg_time:.4f} seconds ({len(times)} runs)")
    
    def update_results_table(self):
        """Update the results comparison table."""
        # Clear the table
        self.results_table.setRowCount(0)
        
        if not self.generation_times:
            return
        
        # Get baseline time (standard method)
        baseline_time = 0
        if "standard" in self.generation_times and self.generation_times["standard"]:
            baseline_time = sum(self.generation_times["standard"]) / len(self.generation_times["standard"])
            if baseline_time <= 0:
                baseline_time = 1  # Avoid division by zero
        
        # Add rows for each method
        row = 0
        for method, times in self.generation_times.items():
            if not times:
                continue
                
            self.results_table.insertRow(row)
            
            # Method name
            name_item = QTableWidgetItem(method)
            self.results_table.setItem(row, 0, name_item)
            
            # Average time
            avg_time = sum(times) / len(times)
            time_item = QTableWidgetItem(f"{avg_time:.4f}")
            self.results_table.setItem(row, 1, time_item)
            
            # Speedup compared to standard
            speedup = baseline_time / avg_time if avg_time > 0 else 0
            speedup_str = f"{speedup:.2f}x" if method != "standard" else "baseline"
            speedup_item = QTableWidgetItem(speedup_str)
            self.results_table.setItem(row, 2, speedup_item)
            
            # Status
            runs_str = f"{len(times)} runs"
            status_item = QTableWidgetItem(runs_str)
            self.results_table.setItem(row, 3, status_item)
            
            # Highlight current method
            if method == self.current_method:
                for col in range(4):
                    item = self.results_table.item(row, col)
                    if item:
                        item.setBackground(Qt.GlobalColor.lightGray)
            
            row += 1
    
    def reset_metrics(self):
        """Reset the performance metrics."""
        self.generation_times = {}
        self.last_time_label.setText("Last generation time: N/A")
        self.avg_time_label.setText("Average generation time: N/A")
        self.reset_btn.setEnabled(False)
        self.results_table.setRowCount(0)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")  # Consistent style across platforms
    
    # Create and show the main window
    window = VideoThumbnailTester()
    window.show()
    
    sys.exit(app.exec()) 