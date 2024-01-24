import datetime
import os
import pyodbc
from keras_facenet import FaceNet
import cv2
import numpy as np
from ultralytics import YOLO

import DB_Connection
conn_string = DB_Connection.conn_string()

idNames = {}

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



def recognizeOneVisitorInVideo(video_filename,visitor_id,camera_name,camera_id):

    visitorFound = False

    cap = cv2.VideoCapture(video_filename)
    fps = cap.get(cv2.CAP_PROP_FPS)
    frameCounter = 1

    while cap.isOpened():
        ret, frame = cap.read()
        if ret:
            frameCounter += 1
            if frameCounter % int(fps) == 0:

                bounding_boxes = detectYolo(frame)

                if bounding_boxes is not None:

                    for bounding_box in bounding_boxes:
                        x1, y1, x2, y2 = map(int, bounding_box[:4])
                        color = (0, 255, 0)
                        thickness = 2
                        cv2.rectangle(frame, (x1, y1), (x2, y2), color, thickness)

                        bounding_box_image = frame[y1:y2, x1:x2]
                        result = recognizeOneVisitorFrame(bounding_box_image,visitor_id)
                        if result:

                            visitorFound=True

                            name="";
                            if visitor_id in idNames:
                                name = idNames[visitor_id]
                            else:
                                query = f"SELECT name,phone FROM [Visitor] where id={visitor_id}"
                                with pyodbc.connect(conn_string) as conn:
                                    with conn.cursor() as cursor:
                                        cursor.execute(query)
                                        columns = [column[0] for column in cursor.description]
                                        rows = [dict(zip(columns, row)) for row in cursor.fetchall()]

                                name = rows[0]['name']
                                idNames[visitor_id] = name

                            font = cv2.FONT_HERSHEY_SIMPLEX
                            font_scale = 1.1
                            text_color = (255, 255, 255)
                            text_thickness = 2
                            cv2.putText(frame, name, (x1, y1 - 10), font, font_scale, text_color, text_thickness)

                            if visitorFound:
                                frame_filename = os.path.join('CamerasResult', f"{visitor_id}_{camera_name}.jpg")
                                cv2.imwrite(frame_filename, frame)
                                return [visitorFound]

                        else:
                            unknown_persons_folder = os.path.join('Unknown_Persons', str(camera_id))
                            if not os.path.exists(unknown_persons_folder):
                                os.makedirs(unknown_persons_folder)

                            timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
                            image_filename = os.path.join(unknown_persons_folder, f"{timestamp}.jpg")
                            cv2.imwrite(image_filename, bounding_box_image)
        else:
            break

    cap.release()
    return [visitorFound]




def recognizeOneVisitorFrame(frame, visitor_id):
    faces = model.extract(frame, threshold=0.50)
    test_embeddings = np.array([face['embedding'] for face in faces])

    threshold_distance = 0.95

    for i, test_embedding in enumerate(test_embeddings):
        distances = np.linalg.norm(known_embeddings - test_embedding, axis=1)
        closest_match_index = np.argmin(distances)
        closest_match_distance = distances[closest_match_index]
        closest_match_label = known_labels[closest_match_index]

        if closest_match_distance < threshold_distance:
            if closest_match_label == visitor_id:
                return True
