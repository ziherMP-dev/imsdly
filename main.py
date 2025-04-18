import sys
import logging
from PyQt6.QtWidgets import QApplication
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
    
    window = MainWindow()
    window.show()
    
    logger.info("Application window displayed")
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
