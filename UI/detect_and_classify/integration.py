import os
import time
from collections import defaultdict

import cv2
import serial

from . import detect_category
from . import opencv_feat_match as feat_match
from . import opencv_simple_poly as simple_poly

DONE_MESSAGE = "pega terminado"
SERIAL_PORT = "/dev/ttyACM0"  # Replace with your serial port
BAUD_RATE = 9600
CAMERA_NUMBER = 0

print("Connecting to Arduino...")
# Initialize serial communication
# ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
time.sleep(2)  # Wait for the connection to initialize


def capture_image_from_webcam(output_path: str):
    cap = cv2.VideoCapture(CAMERA_NUMBER)
    if not cap.isOpened():
        print("Error: Could not open webcam.")
        return None

    ret, frame = cap.read()
    if ret:
        # Save the captured frame to a file
        cv2.imwrite(output_path, frame)
        print(f"Image saved to {output_path}")
    else:
        print("Error: Could not read frame from webcam.")
        frame = None

    # Release the webcam
    cap.release()
    return frame


def convert_pixel_centroid_to_arduino(centroid):
    image_x = 3840 - 3840 / 8 - 3840 / 5
    image_y = 2160
    arduino_x = 1680
    arduino_y = 1800
    arduino_centroid_x = ((centroid[0] - 3840 / 5) / image_x) * arduino_x
    arduino_centroid_y = (centroid[1] / image_y) * arduino_y
    return arduino_x - arduino_centroid_x, arduino_y - arduino_centroid_y


def send_centroids_to_arduino(box_number, centroid):
    arduino_x, arduino_y = convert_pixel_centroid_to_arduino(centroid)

    coord_str = (
        f"pega {box_number} {str(arduino_x).zfill(4)} {str(arduino_y).zfill(4)}\n"
    )
    ser.write(coord_str.encode("utf-8"))
    print(f"Sent to Arduino: {coord_str.strip()}")
    time.sleep(0.1)  # Small delay to ensure the command is processed

    while True:
        # Read a line from the serial port
        response = ser.readline().decode("utf-8").strip()
        print(f"Received from Arduino: {response}")
        if response == DONE_MESSAGE:
            print("Expected message received. Stopping send_centroids_to_arduino.")
            break


""" def test_walk(position_x, position_y):
    coord_str = f"pega 1 {str(position_x).zfill(4)} {str(position_y).zfill(4)}"
    ser.write(coord_str.encode("utf-8"))
    print(f"Sent to Arduino: '{coord_str}'")

    while True:
        # Read a line from the serial port
        response = ser.readline().decode("utf-8").strip()
        print(f"Received from Arduino: {response}") """


def process_image_objects(image_objects, captured_image_path):
    for obj in image_objects:
        print(f"Processing image for {obj['exemplar_image_path']}...")
        centroids = feat_match.process_image_and_find_centroids(
            obj["exemplar_image_path"],
            captured_image_path,
            obj["nfeatures"],
            obj["ratio_test_threshold"],
        )
        if centroids:
            print(f"Centroids found: {centroids}")
            send_centroids_to_arduino(obj["box_id"], centroids[0])
            return True  # Centroids found
        print("No centroids found for this object")
    return False  # No centroids found


def process_polygon_objects(poly_objects, captured_image_path):
    for (color, shape), obj_list in poly_objects.items():
        print(f"Processing image for {color} {shape}...")
        centroids, file_paths = simple_poly.crop_to_largest_polygons(
            captured_image_path,
            color,
            shape,
            os.path.join("detect_and_classify", "output", "output_crop_{}.jpg"),
        )
        if centroids and file_paths:
            print(f"Centroids found: {centroids}")
            for centroid, file_path in zip(centroids, file_paths):
                obj_name = detect_category.detect(
                    file_path,
                    [
                        detect_category.Category(obj["name"], obj["descricao"])
                        for obj in obj_list
                    ],
                )
                if not obj_name:
                    print("Object is not in our categories. Continuing to next crop.")
                    continue
                identified_obj = next(
                    (obj for obj in obj_list if obj["name"] == obj_name)
                )
                send_centroids_to_arduino(
                    identified_obj["box_id"],
                    centroid,
                )
                return True  # Centroids found
        else:
            print("No centroid found for this color and shape")
    return False  # No centroids found


def take_photo_command_arduino(objects: list[dict]):
    captured_image_path = os.path.join("webcam", "webcam_photo.jpg")

    image_objects = [obj for obj in objects if obj["mode"] == "image"]
    poly_objects = defaultdict(list)

    for obj in objects:
        if obj["mode"] == "polygon":
            poly_objects[(obj["color"], obj["polygon"])].append(obj)

    # ser.write("anda 0100 0100\n".encode("utf-8"))
    print("Sent to Arduino: anda 0100 0100")
    time.sleep(5)

    while True:
        # ser.write("reinicia\n".encode("utf-8"))
        print("Sent to Arduino: reinicia")
        time.sleep(15)
        # capture_image_from_webcam(captured_image_path)

        if process_image_objects(image_objects, captured_image_path):
            continue  # Continue if centroids were found for image objects

        if process_polygon_objects(poly_objects, captured_image_path):
            continue  # Continue if centroids were found for polygon objects

        print("No centroids found, sorting ended.")
        break

    print(objects)
    return


def send_register_box_to_arduino(box_number, position_x, position_y):
    coord_str = f"registra_caixa {box_number} {str(position_x).zfill(4)} {str(position_y).zfill(4)}\n"
    # ser.write(coord_str.encode("utf-8"))
    print(f"Sent to Arduino: {coord_str.strip()}")
    time.sleep(0.1)  # Small delay to ensure the command is processed

    while True:
        # Read a line from the serial port
        # response = ser.readline().decode("utf-8").strip()
        # print(f"Received from Arduino: {response}")
        print("Stopping send_register_box_to_arduino.")
        break


def register_boxes(database_objects: list[dict]):
    for obj in database_objects:
        send_register_box_to_arduino(
            obj["box_id"], obj["position_x"], obj["position_y"]
        )


if __name__ == "__main__":
    # capture_image_from_webcam(os.path.join("webcam", "webcam_photo.jpg"))
    database_objects = [
        {
            "name": "Brazilian Real",
            "position_x": 1000,
            "position_y": 1500,
            "exemplar_image_path": os.path.join(
                "exemplar_images", "50_Brazil_real_Second_Reverse.jpeg"
            ),
            "nfeatures": 12000,
            "ratio_test_threshold": 0.7,
            "mode": "image",
            "descricao": "Banknote",
        },
        {
            "name": "Cartão de fidelidade do Tabu Club",
            "position_x": 800,
            "position_y": 1500,
            "mode": "polygon",
            "color": "white",
            "polygon": "rectangle",
            "descricao": "Cartão de fidelidade do Tabu Club, uma casa de jogos de tabuleiro",
        },
        {
            "name": "Cartão da HotZone",
            "position_x": 1200,
            "position_y": 1500,
            "mode": "polygon",
            "color": "white",
            "polygon": "rectangle",
            "descricao": "Cartão usado na HotZone para brincar nos brinquedos",
        },
    ]
    register_boxes(database_objects)
    take_photo_command_arduino(database_objects)
    # test_walk(1300, 1000)
