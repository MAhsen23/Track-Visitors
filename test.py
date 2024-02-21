import cv2
from threading import Thread
import time

import numpy as np
from keras_facenet import FaceNet
from ultralytics import YOLO
import DB_Connection

conn_string = DB_Connection.conn_string()


def detectYolo(source):
    model = YOLO("F:\TrainModel\models\yolov8s.pt")
    classes = [0, 1]

    conf_thresh = 0.5
    results = model.predict(source=source, classes=classes, conf=conf_thresh)

    boundingBoxes = []
    for result in results[0].boxes.data:
        boundingBoxes.append(result.tolist())
    return boundingBoxes


model = FaceNet()
embeddings_path = 'embeddings.npy'
labels_path = 'labels.npy'

known_embeddings = np.load(embeddings_path)
known_labels = np.load(labels_path)


def recognizeOneBoundingBox(frame):
    faces = model.extract(frame, threshold=0.50)
    test_embeddings = np.array([face['embedding'] for face in faces])

    threshold_distance = 0.95

    for i, test_embedding in enumerate(test_embeddings):
        distances = np.linalg.norm(known_embeddings - test_embedding, axis=1)
        closest_match_index = np.argmin(distances)
        closest_match_distance = distances[closest_match_index]
        closest_match_label = known_labels[closest_match_index]

        if closest_match_distance < threshold_distance:
            return closest_match_label


class VideoPlayer:
    def __init__(self, video_path):
        self.video_path = video_path
        self.video = cv2.VideoCapture(video_path)
        self.current_frame = None
        self.playing = False
        self.frame_counter = 0

    def process_frame(self, frame):

        bounding_boxes = detectYolo(frame)
        if bounding_boxes is not None:
            for bounding_box in bounding_boxes:
                x1, y1, x2, y2 = map(int, bounding_box[:4])
                color = (0, 255, 0)
                thickness = 2
                cv2.rectangle(frame, (x1, y1), (x2, y2), color, thickness)
                bounding_box_image = frame[y1:y2, x1:x2]
                result = recognizeOneBoundingBox(bounding_box_image)
                print("Detected Person", result)

                font = cv2.FONT_HERSHEY_SIMPLEX
                font_scale = 1.1
                text_color = (255, 255, 255)
                text_thickness = 2
                cv2.putText(frame, result, (x1, y1 - 10), font, font_scale, text_color, text_thickness)

        return frame

    def play(self):
        self.playing = True
        while self.playing:
            ret, frame = self.video.read()
            if not ret:
                break
            self.current_frame = frame

            self.frame_counter += 1

            if self.frame_counter % 30 == 0:
                processed_frame = self.process_frame(self.current_frame)

                height, width = processed_frame.shape[:2]
                scale = min(1, 720 / height, 1280 / width)
                resized_frame = cv2.resize(processed_frame, None, fx=scale, fy=scale)
                cv2.imshow("Video", resized_frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break

        self.video.release()
        cv2.destroyAllWindows()

    def stop(self):
        self.playing = False


if __name__ == "__main__":
    video_path = "CamerasVideo/25.webm"
    player = VideoPlayer(video_path)
    player_thread = Thread(target=player.play)
    player_thread.start()
