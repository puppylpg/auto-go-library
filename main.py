import json
import schedule
import time
from datetime import datetime
import os
import sys
from send_request import *
from manager import Manager
import argparse
import logging

manager: Manager = Manager()

DATE_HOUR = str(datetime.now().strftime('%Y-%m-%d-%H'))
DATE_TIME = DATE_HOUR

# log file
LOG_PATH = "log"
NORMAL_LOGGER = os.path.join(LOG_PATH, 'log_' + DATE_TIME + '.log')

formatter = logging.Formatter("%(asctime)s [%(levelname)-5.5s]  %(message)s")

def get_logger(name, log_file, level=logging.DEBUG, format=True):
    """To setup as many loggers as you want"""

    # output to both console and file
    console_handler = logging.StreamHandler(sys.stdout)
    file_handler = logging.FileHandler(log_file, mode='w', encoding='utf-8')

    if format:
        console_handler.setFormatter(formatter)
        file_handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger


# mkdir if not exist
if not os.path.exists(os.path.dirname(NORMAL_LOGGER)):
    os.mkdir(os.path.dirname(NORMAL_LOGGER))


log = get_logger('normal', os.path.abspath(NORMAL_LOGGER))


def read_info():
    with open("./configure.json", 'r') as f:
        configure = json.load(f)
        users = configure['users']
        for user in users:
            name = user['name']
            s = get_session(user["cookies"])
            res = post_home_page(s)
            log.info("post home page res: {}".format(res))
            if "errors" not in res.keys():
                manager.add_user(name, user["cookies"], s)
                log.info(name + "添加session成功")
            else:
                log.info(name + "添加session失败")


all_seat = [
    {
        "info": "A201考研自习室 216号",
        "lib_id": 114224,
        "seat_key": "33,13",
        "status": 1
    },
    {
        "info": "A201考研自习室 214号",
        "lib_id": 114224,
        "seat_key": "33,15",
        "status": 1
    },
    {
        "info": "A201考研自习室 222号",
        "lib_id": 114224,
        "seat_key": "31,14",
        "status": 1
    },
    {
        "info": "A201考研自习室 217号",
        "lib_id": 114224,
        "seat_key": "33,12",
        "status": 1
    },
    {
        "info": "A201考研自习室 218号",
        "lib_id": 114224,
        "seat_key": "33,11",
        "status": 1
    }
]


def go(name: str, s: requests.Session):
    # res = post_home_page(s)
    # log.info("post home page res: {}".format(res))
    # often_seat = res['data']['userAuth']['oftenseat']["list"]
    often_seat = all_seat
    often_seat_key = []
    for seat in often_seat:
        often_seat_key.append([seat['seat_key'], seat['lib_id'], seat['info']])
    log.info("ofter seats: {}".format(often_seat_key))

    for key in often_seat_key:
        log.info("{}开始预约: {}".format(name, key))
        res = book(s, key)
        log.info("book result: {}".format(res))
        status = res['data']['userAuth']['reserve']['reserveSeat']
        if status is not None and status:
            log.info("{}预约成功: {}".format(name, key))
            return
        else:
            log.info("{}预约失败: {}".format(name, key))
            # add a break
            post_home_page(s)
    log.info("{}一个也没约着……".format(name))


def save_info():
    if len(manager.get_json_object()) == 0:
        return
    output = {"users": manager.get_json_object()}
    output = json.dumps(output)
    with open("./configure.json", 'w') as f:
        f.write(output)


def job():
    log.info("{}, 开抢！！！".format(time.ctime(time.time())))
    for i in range(3):
        for user in manager.get_users():
            try:
                go(user.name, user.session)
            except Exception as e:
                log.error("Unknown error for job. Try again. Error string: {}".format(e))
                job()


def job_thread(threadName):
    schedule.every().day.at("07:00").do(job)
    schedule.every().day.at("22:35").do(job)
    while True:
        try:
            job_thread_keep_alive()
        except Exception as e:
            log.error("Unknown error for job thread keep alive. Try again. Error string: {}".format(e))


def job_thread_keep_alive():
    count_60 = 0
    while True:
        schedule.run_pending()
        time.sleep(1)
        count_60 += 1
        if count_60 == 60:
            for user in manager.get_users():
                s = user.session
                res = post_home_page(s)
                log.info("post home page res: {}".format(res))
                if res.get('errors') and res.get('errors')[0].get('code') != 0:
                    log.info(res)
                    log.info("出现了error")
                    exit()
                hold_validate(s)
            count_60 = 0
            save_info()
            log.info("save cookies success")


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-r", "--run-once", type=bool, help="run once to test", default=False)
    read_info()
    if len(manager.get_users()) == 0:
        log.info("没有可用的session")
        exit()
    if not parser.parse_args().run_once:
        job_thread("job_thread")
    else:
        job()
