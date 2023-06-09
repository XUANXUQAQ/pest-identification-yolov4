import os

import numpy as np
import torch
import torch.backends.cudnn as cudnn
import torch.optim as optim
from torch.autograd import Variable
from torch.utils.data import DataLoader
from tqdm import tqdm

from nets.yolo4 import YoloBody
from nets.yolo_training import Generator, YOLOLoss
from utils.dataloader import YoloDataset, yolo_dataset_collate

model: YoloBody
optimizer: optim.Adam
total_loss = 0
__total_loss = 100
__iterationCount = 1

# 是否使用Cuda
Cuda = True
# Dataloder的使用
Use_Data_Loader = True
# 是否对损失进行归一化，用于改变loss的大小
# 用于决定计算最终loss是除上batch_size还是除上正样本数量
normalize = False

input_shape = (608, 608)

mosaic = False
Cosine_lr = False
smooth_label = 0.005


# 获得类和先验框
def get_classes(classes_path):
    """loads the classes"""
    with open(classes_path, encoding='utf-8') as f:
        class_names = f.readlines()
    class_names = [c.strip() for c in class_names]
    return class_names


def get_anchors(anchors_path):
    """loads the anchors from a file"""
    with open(anchors_path, encoding='utf-8') as f:
        anchors = f.readline()
    anchors = [float(x) for x in anchors.split(',')]
    return np.array(anchors).reshape([-1, 3, 2])[::-1, :, :]


def get_lr(optimizer):
    for param_group in optimizer.param_groups:
        return param_group['lr']


def fit_one_epoch(net, yolo_losses, epoch, epoch_size, epoch_size_val, gen, genval, Epoch, cuda, queue=None):
    global total_loss, __iterationCount
    val_loss = 0

    net.train()
    with tqdm(total=epoch_size, desc=f'Epoch {epoch + 1}/{Epoch}', postfix=dict, mininterval=0.3) as pbar:
        for iteration, batch in enumerate(gen):
            if iteration >= epoch_size:
                break
            if queue is not None:
                queue.put((get_loss(), get_iteration()))
            images, targets = batch[0], batch[1]
            with torch.no_grad():
                if cuda:
                    images = Variable(torch.from_numpy(images).type(torch.FloatTensor)).cuda()
                    targets = [Variable(torch.from_numpy(ann).type(torch.FloatTensor)) for ann in targets]
                else:
                    images = Variable(torch.from_numpy(images).type(torch.FloatTensor))
                    targets = [Variable(torch.from_numpy(ann).type(torch.FloatTensor)) for ann in targets]

            # 清零梯度
            optimizer.zero_grad()
            # 前向传播
            outputs = net(images)
            losses = []
            num_pos_all = 0
            # 计算损失
            for each in range(3):
                loss_item, num_pos = yolo_losses[each](outputs[each], targets)
                losses.append(loss_item)
                num_pos_all += num_pos

            loss = sum(losses) / num_pos_all
            # 反向传播
            loss.backward()
            optimizer.step()

            total_loss += loss.item()
            global __total_loss
            __total_loss = total_loss / (iteration + 1)

            pbar.set_postfix(**{'total_loss': __total_loss,
                                'lr': get_lr(optimizer)})
            pbar.update(1)

    net.eval()
    print('Start Validation')
    with tqdm(total=epoch_size_val, desc=f'Epoch {epoch + 1}/{Epoch}', postfix=dict, mininterval=0.3) as pbar:
        for iteration, batch in enumerate(genval):
            if iteration >= epoch_size_val:
                break
            if queue is not None:
                queue.put((get_loss(), get_iteration()))
            images_val, targets_val = batch[0], batch[1]

            with torch.no_grad():
                if cuda:
                    images_val = Variable(torch.from_numpy(images_val).type(torch.FloatTensor)).cuda()
                    targets_val = [Variable(torch.from_numpy(ann).type(torch.FloatTensor)) for ann in targets_val]
                else:
                    images_val = Variable(torch.from_numpy(images_val).type(torch.FloatTensor))
                    targets_val = [Variable(torch.from_numpy(ann).type(torch.FloatTensor)) for ann in targets_val]
                optimizer.zero_grad()
                outputs = net(images_val)
                losses = []
                num_pos_all = 0
                for each in range(3):
                    loss_item, num_pos = yolo_losses[each](outputs[each], targets_val)
                    losses.append(loss_item)
                    num_pos_all += num_pos
                loss = sum(losses) / num_pos_all
                val_loss += loss.item()
            pbar.set_postfix(**{'total_loss': val_loss / (iteration + 1)})
            pbar.update(1)
    print('Finish Validation')
    print('Epoch:' + str(epoch + 1) + '/' + str(Epoch))
    print('Total Loss: %.4f || Val Loss: %.4f ' % (total_loss / (epoch_size + 1), val_loss / (epoch_size_val + 1)))

    print('Saving state, iter:', str(epoch + 1))
    __iterationCount += 1
    log = 'Epoch:%d----Total loss:%.4f----Val loss:%.4f----file_name:Epoch%d.pth' % \
          ((epoch + 1), __total_loss / (epoch_size + 1), val_loss / (epoch_size_val + 1), ((epoch + 1) % 100))
    with open('logs/epoch-status.log', 'a', encoding='utf-8') as log_file:
        log_file.write(log)
        log_file.write('\n')
    torch.save(model.state_dict(), 'logs/Epoch%d.pth' % ((epoch + 1) % 100))


def get_loss():
    global __total_loss
    return __total_loss


def get_iteration():
    global __iterationCount
    return __iterationCount


def start_train(queue=None):
    global model, __iterationCount
    __iterationCount = 1

    # classes和anchor的路径
    anchors_path = 'model_data/yolo_anchors.txt'
    classes_path = 'model_data/all_classes.txt'
    # 获取classes和anchor
    class_names = get_classes(classes_path)
    anchors = get_anchors(anchors_path)
    num_classes = len(class_names)

    # 创建yolo模型
    model = YoloBody(len(anchors[0]), num_classes)

    model_path = "model_data/yolo4_weights.pth"
    print('Loading weights into state dict...')
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    if os.path.exists(model_path):
        model_dict = model.state_dict()
        pretrained_dict = torch.load(model_path, map_location=device)
        pretrained_dict = {k: v for k, v in pretrained_dict.items() if np.shape(model_dict[k]) == np.shape(v)}
        model_dict.update(pretrained_dict)
        model.load_state_dict(model_dict)
        print('Finished!')
    else:
        print("error no pretrained model")

    net = model.train()

    if Cuda:
        net = torch.nn.DataParallel(model)
        cudnn.benchmark = True
        net = net.cuda()

    # 建立loss函数
    yolo_losses = []
    for i in range(3):
        yolo_losses.append(YOLOLoss(np.reshape(anchors, [-1, 2]), num_classes,
                                    (input_shape[1], input_shape[0]), smooth_label, Cuda, normalize))

    # 获得图片路径和标签
    annotation_path = '2007_train.txt'
    val_split = 0.1
    with open(annotation_path, encoding='utf-8') as f:
        lines = f.readlines()
    np.random.seed(10101)
    np.random.shuffle(lines)
    np.random.seed(None)
    num_val = int(len(lines) * val_split)
    num_train = len(lines) - num_val

    Init_Epoch = 0
    Freeze_Epoch = 200
    Unfreeze_Epoch = 300

    # 冻结训练部分
    lr = 1e-3
    Batch_size = 4

    global optimizer
    optimizer = optim.Adam(net.parameters(), lr)
    if Cosine_lr:
        lr_scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=5, eta_min=1e-5)
    else:
        lr_scheduler = optim.lr_scheduler.StepLR(optimizer, step_size=1, gamma=0.92)

    if Use_Data_Loader:
        train_dataset = YoloDataset(lines[:num_train], (input_shape[0], input_shape[1]), mosaic=mosaic,
                                    is_train=True)
        val_dataset = YoloDataset(lines[num_train:], (input_shape[0], input_shape[1]), mosaic=False, is_train=False)
        gen = DataLoader(train_dataset, shuffle=True, batch_size=Batch_size, num_workers=4, pin_memory=True,
                         drop_last=True, collate_fn=yolo_dataset_collate)
        gen_val = DataLoader(val_dataset, shuffle=True, batch_size=Batch_size, num_workers=4, pin_memory=True,
                             drop_last=True, collate_fn=yolo_dataset_collate)
    else:
        gen = Generator(Batch_size, lines[:num_train],
                        (input_shape[0], input_shape[1])).generate(train=True, mosaic=mosaic)
        gen_val = Generator(Batch_size, lines[num_train:],
                            (input_shape[0], input_shape[1])).generate(train=False, mosaic=mosaic)

    epoch_size = max(1, num_train // Batch_size)
    epoch_size_val = num_val // Batch_size
    # 冻结训练
    for param in model.backbone.parameters():
        param.requires_grad = False

    for epoch in range(Init_Epoch, Freeze_Epoch):
        fit_one_epoch(net, yolo_losses, epoch, epoch_size, epoch_size_val, gen, gen_val, Freeze_Epoch, Cuda,
                      queue=queue)
        lr_scheduler.step()

    # 解冻训练
    lr = 1e-4
    Batch_size = 2

    optimizer = optim.Adam(net.parameters(), lr)
    if Cosine_lr:
        lr_scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=5, eta_min=1e-5)
    else:
        lr_scheduler = optim.lr_scheduler.StepLR(optimizer, step_size=1, gamma=0.92)

    if Use_Data_Loader:
        train_dataset = YoloDataset(lines[:num_train], (input_shape[0], input_shape[1]), mosaic=mosaic,
                                    is_train=True)
        val_dataset = YoloDataset(lines[num_train:], (input_shape[0], input_shape[1]), mosaic=False, is_train=False)
        gen = DataLoader(train_dataset, shuffle=True, batch_size=Batch_size, num_workers=4, pin_memory=True,
                         drop_last=True, collate_fn=yolo_dataset_collate)
        gen_val = DataLoader(val_dataset, shuffle=True, batch_size=Batch_size, num_workers=4, pin_memory=True,
                             drop_last=True, collate_fn=yolo_dataset_collate)
    else:
        gen = Generator(Batch_size, lines[:num_train],
                        (input_shape[0], input_shape[1])).generate(train=True, mosaic=mosaic)
        gen_val = Generator(Batch_size, lines[num_train:],
                            (input_shape[0], input_shape[1])).generate(train=False, mosaic=mosaic)

    epoch_size = max(1, num_train // Batch_size)
    epoch_size_val = num_val // Batch_size
    # 解冻后训练
    for param in model.backbone.parameters():
        param.requires_grad = True

    for epoch in range(Freeze_Epoch, Unfreeze_Epoch):
        fit_one_epoch(net, yolo_losses, epoch, epoch_size, epoch_size_val, gen, gen_val, Unfreeze_Epoch, Cuda,
                      queue=queue)
        lr_scheduler.step()


if __name__ == '__main__':
    start_train()
