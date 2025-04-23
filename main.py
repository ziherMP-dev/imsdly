import sys
import logging
import os
import platform
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import QSize
from ui.main_window import MainWindow
from ui.resources import initialize_resources

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def main():
    """Main entry point for the application."""
    logger.info("Starting Imsdly application")
    
    app = QApplication(sys.argv)
    
    # Initialize resources
    if initialize_resources():
        logger.info("Resources initialized successfully")
    else:
        logger.warning("Failed to initialize resources")
    
    # Set application icon
    try:
        # Get the path to the icons directory
        base_dir = os.path.dirname(os.path.abspath(__file__))
        icon_files = [
            os.path.join(base_dir, 'icons', 'imsdly_logo.ico'),
            os.path.join(base_dir, 'icons', 'imsdly_logo.png')
        ]
        
        # Find the first available icon file
        icon_path = None
        for path in icon_files:
            if os.path.exists(path):
                icon_path = path
                break
        
        if icon_path:
            app_icon = QIcon(icon_path)
            
            # Set high-DPI versions if available
            icon_sizes = [16, 24, 32, 48, 64, 128, 256]
            for size in icon_sizes:
                size_path = os.path.join(base_dir, 'icons', f"imsdly_logo_{size}x{size}.png")
                if os.path.exists(size_path):
                    app_icon.addFile(size_path, QSize(size, size))
            
            # Set app icon
            app.setWindowIcon(app_icon)
            
            # Set taskbar icon on Windows
            if platform.system() == 'Windows':
                try:
                    import ctypes
                    app_id = 'com.imsdly.app'  # Arbitrary string
                    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)
                    logger.info(f"Windows taskbar icon set with app ID: {app_id}")
                except Exception as e:
                    logger.warning(f"Failed to set Windows taskbar icon: {e}")
            
            logger.info(f"Application icon set from {icon_path}")
        else:
            logger.warning(f"No icon files found in {os.path.join(base_dir, 'icons')}")
    except Exception as e:
        logger.error(f"Failed to set application icon: {e}")
    
    window = MainWindow()
    window.show()
    
    logger.info("Application window displayed")
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
