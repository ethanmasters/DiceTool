import cv2
import numpy as np
import os
import xml.etree.ElementTree as ET
from datetime import datetime
import tkinter as tk
from tkinter import simpledialog
from PIL import Image, ImageTk
import json


# Function to reset the snapshot
def reset_snapshot():
    global cap, snapshot
    _, snapshot = cap.read()
    print("Snapshot reset")

# Function to collect full frame, isolated new regions, and bounding box information
def collect_screenshot_data(full_frame, regions, bounding_boxes, dataset_dir="Dataset"):
    if not os.path.exists(dataset_dir):
        os.makedirs(dataset_dir)

    # Ensure subdirectories exist
    full_frame_dir = os.path.join(dataset_dir, "FullFrame")
    cropped_dir = os.path.join(dataset_dir, "CroppedDice")
    annotations_dir = os.path.join(dataset_dir, "Annotations")

    for subdir in [full_frame_dir, cropped_dir, annotations_dir]:
        if not os.path.exists(subdir):
            os.makedirs(subdir)

    # Generate timestamp for unique filenames
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Save the full frame
    full_frame_path = os.path.join(full_frame_dir, f"image_{timestamp}_full_frame.png")
    cv2.imwrite(full_frame_path, full_frame)

    # Save cropped dice images and get annotations (dice values)
    annotations = []
    cropped_dir_path = os.path.join(cropped_dir, f"image_{timestamp}")
    os.makedirs(cropped_dir_path)

    for i, region in enumerate(regions):
        # Calculate the aspect ratio of the original and cropped images
        original_aspect_ratio = full_frame.shape[1] / full_frame.shape[0]
        cropped_aspect_ratio = region.shape[1] / region.shape[0]

        # Resize the cropped image to match the cropped aspect ratio
        if original_aspect_ratio > cropped_aspect_ratio:
            new_width = int(region.shape[0] * original_aspect_ratio)
            padded_region = np.zeros((region.shape[0], new_width, 3), dtype=np.uint8)
            padded_region[:, :region.shape[1], :] = region
        else:
            new_height = int(region.shape[1] / original_aspect_ratio)
            padded_region = np.zeros((new_height, region.shape[1], 3), dtype=np.uint8)
            padded_region[:region.shape[0], :, :] = region

        # Save cropped image
        cropped_path = os.path.join(cropped_dir_path, f"dice_{i + 1}.png")
        cv2.imwrite(cropped_path, region)

        # Get user input for dice value using Tkinter
        root = tk.Tk()
        root.title(f"Cropped Image {i + 1}")

        # Display the cropped image
        image_label = tk.Label(root)
        image_label.pack()
        image = cv2.cvtColor(padded_region, cv2.COLOR_BGR2RGB)
        image = Image.fromarray(image)
        
        # Adjust the scale factor to make the image larger
        scale_factor = 4  # You can modify this factor according to your preference
        new_size = (image.width * scale_factor, image.height * scale_factor)
        image = image.resize(new_size)
        
        imgtk = ImageTk.PhotoImage(image=image)
        image_label.imgtk = imgtk
        image_label.config(image=imgtk)

        # Create a text box for entering dice value
        entry_var = tk.StringVar()
        entry_label = tk.Label(root, text="Enter Value:")
        entry_label.pack()
        entry = tk.Entry(root, textvariable=entry_var)
        entry.pack()

        def on_submit():
            entered_value = entry_var.get()
            # Process the entered value (save to annotations, etc.)
            annotations.append(int(entered_value))
            root.destroy()

        submit_button = tk.Button(root, text="Submit", command=on_submit)
        submit_button.pack()

        root.mainloop()

    # Save bounding box information in XML format
    annotations_dir_path = os.path.join(annotations_dir, f"image_{timestamp}")
    os.makedirs(annotations_dir_path)

    for i, bounding_box in enumerate(bounding_boxes):
        xml_path = os.path.join(annotations_dir_path, f"image_{timestamp}_dice_{i + 1}.xml")
        save_bounding_box_xml(xml_path, f"image_{timestamp}_dice_{i + 1}.png", bounding_box, annotations[i])
        
    update_monitoring_data(1, len(regions), annotations)

    print(f"Saved full frame, {len(regions)} isolated regions, and annotations for the current frame.")

# Function to save bounding box information in XML format
def save_bounding_box_xml(xml_path, filename, bounding_box, annotation):
    root = ET.Element("annotation")

    filename_elem = ET.SubElement(root, "filename")
    filename_elem.text = filename

    object_elem = ET.SubElement(root, "object")
    name_elem = ET.SubElement(object_elem, "name")
    name_elem.text = "dice"

    bndbox_elem = ET.SubElement(object_elem, "bndbox")
    xmin_elem = ET.SubElement(bndbox_elem, "xmin")
    ymin_elem = ET.SubElement(bndbox_elem, "ymin")
    xmax_elem = ET.SubElement(bndbox_elem, "xmax")
    ymax_elem = ET.SubElement(bndbox_elem, "ymax")

    xmin_elem.text = str(bounding_box[0])
    ymin_elem.text = str(bounding_box[1])
    xmax_elem.text = str(bounding_box[0] + bounding_box[2])
    ymax_elem.text = str(bounding_box[1] + bounding_box[3])

    # Add annotation (dice value)
    annotation_elem = ET.SubElement(object_elem, "value")
    annotation_elem.text = str(annotation)

    tree = ET.ElementTree(root)
    tree.write(xml_path)

def update_monitoring_data(new_full_frame_photos, new_cropped_dice_photos, new_dice_values, file_path='monitoring_data.json'):
    # Read the current data
    with open(file_path, 'r') as file:
        data = json.load(file)
    
    # Update the data
    data['total_full_frame_photos'] += new_full_frame_photos
    data['total_cropped_dice_photos'] += new_cropped_dice_photos
    for value in new_dice_values:
        value_str = str(value)  # Ensure the key is a string
        if value_str in data['dice_face_counts']:
            data['dice_face_counts'][value_str] += 1

    # Save the updated data back to the file
    with open(file_path, 'w') as file:
        json.dump(data, file, indent=4)

# Capture video from the camera (0 is usually the default camera)
cap = cv2.VideoCapture(0)

# Take the initial snapshot
_, snapshot = cap.read()

# Minimum and maximum contour area thresholds
min_contour_area = 1000
max_contour_area = 5000

# Font settings for displaying text on the frame
font = cv2.FONT_HERSHEY_SIMPLEX
font_scale = 0.75
font_thickness = 1

while True:
    # Capture the current frame
    ret, frame = cap.read()

    # Calculate the absolute difference between the snapshot and the current frame
    diff = cv2.absdiff(frame, snapshot)

    # Convert the difference to grayscale
    gray_diff = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)

    # Threshold the grayscale difference
    _, threshold = cv2.threshold(gray_diff, 25, 255, cv2.THRESH_BINARY)

    # Find contours in the threshold image
    contours, _ = cv2.findContours(threshold, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Draw red contours for detected objects with desired size and convex hull
    isolated_regions = []  # List to store isolated new regions for the current frame
    bounding_boxes = []  # List to store bounding box information for the current frame
    display_frame = frame.copy()  # Create a copy for display purposes

    for contour in contours:
        # Calculate the area of each contour
        area = cv2.contourArea(contour)

        # If the area is within the desired range
        if min_contour_area < area < max_contour_area:
            # Calculate convex hull
            hull = cv2.convexHull(contour)
            # Draw the contour in red
            cv2.drawContours(display_frame, [hull], 0, (0, 0, 255), 2)
            # Store the region and bounding box for the current frame
            x, y, w, h = cv2.boundingRect(hull)
            isolated_regions.append(frame[y:y+h, x:x+w])
            bounding_boxes.append((x, y, w, h))

    # Display the resulting frame with the number of isolated regions
    cv2.putText(display_frame, f"Number of Dice Estimated: {len(isolated_regions)}", (10, 20),
                font, font_scale, (255, 105, 180), font_thickness, cv2.LINE_AA)  # Hot pink color
    cv2.imshow("Live Feed", display_frame)

    # Check for keyboard input
    key = cv2.waitKey(1) & 0xFF

    # Break the loop if 'q' key is pressed
    if key == ord('q'):
        print("Goodbye!")
        break

    # Save full frame, cropped images, and annotations if 'p' key is pressed
    elif key == ord('p'):
        collect_screenshot_data(frame, isolated_regions, bounding_boxes)

    # Reset snapshot if 'r' key is pressed
    elif key == ord('r'):
        reset_snapshot()

# Release the video capture object and close all windows
cap.release()
cv2.destroyAllWindows()