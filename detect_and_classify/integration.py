import time

import cv2
import opencv_feat_match as feat_match
import opencv_simple_poly as simple_poly
import serial

DONE_MESSAGE = "reiniciado"
SERIAL_PORT = "/dev/ttyACM0"  # Replace with your serial port
BAUD_RATE = 9600


def capture_image_from_webcam(output_path):
    # Open a connection to the webcam (0 is the default ID for the primary camera)
    cap = cv2.VideoCapture(0)
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


def send_centroids_to_arduino(box_x, box_y, centroid):
    serial_port = SERIAL_PORT
    baud_rate = BAUD_RATE
    print(f"Sending to Arduino: {box_x} {box_y} {centroid}")
    time.sleep(3)  # Small delay to ensure the command is processed
    print("Arduino responded: Done")
    """# Initialize serial communication
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
            break"""


def take_photo_command_arduino(objects: list[dict]):
    captured_image_path = "white_rect_and_banknote.jpg"

    image_objects = [obj for obj in objects if obj["mode"] == "image"]
    poly_objects = [obj for obj in objects if obj["mode"] == "polygon"]
    poly_characteristics = set((obj["color"], obj["shape"]) for obj in poly_objects)

    while True:
        # capture_image_from_webcam(captured_image_path)

        centroids_found = False

        for obj in image_objects:
            centroids = feat_match.process_image_and_find_centroids(
                obj["exemplar_image_path"],
                captured_image_path,
                obj["nfeatures"],
                obj["ratio_test_threshold"],
            )
            if centroids:
                send_centroids_to_arduino(obj["box_x"], obj["box_y"], centroids[0])
                centroids_found = True
                break

        if not centroids_found:
            for obj in poly_objects:
                centroids = simple_poly.process_image_and_find_centroids(
                    captured_image_path,
                    obj["color"],
                    obj["shape"],
                    "output/output_image.jpg",
                )
                if centroids:
                    send_centroids_to_arduino(obj["box_x"], obj["box_y"], centroids[0])
                    centroids_found = True
                    break

        if not centroids_found:
            print("No centroids found, sorting ended.")
            break

    return


if __name__ == "__main__":
    database_objects = [
        {
            "box_x": 1,
            "box_y": 1,
            "exemplar_image_path": "50_Brazil_real_Second_Reverse.jpeg",
            "nfeatures": 12000,
            "ratio_test_threshold": 0.7,
            "mode": "image",
            "text_description": "Banknote",
        },
        {
            "box_x": 2,
            "box_y": 2,
            "mode": "polygon",
            "color": "white",
            "shape": "rectangle",
            "text_description": "Paper",
        },
    ]
    take_photo_command_arduino(database_objects)
