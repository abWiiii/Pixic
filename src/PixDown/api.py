from . import utils
from . import pixdown
from .utils import CONFIG

import os
from concurrent.futures import ThreadPoolExecutor

__all__ = ('pixAPI')


class pixAPI(pixdown.PixDown):
    """ API of pixdown """

    def __init__(self):
        super(pixAPI, self).__init__()

    @staticmethod
    def addSettingPath(path: str):
        """ 设置setting文件 """
        utils.setSettingPath(path)

    def printFollowList(self):
        """ 写入关注画师列表到FILE """
        FILE = "Following_list.json"

        def get(publicity) -> (dict, int):
            pamas = {'publicity': publicity,
                     'per_page': CONFIG['FOLLOW_PER_PAGE'], }
            rog_dict = self.getResult(
                func=self.pixiv.me_following, pamas=pamas)
            rog_dict, total = rog_dict
            if rog_dict is False:
                print("获取关注用户列表失败")
            id_dict = {}
            if total != 0:
                rog_dict = rog_dict['response']  # 'response'的value是list
                for info in rog_dict:
                    id_dict[info['id']] = info['name']
            else:
                id_dict['None'] = 'None'
            return (id_dict, total)

        print("get following user ID ...")
        # 多线程
        public_thread = utils.MyThread(target=get, args=("public",))
        public_thread.start()
        private = get(publicity="private")
        public_thread.join()
        public = public_thread.result

        all_dict = {'total': {'public': public[1],
                              'private': private[1]},
                    'public': public[0],
                    'private': private[0]}

        utils.writefile(FILE, all_dict)
        path = os.path.join(os.getcwd(), "log")
        print("id_list output: " + path + "\\" + FILE)

    def downloadFollowWorks(self):
        """ 下载全部关注用户的全部作品(Pixiv事务所除外UID=11) """
        id_list = self.getFollowList()
        if id_list is False:
            print("获取关注用户列表失败")
        total = len(id_list)
        user_n = 1
        with ThreadPoolExecutor(max_workers=CONFIG['MAXWORKERS'], thread_name_prefix=('UserWorks_')) as thread_pool:
            for user_id in id_list:
                thread_pool.submit(self.downloadUserWorks,
                                   user_id=user_id, user_n=user_n, user_total=total)
                user_n += 1
