# ----------------------------------------------------------------------#
#   验证集的划分在train.py代码里面进行
#   test.txt和val.txt里面没有内容是正常的。训练不会使用到。
# ----------------------------------------------------------------------#
"""
#--------------------------------注意----------------------------------#
如果在pycharm中运行时提示：
FileNotFoundError: [WinError 3] 系统找不到指定的路径。: './VOCdevkit/VOC2007/Annotations'
这是pycharm运行目录的问题，最简单的方法是将该文件复制到根目录后运行。
可以查询一下相对目录和根目录的概念。在VSCODE中没有这个问题。
#--------------------------------注意----------------------------------#
"""
import os
import random

random.seed(0)

xmlfilepath = r'Annotations'
saveBasePath = r"ImageSets\Main"

# ----------------------------------------------------------------------#
#   想要增加测试集修改trainval_percent
#   train_percent不需要修改
# ----------------------------------------------------------------------#
trainval_percent = 0.9
train_percent = 1

current_path = os.path.abspath(__file__)
father_path = os.path.abspath(os.path.dirname(current_path) + os.path.sep + ".")

saveBasePath = os.path.join(father_path, saveBasePath)

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
print("traub suze", tr)
ftrainval = open(os.path.join(saveBasePath, 'trainval.txt'), 'w')
ftest = open(os.path.join(saveBasePath, 'test.txt'), 'w')
ftrain = open(os.path.join(saveBasePath, 'train.txt'), 'w')
fval = open(os.path.join(saveBasePath, 'val.txt'), 'w')

for i in lists:
    name = total_xml[i][:-4] + '\n'
    if i in trainval:
        ftrainval.write(name)
        if i in train:
            ftrain.write(name)
        else:
            fval.write(name)
    else:
        ftest.write(name)

ftrainval.close()
ftrain.close()
fval.close()
ftest.close()
