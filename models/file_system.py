import os
import datetime
import logging
from typing import Dict, List, Optional

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FileSystemModel:
    """Model for representing files on an SD card."""
    
    def __init__(self, root_path: str):
        """Initialize with the root path of the SD card.
        
        Args:
            root_path: The path to the SD card or directory
        """
        self.root_path = root_path
        self.files: List[Dict] = []
        logger.info(f"Initialized FileSystemModel with path: {root_path}")
        
    def scan_directory(self, file_types: Optional[List[str]] = None) -> None:
        """Scan the directory for files.
        
        Args:
            file_types: Optional list of file types to scan for (e.g., ['image', 'video'])
        """
        logger.debug(f"Scanning directory {self.root_path} for file types: {file_types}")
        self.files = []
        
        if not os.path.exists(self.root_path):
            logger.warning(f"Path does not exist: {self.root_path}")
            return
            
        logger.info(f"Scanning directory: {self.root_path}")
        file_count = 0
        
        try:
            for root, _, files in os.walk(self.root_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    try:
                        file_info = self._get_file_info(file_path)
                        
                        # Skip if file type doesn't match filter
                        if file_types and file_info['type'] not in file_types:
                            continue
                            
                        self.files.append(file_info)
                        file_count += 1
                    except Exception as e:
                        logger.warning(f"Error processing file {file_path}: {str(e)}")
            
            logger.info(f"Found {file_count} files in {self.root_path}")
        except Exception as e:
            logger.error(f"Error scanning directory: {str(e)}")
            self.files = []
    
    def _get_file_info(self, file_path: str) -> Dict:
        """Get file metadata.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Dictionary containing file metadata
        """
        try:
            file_stat = os.stat(file_path)
            file_info = {
                'name': os.path.basename(file_path),
                'path': file_path,
                'size': file_stat.st_size,
                'created': datetime.datetime.fromtimestamp(file_stat.st_ctime),
                'modified': datetime.datetime.fromtimestamp(file_stat.st_mtime),
                'relative_path': os.path.relpath(file_path, self.root_path),
                'type': self._get_file_type(file_path)
            }
            return file_info
        except Exception as e:
            logger.error(f"Error getting file info for {file_path}: {e}")
            # Return minimal info if error occurs
            return {
                'name': os.path.basename(file_path),
                'path': file_path,
                'size': 0,
                'created': datetime.datetime.now(),
                'modified': datetime.datetime.now(),
                'relative_path': '',
                'type': 'other'
            }
    
    def _get_file_type(self, file_path: str) -> str:
        """Determine file type based on extension.
        
        Args:
            file_path: Path to the file
            
        Returns:
            String representing file type (image, video, etc.)
        """
        ext = os.path.splitext(file_path)[1].lower()
        
        image_exts = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.raw', '.cr2', '.nef']
        video_exts = ['.mp4', '.mov', '.avi', '.mkv', '.mpg', '.mpeg', '.3gp']
        
        if ext in image_exts:
            return 'image'
        elif ext in video_exts:
            return 'video'
        else:
            return 'other'
    
    def get_files(self) -> List[Dict]:
        """Get all files.
        
        Returns:
            List of file info dictionaries
        """
        return self.files
        
    def get_file_count(self) -> int:
        """Get the number of files.
        
        Returns:
            Number of files in the model
        """
        return len(self.files) 