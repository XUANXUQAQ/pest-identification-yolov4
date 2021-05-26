import os
import random

random.seed(0)

# ----------------------------------------------------------------------#
#   想要增加测试集修改trainval_percent
#   train_percent不需要修改
# ----------------------------------------------------------------------#
trainval_percent = 1


def voc2Yolo4Offline():
    global trainval_percent
    xmlfilepath = r'Annotations'
    saveBasePath = r"ImageSets/Offline"
    train_percent = 1

    current_path = os.path.abspath(__file__)
    father_path = os.path.abspath(os.path.dirname(current_path) + os.path.sep + ".")

    saveBasePath = os.path.join(father_path, saveBasePath)
    if not os.path.exists(saveBasePath):
        os.makedirs(saveBasePath)

    temp_xml = os.listdir(os.path.join(father_path, xmlfilepath))
    total_xml = []
    for xml in temp_xml:
        if xml.endswith(".xml"):
            total_xml.append(xml)

    xml_num = len(total_xml)
    lists = range(xml_num)
    tv = int(xml_num * trainval_percent)
    tr = int(tv * train_percent)
    trainval = random.sample(lists, tv)
    train = random.sample(trainval, tr)

    print("train and val size", tv)
    print("train size", tr)
    ftrainval = open(os.path.join(saveBasePath, 'trainval.txt'), 'wb')
    ftest = open(os.path.join(saveBasePath, 'test.txt'), 'wb')
    ftrain = open(os.path.join(saveBasePath, 'train.txt'), 'wb')
    fval = open(os.path.join(saveBasePath, 'val.txt'), 'wb')

    for i in lists:
        name = total_xml[i][:-4] + '\n'
        if i in trainval:
            ftrainval.write(name.encode('utf-8'))
            if i in train:
                ftrain.write(name.encode('utf-8'))
            else:
                fval.write(name.encode('utf-8'))
        else:
            ftest.write(name.encode('utf-8'))

    ftrainval.close()
    ftrain.close()
    fval.close()
    ftest.close()


def update_train_percent(train_percent):
    global trainval_percent
    trainval_percent = train_percent


if __name__ == '__main__':
    voc2Yolo4Offline()
