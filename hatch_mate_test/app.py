import json

from flask import Flask, render_template
import os,yaml
from blueprints.dispatch_test import dispatch
from blueprints.action_test import action
from common.base_method import get_all_config

app = Flask(__name__)
app.register_blueprint(dispatch)
app.register_blueprint(action)
app.config['SECRET_KEY'] = os.urandom(24)



@app.route('/')
def index():
    return render_template('index.html')

@app.route('/dispatch_test')
def dispatch_test():
    config = get_all_config['rabbitmq_config']
    return render_template('dispatch_test.html',ip = config['connect_info']['host'],
                          port=config['connect_info']['port'],
                           username = config['connect_info']['username'],
                           password = config['connect_info']['password'],
                           cu = config['producer']['routing_key'])


@app.route('/action_test')
def action_test():
    data = get_all_config['plc_config']
    return render_template('action_test.html',plc_ip=data['PLC_IP'],plc_port=data['PLC_PORT'])


if __name__ == '__main__':
    app.run(debug=True)
