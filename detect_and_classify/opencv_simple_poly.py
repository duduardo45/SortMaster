import os

import cv2
import numpy as np
import opencv_utils as utils
from shapely.geometry import Polygon

# Red
LOWER_RED_HSV_1 = np.array([0, 50, 50])
UPPER_RED_HSV_1 = np.array([10, 255, 255])
LOWER_RED_HSV_2 = np.array([170, 50, 50])
UPPER_RED_HSV_2 = np.array([180, 255, 255])

# Green
LOWER_GREEN_HSV = np.array([35, 50, 0])
UPPER_GREEN_HSV = np.array([85, 255, 255])

# Blue
LOWER_BLUE_HSV = np.array([100, 50, 50])
UPPER_BLUE_HSV = np.array([140, 255, 255])

# Yellow
LOWER_YELLOW_HSV = np.array([20, 50, 50])
UPPER_YELLOW_HSV = np.array([30, 255, 255])

# Cyan
LOWER_CYAN_HSV = np.array([85, 50, 50])
UPPER_CYAN_HSV = np.array([95, 255, 255])

# Magenta
LOWER_MAGENTA_HSV = np.array([140, 50, 50])
UPPER_MAGENTA_HSV = np.array([170, 255, 255])

# White
LOWER_WHITE_HSV = np.array([0, 0, 200])
UPPER_WHITE_HSV = np.array([180, 100, 255])

# Black
LOWER_BLACK_HSV = np.array([0, 0, 0])
UPPER_BLACK_HSV = np.array([180, 255, 120])

LOWER_BANKNOTE_HSV = np.array([8, 13, 153])
UPPER_BANKNOTE_HSV = np.array([50, 128, 230])

color_mapping = {
    "red": (LOWER_RED_HSV_1, UPPER_RED_HSV_1),
    "green": (LOWER_GREEN_HSV, UPPER_GREEN_HSV),
    "blue": (LOWER_BLUE_HSV, UPPER_BLUE_HSV),
    "yellow": (LOWER_YELLOW_HSV, UPPER_YELLOW_HSV),
    "cyan": (LOWER_CYAN_HSV, UPPER_CYAN_HSV),
    "magenta": (LOWER_MAGENTA_HSV, UPPER_MAGENTA_HSV),
    "white": (LOWER_WHITE_HSV, UPPER_WHITE_HSV),
    "black": (LOWER_BLACK_HSV, UPPER_BLACK_HSV),
    "banknote": (LOWER_BANKNOTE_HSV, UPPER_BANKNOTE_HSV),
}

ASPECT_RATIO_TOLERANCE = 10

DEFAULT_EPSILON_FACTOR = 0.02


def is_shape(approx, shape, tolerance=ASPECT_RATIO_TOLERANCE):
    if shape == "rectangle":
        if len(approx) != 4:
            return False
        (x, y, w, h) = cv2.boundingRect(approx)
        aspect_ratio = float(w) / h if h != 0 else 0
        return 1 - tolerance <= aspect_ratio <= 1 + tolerance
    elif shape == "triangle":
        return len(approx) == 3
    elif shape == "circle":
        # Approximation with a specific number of vertices
        perimeter = cv2.arcLength(approx, True)
        area = cv2.contourArea(approx)
        circularity = 4 * np.pi * (area / (perimeter**2))
        return 0.7 <= circularity <= 1.3
    else:
        raise ValueError(f"Unsupported shape: {shape}")


def find_and_draw_polygons_by_color(
    scene_image: np.ndarray,
    lower_color: np.ndarray,
    upper_color: np.ndarray,
    shape: str = "rectangle",
    epsilon_factor=DEFAULT_EPSILON_FACTOR,
) -> list[tuple[Polygon, np.ndarray]]:
    hsv_image = cv2.cvtColor(scene_image, cv2.COLOR_BGR2HSV)
    binary_mask = cv2.inRange(hsv_image, lower_color, upper_color)
    mask_with_polygons = cv2.cvtColor(binary_mask, cv2.COLOR_GRAY2BGR)

    contours, _ = cv2.findContours(binary_mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    polygons = []
    for contour in contours:
        # if contour area is too small, ignore
        if cv2.contourArea(contour) < 100:
            continue
        perimeter = cv2.arcLength(contour, True)
        epsilon = epsilon_factor * perimeter
        approx = cv2.approxPolyDP(contour, epsilon, True)

        if is_shape(approx, shape):
            print("found shape")
            polygons.append((Polygon(approx.reshape(-1, 2)), approx))
            if shape == "circle":
                (x, y), radius = cv2.minEnclosingCircle(contour)
                center = (int(x), int(y))
                radius = int(radius)
                cv2.circle(mask_with_polygons, center, radius, (255, 0, 0), 2)
            else:
                cv2.polylines(mask_with_polygons, [approx], True, (255, 0, 0), 2)

    return polygons


def find_and_draw_largest_colored_polygons(
    scene_image_path, lower_color, upper_color, output_filename, shape="rectangle"
) -> tuple[np.ndarray, list[tuple[Polygon, np.ndarray]]]:
    scene_image = cv2.imread(scene_image_path)

    polygons = find_and_draw_polygons_by_color(
        scene_image, lower_color, upper_color, shape
    )
    polygon_groups = utils.group_overlapping_polygons(polygons)
    largest_polygons = [max(group, key=lambda x: x[0].area) for group in polygon_groups]

    cv2.imwrite(output_filename, scene_image)
    return scene_image, largest_polygons


def process_image_and_find_centroids(
    scene_image_path: str,
    color: str,
    shape: str,
    output_filename: str,
) -> list[tuple[float, float]]:
    # Find and draw colored polygons
    lower_color, upper_color = color_mapping[color]
    _, largest_polygons = find_and_draw_largest_colored_polygons(
        scene_image_path, lower_color, upper_color, output_filename, shape
    )

    # Find centroids of the largest polygons
    centroids = utils.find_centroids(largest_polygons)

    return centroids


if __name__ == "__main__":
    image_path = "white_rect_and_banknote.jpg"
    output_filename = "output/output_image.jpg"
    centroids = process_image_and_find_centroids(
        image_path,
        "white",
        "rectangle",
        output_filename,
    )
    scene_image = cv2.imread(image_path, cv2.IMREAD_COLOR)
    for centroid in centroids:
        cv2.circle(
            scene_image, (int(centroid[0]), int(centroid[1])), 5, (0, 0, 255), -1
        )
        cv2.putText(
            scene_image,
            f"({int(centroid[0])}, {int(centroid[1])})",
            (int(centroid[0]) + 10, int(centroid[1])),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (0, 0, 255),
            1,
        )

    # Save and display the result image
    cv2.imwrite(output_filename, scene_image)
    if os.name == "nt":  # For Windows
        os.startfile(output_filename)
    elif os.uname()[0] == "Darwin":  # For macOS
        os.system(f'open "{output_filename}"')
    else:  # For Linux and other Unix-like OS
        os.system(f'xdg-open "{output_filename}"')

    # Print centroids
    print("Centroids of important polygons:", centroids)
