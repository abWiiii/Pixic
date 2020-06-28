from . import utils
from . import setting

import pixivpy3
import os
import logging
import time
from random import random
from concurrent.futures import ThreadPoolExecutor
# import asyncio
# from pprint import pprint

__all__ = ("PixDown")


class PixDown():
    """ Main function of this package """

    def __init__(self):
        self.setLog()
        params = self.setProxy()
        self.pixiv = pixivpy3.PixivAPI(**params)
        self.pixiv.set_accept_language("zh-cn")
        self.login()

    def setLog(self):
        """ 设置log """
        logging.basicConfig(level=logging.INFO, filename="log.log", filemode='a',
                            format='%(asctime)s - [Line:%(lineno)d] - %(module)s \n%(levelname)s : %(message)s \n')

    def login(self):
        """ 登录 """
        info = self.getUser()
        print(r"正在登录...")
        try:
            self.pixiv.login(info[0], info[1])
        except Exception as e:
            print(r"登录失败")
            print(e)
            print("————退出————")
            os._exit(0)
        print(r"已登录...")

    def getUser(self) -> (str, str):
        """ 获取账号密码 """
        user_id = ""
        user_password = ""
        try:
            user_id = setting.user_id
            user_password = setting.user_password
        except Exception:
            print(r"请输入用户名密码:")
            while user_id == "":
                user_id = input(r"邮箱地址/Pixiv ID:")
            while user_password == "":
                user_password = input(r"密码:")
            # ---------or use fetpass-------
            # from getpass import getpass
            # while user_password == "":
            #     user_password = getpass("密码:")

        return (user_id, user_password)

    def setProxy(self):
        """ 设置代理 """
        try:
            params = setting.PAMAS
            print("Proxy = ", params)
        except Exception:
            print("NOT proxy")
            params = {}
        # TODO 读取config中的代理，留下全局代理位
        return params

    def getResult(self, func, pamas: dict):
        """ json_result获取函数 """

        # 多次重连
        def connection(func, pamas: dict):
            logging.info("{0} - {1}" .format(func, pamas))
            connection_n = 1
            json_result = {'status': 'failure'}
            while json_result['status'] == 'failure':
                try:
                    json_result = func(**pamas)
                    if json_result['status'] == 'success':
                        break
                    logging.warning(
                        "No.{0} : json_result['status'] == 'failure' - {1}" .format(connection_n, func))
                except Exception as e:
                    logging.warning("No.{0} : {1}" .format(connection_n, e))
                if connection_n == setting.RECONNECTION:
                    logging.warning("reconnection error")
                    print(func, pamas, " : reconnection error")
                    break
                connection_n += 1
                time.sleep(3)
            return json_result

        json_result = connection(func, pamas)
        if 'per_page' in pamas:
            per_page = pamas['per_page']
            total = json_result['pagination']['total']
            if total >= per_page:
                json_result = connection(func, pamas)
        else:
            total = None

        return (json_result, total)

    def download(self, url, path, replace=False):
        """ 下载 """
        logging.info("{0} - {1}" .format(path, url))
        down_bool = False
        download_n = 1
        while down_bool is False:
            down_bool = self.pixiv.download(
                url=url, path=path, replace=replace)
            print(down_bool, end=" ")
            if down_bool:
                print("")
                break
            if download_n == setting.RECONNECTION:
                print("download failure:", url)
                logging.warning("download failure: {0}" .format(url))
                break
            download_n += 1

            time.sleep(5)

    # ------------------IO--------------------

    def printFollowList(self):
        """ 写入关注画师列表到FILE """
        FILE = "Following_list.json"

        def get(publicity) -> (dict, int):
            pamas = {'publicity': publicity,
                     'per_page': setting.FOLLOW_PER_PAGE, }
            rog_dict = self.getResult(
                func=self.pixiv.me_following, pamas=pamas)
            rog_dict, total = rog_dict
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
        total = len(id_list)
        user_n = 1
        with ThreadPoolExecutor(max_workers=setting.MAXWORKERS, thread_name_prefix=('UserWorks_')) as thread_pool:
            for user_id in id_list:
                thread_pool.submit(self.downloadUserWorks,
                                   user_id=user_id, user_n=user_n, user_total=total)
                user_n += 1

    # ----------------------------------------

    def getFollowList(self) -> list:
        """ 获取关注的用户列表 (Pixiv事务所除外UID=11)"""

        def get(publicity) -> list:

            pamas = {'publicity': publicity,
                     'per_page': setting.FOLLOW_PER_PAGE, }
            rog_dict = self.getResult(
                func=self.pixiv.me_following, pamas=pamas)
            rog_dict, total = rog_dict
            id_dict = []
            if total != 0:
                rog_dict = rog_dict['response']
                for i in rog_dict:
                    id_dict.append(i['id'])
            return id_dict

        print("获取关注列表...")
        public_thread = utils.MyThread(target=get, args=("public",))
        public_thread.start()
        private = get(publicity="private")
        public_thread.join()
        public = public_thread.result

        id_list = private + public
        # 去除关注列表的UID=11->Pixiv事务所
        if 11 in id_list:
            id_list.remove(11)
        return id_list

    def downloadUserWorks(self, user_id, user_n, user_total):
        """ 下载用户id的作品列表 """
        time.sleep(random() * 4)
        print("get user %d works..." % user_id)
        pamas = {"author_id": user_id,
                 'per_page': setting.USER_WORKS_PER_PAGE, }
        json_dict, total = self.getResult(
            func=self.pixiv.users_works, pamas=pamas)
        if total == 0:
            print("user %d no work!" % user_id)
            return

        path = utils.setdir(setting.DOWNLOAD_WORKS, str(user_id))
        json_dict = json_dict['response']
        works_n = 1
        for illust in json_dict:
            # illust["page_count"]是一个illust作品数量
            print(">>> {0:>5}/{1:<5}user {2:<10} - works {3:<10} : {4:>4}/{5:<4}\n" .format(
                user_n, user_total, user_id, illust['id'], works_n, total), end="")
            if illust['page_count'] > 1:
                self.getWorks(
                    illust_id=illust['id'],
                    page_count=illust['page_count'],
                    path=path)
            else:
                self.download(url=illust.image_urls['large'], path=path)
            works_n += 1

    def getWorks(self, illust_id, page_count, path):
        """ 下载一个illust_id下多页作品 """
        # json_result = self.pixiv.works(illust_id=illust_id)
        pamas = {'illust_id': illust_id}
        json_result, _ = self.getResult(func=self.pixiv.works, pamas=pamas)
        json_result = json_result['response'][0]['metadata']['pages']
        for i in json_result:
            self.download(url=i['image_urls']['large'], path=path)
