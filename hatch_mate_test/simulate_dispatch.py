from common.rabbitmq import RabbitMQ
import threading
import json
from datetime import datetime
import time
import random,os
from log import log
from common.base_method import get_all_config

path = os.path.dirname(__file__) + '/report/'
if not os.path.exists(path):
    os.mkdir(path)
log_path = path + time.strftime('%Y%m%d')+ 'simulate.txt'


class Dispatch():
    def __init__(self):
        self.msg = []
        self.task = None
        self.response = None
        self.mq_consumer = RabbitMQ(self.msg)
        self.mq_consumer.create_consumer()
        self.pro = RabbitMQ(self.msg)
        self.pro.create_producer()
        self.get_msg = threading.Thread(target=self.rec)
        self.get_msg.start()
        self.buc_in = 0
        self.is_return_buc = True
        self.is_receive_bucket = True
        self.log = log.Logger.get_logger(log_path)
        self.status = []
        self.cu = get_all_config['rabbitmq_config']['producer']['routing_key']

    def send(self, data):
        self.out_log(1,data)
        self.pro.producer_send(json.dumps(data))

    def rec(self):
        self.mq_consumer.start_consumer()

    def cur_time(self):
        time = datetime.utcnow()
        utc = time.strftime("%Y-%m-%dT%H:%M:%SZ")
        return utc

    def get_task_id(self):
        task_id = time.strftime("%m%d%H%M") + str(random.randint(0, 9)) + str(random.randint(0, 9))
        return task_id

    def storing_begin(self, data):
        self.task = self.get_task_id()
        if data['is_return_buc']:
            self.is_return_buc = True
        else:
            self.is_return_buc = False
        self.response = "rack_storing"
        res = {
            "request": self.response,
            "time": self.cur_time(),
            "data": {
                "cu": self.cu,
                "control": False,
                "type": "begin",
                "task_id": self.task,
                "name": "测试项目",
                "store_empty_rack": False,
                "begin_time": self.cur_time(),
                "is_demo": False,
                "minimum_weight": data['buc_min'],
                "target_weight": data['buc_max'],
                "exit_bucket": True if data['is_return_buc'] else False,
                "task_data": [
                    {
                    "scan": True,
                    "rack_scan": True,
                    "rack_id": data['rack_id'],
                    "rack": data['rack'],
                    "tube": data['tube'],
                    "extend_x": 0,
                    "extend_y": 0,
                    "logic_id": 0,
                    "is_source": True if data['is_source'] else False,
                }
                ],
                            }
        }
        # print(res)
        return res

    def retrieving_begin(self, data):
        self.task = self.get_task_id()
        if data['is_receive_bucket']:
            self.is_receive_bucket = False
        else:
            self.is_receive_bucket = True
        self.response = "rack_retrieving"
        res = {
    "request": self.response,
    "time": self.cur_time(),
    "data": {
        "cu": self.cu,
        "control": True,
        "type": "begin",
        "task_id": self.task,
        "name": "疾病专项研究",
        "begin_time": self.cur_time(),
        "task_data": [{
            "rack_id": data['rack_id'],
            "rack": data['rack'],
            "tube": data['tube']
        }],
        "minimum_weight": data['buc_min'],
        "target_weight": data['buc_max'],
        "exit_bucket":True if data['is_receive_bucket'] else False
    }
}
        return res

    def get_tube_no(self,data):
        res = []
        data = data.split(',')
        for i in data:
            try:
                i.split('-')
                for y in range(int(i.split('-')[0]), int(i.split('-')[1]) + 1):
                    res.append(y)
            except:
                res.append(int(i))
        return res

    def tubes_move(self,data):
        tube = []
        souce_area = self.get_tube_no(data['source_move'])
        target_area = self.get_tube_no(data['target_move'])
        for i in range(int(data['tube_num'])):
            s_no = random.choice(souce_area)
            t_no = random.choice(target_area)
            souce_area.remove(s_no)
            target_area.remove(t_no)
            tube.append({
                        "s_no": s_no,
                        "t_no": t_no,
                        "id": str(random.randint(1000,100000000000))
                    })
        return tube

    def not_move_tube(self,data):
        not_move_tube = []
        if data != '0':
            area = self.get_tube_no(data)
            for i in area:
                not_move_tube.append({
                        "no": i,
                        "id": str(random.randint(1000,100000000000))
                    })
        return not_move_tube

    def moving_begin(self,data):
        self.response = "moving"
        self.task = self.get_task_id()
        res = {
    "request": self.response,
    "time": self.cur_time(),
    "data": {
        "cu": self.cu,
        "control": True,
        "type": "begin",
        "task_id": self.task,
        "name": "疾病专项研究",
        "begin_time": self.cur_time(),
        "task_data": [{
            "rack_id": data['source_rack'],
            "rack": data['rack'],
            "tube": data['tube'],
            "tubes_move": [{
                "target_rack_id": data['target_rack'],
                "tubes": self.tubes_move(data)
            }],
            "tubes_notmove": self.not_move_tube(data['source_not_move']),
        }],
        "rack_location": [
            {
                "rack_id": data['target_rack'],
                "rack": data['rack'],
                "tube": data['tube'],
                "location": {
                    "cu": 0,
                    "ltu": 0,
                    "group": 0,
                    "unit": 0,
                    "pos": 0,
                    "is_temp_storage": False
                },
                "tubes_notmove": self.not_move_tube(data['target_not_move'])
            }
        ]
    }
}
        return res

    def begin_running(self, response, task):
        res = {
            "request": response,
            "time": self.cur_time(),
            "data": {
                "type": "begin_running",
                "task_id": task
            }
        }
        return res

    def open(self, response, task):
        res = {
            "request": response,
            "time": self.cur_time(),
            "data": {
                "type": "open",
                "task_id": task,
                "ee_list": [
                    1
                ]
            }
        }
        return res

    def pail_storing(self, response, task):
        res = {
            "request": response,
            "time": self.cur_time(),
            "data": {
                "type": "pail_storing",
                "task_id": task
            }
        }
        return res

    def close(self, response, task):
        res = {
            "request": response,
            "time": self.cur_time(),
            "data": {
                "type": "close",
                "task_id": task,
                "ee_list": [
                    1
                ]
            }
        }
        return res

    def pail_retrieving(self, response, task):
        res = {
            "request": response,
            "time": self.cur_time(),
            "data": {
                "type": "pail_retrieving",
                "task_id": task
            }
        }
        return res

    def out_log(self,status,data):
        if status==1:
            self.status.append('发起请求：{}'.format(data))
            return self.log.info('发起请求：{}'.format(data))
        if status==0:
            self.status.append('收到请求：{}'.format(data))
            return self.log.info('收到请求：{}'.format(data))

    def storing(self, data):
        self.log.info('---------------------开始存盒任务---------------------')
        self.status.append('开始存盒任务')
        self.send(self.storing_begin(data))
        while True:
            if self.msg:
                if self.msg[0].get('response') != 'report_data' and self.msg[0].get('response') != 'task_activate':
                    if self.msg[0]['data']['type'] == 'ready':
                        self.out_log(0,self.msg[0])
                        self.send(self.begin_running(self.response, self.task))
                        self.msg.pop(0)
                    elif self.msg[0]['data']['type'] == 'waiting_open':
                        self.out_log(0,self.msg[0])
                        self.send(self.open(self.response, self.task))
                        self.msg.pop(0)
                    elif self.msg[0]['data']['type'] == 'opened':
                        self.out_log(0, self.msg[0])
                        self.status.append('等待10s转动皮带，请将桶放入或者取出')
                        time.sleep(10)
                        if self.buc_in == 0:
                            self.send(self.pail_storing(self.response, self.task))
                            self.buc_in = 1
                        elif self.buc_in == 1 & self.is_return_buc:
                            self.send(self.pail_retrieving(self.response, self.task))
                            self.buc_in = 0
                        self.msg.pop(0)
                    elif self.msg[0]['data']['type'] == 'waiting_close':
                        self.out_log(0, self.msg[0])
                        self.msg.pop(0)
                    elif self.msg[0]['data']['type'] in ['end', 'abnormal_end', 'reject']:
                        self.out_log(0, self.msg[0])
                        self.status.append('存盒流程结束')
                        self.status.append('end')
                        self.msg.pop(0)
                        break
                    else:
                        self.out_log(0, self.msg[0])
                        self.msg.pop(0)
                else:
                    self.msg.pop(0)
            else:
                continue

    def send_close(self):
        self.send(self.close(self.response, self.task))


    def retrieving(self, data):
        self.log.info('---------------------开始取盒任务---------------------')
        self.status.append('开始取盒任务')
        print(self.status)
        self.send(self.retrieving_begin(data))
        while True:
            if self.msg:
                if self.msg[0].get('response') != 'report_data' and self.msg[0].get('response') != 'task_activate':
                    if self.msg[0]['data']['type'] == 'ready':
                        # self.status.append('收到设备准备消息：'+str(self.msg[0]))
                        self.out_log(0, self.msg[0])
                        self.send(self.begin_running(self.response, self.task))
                        self.msg.pop(0)
                    elif self.msg[0]['data']['type'] == 'waiting_open':
                        # self.status.append('收到设备等待开门消息：' + str(self.msg[0]))
                        self.out_log(0, self.msg[0])
                        self.send(self.open(self.response, self.task))
                        self.msg.pop(0)
                    elif self.msg[0]['data']['type'] == 'opened':
                        # self.status.append('收到设备开门完成消息：' + str(self.msg[0]))
                        self.out_log(0, self.msg[0])
                        self.status.append('等待10s转动皮带，请将桶放入或者取出')
                        time.sleep(10)
                        # if self.buc_in == 0 & self.is_receive_bucket:
                        #     self.send(self.pail_storing(self.response, self.task))
                        #     self.buc_in = 1
                        # elif self.buc_in == 1 :
                        self.send(self.pail_retrieving(self.response, self.task))
                            # self.buc_in = 0
                        self.msg.pop(0)
                    elif self.msg[0]['data']['type'] == 'waiting_close':
                        # self.status.append('收到设备等待关门消息：' + str(self.msg[0]))
                        self.out_log(0, self.msg[0])
                        self.msg.pop(0)
                    elif self.msg[0]['data']['type'] in ['end', 'abnormal_end', 'reject']:
                        # self.status.append('收到设备结束或者异常消息：' + str(self.msg[0]))
                        self.out_log(0, self.msg[0])
                        self.status.append('取盒流程结束')
                        self.status.append('end')
                        self.msg.pop(0)
                        break
                    else:
                        self.out_log(0, self.msg[0])
                        self.msg.pop(0)
                else:
                    self.msg.pop(0)
            else:
                continue

    def moving(self,data):
        self.log.info('---------------------开始挑管任务---------------------')
        self.status.append('开始挑管任务')
        self.send(self.moving_begin(data))
        while True:
            if self.msg:
                if self.msg[0].get('response') != 'report_data' and self.msg[0].get('response') != 'task_activate':
                    if self.msg[0]['data']['type'] == 'ready':
                        # self.status.append('收到设备准备消息：' + str(self.msg[0]))
                        self.out_log(0, self.msg[0])
                        self.send(self.begin_running(self.response, self.task))
                        self.msg.pop(0)
                    elif self.msg[0]['data']['type'] in ['end', 'abnormal_end', 'reject']:
                        # self.status.append('收到设备结束或者异常消息：' + str(self.msg[0]))
                        self.out_log(0, self.msg[0])
                        self.status.append('挑管流程结束')
                        self.status.append('end')
                        self.msg.pop(0)
                        break
                    else:
                        self.out_log(0, self.msg[0])
                        self.msg.pop(0)
                else:
                    self.msg.pop(0)
            else:
                continue


    def buc_sto_or_ret(self,way):
        if way == 1:
            self.response = 'bucket_storing'
        else:
            self.response = 'bucket_retrieving'
        self.task = self.get_task_id()
        self.log.info('---------------------开始{}桶任务---------------------'.format('存' if way else '取'))
        self.status.append('开始{}桶任务'.format('存' if way else '取'))
        self.send(self.open(self.response,self.task))
        while True:
            if self.msg:
                if self.msg[0].get('response') != 'report_data' and self.msg[0].get('response') != 'task_activate':
                    if self.msg[0]['data']['type'] == 'opened':
                        self.status.append('收到设备开门完成消息：' + str(self.msg[0]))
                        self.out_log(0, self.msg[0])
                        time.sleep(10)
                        self.status.append('等待10s转动皮带，请将桶放入或者取出')
                        # if self.buc_in == 0 & self.is_receive_bucket:
                        if way:
                            self.send(self.pail_storing(self.response, self.task))
                            self.buc_in = 1
                        # elif self.buc_in == 1:
                        else:
                            self.send(self.pail_retrieving(self.response, self.task))
                            self.buc_in = 0
                        self.msg.pop(0)
                    elif self.msg[0]['data']['type'] == 'waiting_close':
                        # self.status.append('收到设备等待关门消息：' + str(self.msg[0]))
                        self.out_log(0, self.msg[0])
                        self.msg.pop(0)
                    elif self.msg[0]['data']['type'] =='closed':
                        # self.status.append('收到设备关门消息：' + str(self.msg[0]))
                        self.out_log(0, self.msg[0])
                        self.status.append('{}桶流程结束'.format('存' if way else '取'))
                        self.status.append('end')
                        self.msg.pop(0)
                        break
                    else:
                        self.out_log(0, self.msg[0])
                        self.msg.pop(0)
                else:
                    self.msg.pop(0)
            else:
                continue