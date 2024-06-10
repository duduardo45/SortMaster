""" import os

import cv2
import numpy as np

output_folder = "output"
os.makedirs(output_folder, exist_ok=True)
output_filename = os.path.join(output_folder, "processed_image.jpg")


def register_exemplar(image_path):
    #Registers an exemplar by extracting its features and keypoints.
    image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    orb = cv2.ORB_create(nfeatures=2000)  # Increased number of features
    keypoints, descriptors = orb.detectAndCompute(image, None)
    return image, keypoints, descriptors


def match_features(
    exemplar_image, exemplar_keypoints, exemplar_descriptors, scene_image_path
):
    #Matches features between the exemplar and a scene image, and finds the object using homography.
    scene_image = cv2.imread(scene_image_path, cv2.IMREAD_GRAYSCALE)
    orb = cv2.ORB_create(nfeatures=2000)  # Increased number of features
    scene_keypoints, scene_descriptors = orb.detectAndCompute(scene_image, None)

    bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=False)
    matches = bf.knnMatch(exemplar_descriptors, scene_descriptors, k=2)

    # Apply ratio test as per Lowe's paper
    good_matches = []
    for m, n in matches:
        if m.distance < 0.7 * n.distance:  # Adjusted ratio test threshold
            good_matches.append(m)

    # Continue searching for multiple homographies
    found_matches = []
    MIN_MATCH_COUNT = 10  # Minimum number of matches to find a valid homography

    while len(good_matches) >= MIN_MATCH_COUNT:
        src_pts = np.float32(
            [exemplar_keypoints[m.queryIdx].pt for m in good_matches]
        ).reshape(-1, 2)
        dst_pts = np.float32(
            [scene_keypoints[m.trainIdx].pt for m in good_matches]
        ).reshape(-1, 2)

        # Find homography
        M, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 5.0)
        matchesMask = mask.ravel().tolist()

        h, w = exemplar_image.shape
        pts = np.float32([[0, 0], [0, h - 1], [w - 1, h - 1], [w - 1, 0]]).reshape(
            -1, 1, 2
        )
        dst = cv2.perspectiveTransform(pts, M)

        scene_image = cv2.polylines(
            scene_image, [np.int32(dst)], True, 255, 3, cv2.LINE_AA
        )

        # Filter out the used matches
        good_matches = [
            m for m, mask_value in zip(good_matches, matchesMask) if mask_value == 0
        ]

    # Draw all matches
    result_image = cv2.drawMatches(
        exemplar_image,
        exemplar_keypoints,
        scene_image,
        scene_keypoints,
        found_matches,
        None,
    )

    cv2.imwrite(output_filename, result_image)

    # Open the image using the default image viewer
    if os.name == "nt":  # For Windows
        os.startfile(output_filename)
    elif os.uname()[0] == "Darwin":  # For macOS
        os.system(f'open "{output_filename}"')
    else:  # For Linux and other Unix-like OS
        os.system(f'xdg-open "{output_filename}"')


if __name__ == "__main__":
    exemplar_image_path = "50_Brazil_real_Second_Reverse.jpeg"
    scene_image_path = "even_more_more_currency.jpg"

    exemplar_image, exemplar_keypoints, exemplar_descriptors = register_exemplar(
        exemplar_image_path
    )
    match_features(
        exemplar_image, exemplar_keypoints, exemplar_descriptors, scene_image_path
    )
 """

import tkinter as tk

from debug_gui import setup_gui


def main():
    # Create the main window
    root = tk.Tk()
    root.title("Image Matching Debugger")

    # Setup the GUI
    setup_gui(root)

    # Run the application
    root.mainloop()


if __name__ == "__main__":
    main()
