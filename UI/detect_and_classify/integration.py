import os
import time
from collections import defaultdict

import cv2
import detect_category
import opencv_feat_match as feat_match
import opencv_simple_poly as simple_poly
import serial

DONE_MESSAGE = "reiniciado"
SERIAL_PORT = "/dev/ttyACM0"  # Replace with your serial port
BAUD_RATE = 9600

print("Connecting to Arduino...")
# Initialize serial communication
ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
time.sleep(2)  # Wait for the connection to initialize

ser.write("anda 0100 0100\n".encode("utf-8"))

time.sleep(5)

ser.write("reinicia\n".encode("utf-8"))
time.sleep(10)
print("Sent to Arduino: reinicia")


def capture_image_from_webcam(output_path):
    cap = cv2.VideoCapture(2)
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


def send_centroids_to_arduino(position_x, position_y, centroid):
    print(f"Sending to Arduino: {position_x} {position_y} {centroid}")
    time.sleep(3)  # Small delay to ensure the command is processed
    print("Arduino responded: Done")
    # Initialize serial communication
    ser = serial.Serial(serial_port, baud_rate, timeout=1)
    time.sleep(2)  # Wait for the connection to initialize

    coord_str = (
        f"pega {box_number} {str(centroid[0]).zfill(4)},{str(centroid[1]).zfill(4)}\n"
    )
    ser.write(coord_str.encode("utf-8"))
    print(f"Sent to Arduino: {coord_str.strip()}")
    time.sleep(0.1)  # Small delay to ensure the command is processed

    while True:
        # Read a line from the serial port
        response = ser.readline().decode("utf-8").strip()
        print(f"Received from Arduino: {response}")
        if response == DONE_MESSAGE:
            print("Expected message received. Closing serial connection.")
            break


def test_walk(position_x, position_y):
    coord_str = f"pega 1 {str(position_x).zfill(4)} {str(position_y).zfill(4)}\n"
    ser.write(coord_str.encode("utf-8"))
    print(f"Sent to Arduino: {coord_str.strip()}")

    while True:
        # Read a line from the serial port
        response = ser.readline().decode("utf-8").strip()
        print(f"Received from Arduino: {response}")


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
            send_centroids_to_arduino(
                obj["position_x"], obj["position_y"], centroids[0]
            )
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
                    identified_obj["position_x"],
                    identified_obj["position_y"],
                    centroid,
                )
                return True  # Centroids found
        else:
            print("No centroid found for this color and shape")
    return False  # No centroids found


def take_photo_command_arduino(objects: list[dict]):
    captured_image_path = os.path.join(
        "detect_and_classify", "test_images", "dois_white_rects.jpg"
    )

    image_objects = [obj for obj in objects if obj["mode"] == "image"]
    poly_objects = defaultdict(list)

    for obj in objects:
        if obj["mode"] == "polygon":
            poly_objects[(obj["color"], obj["polygon"])].append(obj)

    while True:
        # capture_image_from_webcam(captured_image_path)

        if process_image_objects(image_objects, captured_image_path):
            break  # Stop if centroids were found for image objects

        if process_polygon_objects(poly_objects, captured_image_path):
            break  # Stop if centroids were found for polygon objects

        print("No centroids found, sorting ended.")
        break

    print(objects)
    return


if __name__ == "__main__":
    capture_image_from_webcam(os.path.join("webcam", "webcam_photo.jpg"))
    database_objects = [
        {
            "name": "Brazilian Real",
            "position_x": 1,
            "position_y": 1,
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
            "position_x": 2,
            "position_y": 2,
            "mode": "polygon",
            "color": "white",
            "polygon": "rectangle",
            "descricao": "Cartão de fidelidade do Tabu Club, uma casa de jogos de tabuleiro",
        },
        {
            "name": "Cartão da HotZone",
            "position_x": 3,
            "position_y": 3,
            "mode": "polygon",
            "color": "white",
            "polygon": "rectangle",
            "descricao": "Cartão usado na HotZone para brincar nos brinquedos",
        },
    ]
    # take_photo_command_arduino(database_objects)
    test_walk(1000, 1000)
