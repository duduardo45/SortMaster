import os
from typing import Any

import cv2
import numpy as np
import opencv_utils as utils
from shapely.geometry import Polygon

output_filename = "output/feat_match_processed_image.jpg"

MIN_MATCH_COUNT = 10


def register_exemplar(image_path, nfeatures):
    """Registers an exemplar by extracting its features and keypoints."""
    image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    orb = cv2.ORB_create(nfeatures=nfeatures)
    keypoints, descriptors = orb.detectAndCompute(image, None)
    return image, keypoints, descriptors


def detect_and_compute_keypoints(image_path, nfeatures) -> tuple:
    image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    orb = cv2.ORB_create(nfeatures=nfeatures)
    keypoints, descriptors = orb.detectAndCompute(image, None)
    return image, keypoints, descriptors


def match_descriptors(
    exemplar_descriptors: np.ndarray,
    scene_descriptors: np.ndarray,
    ratio_test_threshold: float,
) -> list[Any]:
    bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=False)
    matches = bf.knnMatch(exemplar_descriptors, scene_descriptors, k=2)

    good_matches = []
    for m, n in matches:
        if m.distance < ratio_test_threshold * n.distance:
            good_matches.append(m)
    return good_matches


def compute_homography_polygons(
    exemplar_keypoints, scene_keypoints, good_matches, exemplar_image
) -> list[tuple[Polygon, np.ndarray]]:
    homography_polygons = []
    while len(good_matches) >= MIN_MATCH_COUNT:
        src_pts = np.float32(
            [exemplar_keypoints[m.queryIdx].pt for m in good_matches]
        ).reshape(-1, 2)
        dst_pts = np.float32(
            [scene_keypoints[m.trainIdx].pt for m in good_matches]
        ).reshape(-1, 2)

        M, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 5.0)
        matchesMask = mask.ravel().tolist()

        h, w = exemplar_image.shape
        pts = np.float32([[0, 0], [0, h - 1], [w - 1, h - 1], [w - 1, 0]]).reshape(
            -1, 1, 2
        )
        dst = cv2.perspectiveTransform(pts, M)

        homography_polygons.append((Polygon(dst.reshape(-1, 2)), dst))

        good_matches = [
            m for m, mask_value in zip(good_matches, matchesMask) if mask_value == 0
        ]
    return homography_polygons


def match_features(
    exemplar_image,
    exemplar_keypoints,
    exemplar_descriptors: np.ndarray,
    scene_image_path: str,
    nfeatures: int,
    ratio_test_threshold: float,
    output_filename: str,
) -> tuple[Any, list[tuple[Polygon, np.ndarray]]]:
    scene_image, scene_keypoints, scene_descriptors = detect_and_compute_keypoints(
        scene_image_path, nfeatures
    )
    good_matches = match_descriptors(
        exemplar_descriptors, scene_descriptors, ratio_test_threshold
    )
    homography_polygons = compute_homography_polygons(
        exemplar_keypoints, scene_keypoints, good_matches, exemplar_image
    )
    polygon_groups = utils.group_overlapping_polygons(homography_polygons)
    largest_polygons = [max(group, key=lambda x: x[0].area) for group in polygon_groups]
    scene_image = utils.draw_polygons_groups(scene_image, polygon_groups)

    result_image = cv2.drawMatches(
        exemplar_image,
        exemplar_keypoints,
        scene_image,
        scene_keypoints,
        good_matches,
        None,
    )

    cv2.imwrite(output_filename, result_image)
    return result_image, largest_polygons


def process_image_and_find_centroids(
    exemplar_image_path, scene_image_path, nfeatures, ratio_test_threshold
) -> list[tuple[float, float]]:
    exemplar_image, exemplar_keypoints, exemplar_descriptors = register_exemplar(
        exemplar_image_path, nfeatures
    )

    # Match features and get largest polygons
    _, largest_polygons = match_features(
        exemplar_image,
        exemplar_keypoints,
        exemplar_descriptors,
        scene_image_path,
        nfeatures,
        ratio_test_threshold,
        output_filename,
    )
    # Find centroids of the largest polygons
    centroids = utils.find_centroids(largest_polygons)

    return centroids


if __name__ == "__main__":
    scene_image_path = "white_rect_and_banknote.jpg"
    centroids = process_image_and_find_centroids(
        "50_Brazil_real_Second_Reverse.jpeg", scene_image_path, 12000, 0.7
    )
    scene_image = cv2.imread(scene_image_path, cv2.IMREAD_COLOR)

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
