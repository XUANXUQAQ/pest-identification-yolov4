#!/usr/bin/python
# -*- coding: UTF-8 -*-
import multiprocessing
from multiprocessing import Process

exitFlag = 0


class CustomProcess(Process):  # 继承父类threading.Thread
    def __init__(self, name, function, **kwargs):
        super(CustomProcess, self).__init__()
        multiprocessing.set_start_method('spawn')
        self.name = name
        self.function = function
        self.args = kwargs

    def run(self):  # 把要执行的代码写到run函数里面 线程在创建后会直接运行run函数
        self.function(self.args)
