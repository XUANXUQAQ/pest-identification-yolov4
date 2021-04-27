#!/usr/bin/python
# -*- coding: UTF-8 -*-

import threading

exitFlag = 0


class Thread(threading.Thread):  # 继承父类threading.Thread
    def __init__(self, name, function, **kwargs):
        threading.Thread.__init__(self)
        self.name = name
        self.function = function
        self.args = kwargs

    def run(self):  # 把要执行的代码写到run函数里面 线程在创建后会直接运行run函数
        self.function(self.args)
