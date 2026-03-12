import cv2
import numpy as np
from io import BytesIO


def process_image(image_bytes: bytes, dimensions=None):

    img = cv2.imdecode(np.frombuffer(image_bytes, np.uint8), -1)

    if img is None:
        raise ValueError("Invalid image")

    if dimensions:
        img = cv2.resize(img, dimensions)

    success, encoded = cv2.imencode(".jpg", img)

    if not success:
        raise ValueError("Image encoding failed")

    return encoded.tobytes()

