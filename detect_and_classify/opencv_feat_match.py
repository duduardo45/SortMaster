import os

import cv2
import numpy as np
from shapely.geometry import Polygon

output_filename = "output/processed_image.jpg"


def register_exemplar(image_path, nfeatures):
    """Registers an exemplar by extracting its features and keypoints."""
    image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    orb = cv2.ORB_create(nfeatures=nfeatures)
    keypoints, descriptors = orb.detectAndCompute(image, None)
    return image, keypoints, descriptors


def match_features(
    exemplar_image,
    exemplar_keypoints,
    exemplar_descriptors,
    scene_image_path,
    nfeatures,
    ratio_test_threshold,
    output_filename,
):
    scene_image = cv2.imread(scene_image_path, cv2.IMREAD_GRAYSCALE)
    orb = cv2.ORB_create(nfeatures=nfeatures)
    scene_keypoints, scene_descriptors = orb.detectAndCompute(scene_image, None)

    bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=False)
    matches = bf.knnMatch(exemplar_descriptors, scene_descriptors, k=2)

    good_matches = []
    for m, n in matches:
        if m.distance < ratio_test_threshold * n.distance:
            good_matches.append(m)

    found_matches = []
    MIN_MATCH_COUNT = 10
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

    # Group overlapping polygons
    polygon_groups = []
    for polygon, dst in homography_polygons:
        added_to_group = False
        for group in polygon_groups:
            if any(polygon.intersects(p[0]) for p in group):
                group.append((polygon, dst))
                added_to_group = True
                break
        if not added_to_group:
            polygon_groups.append([(polygon, dst)])

    # Determine the largest polygon in each group
    largest_polygons = []
    for group in polygon_groups:
        largest_polygon = max(group, key=lambda x: x[0].area)
        largest_polygons.append(largest_polygon)

    # Draw the polygons on the image
    for group in polygon_groups:
        for polygon, dst in group:
            color = (
                (0, 255, 0)
                if polygon == max(group, key=lambda x: x[0].area)[0]
                else (255, 255, 255)
            )
            scene_image = cv2.polylines(
                scene_image, [np.int32(dst)], True, color, 3, cv2.LINE_AA
            )

    result_image = cv2.drawMatches(
        exemplar_image,
        exemplar_keypoints,
        scene_image,
        scene_keypoints,
        found_matches,
        None,
    )

    cv2.imwrite(output_filename, result_image)
    return result_image, largest_polygons


def find_centroids(largest_polygons):
    """Finds the centroids of the largest polygons."""
    centroids = []
    for polygon, _ in largest_polygons:
        centroid = polygon.centroid
        centroids.append((centroid.x, centroid.y))
    return centroids


def process_image_and_find_centroids(
    exemplar_image_path, scene_image_path, nfeatures, ratio_test_threshold
):
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
    centroids = find_centroids(largest_polygons)

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

    return centroids


process_image_and_find_centroids(
    "50_Brazil_real_Second_Reverse.jpeg", "even_more_more_currency.jpg", 12000, 0.7
)
