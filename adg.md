# Imsdly Application Development Guide

## Phase 1: Setup & Basic Structure

### Step 1: Environment Setup
1.1. Install Python (3.8+ recommended)
1.2. Install PyQt6 using pip: `pip install PyQt6`
1.3. Create a new project folder named "Imsdly"
1.4. Set up a virtual environment (optional but recommended)

### Step 2: Basic Application Structure
2.1. Create main.py as entry point
2.2. Set up basic QApplication and main window classes
2.3. Create a simple folder structure:
   - imsdly/ (main folder)
     - main.py (entry point)
     - ui/ (folder for UI files)
     - utils/ (utility functions)
     - models/ (data models)

### Step 3: Basic Window UI
3.1. Create a main window with a basic layout
3.2. Add a menu bar with File menu (Exit, Settings options)
3.3. Add a status bar for displaying messages
3.4. Test that the application launches with proper window

## Phase 2: SD Card Detection

### Step 4: SD Card Detection
4.1. Create a utility function to detect mounted drives
4.2. Add functionality to filter for removable drives (likely SD cards)
4.3. Implement event-based detection for when an SD card is inserted
4.4. Display detected SD card information in the UI

### Step 5: File System Model
5.1. Create a model to represent files on the SD card
5.2. Implement functions to read file metadata (date taken, size, type)
5.3. Create a view to display the files in a list or grid format
5.4. Test browsing files on a connected SD card

## Phase 3: File Preview & Selection

### Step 6: File Preview
6.1. Add thumbnail generation for images and videos
6.2. Create a preview panel in the UI
6.3. Implement functionality to display selected file previews
6.4. Add option to toggle preview feature on/off

### Step 7: File Selection & Filtering
7.1. Implement multi-select functionality for files
7.2. Create filter controls for date taken, file size, and file type
7.3. Hook up the filters to the file system model
7.4. Test filtering and selection functionality

## Phase 4: Destination & Organization

### Step 8: Destination Selection
8.1. Add controls to select destination folder
8.2. Create functionality to save/load default destination folder
8.3. Implement a settings dialog for configuring defaults
8.4. Test saving and loading settings

### Step 9: File Organization Options
9.1. Create UI controls for selecting organization method:
   - By date (create options for format: YYYY-MM-DD, etc.)
   - By custom metadata structure
9.2. Add interface for defining custom folder structures
9.3. Implement preview of resulting folder structure
9.4. Test different organization methods

### Step 10: Batch Renaming
10.1. Create UI for batch rename options
10.2. Implement functionality to generate preview of renamed files
10.3. Add sequential numbering logic
10.4. Test renaming preview functionality

## Phase 5: Transfer Implementation

### Step 11: Basic Transfer Logic
11.1. Create a transfer manager class to handle file transfers
11.2. Implement file copy functionality
11.3. Add progress tracking for individual files and overall process
11.4. Test basic file transfer from SD to destination

### Step 12: Transfer Verification
12.1. Implement file verification (checksum comparison)
12.2. Add error handling and reporting
12.3. Create recovery options for failed transfers
12.4. Test verification with various file types and sizes

### Step 13: Post-Transfer Options
13.1. Add functionality to remove files from SD card after transfer
13.2. Implement confirmation dialog before deletion
13.3. Add reporting of successful/failed operations
13.4. Test deletion functionality with safety checks

## Phase 6: Polish & Finalization

### Step 14: UI Refinement
14.1. Improve visual design and layout
14.2. Add intuitive icons and visual indicators
14.3. Implement drag-and-drop support if desired
14.4. Ensure all UI elements have proper tooltips

### Step 15: Error Handling
15.1. Implement comprehensive error handling
15.2. Add user-friendly error messages
15.3. Create recovery options where possible
15.4. Test application behavior with various error scenarios

### Step 16: Final Testing
16.1. Test the complete workflow end-to-end
16.2. Verify all features work as expected
16.3. Perform basic usability testing
16.4. Fix any remaining issues

### Step 17: Packaging
17.1. Create an installer/package for easy distribution
17.2. Set up version information
17.3. Prepare documentation for users
17.4. Test installation on fresh systems