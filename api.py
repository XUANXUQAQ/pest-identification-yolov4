import os

from flask import Flask, jsonify, request
import predict
import utils.sha1_utils as sha1
import json

app = Flask(__name__)
UPLOAD_FOLDER = 'img'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
basedir = os.path.abspath(os.path.dirname(__file__))
ALLOWED_EXTENSIONS = {'png', 'jpg', 'JPG', 'PNG', 'gif', 'GIF'}

CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cache")
CACHE_DATA_NAME = "data.json"

pictures = []
index_count = len(os.listdir('cache'))
MAX_INDEX_NUM = 10000


def allowed_files(filename):
    try:
        return '.' in filename and filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS
    except:
        return False


def save_index(img_path, statistics) -> bool:
    if index_count > MAX_INDEX_NUM:
        print("缓存大小超出限制")
        return False
    sha1_str = sha1.sha1(img_path)
    if not os.path.exists(CACHE_DIR):
        os.mkdir(CACHE_DIR)
    file_dir = os.path.join(CACHE_DIR, sha1_str)
    if not os.path.exists(file_dir):
        os.mkdir(file_dir)
    json_file = json.dumps(statistics)
    try:
        with open(os.path.join(file_dir, CACHE_DATA_NAME), "wb") as f:
            f.write(json_file.encode("utf-8"))
            return True
    except:
        return False


def load_index(img_path) -> dict:
    sha1_str = sha1.sha1(img_path)
    file_dir = os.path.join(CACHE_DIR, sha1_str)
    file_dir = os.path.join(file_dir, CACHE_DATA_NAME)
    if os.path.exists(file_dir):
        try:
            with open(file_dir, "rb") as f:
                strs = f.read()
                dict_data = json.loads(strs)
                print("已找到缓存")
                return dict_data
        except:
            return {}
    else:
        return {}


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
        pictures.append(path)
        return jsonify({"success": 20000, "msg": "上传成功"})
    else:
        return jsonify({"error": 40001, "msg": "上传失败"})


@app.route('/start_predict', methods=['POST'])
def start_predict():
    ret = {}
    if not pictures:
        print("还未上传文件")
        return jsonify({"error": 40000, "msg": "未上传文件"})
    for each in pictures:
        each_statistics = load_index(each)
        if not each_statistics:
            each_statistics = predict.predict_img(each)
            ret[os.path.basename(each)] = each_statistics
            if not each_statistics["error"]:
                save_index(each, each_statistics)
        else:
            ret[os.path.basename(each)] = each_statistics
    pictures.clear()
    return jsonify({"success": 20000, "statistics": ret})


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8899, debug=True)
