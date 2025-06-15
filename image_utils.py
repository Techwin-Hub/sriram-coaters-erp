import os
import shutil
import uuid
from PIL import Image, ImageTk

def save_uploaded_file(source_file_path, destination_folder, unique_filename_prefix):
    """
    Saves an uploaded file to a destination folder with a unique filename.

    Args:
        source_file_path (str): The path to the source file.
        destination_folder (str): The folder where the file should be saved.
        unique_filename_prefix (str): A prefix for the unique filename.

    Returns:
        str: The full path to the saved file, or None if saving fails.
    """
    if not source_file_path or not os.path.exists(source_file_path):
        print(f"Error: Source file '{source_file_path}' not found.")
        return None

    if not os.path.exists(destination_folder):
        try:
            os.makedirs(destination_folder)
        except OSError as e:
            print(f"Error creating directory {destination_folder}: {e}")
            return None

    try:
        _, extension = os.path.splitext(source_file_path)
        unique_filename = f"{unique_filename_prefix}_{uuid.uuid4().hex}{extension}"
        destination_path = os.path.join(destination_folder, unique_filename)
        shutil.copy2(source_file_path, destination_path)
        return destination_path
    except OSError as e:
        print(f"OS error saving file to {destination_path} from {source_file_path}: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error saving file to {destination_path} from {source_file_path}: {e}")
        return None

def get_image_for_display(image_path, size=(100, 100)):
    """
    Opens, resizes, and returns a PhotoImage object for Tkinter labels.

    Args:
        image_path (str): The path to the image file.
        size (tuple): The desired size (width, height) for the image.

    Returns:
        ImageTk.PhotoImage: The PhotoImage object, or None if an error occurs.
    """
    if not image_path or not os.path.exists(image_path):
        # print(f"Error: Image file '{image_path}' not found.") # Can be noisy if path is initially None
        return None
    try:
        img = Image.open(image_path)
        img.thumbnail(size)
        return ImageTk.PhotoImage(img)
    except FileNotFoundError:
        print(f"Error: Image file not found at path: {image_path}")
        return None
    except Exception as e:
        print(f"Error processing image {image_path}: {e}")
        return None

if __name__ == '__main__':
    # Test save_uploaded_file
    # Create a dummy source file
    test_source_dir = "test_source_files"
    if not os.path.exists(test_source_dir):
        os.makedirs(test_source_dir)

    dummy_file_path = os.path.join(test_source_dir, "test_image.png")
    try:
        Image.new('RGB', (60, 30), color = 'red').save(dummy_file_path)
        print(f"Created dummy file: {dummy_file_path}")
    except Exception as e:
        print(f"Error creating dummy file: {e}")

    destination_dir = "data/test_uploads"

    if os.path.exists(dummy_file_path):
        saved_path = save_uploaded_file(dummy_file_path, destination_dir, "test_img")
        if saved_path:
            print(f"File saved successfully: {saved_path}")
            # Test get_image_for_display
            # Note: Tkinter PhotoImage needs a root window to exist,
            # so direct testing here might be limited without a Tk app.
            # We'll assume it works if Pillow processes it.
            img_obj = get_image_for_display(saved_path)
            if img_obj:
                print(f"Image loaded successfully for display: {img_obj}")
            else:
                print("Failed to load image for display.")
        else:
            print("Failed to save file.")
    else:
        print(f"Skipping save test as dummy file {dummy_file_path} was not created.")

    # Clean up dummy file and dir
    # if os.path.exists(dummy_file_path):
    #     os.remove(dummy_file_path)
    # if os.path.exists(test_source_dir):
    #     os.rmdir(test_source_dir)
    # if os.path.exists(destination_dir) and not os.listdir(destination_dir): # only remove if empty
    #     os.rmdir(destination_dir)

    # Test with a non-existent file
    print("\nTesting with non-existent source file:")
    non_existent_file = "non_existent.png"
    saved_path_ne = save_uploaded_file(non_existent_file, destination_dir, "test_ne")
    if not saved_path_ne:
        print("Correctly handled non-existent source file.")

    print("\nTesting get_image_for_display with non-existent image:")
    img_obj_ne = get_image_for_display(non_existent_file)
    if not img_obj_ne:
        print("Correctly handled non-existent image file for display.")

    print("\nTesting get_image_for_display with None path:")
    img_obj_none = get_image_for_display(None)
    if not img_obj_none:
        print("Correctly handled None image path for display.")
