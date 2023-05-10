from flask import Blueprint,request,jsonify,render_template
from common.base_method import get_all_config,modify_config
from action_Test import action_
import traceback

action = Blueprint('action',__name__)


init_action = action_()
@action.route('/action_tube_move')
def action_tube_move():
    return render_template('action_tube_move.html')

@action.route('/action_rack_move')
def action_rack_move():
    return render_template('action_rack_move.html')

@action.route('/action_all_test')
def action_all_test():
    return render_template('action_all_test.html')


@action.route('/action_test_con')
def action_test_con():
    ip = request.args['IP']
    port = request.args['PORT']
    select = request.args['SELECT']
    data = get_all_config
    data['plc_config']['PLC_IP']=ip
    data['plc_config']['PLC_PORT']=port
    data['plc_config']['PLC_AGREEMENT']=select
    modify_config(data)
    res = init_action.con()
    return res

@action.route('/action_move_tube')
def action_move_tube():
    # print(request.args)
    try:
        res = list(map(int, [request.args['loop_times'], request.args['move_ways'], request.args['tube_nums'],
                  request.args['stor_rackA'], request.args['stor_rackB'], request.args['stor_tubeA'],
                  request.args['stor_tubeB'], request.args['is_ran'], request.args['move_order']]))
        init_action.tube_move(res[0],res[1],res[2],res[3],res[4],res[5],res[6],res[7],res[8])
    except:
        return '执行失败'
    return '执行完成'


@action.route('/action_move_all')
def action_move_all():
    # print(request.args)
    try:
        init_action.all_test(int(request.args['all_loop_times']),int(request.args['all_tube_num']),int(request.args['all_rackA']),int(request.args['all_tubeA']),
                             int(request.args['all_rackB']), int(request.args['all_tubeB']),int(request.args['move_ways']))
    except Exception as e:
        print('traceback.format_exc\t', traceback.format_exc(e))
    return '执行完成'


@action.route('/action_move_rack')
def action_move_rack():
    try:
        init_action.rack_move(int(request.args['stor_rack']),int(request.args['stor_tube']))
    except Exception as e:
        print('traceback.format_exc\t', traceback.format_exc(e))
        return '执行失败'
    return '执行完成'

@action.route('/stop')
def stop():
    try:
        init_action.stop()
    except:
        return '停止失败'
    return '停止成功'

@action.route('/stop_move_rack')
def stop_move():
    try:
        init_action.stop_move()
    except:
        return '停止失败'
    return '停止成功'