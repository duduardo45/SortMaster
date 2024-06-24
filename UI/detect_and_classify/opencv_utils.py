import cv2
import numpy as np
from shapely.geometry import Polygon


def find_centroids(
    largest_polygons: list[tuple[Polygon, np.ndarray]]
) -> list[tuple[float, float]]:
    """Finds the centroids of the largest polygons."""
    centroids = []
    for polygon, _ in largest_polygons:
        centroid = polygon.centroid
        centroids.append((centroid.x, centroid.y))
    return centroids


def draw_polygons_groups(
    scene_image, polygon_groups: list[list[tuple[Polygon, np.ndarray]]]
):
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
    return scene_image


def group_overlapping_polygons(
    homography_polygons: list[tuple[Polygon, np.ndarray]]
) -> list[list[tuple[Polygon, np.ndarray]]]:
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
    return polygon_groups
