from flask import Blueprint,request,jsonify
import json,yaml,os
from simulate_dispatch import Dispatch
from common.base_method import get_all_config,modify_config

dispatch = Blueprint('dispatch',__name__)
global dis_con


@dispatch.route('/dispatch_con',methods=['GET'])
def dispatch_con():
    global dis_con
    try:
        ip = request.args['ip']
        port = request.args['port']
        username = request.args['username']
        password = request.args['password']
        cu = request.args['cu']
        data = get_all_config
        data['rabbitmq_config']['connect_info']['host'] = ip
        data['rabbitmq_config']['connect_info']['port'] = port
        data['rabbitmq_config']['connect_info']['username'] =username
        data['rabbitmq_config']['connect_info']['password'] = password
        data['rabbitmq_config']['producer']['routing_key'] = cu
        modify_config(data)
        dis_con = Dispatch()
        print('connect success')
        return 'connect success'
    except:
        return 'connect failed,please check your config!'

@dispatch.route('/dispatch_storing',methods=['POST'])
def dispatch_storing():
    global dis_con
    data = json.loads(request.get_data())
    dis_con.storing(data)
    return '执行完成'


@dispatch.route('/dispatch_retrieving',methods=['POST'])
def dispatch_retrieving():
    global dis_con
    data = json.loads(request.get_data())
    dis_con.retrieving(data)
    return '执行完成'

@dispatch.route('/dispatch_moving',methods = ['POST'])
def dispatch_moving():
    global dis_con
    data = json.loads(request.get_data())
    dis_con.moving(data)
    return '执行完成'


@dispatch.route('/show_status',methods= ['GET'])
def show_status():
    global dis_con
    if dis_con.status:
        res = dis_con.status[0]
        print(res)
        dis_con.status.pop(0)
        return res
    else:
        return 'None'


