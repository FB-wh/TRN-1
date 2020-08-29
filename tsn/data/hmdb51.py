# -*- coding: utf-8 -*-

"""
@date: 2020/8/28 下午4:37
@file: hmdb51.py
@author: zj
@description: 
"""

import cv2
from PIL import Image
import random
import os
import numpy as np

import torch
from torch.utils.data import Dataset
from tsn.util.image import rgbdiff


class HMDB51(Dataset):

    def __init__(self, data_dir, annotation_dir, modality=("RGB"), num_seg=3, split=1, train=True, transform=None):
        assert modality == ('RGB') or modality == ('RGBDiff') or modality == ('RGB', 'RGBDiff')

        if train:
            annotation_path = os.path.join(annotation_dir, f'hmdb51_train_split_{split}_rawframes.txt')
        else:
            annotation_path = os.path.join(annotation_dir, f'hmdb51_val_split_{split}_rawframes.txt')

        if not os.path.isfile(annotation_path):
            raise ValueError(f'{annotation_path}不是文件路径')

        self.data_dir = data_dir
        self.transform = transform
        self.num_seg = num_seg
        self.modality = modality

        video_list = list()
        img_num_list = list()
        cate_list = list()
        with open(annotation_path, 'r') as f:
            lines = f.readlines()
            for line in lines:
                dir_name, img_num, cate = line.strip().split(' ')

                video_list.append(dir_name)
                img_num_list.append(int(img_num))
                cate_list.append(int(cate))
        self.video_list = video_list
        self.img_num_list = img_num_list
        self.cate_list = cate_list

    def __getitem__(self, index: int):
        """
        从选定的视频文件夹中随机选取T帧
        如果选择了输入模态为RGB或者RGBDiff,则返回(T, C, H, W)，其中T表示num_seg；
        如果输入模态为(RGB, RGBDiff)，则返回(T*2, C, H, W)
        """
        assert index < len(self.video_list)
        target = self.cate_list[index]

        # 视频帧数
        video_length = self.img_num_list[index]
        # 每一段帧数
        seg_length = int(video_length / self.num_seg)
        num_list = list()
        if 'RGBDiff' in self.modality:
            # 在每段中随机挑选一帧
            for i in range(self.num_seg):
                # 如果使用`RGBDiff`，需要采集前后两帧进行差分
                # random.randint(a, b) -> [a, b]
                num_list.append(random.randint(i * seg_length, (i + 1) * seg_length - 2))
        else:
            # 在每段中随机挑选一帧
            for i in range(self.num_seg):
                num_list.append(random.randint(i * seg_length, (i + 1) * seg_length - 1))
        video_path = os.path.join(self.data_dir, self.video_list[index])

        image_list = list()
        for num in num_list:
            if 'RGB' in self.modality:
                image_path = os.path.join(video_path, 'img_{:0>5d}.jpg'.format(num))
                img = cv2.imread(image_path)

                if self.transform:
                    img = self.transform(img)
                image_list.append(img)
            if 'RGBDiff' in self.modality:
                img1_path = os.path.join(video_path, 'img_{:0>5d}.jpg'.format(num))
                # img1 = cv2.imread(img1_path, cv2.IMREAD_COLOR)
                img1 = np.array(Image.open(img1_path))

                img2_path = os.path.join(video_path, 'img_{:0>5d}.jpg'.format(num + 1))
                # img2 = cv2.imread(img2_path, cv2.IMREAD_COLOR)
                img2 = np.array(Image.open(img2_path))

                # print(img1.shape, img2.shape)
                img = rgbdiff(img1, img2)
                if self.transform:
                    img = self.transform(img)
                image_list.append(img)
        image = torch.stack(image_list)

        return image, target

    def __len__(self) -> int:
        return len(self.video_list)
