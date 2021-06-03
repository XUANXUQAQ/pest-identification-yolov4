import base64
import os

from PIL import Image

from yolo import YOLO

yolo = YOLO()


# noinspection PyBroadException
def predict_img(image_path):
    try:
        parent_path = os.path.dirname(image_path)
        image_name = os.path.basename(image_path)
        processed_name = os.path.join(parent_path, "processed_" + image_name)
        image = Image.open(image_path)
        classes_statistics, r_image = yolo.detect_image(image)
        r_image.save(processed_name)
        with open(processed_name, 'rb') as f:
            base64_str = str(base64.b64encode(f.read()), encoding='utf-8')
        return classes_statistics, base64_str
    except Exception as e:
        print(e)
        return {"error": ""}, ''


def update_model():
    global yolo
    yolo = YOLO()


if __name__ == '__main__':
    statistics, image = predict_img(r'img/test.jpg')
    print(statistics)
