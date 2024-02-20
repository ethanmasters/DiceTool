import cv2
import numpy as np
import os

# Function to reset the snapshot
def reset_snapshot():
    global cap, snapshot
    _, snapshot = cap.read()
    print("Snapshot reset")

# Function to save isolated new regions
def save_isolated_regions(regions, directory="DiceGrabs"):
    if not os.path.exists(directory):
        os.makedirs(directory)

    existing_files = os.listdir(directory)
    existing_count = len(existing_files)

    for i, region in enumerate(regions):
        cv2.imwrite(os.path.join(directory, f"region_{existing_count + i + 1}.png"), region)

    print(f"Saved {len(regions)} isolated regions for the current frame.")

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
            # Store the region for the current frame
            x, y, w, h = cv2.boundingRect(hull)
            isolated_regions.append(frame[y:y+h, x:x+w])

    # Display the resulting frame with the number of isolated regions
    cv2.putText(display_frame, f"Number of Dice Estimated: {len(isolated_regions)}", (10, 20),
                font, font_scale, (255, 105, 180), font_thickness, cv2.LINE_AA)  # Hot pink color
    cv2.imshow("Live Feed", display_frame)

    # Check for keyboard input
    key = cv2.waitKey(1) & 0xFF

    # Break the loop if 'q' key is pressed
    if key == ord('q'):
        break

    # Save isolated regions for the current frame if 'p' key is pressed
    elif key == ord('p'):
        save_isolated_regions(isolated_regions)

    # Reset snapshot if 'r' key is pressed
    elif key == ord('r'):
        reset_snapshot()

# Release the video capture object and close all windows
cap.release()
cv2.destroyAllWindows()
