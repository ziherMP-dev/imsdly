import os
import sys
from PyQt6.QtCore import QDir, QFile, QIODevice, QResource

def initialize_resources():
    """Initialize resources for the application"""
    # Define the base directory relative to this file
    base_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    icons_dir = os.path.join(base_dir, 'icons')
    
    # Ensure the icons directory exists
    if not os.path.exists(icons_dir):
        print(f"Warning: Icons directory not found at {icons_dir}")
        return False
    
    # Register the icons directory as a resource path
    QDir.addSearchPath('icons', icons_dir)
    
    print(f"Registered icons directory: {icons_dir}")
    
    # Optional: List all available icons for debugging
    available_icons = os.listdir(icons_dir)
    print(f"Available icons: {available_icons}")
    
    return True 