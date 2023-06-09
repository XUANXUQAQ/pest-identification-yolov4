import xml.etree.ElementTree as ET
from os import getcwd


def gen_annotation():
    sets = [('2007', 'train'), ('2007', 'val'), ('2007', 'test')]

    classes = []
    with open(r"model_data/all_classes.txt", "r", encoding='utf-8') as f:
        line = f.readline().replace('\n', '')
        while line:
            if not line.isspace():
                classes.append(line)
                line = f.readline().replace('\n', '')

    def convert_annotation(year, image_id, list_file):
        in_file = open(r'VOCdevkit/VOC%s/Annotations/%s.xml' % (year, image_id), encoding='utf-8')
        tree = ET.parse(in_file)
        root = tree.getroot()

        for obj in root.iter('object'):
            difficult = 0
            if obj.find('difficult') is not None:
                difficult = obj.find('difficult').text

            cls = obj.find('name').text.strip()
            if cls not in classes or int(difficult) == 1:
                continue
            cls_id = classes.index(cls)
            xmlbox = obj.find('bndbox')
            b = (int(xmlbox.find('xmin').text), int(xmlbox.find('ymin').text), int(xmlbox.find('xmax').text),
                 int(xmlbox.find('ymax').text))
            list_file.write(" " + ",".join([str(a) for a in b]) + ',' + str(cls_id))

    wd = getcwd()

    for year, image_set in sets:
        image_ids = open(r'VOCdevkit/VOC%s/ImageSets/Main/%s.txt' % (year, image_set),
                         encoding='utf-8').read().strip().split()
        list_file = open('%s_%s.txt' % (year, image_set), 'w', encoding='utf-8')
        for image_id in image_ids:
            list_file.write(r'%s/VOCdevkit/VOC%s/JPEGImages/%s.jpg' % (wd, year, image_id))
            convert_annotation(year, image_id, list_file)
            list_file.write('\n')
        list_file.close()


if __name__ == '__main__':
    gen_annotation()
