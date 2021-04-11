import os

from flask import Flask, jsonify, request
import predict

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
