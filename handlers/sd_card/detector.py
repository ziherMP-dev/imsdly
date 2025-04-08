import time
from typing import List, Dict, Any, Callable, Set
import threading
import logging
from PyQt6.QtCore import QObject, pyqtSignal

from utils.drive_utils import get_removable_drives, is_drive_available


class SDCardDetector(QObject):
    """
    Detector for SD cards that monitors for insertion and removal events.
    
    Emits signals when SD cards are inserted or removed.
    """
    
    # Signals for SD card events
    card_inserted = pyqtSignal(dict)  # Emitted when a new SD card is detected
    card_removed = pyqtSignal(dict)   # Emitted when an SD card is removed
    cards_updated = pyqtSignal(list)  # Emitted with the full list of currently available cards
    
    def __init__(self, polling_interval: float = 1.0):
        """
        Initialize the SD card detector.
        
        Args:
            polling_interval: Time in seconds between checks for SD card changes
        """
        super().__init__()
        self._polling_interval = polling_interval
        self._current_cards: Dict[str, Dict[str, Any]] = {}  # Path -> card info
        self._running = False
        self._thread = None
        self._lock = threading.Lock()
        self.logger = logging.getLogger(__name__)
    
    def start(self) -> None:
        """Start monitoring for SD card events."""
        with self._lock:
            if self._running:
                return
                
            self._running = True
            self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
            self._thread.start()
            self.logger.info("SD card detector started")
    
    def stop(self) -> None:
        """Stop monitoring for SD card events."""
        with self._lock:
            if not self._running:
                return
                
            self._running = False
            if self._thread and self._thread.is_alive():
                self._thread.join(timeout=2.0)
            self.logger.info("SD card detector stopped")
    
    def get_current_cards(self) -> List[Dict[str, Any]]:
        """
        Get a list of currently available SD cards.
        
        Returns:
            List[Dict[str, Any]]: List of SD card information dictionaries
        """
        with self._lock:
            return list(self._current_cards.values())
    
    def _monitor_loop(self) -> None:
        """Main monitoring loop that runs in a separate thread."""
        last_check_time = 0
        
        while self._running:
            # Only check at the specified interval
            current_time = time.time()
            if current_time - last_check_time < self._polling_interval:
                time.sleep(0.1)  # Short sleep to prevent CPU hogging
                continue
                
            try:
                self._check_for_changes()
            except Exception as e:
                self.logger.error(f"Error checking for SD card changes: {e}")
                
            last_check_time = time.time()
    
    def _check_for_changes(self) -> None:
        """Check for changes in available SD cards."""
        new_cards = get_removable_drives()
        new_cards_dict = {card["path"]: card for card in new_cards}
        has_changes = False
        
        with self._lock:
            # Find new cards
            for path, card_info in new_cards_dict.items():
                if path not in self._current_cards:
                    # New card inserted
                    self.logger.info(f"SD card inserted: {card_info['name']} at {path}")
                    self._current_cards[path] = card_info
                    # Emit in the main thread
                    self.card_inserted.emit(card_info)
                    has_changes = True
            
            # Find removed cards
            removed_paths = []
            for path, card_info in self._current_cards.items():
                if path not in new_cards_dict or not is_drive_available(path):
                    # Card removed
                    self.logger.info(f"SD card removed: {card_info['name']} at {path}")
                    removed_paths.append(path)
                    # Emit in the main thread
                    self.card_removed.emit(card_info)
                    has_changes = True
            
            # Remove cards from internal state
            for path in removed_paths:
                self._current_cards.pop(path, None)
            
            # Emit updated list if there were any changes
            if has_changes:
                self.cards_updated.emit(list(self._current_cards.values())) 