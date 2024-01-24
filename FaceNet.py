from keras_facenet import FaceNet
import cv2
import os
import numpy as np
from scipy import spatial
import tensorflow as tf

def training():
    model = FaceNet()

    dataset_path = r'images'
    embeddings_path = 'embeddings.npy'
    labels_path = 'labels.npy'

    embeddings = []
    labels = []

    for subdirectory in os.listdir(dataset_path):
        subdirectory_path = os.path.join(dataset_path, subdirectory)
        for filename in os.listdir(subdirectory_path):
            image_path = os.path.join(subdirectory_path, filename)

            image = cv2.imread(image_path)
            faces = model.extract(image, threshold=0.95)

            for face in faces:
                try:
                    embedding = face['embedding']
                    embeddings.append(embedding)
                    labels.append(subdirectory)
                except KeyError:
                    print("Cannot extract embedding for face")

    embeddings = np.array(embeddings)
    labels = np.array(labels)
    np.save(embeddings_path, embeddings)
    np.save(labels_path, labels)