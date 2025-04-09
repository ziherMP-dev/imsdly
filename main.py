import sys
import logging
from PyQt6.QtWidgets import QApplication
from ui.main_window import MainWindow

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
    window = MainWindow()
    window.show()
    
    logger.info("Application window displayed")
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
