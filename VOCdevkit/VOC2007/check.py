import os
import shutil
import xml.etree.ElementTree as ET

baseDir = os.path.dirname(os.path.abspath(__file__))
jpeg_dir = os.path.join(baseDir, 'JPEGImages')
xml_dir = os.path.join(baseDir, 'Annotations')

backup_dir = os.path.join(baseDir, 'backup')
backup_xml_dir = os.path.join(backup_dir, 'xml')
backup_jpg_dir = os.path.join(backup_dir, 'jpg')

xml_list = []
jpg_list = []
available_data_num = 0


def progress(percent, width=50):
    """进度打印功能"""
    if percent >= 100:
        percent = 100

    show_str = ('[%%-%ds]' % width) % (int(width * percent / 100) * "#")  # 字符串拼接的嵌套使用
    print('\r%s %d%% ' % (show_str, percent), end='')


def is_valid_jpg(jpg_file):
    with open(jpg_file, 'rb') as f:
        f.seek(-2, 2)
        buf = f.read()
        f.close()
        return buf == b'\xff\xd9'  # 判定jpg是否包含结束字段


def is_xml_has_jpg():
    for each_file in os.listdir(jpeg_dir):
        portion = os.path.splitext(each_file)
        if portion[1].lower() == '.jpg':
            file_name = portion[0] + '.xml'
            full_xml_path = os.path.join(xml_dir, file_name)
            if not os.path.exists(full_xml_path):
                print('jpg file: ' + each_file + ' does not have xml: ' + full_xml_path)
                jpg_tmp = os.path.join(jpeg_dir, each_file)
                shutil.copy(jpg_tmp, os.path.join(backup_jpg_dir, each_file))
                os.remove(jpg_tmp)


def is_jpg_has_xml():
    global available_data_num
    available_data_num = 0
    for each_file in os.listdir(xml_dir):
        portion = os.path.splitext(each_file)
        if portion[1].lower() == '.xml':
            # 获取xml中的file
            xml_path = os.path.join(xml_dir, each_file)
            tree = ET.parse(xml_path)
            jpg_file_in_xml = tree.find('filename')
            full_path_in_xml = os.path.join(jpeg_dir, jpg_file_in_xml.text)
            full_path_by_xml_name = os.path.join(jpeg_dir, portion[0] + '.jpg')
            if not os.path.exists(full_path_in_xml):
                if not os.path.exists(full_path_by_xml_name):
                    print('neither ' + full_path_in_xml + ' nor ' + full_path_by_xml_name + ' exist')
                    origin = os.path.join(xml_dir, each_file)
                    shutil.copy(origin, os.path.join(backup_xml_dir, each_file))
                    os.remove(os.path.join(xml_dir, each_file))
                    xml_list.append(each_file)
                else:
                    available_data_num += 1
            else:
                # 给图片改名，改为xml名字
                os.rename(full_path_in_xml, full_path_by_xml_name)
                available_data_num += 1
        else:
            xml_list.append(each_file)


def check():
    data_size = len([lists for lists in os.listdir(jpeg_dir) if os.path.isfile(os.path.join(jpeg_dir, lists))])
    recv_size = 0
    incompleteFile = 0
    print('jpg total : %d' % data_size)

    if not os.path.exists(backup_dir):
        os.mkdir(backup_dir)
    if not os.path.exists(backup_jpg_dir):
        os.mkdir(backup_jpg_dir)
    if not os.path.exists(backup_xml_dir):
        os.mkdir(backup_xml_dir)

    for file in os.listdir(jpeg_dir):
        if os.path.splitext(file)[1].lower() == '.jpg':
            ret = is_valid_jpg(os.path.join(jpeg_dir, file))
            if not ret:
                incompleteFile = incompleteFile + 1
                shutil.copy(os.path.join(jpeg_dir, file), os.path.join(backup_jpg_dir, file))
                origin_path = os.path.join(jpeg_dir, file)
                os.remove(origin_path)
                jpg_list.append(file)

        recv_per = int(100 * recv_size / data_size)
        progress(recv_per, width=30)
        recv_size = recv_size + 1

    progress(100, width=30)
    print('\n incomplete file : %d' % incompleteFile)

    is_jpg_has_xml()
    is_xml_has_jpg()


def get_xml_list():
    return xml_list


def get_jpg_list():
    return jpg_list


def get_available_data_num():
    global available_data_num
    return available_data_num


def get_all_xml_num():
    return len(os.listdir(xml_dir))


def add_error_img(img_name):
    jpg_list.append(img_name)


def add_error_xml(xml_name):
    xml_list.append(xml_name)


if __name__ == '__main__':
    check()
