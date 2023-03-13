import os,yaml


project_path = os.path.dirname(os.path.dirname(__file__))
file = os.path.join(project_path, 'config', 'config.yaml')

# 获取所有配置
def get_config():
    with open(file, encoding='utf-8') as f:
        return yaml.safe_load(f)

def modify_config(data):
    with open(file, 'w') as f:
        return yaml.dump(data, f)

class config:
    def __init__(self):
        self.config = get_config()


get_all_config = config().config
print(get_all_config)