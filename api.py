import os

from flask import Flask, jsonify, request
import predict
import utils.sha1_utils as sha1

app = Flask(__name__)
UPLOAD_FOLDER = 'img'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
basedir = os.path.abspath(os.path.dirname(__file__))
ALLOWED_EXTENSIONS = {'png', 'jpg', 'JPG', 'PNG', 'gif', 'GIF'}

pictures = {}


def allowed_files(filename):
    try:
        return '.' in filename and filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS
    except:
        return False


def save_index(img_path, statistics) -> bool:
    # todo 创建一个sha1索引，每次上传识别后的图片都进行索引保存，下次上传上来如果索引中已经有了该图片则直接返回信息
    sha1_str = sha1.sha1(img_path)
    return False


def load_index(img_path) -> dict:
    # todo 返回statistics
    sha1_str = sha1.sha1(img_path)
    return None


@app.route('/upload_photo', methods=['POST'], strict_slashes=False)
def api_upload():
    ip = request.remote_addr
    file_dir = os.path.join(basedir, app.config['UPLOAD_FOLDER'])
    file_dir = os.path.join(file_dir, ip.replace(".", '_'))
    if not os.path.exists(file_dir):
        os.makedirs(file_dir)
    f = request.files['file']
    if f and allowed_files(f.filename):
        path = os.path.join(file_dir, f.filename)
        f.save(path)
        pictures[path] = None
        return jsonify({"success": 20000, "msg": "上传成功"})
    else:
        return jsonify({"error": 40000, "msg": "上传失败"})


@app.route('/start_predict', methods=['POST'])
def start_predict():
    for each in pictures.keys():
        each_statistics = predict.predict_img(each)
        pictures[each] = each_statistics
    return jsonify({"success": 20000, "statistics": pictures})


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8899, debug=True)
