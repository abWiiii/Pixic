from . import utils
from .utils import CONFIG

import pixivpy3
import os
import time
import logging
from random import randint

__all__ = ('PixDown')


class PixDown():
    """ Main function of this package """

    def __init__(self):
        self.DOWNLOAD_REEOR = {'user': [],
                               'works': []}
        utils.loadConfig()

        self.setLog()
        params = self.setProxy()
        self.pixiv = pixivpy3.PixivAPI(**params)
        self.pixiv.set_accept_language("zh-cn")
        self.login()

    def setLog(self):
        """ 设置log """
        logging.basicConfig(level=CONFIG['LOGGING_LEVEL'], filename="log.log", filemode='a',
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
        try:
            user_id = CONFIG['user_id']
            user_password = CONFIG['user_password']
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
            params = CONFIG['PAMAS']
            print("Proxy = ", params)
        except Exception:
            print("NOT proxy")
            params = {}
        # TODO 读取config中的代理，留下全局代理位
        return params

    # --------------------------------------------------------

    def getResult(self, func, pamas: dict):
        """ json_result获取函数 """
        logging.info("getResult - {0} - {1}" .format(func, pamas))

        # 多次重连
        def connection(func, pamas: dict):
            logging.debug("{0} - {1}" .format(func, pamas))
            connection_n = 1
            json_result = {'status': 'failure'}
            while json_result['status'] == 'failure':
                try:
                    json_result = func(**pamas)
                    if json_result['status'] == 'success':
                        return json_result
                    logging.debug(
                        "getResult.connection - json_result['status']=='failure' Reconnection={0} - {1}" .format(connection_n, func))
                except Exception as e:
                    logging.debug(
                        "Reconnection={0} : {1}" .format(connection_n, e))
                if connection_n == CONFIG['JSON_RECONNECTION']:
                    logging.warning(
                        "reconnection error: {0} - {1}".format(func, pamas))
                    print("reconnection error: {0} - {1}" .format(func, pamas))
                    return False
                connection_n += 1
                time.sleep(randint(5, 20))
            return json_result

        json_result = connection(func, pamas)
        if 'per_page' in pamas:
            per_page = pamas['per_page']
            total = json_result['pagination']['total']
            if total >= per_page:
                json_result = connection(func, pamas)
        else:
            total = None
        if json_result is False:
            return(False, False)

        return (json_result, total)

    def download(self, illust_id, page_count, url, path, replace=False):
        """ 下载 """
        logging.info("{0} - {1}:{2} - {3}" .format(path,
                                                   illust_id, page_count, url))

        def download(_url):
            logging.debug("illust_id={0} downloading" .format(illust_id))
            down_bool = False
            download_n = 1
            while down_bool is False:
                down_bool = self.pixiv.download(
                    url=_url, path=path, replace=replace)
                if down_bool:
                    print(illust_id, "download done")
                    logging.debug(
                        "illust_id {0} download done - {1}" .format(illust_id, download_n))
                    break
                if download_n == CONFIG['DOWN_RECONNECTION']:
                    print("download failure:", illust_id)
                    logging.warning(
                        "download failure: {0} - {1}".format(illust_id, _url))
                    self.DOWNLOAD_REEOR['works'].append(illust_id)
                    break
                download_n += 1
                print(illust_id, " relink - ", download_n)
                time.sleep(randint(3, 15))

        if page_count > 1:
            pamas = {'illust_id': illust_id}
            json_result, _ = self.getResult(func=self.pixiv.works, pamas=pamas)
            if json_result is False:
                print("get illust id {0} unsuccess".format(illust_id))
            json_result = json_result['response'][0]['metadata']['pages']
            for i in json_result:
                download(_url=i['image_urls']['large'])
        else:
            download(_url=url)

    # ------------------------------------------------------------------------

    def getFollowList(self) -> list:
        """ 获取关注的用户列表 (Pixiv事务所除外UID=11)"""

        def get(publicity) -> list:

            pamas = {'publicity': publicity,
                     'per_page': CONFIG['FOLLOW_PER_PAGE'], }
            rog_dict = self.getResult(
                func=self.pixiv.me_following, pamas=pamas)
            rog_dict, total = rog_dict
            if rog_dict is False:
                return False
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

    def getUserWorks(self, user_id):
        """ 获取用户id的作品列表 """
        # time.sleep(random() * 4)
        print("get user %d works..." % user_id)
        pamas = {"author_id": user_id,
                 'per_page': CONFIG['USER_WORKS_PER_PAGE'], }
        json_dict, total = self.getResult(
            func=self.pixiv.users_works, pamas=pamas)
        if json_dict is False:
            return (False, False)
        if total == 0:
            print("user %d no work!" % user_id)
            return (False, False)
        else:
            return json_dict['response'], total

    def downloadUserWorks(self, user_id, user_n, user_total):
        """ 下载用户id的作品列表 """
        time.sleep(randint(1, 6))
        json_dict, total = self.getUserWorks(user_id)
        if json_dict is False:
            print("error: get user{0} works unsuccess" .format(user_id))
            return

        path = utils.setdir(CONFIG['DOWNLOAD_WORKS'], str(user_id))
        works_n = 1
        for illust in json_dict:
            # illust["page_count"]是一个illust作品数量
            print(">>> {0:>5}/{1:<5}user {2:<10} - works {3:<10} : {4:>4}/{5:<4}\n" .format(
                user_n, user_total, user_id, illust['id'], works_n, total), end="")
            illust_id = illust['id'],
            page_count = illust['page_count']
            self.download(illust_id=illust_id, page_count=page_count,
                          url=illust.image_urls['large'], path=path)
            works_n += 1
