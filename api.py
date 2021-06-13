import base64
import json
import multiprocessing
import os
import shutil
import zipfile
from multiprocessing import Queue

from flask import Flask, request
from flask_cors import CORS

import VOCdevkit.VOC2007.check as check
import VOCdevkit.VOC2007.voc2yolo4 as voc2yolo4
import get_dr_txt
import get_gt_txt
import get_map
import kmeans_for_anchors
import predict
import train
import utils.sha1_utils as sha1
import voc_annotation
from utils import resp_utils

app = Flask(__name__)
CORS(app, supports_credentials=True)
UPLOAD_FOLDER = 'img'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
basedir = os.path.abspath(os.path.dirname(__file__))
ALLOWED_EXTENSIONS = {'png', 'jpg', 'JPG', 'PNG', 'gif', 'GIF'}

CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cache")
CACHE_DATA_NAME = "data.json"

train_loss_queue = None

pictures = []
if not os.path.exists('cache'):
    os.mkdir('cache')
index_count = len(os.listdir('cache'))
MAX_INDEX_NUM = 10000

train_proc = None
is_thread_starting = False

multiprocessing.set_start_method('spawn', force=True)


def allowed_files(filename, suffix=None):
    if suffix is None:
        suffix = ALLOWED_EXTENSIONS
    try:
        return '.' in filename and filename.rsplit('.', 1)[1] in suffix
    except Exception as e:
        print(e)
        return False


def save_index(img_path, processed_img_base64, statistics) -> bool:
    if index_count > MAX_INDEX_NUM:
        print("缓存大小超出限制")
        return False
    sha1_str = sha1.sha1(img_path)
    if not os.path.exists(CACHE_DIR):
        os.mkdir(CACHE_DIR)
    file_dir = os.path.join(CACHE_DIR, sha1_str)
    if not os.path.exists(file_dir):
        os.mkdir(file_dir)
    data = {'statistics': statistics, 'img': processed_img_base64}
    json_file = json.dumps(data)
    try:
        with open(os.path.join(file_dir, CACHE_DATA_NAME), "wb") as f:
            f.write(json_file.encode("utf-8"))
            return True
    except Exception as e:
        print(e)
        return False


def get_all_classes_from_file(file):
    classes = []
    with open(file, "r", encoding='utf-8') as f:
        line = f.readline().replace('\n', '')
        while line:
            if not line.isspace():
                classes.append(line)
                line = f.readline().replace('\n', '')
    return classes


def write_classes_to_file(classes):
    with open('model_data/all_classes.txt', 'w', encoding='utf-8') as f:
        for each in classes:
            f.write(each)
            f.write('\n')


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
        except Exception as e:
            print(e)
            return {}
    else:
        return {}


def unzip_file(zip_src, dst_dir):
    r = zipfile.is_zipfile(zip_src)
    if r:
        fz = zipfile.ZipFile(zip_src, 'r')
        for file in fz.namelist():
            fz.extract(file, dst_dir)
    else:
        print('This is not zip')


@app.route('/accuracy', methods=['GET'])
def test_accuracy():
    get_dr_txt.get_dr_txt()
    get_gt_txt.get_gt_txt()
    mAP = get_map.get_map()
    return resp_utils.success({
        'accuracy': mAP
    })


@app.route('/train', methods=['DELETE'])
def stop_train():
    if train_proc is not None:
        train_proc.terminate()
        train_proc.join()
        return resp_utils.success()
    else:
        return resp_utils.error("已经停止")


@app.route('/loss', methods=['GET'])
def get_total_loss():
    try:
        global train_proc, is_thread_starting
        if (train_proc is None) or (not train_proc.is_alive()) and not is_thread_starting:
            return resp_utils.error('深度学习意外停止')
        else:
            try:
                loss, iteration = train_loss_queue.get()
                print("loss: " + str(loss))
                print("iteration: " + str(iteration))
            except Exception as ex:
                print('从队列中获取信息失败')
                print(ex)
                loss = 100
                iteration = 1
            return resp_utils.success({
                'loss': loss,
                'iteration': iteration
            })
    except Exception as e:
        print(e)
        return resp_utils.error('服务器出现错误')


def __train_func(_train_loss_queue):
    voc2yolo4.voc2Yolo4()
    voc_annotation.gen_annotation()
    kmeans_for_anchors.get_anchors()
    train.start_train(queue=_train_loss_queue)


@app.route('/train', methods=['POST'])
def start_train():
    try:
        global train_proc, is_thread_starting, train_loss_queue
        train_loss_queue = Queue()
        if (train_proc is None) or (not train_proc.is_alive()):
            is_thread_starting = True
            train_proc = multiprocessing.Process(target=__train_func, args=(train_loss_queue,))
            train_proc.start()
            is_thread_starting = False
            return resp_utils.success()
        else:
            return resp_utils.error('已经开始训练')
    except Exception as e:
        print(e)
        return resp_utils.error('启动训练失败')


@app.route('/trainData', methods=['DELETE'])
def cancel_add_train_data():
    try:
        ip = request.remote_addr
        tmp_path = os.path.join('tmp', ip.replace('.', '_'))
        if os.path.exists(tmp_path):
            shutil.rmtree(tmp_path)
            os.mkdir(tmp_path)
        return resp_utils.success()
    except Exception as e:
        print(e)
        return resp_utils.error('操作失败')


@app.route('/trainData', methods=['POST'])
def confirm_add_train_data():
    try:
        ip = request.remote_addr
        file_dir = os.path.join(basedir, 'tmp')
        file_dir = os.path.join(file_dir, ip.replace('.', '_'))
        for each_file in os.listdir(file_dir):
            if os.path.isdir(os.path.join(file_dir, each_file)):
                continue
            if not allowed_files(each_file, {'zip'}):
                continue
            full_path = os.path.join(file_dir, each_file)
            unzip_file(full_path, file_dir)
        jpeg_dir = os.path.join(file_dir, 'JPEGImages')
        for each_file in os.listdir(jpeg_dir):
            copy_path = os.path.join('VOCdevkit/VOC2007/JPEGImages', each_file)
            src_path = os.path.join(jpeg_dir, each_file)
            if not os.path.exists(copy_path):
                shutil.copy(src_path, copy_path)
            else:
                check.add_error_img(each_file)
                shutil.copy(src_path, os.path.join('VOCdevkit/VOC2007/backup/jpg', each_file))
        annotation_dir = os.path.join(file_dir, 'Annotations')
        for each_file in os.listdir(annotation_dir):
            copy_path = os.path.join('VOCdevkit/VOC2007/Annotations', each_file)
            src_path = os.path.join(annotation_dir, each_file)
            if not os.path.exists(copy_path):
                shutil.copy(src_path, copy_path)
            else:
                check.add_error_xml(each_file)
                shutil.copy(src_path, os.path.join('VOCdevkit/VOC2007/backup/xml', each_file))
        return resp_utils.success()
    except Exception as e:
        print(e)
        return resp_utils.error('操作失败')


@app.route('/uploadTrainData', methods=['POST'])
def upload_trainData():
    """
    根据ip地址来区分用户，保存到tmp/${ip}
    :return:
    """
    ip = request.remote_addr
    file_dir = os.path.join(basedir, 'tmp')
    file_dir = os.path.join(file_dir, ip.replace('.', '_'))
    if not os.path.exists(file_dir):
        os.makedirs(file_dir)
    f = request.files['file']
    if f and allowed_files(f.filename, suffix={'zip'}):
        path = os.path.join(file_dir, f.filename)
        f.save(path)
        return resp_utils.success()
    else:
        return resp_utils.error('上传失败')


@app.route('/trainPercent', methods=['POST'])
def update_train_percent():
    data = request.json
    try:
        percent = float(data['percent'])
        voc2yolo4.update_train_percent(percent)
        return resp_utils.success()
    except Exception as e:
        print(e)
        return resp_utils.error('输入无效')


@app.route('/classes', methods=['GET'])
def get_all_classes():
    return resp_utils.success({
        'classes': get_all_classes_from_file('model_data/all_classes.txt')
    })


@app.route('/classes', methods=['POST'])
def write_classes():
    try:
        classesStr = request.json
        classes = classesStr.split(',')
        write_classes_to_file(classes)
        return resp_utils.success()
    except Exception as e:
        print(e)
        return resp_utils.error('写入失败')


@app.route('/uploadPhoto', methods=['POST'])
def api_upload():
    """
    上传需要识别的图片，保存到img/${ip}
    :return:
    """
    ip = request.remote_addr
    file_dir = os.path.join(basedir, app.config['UPLOAD_FOLDER'])
    file_dir = os.path.join(file_dir, ip.replace(".", '_'))
    if not os.path.exists(file_dir):
        os.makedirs(file_dir)
    jsonData = request.json
    imgBase64 = jsonData['file']
    fileName = jsonData['name']
    f = base64.b64decode(imgBase64)
    if f and allowed_files(fileName):
        path = os.path.join(file_dir, fileName)
        with open(path, 'wb') as file:
            file.write(f)
        pictures.append(path)
        return resp_utils.success()
    else:
        return resp_utils.error('上传失败')


@app.route('/startPredict', methods=['POST'])
def start_predict():
    """
    开始对img/${ip}中的图片进行预测，返回预测结果
    :return:
    """
    ret = {}
    each_statistics: dict
    if not pictures:
        return resp_utils.error('还未上传文件')
    for each in pictures:
        info = load_index(each)
        if not info:
            each_statistics, base64_str = predict.predict_img(each)
            ret[os.path.basename(each)] = {'statistics': each_statistics, 'img': base64_str}
            if 'error' not in each_statistics:
                save_index(each, base64_str, each_statistics)
        else:
            each_statistics = info['statistics']
            base64_str = info['img']
            ret[os.path.basename(each)] = {'statistics': each_statistics, 'img': base64_str}
    pictures.clear()
    return resp_utils.success(ret)


@app.route('/trainedModels', methods=['GET'])
def get_all_train_model():
    tmp = []
    for each in os.listdir('logs'):
        if allowed_files(each, {'pth'}):
            tmp.append(os.path.join('logs', each))
    return resp_utils.success({
        'fileList': tmp
    })


@app.route('/updateTrainModel', methods=['POST'])
def update_train_model():
    try:
        data = request.json
        file_path = data.get('path')
        shutil.copy(file_path, 'model_data/yolo4_weights.pth')
        predict.update_model()
        return resp_utils.success()
    except Exception as e:
        print(e)
        return resp_utils.error('替换文件失败')


@app.route('/check', methods=['GET'])
def check_data():
    try:
        check.check()
        return resp_utils.success({
            'jpgList': check.get_jpg_list(),
            'xmlList': check.get_xml_list()
        })
    except Exception as e:
        print(e)
        return resp_utils.error('检查文件失败')


@app.route('/allTrainData', methods=['GET'])
def get_all_train_data_num():
    return resp_utils.success({
        'num': check.get_all_xml_num()
    })


@app.route('/availableTrainData', methods=['GET'])
def get_available_data_num():
    return resp_utils.success({
        'num': check.get_available_data_num()
    })


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8899, debug=False)
