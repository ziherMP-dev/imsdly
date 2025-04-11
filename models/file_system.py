import os
import datetime
from typing import Dict, List, Optional, Callable, Any

class FileSystemModel:
    """Model for representing files on an SD card."""
    
    def __init__(self, root_path: str):
        """Initialize with the root path of the SD card.
        
        Args:
            root_path: The path to the SD card or directory
        """
        self.root_path = root_path
        self.files: List[Dict] = []
        self.sort_key = "name"  # Default sort by name
        self.sort_order = "asc"  # Default ascending order
        
    def scan_directory(self, file_types: Optional[List[str]] = None) -> None:
        """Scan the directory for files.
        
        Args:
            file_types: Optional list of file types to scan for (e.g., ['image', 'video'])
        """
        self.files = []
        
        if not os.path.exists(self.root_path):
            return
            
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
                    except Exception:
                        pass
            
            # Apply default sorting
            self.sort_files(self.sort_key, self.sort_order)
        except Exception:
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
        except Exception:
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
        
        # Image file extensions
        image_exts = [
            '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.raw', '.cr2', '.nef',
            '.webp', '.heic', '.heif', '.arw', '.dng', '.orf', '.sr2', '.pef', '.raf',
            '.x3f', '.rw2', '.psd', '.ai', '.eps', '.svg', '.ico', '.jfif', '.jpe',
            '.tif', '.bmp', '.ppm', '.pgm', '.pbm', '.pnm', '.hdr', '.exr'
        ]
        
        # Video file extensions
        video_exts = [
            '.mp4', '.mov', '.avi', '.mkv', '.mpg', '.mpeg', '.3gp',
            '.wmv', '.flv', '.webm', '.m4v', '.vob', '.ogv', '.mts', '.m2ts',
            '.ts', '.mxf', '.rm', '.rmvb', '.asf', '.divx', '.xvid', '.h264',
            '.h265', '.hevc', '.vp8', '.vp9', '.av1', '.m2v', '.m4p', '.m4b',
            '.f4v', '.f4p', '.f4a', '.f4b'
        ]
        
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
        
    def sort_files(self, key: str = "name", order: str = "asc") -> None:
        """Sort files by the specified key and order.
        
        Args:
            key: Sort key ('name', 'size', 'type', 'date')
            order: Sort order ('asc' or 'desc')
        """
        if not self.files:
            return
            
        self.sort_key = key
        self.sort_order = order
        reverse = (order.lower() == "desc")
        
        sort_functions: Dict[str, Callable[[Dict], Any]] = {
            "name": lambda x: x["name"].lower(),
            "size": lambda x: x["size"],
            "type": lambda x: (x["type"], os.path.splitext(x["name"])[1].lower()),
            "date": lambda x: x["modified"]  # Sort by modification date by default
        }
        
        if key in sort_functions:
            self.files.sort(key=sort_functions[key], reverse=reverse)
        else:
            # Default to name if invalid key
            self.files.sort(key=sort_functions["name"], reverse=reverse) 