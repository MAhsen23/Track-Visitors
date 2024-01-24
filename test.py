from ultralytics import YOLO
import cv2

def detectYolo(source):
    model = YOLO("yolov8m-face.pt")

    conf_thresh = 0.5
    results = model.predict(source=source, conf=conf_thresh)

    boundingBoxes = []
    for result in results[0].boxes.data:
        boundingBoxes.append(result.tolist())
    return boundingBoxes

image = cv.imread("Unknown_Persons//26//20240119003149.jpg")
bounding_box = detectYolo(image)

if bounding_box is not None:
    x1, y1, x2, y2 = map(int, bounding_box[:4])
    bounding_box_image = image[y1:y2, x1:x2]
    cv2.imwrite()
