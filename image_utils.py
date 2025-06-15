"""
Image utility functions for the Sriram Coaters ERP application.

This module provides helper functions for common image-related tasks, such as:
- Saving uploaded files (e.g., worker photos, ID proofs) to designated folders
  with unique filenames.
- Loading images from file paths and preparing them for display in Tkinter UI
  (using Pillow for image processing and PhotoImage for Tkinter compatibility).
"""
import os
import shutil  # For file copying operations (shutil.copy2 preserves metadata)
import uuid    # For generating unique filenames to prevent overwrites
from PIL import Image, ImageTk # Pillow library for image manipulation and Tkinter display

def save_uploaded_file(source_file_path, destination_folder, unique_filename_prefix):
    """
    Saves an uploaded file to a specified destination folder with a unique filename.

    The function first checks if the source file exists. It creates the destination
    folder if it doesn't already exist. A unique filename is generated using a
    combination of the provided prefix and a UUID to avoid naming conflicts.
    The file is then copied from the source path to the destination path.

    Args:
        source_file_path (str): The full path to the source file (e.g., from a file dialog).
        destination_folder (str): The path to the folder where the file should be saved
                                  (e.g., "data/worker_photos").
        unique_filename_prefix (str): A prefix to be used in the generated unique filename
                                      (e.g., "worker_photo").

    Returns:
        str: The full path to the newly saved file if successful.
        None: If any error occurs during the process (e.g., source file not found,
              permission issues, error during copy). Error details are printed to the console.
    """
    # Validate source file path
    if not source_file_path or not os.path.exists(source_file_path):
        print(f"Error: Source file '{source_file_path}' not found or path is invalid.")
        return None

    # Ensure the destination folder exists, create if not
    if not os.path.exists(destination_folder):
        try:
            os.makedirs(destination_folder)
            print(f"Info: Created directory {destination_folder}")
        except OSError as e: # Catch errors during directory creation (e.g., permission denied)
            print(f"Error: Could not create directory {destination_folder}: {e}")
            return None

    try:
        # Generate a unique filename to prevent overwriting existing files
        _, extension = os.path.splitext(source_file_path) # Get the original file extension
        # Example: worker_photo_a1b2c3d4e5f6.png
        unique_filename = f"{unique_filename_prefix}_{uuid.uuid4().hex}{extension}"
        destination_path = os.path.join(destination_folder, unique_filename)

        # Copy the file. shutil.copy2 attempts to preserve metadata.
        shutil.copy2(source_file_path, destination_path)
        print(f"Info: File saved successfully to {destination_path}")
        return destination_path
    except OSError as e: # Specific to OS-level errors during file operations (permissions, disk full)
        print(f"OS error saving file to {destination_path} from {source_file_path}: {e}")
        return None
    except Exception as e: # Catch any other unexpected errors during the copy process
        print(f"Unexpected error saving file to {destination_path} from {source_file_path}: {e}")
        return None

def get_image_for_display(image_path, size=(100, 100)):
    """
    Opens an image file, resizes it (thumbnail), and returns a Tkinter PhotoImage object.

    This function is used to prepare images for display in Tkinter labels or other widgets.
    It handles cases where the image file might be missing or corrupted.

    Args:
        image_path (str): The full path to the image file.
        size (tuple): A tuple `(width, height)` specifying the maximum dimensions
                      for the thumbnail. The image will be resized to fit within
                      these dimensions while maintaining aspect ratio.

    Returns:
        ImageTk.PhotoImage: A PhotoImage object suitable for display in Tkinter UI.
        None: If the image cannot be opened, processed, or if the path is invalid.
              Error details are printed to the console.
    """
    # Check if the image path is valid and the file exists
    if not image_path or not os.path.exists(image_path):
        # This print can be noisy if an image is optionally not present (e.g. no ID proof).
        # Consider logging this at a debug level or removing if UI handles None appropriately.
        # print(f"Debug: Image file '{image_path}' not found or path is None for display.")
        return None
    try:
        # Open the image using Pillow
        img = Image.open(image_path)
        # Create a thumbnail. This resizes the image in place to fit within the given size,
        # maintaining aspect ratio.
        img.thumbnail(size)
        # Convert the Pillow Image object to a Tkinter PhotoImage object
        return ImageTk.PhotoImage(img)
    except FileNotFoundError: # Should be caught by os.path.exists, but good to have defense
        print(f"Error: Image file confirmed to exist but not found by Pillow at path: {image_path}")
        return None
    except Exception as e: # Catch other Pillow errors (e.g., unrecognized image format, corrupted file)
        print(f"Error processing image {image_path} for display: {e}")
        return None

if __name__ == '__main__':
    # This block is for testing the utility functions when the script is run directly.
    print("--- Testing image_utils.py ---")

    # Setup a dummy environment for testing save_uploaded_file
    test_source_dir = "temp_test_source_files"
    dummy_image_name = "test_image.png"
    dummy_file_path = os.path.join(test_source_dir, dummy_image_name)

    # Create a dummy image file
    if not os.path.exists(test_source_dir):
        os.makedirs(test_source_dir)
    try:
        # Create a small red PNG image for testing
        Image.new('RGB', (120, 60), color = 'red').save(dummy_file_path)
        print(f"\nCreated dummy source file: {dummy_file_path}")
    except Exception as e:
        print(f"Error creating dummy source file: {e}")
        # If dummy file creation fails, many tests below will be skipped.

    test_destination_dir = "temp_test_data_uploads" # Use a temporary dir for test uploads

    # Test 1: Successful file save and image load
    print("\n--- Test 1: Save valid file and load for display ---")
    if os.path.exists(dummy_file_path):
        saved_image_path = save_uploaded_file(dummy_file_path, test_destination_dir, "test_img_save")
        if saved_image_path:
            print(f"save_uploaded_file: SUCCESS - Saved to '{saved_image_path}'")

            # Test get_image_for_display with the saved image
            # Note: For PhotoImage to fully work, a Tkinter root window usually needs to exist.
            # Here, we are primarily testing if Pillow can process it and create the object.
            img_display_obj = get_image_for_display(saved_image_path, size=(50,50))
            if img_display_obj:
                print(f"get_image_for_display: SUCCESS - Image loaded for display (size: {img_display_obj.width()}x{img_display_obj.height()})")
            else:
                print("get_image_for_display: FAILED to load the saved image.")
        else:
            print("save_uploaded_file: FAILED for a valid dummy file.")
    else:
        print(f"Skipping Test 1 as dummy source file '{dummy_file_path}' was not created.")

    # Test 2: save_uploaded_file with a non-existent source file
    print("\n--- Test 2: Save non-existent source file ---")
    non_existent_source = "non_existent_dummy_file.png"
    saved_path_non_existent = save_uploaded_file(non_existent_source, test_destination_dir, "test_ne_save")
    if not saved_path_non_existent:
        print(f"save_uploaded_file: SUCCESS - Correctly handled non-existent source '{non_existent_source}'.")
    else:
        print(f"save_uploaded_file: FAILED - Did not correctly handle non-existent source, returned '{saved_path_non_existent}'.")

    # Test 3: get_image_for_display with a non-existent image path
    print("\n--- Test 3: Load non-existent image for display ---")
    img_obj_non_existent = get_image_for_display("path/to/non_existent_image.png")
    if not img_obj_non_existent:
        print("get_image_for_display: SUCCESS - Correctly handled non-existent image path.")
    else:
        print("get_image_for_display: FAILED - Did not correctly handle non-existent image path.")

    # Test 4: get_image_for_display with a None path
    print("\n--- Test 4: Load None image path for display ---")
    img_obj_none_path = get_image_for_display(None)
    if not img_obj_none_path:
        print("get_image_for_display: SUCCESS - Correctly handled None image path.")
    else:
        print("get_image_for_display: FAILED - Did not correctly handle None image path.")

    # Clean up: Remove dummy files and directories created for testing
    # This is important to keep the project environment clean.
    print("\n--- Cleaning up test files and directories ---")
    try:
        if os.path.exists(dummy_file_path):
            os.remove(dummy_file_path)
            print(f"Removed dummy source file: {dummy_file_path}")
        if os.path.exists(test_source_dir):
            os.rmdir(test_source_dir) # Remove directory if empty
            print(f"Removed dummy source directory: {test_source_dir}")
        if os.path.exists(test_destination_dir):
            shutil.rmtree(test_destination_dir) # Remove directory and all its contents
            print(f"Removed test destination directory: {test_destination_dir}")
        print("Cleanup complete.")
    except Exception as e:
        print(f"Error during cleanup: {e}")

    print("\n--- image_utils.py testing finished ---")
