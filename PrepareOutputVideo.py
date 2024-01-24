import pyodbc
from keras_facenet import FaceNet
import cv2
import numpy as np
from ultralytics import YOLO
import time

conn_string = 'Driver={SQL Server};Server=DESKTOP-TV1U6PA\\SQLEXPRESS;Database=TrackBIITVisitors;Uid=sa;Pwd=123456;'
idNames = {}

def detectYolo(source):
    model = YOLO("F:\TrainModel\models\yolov8s.pt")
    classes = [0, 1]

    conf_thresh = 0.5
    results = model.predict(source=source, classes=classes, conf=conf_thresh)

    boundingBoxes = []
    print(len(results[0].boxes.data))
    for result in results[0].boxes.data:
        boundingBoxes.append(result.tolist())
    return boundingBoxes


def detectPersonName(frame):

    model = FaceNet()
    embeddings_path = 'embeddings.npy'
    labels_path = 'labels.npy'

    known_embeddings = np.load(embeddings_path)
    known_labels = np.load(labels_path)

    faces = model.extract(frame, threshold=0.50)
    test_embeddings = np.array([face['embedding'] for face in faces])

    threshold_distance = 0.95

    for i, test_embedding in enumerate(test_embeddings):
        distances = np.linalg.norm(known_embeddings - test_embedding, axis=1)
        closest_match_index = np.argmin(distances)
        closest_match_distance = distances[closest_match_index]
        closest_match_label = known_labels[closest_match_index]

        if closest_match_distance < threshold_distance:

            if closest_match_label in idNames:

                return idNames[closest_match_label]

            else:
                query = f"SELECT name,phone FROM [Visitor] where id={closest_match_label}"
                with pyodbc.connect(conn_string) as conn:
                    with conn.cursor() as cursor:
                        cursor.execute(query)
                        columns = [column[0] for column in cursor.description]
                        rows = [dict(zip(columns, row)) for row in cursor.fetchall()]

                name = rows[0]['name']
                idNames[closest_match_label] = name
                return name
        else:
            return "Unknown"


def detect_persons_in_video(video_path):
    video_capture = cv2.VideoCapture(video_path)
    frame_width = int(video_capture.get(3))
    frame_height = int(video_capture.get(4))
    noOfFrames = video_capture.get(cv2.CAP_PROP_FRAME_COUNT)
    fps = video_capture.get(cv2.CAP_PROP_FPS)

    skipFrames = fps
    print("Total frames to process in the video:",int(noOfFrames/skipFrames))

    output_video_path = "output_video_result.avi"
    output_video_writer = cv2.VideoWriter(output_video_path, cv2.VideoWriter_fourcc(*'XVID'), 1, (frame_width, frame_height))

    frameCounter = 0;
    processedFrames = 0;

    while video_capture.isOpened():
        ret, frame = video_capture.read()
        if not ret:
            break

        frameCounter += 1

        if frameCounter%skipFrames==0:

            print(f"\n===========================Processing frame {processedFrames+1}, Remaining frames are {int(noOfFrames/skipFrames)-(processedFrames+1)}===========================")
            processedFrames+=1

            bounding_boxes = detectYolo(frame)
            if bounding_boxes is not None:

                for bounding_box in bounding_boxes:
                    x1, y1, x2, y2 = map(int, bounding_box[:4])
                    color = (0, 255, 0)
                    thickness = 2
                    cv2.rectangle(frame, (x1, y1), (x2, y2), color, thickness)

                    bounding_box_image = frame[y1:y2, x1:x2]
                    person_name=detectPersonName(bounding_box_image)
                    if person_name is None:
                        text = "Unknown"
                    else:
                        text = person_name

                    font = cv2.FONT_HERSHEY_SIMPLEX
                    font_scale = 1.1
                    text_color = (255, 255, 255)
                    text_thickness = 2
                    cv2.putText(frame, text, (x1, y1 - 10), font, font_scale, text_color, text_thickness)

                output_video_writer.write(frame)

    video_capture.release()
    output_video_writer.release()
    cv2.destroyAllWindows()

#detect_persons_in_video(video_path="testing/uniVideo2.mp4")
