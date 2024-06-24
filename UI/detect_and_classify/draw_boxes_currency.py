import os

import cv2
import supervision as sv
from roboflow import Roboflow

# Initialize Roboflow
rf = Roboflow(api_key="")
project = rf.workspace().project("currency-v4f8j")
model = project.version(1).model


def draw_boxes(image_path, output_folder):
    # Create the output folder if it does not exist
    os.makedirs(output_folder, exist_ok=True)

    # Perform inference on the image
    result = model.predict(image_path, confidence=40, overlap=30).json()

    # Load the original image
    image = cv2.imread(image_path)

    # Get the base name of the image file (without directory and extension)
    base_name = os.path.basename(image_path).split(".")[0]

    # Counter for output image naming
    count = 0

    # List to store the file paths of the generated images
    file_paths = []

    # Iterate over the predictions and draw bounding boxes
    for prediction in result["predictions"]:
        x_center = prediction["x"]
        y_center = prediction["y"]
        width = prediction["width"]
        height = prediction["height"]
        conf = prediction["confidence"]
        cls = prediction["class"]
        label = cls

        x1 = int(x_center - width / 2)
        y1 = int(y_center - height / 2)
        x2 = int(x_center + width / 2)
        y2 = int(y_center + height / 2)

        # Create a copy of the original image to draw the bounding box on
        image_copy = image.copy()

        # Draw the bounding box
        cv2.rectangle(image_copy, (x1, y1), (x1 + x2, y1 + y2), (0, 255, 0), 2)
        cv2.putText(
            image_copy,
            f"{label}: {conf:.2f}",
            (x1, y1 - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (0, 255, 0),
            2,
        )
        cv2.circle(image_copy, (int(x_center), int(y_center)), 100, (0, 0, 255), -1)

        # Save the image with bounding box
        output_path = os.path.join(output_folder, f"{base_name}_box_{count}.png")
        cv2.imwrite(output_path, image_copy)

        # Add the file path to the list
        file_paths.append(output_path)

        # Increment the counter
        count += 1

    return file_paths


# Example usage
generated_files = draw_boxes("currency_objects.jpg", "boxed_images")

# The generated_files list now contains the file paths of the generated images
for file_path in generated_files:
    print(file_path)
