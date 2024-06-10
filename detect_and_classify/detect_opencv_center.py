import os

import cv2

output_folder = "output"
os.makedirs(output_folder, exist_ok=True)
output_filename = os.path.join(output_folder, "processed_image.jpg")

# Load the image
image = cv2.imread("currency_objects.jpg")

# Convert to grayscale
gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

# Apply Gaussian Blur
blurred = cv2.GaussianBlur(gray, (11, 11), 0)

# Apply thresholding
_, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

# Find contours in the binary image
contours, _ = cv2.findContours(thresh, cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)


for contour in contours:
    if cv2.contourArea(contour) < 50000:
        continue

    M = cv2.moments(contour)
    if M["m00"] != 0:
        cX = int(M["m10"] / M["m00"])
        cY = int(M["m01"] / M["m00"])

        cv2.circle(image, (cX, cY), 5, (255, 0, 0), -1)
        cv2.putText(
            image,
            "centroid",
            (cX - 25, cY - 25),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (255, 0, 0),
            2,
        )

        x, y, w, h = cv2.boundingRect(contour)
        cv2.rectangle(image, (x, y), (x + w, y + h), (0, 255, 0), 2)

cv2.imwrite(output_filename, image)

# Open the image using the default image viewer
if os.name == "nt":  # For Windows
    os.startfile(output_filename)
elif os.uname()[0] == "Darwin":  # For macOS
    os.system(f'open "{output_filename}"')
else:  # For Linux and other Unix-like OS
    os.system(f'xdg-open "{output_filename}"')
