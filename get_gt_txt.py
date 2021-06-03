import os
import xml.etree.ElementTree as ET


# 获得类
def get_classes(classes_path):
    """loads the classes"""
    with open(classes_path, encoding='utf-8') as f:
        class_names = f.readlines()
    class_names = [c.strip() for c in class_names]
    return class_names


def get_gt_txt():
    image_ids = open('VOCdevkit/VOC2007/ImageSets/Main/test.txt', encoding='utf-8').read().strip().split()

    if not os.path.exists("./input"):
        os.makedirs("./input")
    if not os.path.exists("./input/ground-truth"):
        os.makedirs("./input/ground-truth")

    for image_id in image_ids:
        with open("./input/ground-truth/" + image_id + ".txt", "w", encoding='utf-8') as new_f:
            root = ET.parse("VOCdevkit/VOC2007/Annotations/" + image_id + ".xml").getroot()
            for obj in root.findall('object'):
                difficult_flag = False
                if obj.find('difficult') is not None:
                    difficult = obj.find('difficult').text
                    if int(difficult) == 1:
                        difficult_flag = True
                obj_name = obj.find('name').text
                # 通过这里对不存在的类进行筛选
                classes_path = 'model_data/all_classes.txt'
                class_names = get_classes(classes_path)
                if obj_name not in class_names:
                    continue

                bndbox = obj.find('bndbox')
                left = bndbox.find('xmin').text
                top = bndbox.find('ymin').text
                right = bndbox.find('xmax').text
                bottom = bndbox.find('ymax').text

                if difficult_flag:
                    new_f.write("%s %s %s %s %s difficult\n" % (obj_name, left, top, right, bottom))
                else:
                    new_f.write("%s %s %s %s %s\n" % (obj_name, left, top, right, bottom))

    print("Conversion completed!")


if __name__ == '__main__':
    get_gt_txt()
