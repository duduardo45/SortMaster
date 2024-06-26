import os

import cv2
import numpy as np
from shapely.geometry import Polygon

from . import opencv_utils as utils

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

# Purple
LOWER_PURPLE_HSV = np.array([125, 50, 50])
UPPER_PURPLE_HSV = np.array([155, 255, 255])

# Magenta
LOWER_MAGENTA_HSV = np.array([140, 50, 50])
UPPER_MAGENTA_HSV = np.array([170, 255, 255])

# Orange
LOWER_ORANGE_HSV = np.array([10, 50, 50])
UPPER_ORANGE_HSV = np.array([25, 255, 255])

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
    "purple": (LOWER_PURPLE_HSV, UPPER_PURPLE_HSV),
    "orange": (LOWER_ORANGE_HSV, UPPER_ORANGE_HSV),
}

ASPECT_RATIO_TOLERANCE = 50

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
                cv2.circle(scene_image, center, radius, (255, 0, 0), 2)
            else:
                cv2.polylines(scene_image, [approx], True, (255, 0, 0), 2)

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


def crop_image_to_polygon(
    image: np.ndarray, polygon: Polygon, margin: int = 20
) -> np.ndarray:
    min_x, min_y, max_x, max_y = polygon.bounds
    min_x, min_y, max_x, max_y = map(int, [min_x, min_y, max_x, max_y])

    # Add margin
    min_x = max(min_x - margin, 0)
    min_y = max(min_y - margin, 0)
    max_x = min(max_x + margin, image.shape[1])
    max_y = min(max_y + margin, image.shape[0])

    cropped_image = image[min_y:max_y, min_x:max_x]
    return cropped_image


def crop_to_largest_polygons(
    scene_image_path: str,
    color: str,
    shape: str,
    output_crop_filename_template: str,
) -> tuple[list[tuple[float, float]], list[str]] | tuple[None, None]:
    lower_color, upper_color = color_mapping[color]
    scene_image, largest_polygons = find_and_draw_largest_colored_polygons(
        scene_image_path,
        lower_color,
        upper_color,
        "output/simple_poly_processed_image_in_crop.jpg",
        shape,
    )

    if largest_polygons:
        centroids = utils.find_centroids(largest_polygons)
        cropped_image_paths = []

        for i, polygon in enumerate(largest_polygons):
            cropped_image = crop_image_to_polygon(scene_image, polygon[0])
            output_crop_filename = output_crop_filename_template.format(i)
            cv2.imwrite(output_crop_filename, cropped_image)
            cropped_image_paths.append(output_crop_filename)

        return centroids, cropped_image_paths
    else:
        print("No polygons found.")
        return None, None


if __name__ == "__main__":
    image_path = "UI/detect_and_classify/test_images/smartphone_and_business_card.jpg"
    output_filename = "output/simple_poly_processed_image.jpg"
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
