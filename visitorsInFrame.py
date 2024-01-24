from keras_facenet import FaceNet
import numpy as np
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


def returnVisitorsInFrame(frame):

    visitorsFoundInOneFrame = []
    bounding_boxes = detectYolo(frame)
    if bounding_boxes is not None:

        for bounding_box in bounding_boxes:
            x1, y1, x2, y2 = map(int, bounding_box[:4])
            bounding_box_image = frame[y1:y2, x1:x2]
            visitorFoundId = recognizeOneBoundingBox(bounding_box_image)
            if visitorFoundId is not None and visitorFoundId not in visitorsFoundInOneFrame:
                visitorsFoundInOneFrame.append(visitorFoundId)

    return visitorsFoundInOneFrame

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



