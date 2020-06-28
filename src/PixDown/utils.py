import threading
import os
import json


def loadConfig(filePath: str, key: str):
    """ 读取配置文件 """
    pass


def writefile(file: str, text):
    """ 写入log中的文件 """
    setdir("./log")
    os.chdir("./log")
    with open(file, mode="w", encoding="utf-8") as f:
        if ".json" in file or type(text) != 'str':
            text = json.dumps(text, ensure_ascii=False,
                              sort_keys=True, indent=4,)
        f.write(text)
    os.chdir("../")


def setdir(basepath: str, *add_dir: str):
    """ 若目录不存在则创建目录 """
    for dir in add_dir:
        basepath = os.path.join(basepath, dir)
    if not os.path.exists(basepath):
        os.makedirs(basepath)
    return basepath


class MyThread(threading.Thread):
    """ 有return的thread """

    def __init__(self, target, args=()):
        super(MyThread, self).__init__()
        self.func = target
        self.args = args

    def run(self):
        self.result = self.func(*self.args)

    def result(self):
        try:
            # 如果子线程不使用join方法，此处可能会报没有self.result的错误
            return self.result
        except Exception:
            return None
