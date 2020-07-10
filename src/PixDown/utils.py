import threading
import os
import json

CONFIG = {}


def applyConfig():
    """ 应用配置 """
    global CONFIG
    CONFIG = {}
    CONFIG = loadConfig()


def setSettingPath(file: str):
    """ 添加设置文件（json） """
    global CONFIG
    CONFIG['SETTING_PATH'].insert(0, file)
    if os.path.isfile(file):
        CONFIG = loadConfig()


def loadConfig():
    """ 读取配置文件 """

    def readjson(path):
        try:
            with open(path, mode='r', encoding='utf-8') as file:
                text = file.read()
                text = json.loads(text)
                return text
        except Exception as e:
            print(e)
            return False

    config = {}
    path = os.path.join(os.path.dirname(__file__), "setting.json")
    if os.path.isfile(path):
        text = readjson(path)
    else:
        text = False
    if text is False:
        print("load setting Error")
        os._exit(0)
    config = text
    if 'SETTING_PATH' in CONFIG:
        config['SETTING_PATH'] = CONFIG['SETTING_PATH']

    if 'SETTING_PATH' in text:
        for path in text['SETTING_PATH']:
            if os.path.isfile(path):
                text = readjson(path)
                if "PixDownSetting" in text:
                    text = text["PixDownSetting"]
                for key in text:
                    config[key] = text[key]
                break
    return config


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
    """ 设置目录，若目录不存在则创建目录 """
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
