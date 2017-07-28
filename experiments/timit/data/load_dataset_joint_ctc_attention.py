#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""Load dataset for the Joint CTC-Attention model (TIMIT corpus).
   You can use the multi-GPU version.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from os.path import join
import pickle
import numpy as np

from experiments.utils.progressbar import wrap_iterator
from experiments.utils.data.dataset_loader.all_load.joint_ctc_attention_all_load import DatasetBase


class Dataset(DatasetBase):

    def __init__(self, data_type, label_type, batch_size, eos_index,
                 sort_utt=True, sorta_grad=False,
                 progressbar=False, num_gpu=1):
        """A class for loading dataset.
        Args:
            data_type: string, train or dev or test
            label_type: string, phone39 or phone48 or phone61 or character
            eos_index: int , the index of <EOS> class
            sort_utt: if True, sort all utterances by the number of frames and
                utteraces in each mini-batch are shuffled
            sorta_grad: if True, sorting utteraces are conducted only in the
                first epoch (not shuffled in each mini-batch). After the first
                epoch, training will revert back to a random order. If sort_utt
                is also True, it will be False.
            progressbar: if True, visualize progressbar
            num_gpu: int, if more than 1, divide batch_size by num_gpu
        """
        if data_type not in ['train', 'dev', 'test']:
            raise ValueError('data_type is "train" or "dev" or "test".')

        self.data_type = data_type
        self.label_type = label_type
        self.batch_size = batch_size * num_gpu
        self.eos_index = eos_index
        self.sort_utt = sort_utt if not sorta_grad else False
        self.sorta_grad = sorta_grad
        self.progressbar = progressbar
        self.num_gpu = num_gpu

        input_path = join(
            '/n/sd8/inaguma/corpus/timit/dataset/inputs/', data_type)
        ctc_label_path = join(
            '/n/sd8/inaguma/corpus/timit/dataset/labels/ctc/',
            label_type, data_type)
        att_label_path = join(
            '/n/sd8/inaguma/corpus/timit/dataset/labels/attention/',
            label_type, data_type)

        # Load the frame number dictionary
        with open(join(input_path, 'frame_num.pickle'), 'rb') as f:
            self.frame_num_dict = pickle.load(f)

        # Sort paths to input & label by frame num
        frame_num_tuple_sorted = sorted(self.frame_num_dict.items(),
                                        key=lambda x: x[1])
        input_paths, att_label_paths, ctc_label_paths = [], [], []
        for input_name, frame_num in frame_num_tuple_sorted:
            input_paths.append(join(input_path, input_name + '.npy'))
            att_label_paths.append(join(att_label_path, input_name + '.npy'))
            ctc_label_paths.append(join(ctc_label_path, input_name + '.npy'))
        self.input_paths = np.array(input_paths)
        self.att_label_paths = np.array(att_label_paths)
        self.ctc_label_paths = np.array(ctc_label_paths)
        self.data_num = len(self.input_paths)

        # Load all dataset in advance
        print('=> Loading ' + data_type + ' dataset (' + label_type + ')...')
        input_list, att_label_list, ctc_label_list = [], [], []
        for i in wrap_iterator(range(self.data_num), self.progressbar):
            input_list.append(np.load(self.input_paths[i]))
            att_label_list.append(np.load(self.att_label_paths[i]))
            ctc_label_list.append(np.load(self.ctc_label_paths[i]))
        self.input_list = np.array(input_list)
        self.att_label_list = np.array(att_label_list)
        self.ctc_label_list = np.array(ctc_label_list)
        self.input_size = self.input_list[0].shape[1]

        self.rest = set(range(0, self.data_num, 1))
