import json
import schedule
import time
from send_request import *
from manager import Manager
import argparse

manager: Manager = Manager()


def read_info():
    with open("./configure.json", 'r') as f:
        configure = json.load(f)
        users = configure['users']
        for user in users:
            name = user['name']
            s = get_session(user["cookies"])
            res = post_home_page(s)
            if "errors" not in res.keys():
                manager.add_user(name, user["cookies"], s)
                print(name + "添加session成功")
            else:
                print(name + "添加session失败")


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
    # often_seat = res['data']['userAuth']['oftenseat']["list"]
    often_seat = all_seat
    often_seat_key = []
    for seat in often_seat:
        often_seat_key.append([seat['seat_key'], seat['lib_id'], seat['info']])
    print(often_seat_key)

    for key in often_seat_key:
        print("{}开始预约: {}", name, key)
        res = book(s, key)
        # print(res)
        status = res['data']['userAuth']['reserve']['reserveSeat']
        if status is not None and status:
            print("{}预约成功: {}", name, key)
            return
        else:
            print("{}预约失败: {}", name, key)
    print("{}一个也没约着……", name)


def save_info():
    if len(manager.get_json_object()) == 0:
        return
    output = {"users": manager.get_json_object()}
    output = json.dumps(output)
    with open("./configure.json", 'w') as f:
        f.write(output)


def job():
    print("{}, 开抢！！！", time.ctime(time.time()))
    for i in range(3):
        for user in manager.get_users():
            go(user.name, user.session)
            time.sleep(1)


def job_thread(threadName):
    schedule.every().day.at("07:00").do(job)
    schedule.every().day.at("22:35").do(job)
    count_60 = 0
    while True:
        schedule.run_pending()
        time.sleep(1)
        count_60 += 1
        if count_60 == 60:
            for user in manager.get_users():
                s = user.session
                res = post_home_page(s)
                if res.get('errors') and res.get('errors')[0].get('code') != 0:
                    print(res)
                    print("出现了error")
                    exit()
                hold_validate(s)
            count_60 = 0
            save_info()
            print("save cookies success")


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-r", "--run-once", type=bool, help="run once to test", default=False)
    read_info()
    if len(manager.get_users()) == 0:
        print("没有可用的session")
        exit()
    if not parser.parse_args().run_once:
        job_thread("job_thread")
    else:
        job()
