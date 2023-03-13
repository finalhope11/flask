
import pika
import json

from common.base_method import get_all_config


class RabbitMQ:

    def __init__(self,msg):
        self.config = get_all_config['rabbitmq_config']
        self.conn = self.__create_connection(**self.config['connect_info'])         #建立连接
        self.channel = self.conn.channel()      #开辟管道
        self.msg = msg

    def __create_connection(self, username, password, host, port, virtual_host):
        credentials = pika.PlainCredentials(username=username, password=password)
        parameters = pika.ConnectionParameters(host=host, port=port, virtual_host=virtual_host, credentials=credentials,heartbeat=0)
        return pika.BlockingConnection(parameters=parameters)

    # 创建消费者
    def create_consumer(self):
        self.__create_consumer(**self.config['consumer'])

    # 开始运行
    def start_consumer(self, callback=None):
        queue = self.config['consumer']['queue']

        def callback(channel, method, properties, body):
            try:
                res=json.loads(body)
                print(res,'\n')
                self.msg.append(res)
                # logging.info('接收到json消息{}'.format(res),'\n')
            except:
                print(body,'\n')
                # logging.info('接收到非json消息{}'.format(res), '\n')
            # print(type(body))
            self.channel.basic_ack(delivery_tag=method.delivery_tag)#消费信息，注释后不消费
        self.channel.basic_consume(queue=queue, on_message_callback=callback)
        self.channel.start_consuming()


    
    # 创建生产者
    def create_producer(self):
        self.__create_producer(**self.config['producer'])
    
    # 生产者发送信息
    def producer_send(self, msg):
        self.__producer_send_msg(**self.config['producer'], msg=msg)
    
    def __create_consumer(self, queue='', exchange='', exchange_type='', routing_key=''):
        self.__declare_queue(queue=queue)
        self.__declare_exchange(exchange=exchange, exchange_type=exchange_type)
        self.__binding(queue=queue, exchange=exchange, routing_key=routing_key)

    def __create_producer(self, exchange='', exchange_type='', **kwargs):
        self.__declare_exchange(exchange=exchange, exchange_type=exchange_type)

    def __producer_send_msg(self, exchange='', routing_key='', msg='', **kwargs):
        self.channel.basic_publish(exchange=exchange, routing_key=routing_key, body=msg.encode(),
                                   properties=pika.BasicProperties(delivery_mode=2))

    # 创建队列并持久化
    def __declare_queue(self, queue=''):
        self.channel.queue_declare(queue=queue, durable=True)

    # 创建交换机并持久化
    def __declare_exchange(self, exchange='', exchange_type=''):
        self.channel.exchange_declare(exchange=exchange, exchange_type=exchange_type, durable=True)

    # 绑定交换机
    def __binding(self, queue='', exchange='', routing_key=''):
        self.channel.queue_bind(queue=queue, exchange=exchange, routing_key=routing_key)
