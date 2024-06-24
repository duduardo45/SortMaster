import os

import cv2
import numpy as np
from inference_sdk import InferenceHTTPClient

CLIENT = InferenceHTTPClient(api_url="https://detect.roboflow.com", api_key="")


def draw_bounding_box(img, x, y, width, height, label, color=(255, 0, 0), thickness=2):
    top_left_x = int(x - width / 2)
    top_left_y = int(y - height / 2)
    bottom_right_x = int(x + width / 2)
    bottom_right_y = int(y + height / 2)

    cv2.rectangle(
        img,
        (top_left_x, top_left_y),
        (bottom_right_x, bottom_right_y),
        color,
        thickness,
    )
    cv2.putText(
        img,
        label,
        (top_left_x, top_left_y - 10),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.9,
        color,
        2,
    )


def draw_segmentations(image_path, output_folder):
    # Create the output folder if it does not exist
    os.makedirs(output_folder, exist_ok=True)

    result = CLIENT.infer(image_path, model_id="currency-v4f8j/1")

    image = cv2.imread(image_path)

    base_name = os.path.basename(image_path).split(".")[0]

    file_paths = []

    for idx, pred in enumerate(result["predictions"]):
        # Copy the original image
        img_copy = image.copy()

        # Extract bounding box parameters
        x = pred["x"]
        y = pred["y"]
        width = pred["width"]
        height = pred["height"]
        label = pred["class"]

        # Draw the bounding box
        draw_bounding_box(img_copy, x, y, width, height, label)

        # Save the image with bounding box
        output_path = os.path.join(output_folder, f"{base_name}_seg_{idx}.png")
        cv2.imwrite(output_path, img_copy)

        file_paths.append(output_path)

    return file_paths


"""     base_name = os.path.basename(image_path).split(".")[0]

    # List to store the file paths of the generated images
    file_paths = []

    # Iterate over the results and save segmentations
    for result in results:
        for ci, c in enumerate(result):
            b_mask = np.zeros(image.shape[:2], np.uint8)
            print(type(c.masks))
            contour = c.masks.xy.pop()
            contour = contour.astype(np.int32)
            contour = contour.reshape(-1, 1, 2)

            # Draw contour onto mask
            _ = cv2.drawContours(b_mask, [contour], -1, (255, 255, 255), cv2.FILLED)

            # Create 3-channel mask
            mask3ch = cv2.cvtColor(b_mask, cv2.COLOR_GRAY2BGR)

            # Isolate object with binary mask
            isolated = cv2.bitwise_and(mask3ch, image)

            x1, y1, x2, y2 = c.boxes.xyxy.cpu().numpy().squeeze().astype(np.int32)
            # Crop image to object region
            iso_crop = isolated[y1:y2, x1:x2]

            output_path = os.path.join(output_folder, f"{base_name}_seg_{ci}.png")
            cv2.imwrite(output_path, iso_crop)

            # Add the file path to the list
            file_paths.append(output_path)

    return file_paths """


# Example usage
generated_files = draw_segmentations(
    "raining-money-gif-transparent-2.png", "segmented_images"
)

# The generated_files list now contains the file paths of the generated images
for file_path in generated_files:
    print(file_path)
