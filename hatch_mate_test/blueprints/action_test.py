from flask import Blueprint,request,jsonify,render_template
from common.base_method import get_all_config,modify_config
from action_Test import action_

action = Blueprint('action',__name__)

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
    res = action_().con()
    return res

@action.route('/action_move_tube')
def action_move_tube():
    # print(request.args)
    res = list(map(int, [request.args['loop_times'], request.args['move_ways'], request.args['tube_nums'],
              request.args['stor_rackA'], request.args['stor_rackB'], request.args['stor_tubeA'],
              request.args['stor_tubeB'], request.args['is_ran'], request.args['move_order']]))
    action_().tube_move(res[0],res[1],res[2],res[3],res[4],res[5],res[6],res[7],res[8])
    return '执行完成'


@action.route('/action_move_all')
def action_move_all():
    # print(request.args)
    action_().all_test(int(request.args['all_loop_times']),int(request.args['all_tube_num']),int(request.args['all_rack']),int(request.args['all_tube']),
                       int(request.args['move_ways']))
    return '执行完成'


@action.route('/action_move_rack')
def action_move_rack():
    action_().rack_move(request.args['stor_rack'],request.args['stor_tube'])
    return '执行完成'

@action.route('/stop')
def stop():
    action_().stop()

@action.route('/stop_move_rack')
def stop_move():
    action_().stop_move()