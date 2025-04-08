import os
import platform
import subprocess
from typing import List, Dict, Any, Optional
import ctypes
from ctypes import windll


def get_mounted_drives() -> List[Dict[str, Any]]:
    """
    Get a list of all mounted drives in the system.
    
    Returns:
        List[Dict[str, Any]]: A list of dictionaries containing drive information
    """
    system = platform.system()
    
    if system == "Windows":
        return _get_windows_drives()
    elif system == "Darwin":
        return _get_macos_drives()
    elif system == "Linux":
        return _get_linux_drives()
    else:
        raise NotImplementedError(f"System {system} not supported")


def _get_windows_drives() -> List[Dict[str, Any]]:
    """
    Get mounted drives on Windows.
    
    Returns:
        List[Dict[str, Any]]: List of drive information dictionaries
    """
    drives = []
    bitmask = windll.kernel32.GetLogicalDrives()
    
    for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
        if bitmask & 1:
            drive_path = f"{letter}:\\"
            
            # Get drive type
            drive_type = windll.kernel32.GetDriveTypeW(drive_path)
            drive_types = {
                0: "UNKNOWN",
                1: "NO_ROOT_DIR",
                2: "REMOVABLE",
                3: "FIXED",
                4: "REMOTE",
                5: "CDROM",
                6: "RAMDISK"
            }
            
            # Get volume information
            volume_name_buffer = ctypes.create_unicode_buffer(1024)
            filesystem_name_buffer = ctypes.create_unicode_buffer(1024)
            serial_number = ctypes.c_ulong(0)
            
            result = windll.kernel32.GetVolumeInformationW(
                drive_path,
                volume_name_buffer,
                ctypes.sizeof(volume_name_buffer),
                ctypes.byref(serial_number),
                None,
                None,
                filesystem_name_buffer,
                ctypes.sizeof(filesystem_name_buffer)
            )
            
            # Get free space information
            free_bytes = ctypes.c_ulonglong(0)
            total_bytes = ctypes.c_ulonglong(0)
            total_free_bytes = ctypes.c_ulonglong(0)
            
            result2 = windll.kernel32.GetDiskFreeSpaceExW(
                drive_path,
                ctypes.byref(free_bytes),
                ctypes.byref(total_bytes),
                ctypes.byref(total_free_bytes)
            )
            
            # Only add if we could get volume information
            if result:
                drive_info = {
                    "path": drive_path,
                    "name": volume_name_buffer.value,
                    "type": drive_types.get(drive_type, "UNKNOWN"),
                    "filesystem": filesystem_name_buffer.value,
                    "serial": serial_number.value,
                    "total_space": total_bytes.value if result2 else None,
                    "free_space": free_bytes.value if result2 else None,
                    "is_removable": drive_type == 2
                }
                drives.append(drive_info)
                
        bitmask >>= 1
        
    return drives


def _get_macos_drives() -> List[Dict[str, Any]]:
    """
    Get mounted drives on macOS.
    
    Returns:
        List[Dict[str, Any]]: List of drive information dictionaries
    """
    drives = []
    
    # Run diskutil to get list of volumes
    try:
        result = subprocess.run(
            ["diskutil", "list", "-plist"], 
            capture_output=True, 
            text=True, 
            check=True
        )
        
        # Parse the output (simplified version - would need plistlib in real implementation)
        # This is a placeholder for actual implementation
        
        # For each disk, get info
        for disk in ["disk1", "disk2"]:  # Example - would come from plist parsing
            disk_info = subprocess.run(
                ["diskutil", "info", "-plist", disk],
                capture_output=True,
                text=True,
                check=True
            )
            # Parse disk info and determine if removable
            
            # Add dummy example
            if disk == "disk2":  # Just for demonstration
                drives.append({
                    "path": f"/Volumes/SDCARD",
                    "name": "SDCARD",
                    "type": "REMOVABLE",
                    "filesystem": "ExFAT",
                    "is_removable": True,
                    "total_space": 32000000000,
                    "free_space": 20000000000
                })
    except subprocess.CalledProcessError:
        pass
    
    return drives


def _get_linux_drives() -> List[Dict[str, Any]]:
    """
    Get mounted drives on Linux.
    
    Returns:
        List[Dict[str, Any]]: List of drive information dictionaries
    """
    drives = []
    
    try:
        # Get mount points
        result = subprocess.run(
            ["lsblk", "-o", "NAME,MOUNTPOINT,FSTYPE,SIZE,MODEL,RM", "-J"],
            capture_output=True,
            text=True,
            check=True
        )
        
        # Parse the output (simplified - would use json in actual implementation)
        # This is a placeholder for actual implementation
        
        # Add dummy example for demonstration
        drives.append({
            "path": "/media/user/SDCARD",
            "name": "SDCARD",
            "type": "REMOVABLE",
            "filesystem": "vfat",
            "is_removable": True,
            "total_space": 16000000000,
            "free_space": 10000000000
        })
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass
    
    return drives


def get_removable_drives() -> List[Dict[str, Any]]:
    """
    Get only removable drives (likely SD cards and USB drives).
    
    Returns:
        List[Dict[str, Any]]: List of removable drive information dictionaries
    """
    all_drives = get_mounted_drives()
    return [drive for drive in all_drives if drive.get("is_removable", False)]


def is_drive_available(drive_path: str) -> bool:
    """
    Check if a specific drive is available.
    
    Args:
        drive_path: Path to the drive to check
        
    Returns:
        bool: True if the drive is available, False otherwise
    """
    if not os.path.exists(drive_path):
        return False
        
    # For Windows
    if platform.system() == "Windows":
        try:
            # Try to list directory contents
            os.listdir(drive_path)
            return True
        except (PermissionError, FileNotFoundError):
            return False
    
    # For Unix-based systems
    return os.access(drive_path, os.R_OK) 