import xml.etree.ElementTree as ET
from os import getcwd


def gen_annotation():
    sets = [('2007', 'train'), ('2007', 'val'), ('2007', 'test')]

    classes = {}
    count = 0
    with open(r"model_data/all_classes.txt", "r", encoding='utf-8') as f:
        line = f.readline().replace('\n', '')
        while line:
            if not line.isspace():
                classes[line] = count
                count += 1
                line = f.readline().replace('\n', '')

    def convert_annotation(year, image_id, list_file):
        in_file = open(r'VOCdevkit/VOC%s/Annotations/%s.xml' % (year, image_id), encoding='utf-8')
        tree = ET.parse(in_file)
        root = tree.getroot()

        for obj in root.iter('object'):
            list_file.write(' ' + str(classes[obj.find('name').text.replace('\n', '').strip()]))
            break

    wd = getcwd()

    for year, image_set in sets:
        image_ids = open(r'VOCdevkit/VOC%s/ImageSets/Offline/%s.txt' % (year, image_set),
                         encoding='utf-8').read().strip().split()
        list_file = open('%s_%s.txt' % (year, image_set), 'w', encoding='utf-8')
        for image_id in image_ids:
            list_file.write(r'%s/VOCdevkit/VOC%s/JPEGImages/%s.jpg' % (wd, year, image_id))
            convert_annotation(year, image_id, list_file)
            list_file.write('\n')
        list_file.close()


if __name__ == '__main__':
    gen_annotation()
