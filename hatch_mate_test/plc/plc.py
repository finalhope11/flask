# encoding: utf-8
"""
 @author:   yaowenpei
 @contact:  yaowp@genepoint.cn
 @time:     2021/3/26 19:30
 @desc:     
"""

import socket
import logging
import os
import time
import ast
import struct
from decimal import Decimal

project_path = os.path.dirname(os.path.dirname(__file__))
MCERRCODE = {
    "c050": "指定的子标头是非数值ASCII代码或执行ASCII代码通信时，指定的软元件代码不存在",
    "4a00": "指定的网络编号不是0x00",
    "4b00": "指定的PC编号不是0xff或指定的IO编号不是0x03ff",
    "c058": "执行ASCII代码通信时，指定的数据比设定的软元件数或块数短",
    "c059": "指定了不支持的命令或子命令",
    "c061": "执行二进制代码通信时，指定的数据比设定的软件件数或块数短",
    "c05b": "以二进制代码进行通信时，指定了不存在的软元件代码",
    "c056": "指定的软元件编号超出了范围",
    "c051": "指定的软元件数超出了范围",
    "c05c": "将子命令指定为0001，执行处理位软元件的命令时，却指定了字软元件"
}


class WriteLog:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        directory = os.path.join(project_path, 'report')
        if not os.path.exists(directory):
            os.mkdir(directory)
        # 指定文件名和路径
        path = os.path.join(project_path, 'report', time.strftime('%Y%m%d'))

        handler = logging.FileHandler("{0}.log".format(path))
        handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s,%(levelname)s,%(message)s')
        handler.setFormatter(formatter)

        console = logging.StreamHandler()
        console.setFormatter(formatter)
        console.setLevel(logging.INFO)

        self.logger.addHandler(handler)
        self.logger.addHandler(console)

    pass


logger = WriteLog().logger


# logger = log.logger


class NetWorkBase:
    def __init__(self, ip=None, port=None):
        self.Socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.ip = ip
        self.port = port
        self.net_flag = False

    def link(self, timeout=60):
        self.Socket.settimeout(timeout)
        # self.Socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, True)  # 解决万一出现心跳报文的粘包问题
        # socket长连接设置，可以在客户端，也可以在服务端
        self.Socket.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, True)  # 开启长连接
        self.Socket.ioctl(socket.SIO_KEEPALIVE_VALS,
                          (1,  # 开启保活机制
                           60 * 1000,  # 1分钟后如果对方还没有反应，开始探测连接是否存在
                           15 * 1000)  # 15S探测一次，默认探测10次，失败则断开连接
                          )
        for i in range(5):
            try:
                rev = self.Socket.connect_ex((self.ip, self.port))
                if rev == 0:
                    logger.info("PLC连接成功，地址为%s:%s" % (self.ip, self.port))
                    self.net_flag = True
                    return True
            except Exception as ex:
                logger.error(ex)
                self.net_flag = False
                time.sleep(5)
        return False

    def _send(self, command):
        for i in range(3):
            try:
                if self.net_flag:
                    # sendall成功返回None，失败则抛出异常
                    self.Socket.sendall(command)
                    self.net_flag = True
                    return True
            except Exception as es:
                logger.error(es)
                self.net_flag = False
                self.link()
                time.sleep(5)
        self.net_flag = False
        return False

    def _rev(self):
        try:
            if self.net_flag:
                # 接收不能重复出发接收，因为接收超时了的话，如果要再接收肯定接收不到要的消息，而再重发需要接收的命令的话，PLC状态不知道能不能兼容该命令
                self.Socket.settimeout(60)
                msg = self.Socket.recv(1024 * 20)
                # print(msg)
                self.net_flag = True
                return msg
        except Exception as es:
            logger.error(es)
            self.net_flag = False
            return False

    def send_and_rev(self, command):
        send_flag = self._send(command)
        if send_flag:
            return self._rev()
        else:
            return False

    def close(self):
        self.Socket.close()
        self.net_flag = False
        logger.info("PLC连接关闭")

    pass


class MChelper:
    # 辅助函数：bytearray转换成int
    @staticmethod
    def bytearray2int(byte_array=None, int_type=16):
        """
        辅助函数：bytearray转换成int, 若有表示负数的，直接转换成了负整数
        :byte_array:    bytearray列表，这里一般是MC协议返回后的未经过处理的bytearray字符串
        :int_type:      [16 、 32 、 64]
        :return:        False-转换错误  [……]-转换成功
        """
        if int_type not in [16, 32, 64]:
            logger.error("bytearray仅可转换成[4,16,32,64]类型的Int")
            return False
        real_len = len(byte_array) * 8 // int_type  # 最终转换后的数据的长度
        return_data = []  # 返回的数据列表
        for i in range(real_len):
            if int_type == 16:  # 转换成int16
                i_data = bytearray(2)
                i_data[0] = byte_array[2 * i]  # L8位
                i_data[1] = byte_array[2 * i + 1]  # H8位
                new_data = ast.literal_eval(hex(i_data[1]) + hex(i_data[0])[2:])
                new_data = MChelper.bin2dec_uint(new_data, int_type=int_type)
                return_data.append(new_data)
            elif int_type == 32:  # 转换成int32
                i_data = bytearray(4)
                i_data[0] = byte_array[4 * i]  # 第一个字节的L8位
                i_data[1] = byte_array[4 * i + 1]  # 第一个字节的H8位
                i_data[2] = byte_array[4 * i + 2]  # 第二个字节的L8位
                i_data[3] = byte_array[4 * i + 3]  # 第二个字节的H8位
                new_data = hex(i_data[3]) + hex(i_data[2])[2:] + hex(i_data[1])[2:] + hex(i_data[0])[2:]
                new_data = ast.literal_eval(new_data)
                new_data = MChelper.bin2dec_uint(new_data, int_type=int_type)
                return_data.append(new_data)
            else:  # 转换成int64
                i_data = bytearray(8)
                i_data[0] = byte_array[8 * i]  # 第一个字节的L8位
                i_data[1] = byte_array[8 * i + 1]  # 第一个字节的H8位
                i_data[2] = byte_array[8 * i + 2]  # 第二个字节的L8位
                i_data[3] = byte_array[8 * i + 3]  # 第二个字节的H8位
                i_data[4] = byte_array[8 * i + 4]  # 第三个字节的L8位
                i_data[5] = byte_array[8 * i + 5]  # 第三个字节的H8位
                i_data[6] = byte_array[8 * i + 6]  # 第四个字节的L8位
                i_data[7] = byte_array[8 * i + 7]  # 第四个字节的H8位
                new_data = '0x'
                for index in range(len(i_data)):
                    new_data += hex(i_data[7 - index])[2:]
                # new_data = hex(i_data[7]) + hex(i_data[6])[2:] + hex(i_data[5])[2:] + hex(i_data[4])[2:] + \
                #            hex(i_data[3])[2:] + hex(i_data[2])[2:] + hex(i_data[1])[2:] + hex(i_data[0])[2:]
                new_data = ast.literal_eval(new_data)
                new_data = MChelper.bin2dec_uint(new_data, int_type=int_type)
                return_data.append(new_data)
        return return_data

    # 辅助函数：bytearray转换成bit MC协议标准的4位标识一个bit
    # @staticmethod
    # def bytearray2bit(byte_array=None, length=None):
    #     """
    #     辅助函数：bytearray转换成bit
    #     :byte_array:    bytearray列表，这里一般是MC协议返回后的未经过处理的bytearray字符串
    #     :length:        int, 需要转换的长度
    #     :return:        False-转换错误  [……]-转换成功
    #     """
    #     return_data = []
    #     for i_byte in byte_array:
    #         if i_byte not in [0, 1, 16, 17]:
    #             return False
    #         i_byte = hex(i_byte)[2:]
    #         i_byte = i_byte if len(i_byte) == 2 else "0" + i_byte
    #         return_data.append(int(i_byte[0]))
    #         return_data.append(int(i_byte[1]))
    #     return_data = return_data if len(return_data) == length else return_data[:-1]
    #     return return_data

    @staticmethod
    def bytearray2bit(bytearrays=None, length=1):
        """
        辅助函数：从bytearray转换成bit型
        :param bytearrays: 字节串
        :param length: 读取的长度
        :return:
        """
        return_data = []
        for byte in bytearrays:
            if byte == 0:
                h_byte = 0
                l_byte = 0
            elif byte == 1:
                h_byte = 0
                l_byte = 1
            elif byte == 16:
                h_byte = 1
                l_byte = 0
            else:
                h_byte = 1
                l_byte = 1
            return_data.append(h_byte)
            return_data.append(l_byte)
        return return_data[:length]

    # 辅助函数：bytearry转换成bit,这里是以字节获取的转换,即16位标识16个bit
    @staticmethod
    def bytearray2bit_from_byte(byte_array=None):
        """
        辅助函数：辅助函数：bytearry转换成bit,这里是以字节获取的转换,即16位标识16个bit
        :byte_array:    bytearray列表，这里一般是MC协议返回后的未经过处理的bytearray字符串
        :return:        False-转换错误  [……]-转换成功
        """
        return_data = []
        for i in range(len(byte_array) // 2):
            i_byte = hex(byte_array[2 * i + 1]) + hex(byte_array[2 * i])[2:]
            i_byte = ast.literal_eval(i_byte)
            i_byte = MChelper.filled_in_num(i_byte, num_len=16)  # 16位 “0” “1”列表
            i_byte = i_byte[0]
            i_byte = i_byte[::-1]
            bit_list = []
            for index in i_byte:
                bit_list.append(int(index))
            return_data += bit_list
        return return_data

    # 辅助函数：int16字转换成bit list
    @staticmethod
    def int2bit(int_list=None, int_type=16):
        """
        辅助函数：int16字转换成bit list
        :int_list:      int整数列表
        :return:        False-转换错误  [……]-转换成功
        """
        if int_type not in [16, 32, 64]:
            logger.error("bytearray仅可转换成[4,16,32,64]类型的Int")
            return False
        return_data = []
        for int_data in int_list:
            int_data = MChelper.filled_in_num(int_data, int_type)
            int_data.reverse()
            bit_list = []
            for i in int_data:
                bit_list.append(int(i))
            return_data += bit_list
        return return_data

    # 辅助函数: bit列表转换成整数列表
    @staticmethod
    def bit2int(bit_list=None, int_type=16):
        """
        辅助函数: bit列表转换成整数列表
        :bit_list:      bit列表
        :return:        False-转换错误  [……]-转换成功
        """
        return_data = []
        if len(bit_list) % int_type != 0:
            fill_bit_list = [0] * (int_type - len(bit_list) % int_type)
            bit_list += fill_bit_list
        for i in range(len(bit_list) // int_type):
            i_data = bit_list[16 * i: 16 * i + 16]
            i_data.reverse()
            data = ''
            for index in i_data:
                data += str(index)
            data = int(data, 2)
            return_data.append(data)
        return return_data

    # 辅助函数：int转换成bytearray
    @staticmethod
    def int2bytearray(int_list=None, int_type=16):
        """
        辅助函数：int转换成bytearray， 负整数也可以直接使用
        :byte_array:    int型字符列表列表，这里一般是MC协议返回后的未经过处理的bytearray字符串
        :int_type:      [16 、 32 、 64]
        :return:        False-转换错误  [……]-转换成功
        """
        if int_type not in [16, 32, 64]:
            logger.error("bytearray仅可转换成[4,16,32,64]类型的Int")
            return False
        return_data = bytearray((int_type // 8) * len(int_list))
        for i, i_data in enumerate(int_list):
            if i_data < 0:
                # 如果是负数，将其转换成带符号二进制直接表示的整数
                i_data = MChelper.dec2bin_uint(i_data, int_type=int_type)
            if int_type == 16:  # int16转换成字符串
                i_data = hex(i_data)[2:]
                i_data = i_data if len(i_data) == 4 else "0" * (4 - len(i_data)) + i_data
                return_data[2 * i] = ast.literal_eval(("0x" + i_data[2:]))
                return_data[2 * i + 1] = ast.literal_eval(("0x" + i_data[:2]))
            elif int_type == 32:  # int32位转换成字符串
                i_data = hex(i_data)[2:]
                i_data = i_data if len(i_data) == 8 else "0" * (8 - len(i_data)) + i_data
                return_data[4 * i] = ast.literal_eval(("0x" + i_data[6:]))
                return_data[4 * i + 1] = ast.literal_eval(("0x" + i_data[4:6]))
                return_data[4 * i + 2] = ast.literal_eval(("0x" + i_data[2:4]))
                return_data[4 * i + 3] = ast.literal_eval(("0x" + i_data[:2]))
            else:  # int64位转换成字符串
                i_data = hex(i_data)[2:]
                i_data = i_data if len(i_data) == 16 else "0" * (16 - len(i_data)) + i_data
                return_data[8 * i] = ast.literal_eval(("0x" + i_data[14:]))
                return_data[8 * i + 1] = ast.literal_eval(("0x" + i_data[12:14]))
                return_data[8 * i + 2] = ast.literal_eval(("0x" + i_data[10:12]))
                return_data[8 * i + 3] = ast.literal_eval(("0x" + i_data[8:10]))
                return_data[8 * i + 4] = ast.literal_eval(("0x" + i_data[6:8]))
                return_data[8 * i + 5] = ast.literal_eval(("0x" + i_data[4:6]))
                return_data[8 * i + 6] = ast.literal_eval(("0x" + i_data[2:4]))
                return_data[8 * i + 7] = ast.literal_eval(("0x" + i_data[:2]))
        return return_data

    # 辅助函数： bit转换成bytearray
    @staticmethod
    def bit2bytearray(bit_list=None):
        """
        # 辅助函数： bit转换成bytearray
        :bit_list:
        :return: False-转换错误  [……]-转换成功
        """
        bit_list = bit_list if len(bit_list) % 2 == 0 else bit_list + [0]
        return_data = bytearray(len(bit_list) // 2)
        for i in range(len(return_data)):
            return_data[i] = ast.literal_eval('0x' + str(bit_list[2 * i]) + str(bit_list[2 * i + 1]))
        return return_data

    # 带符号的二进制所表示的整数转换成负整数
    @staticmethod
    def bin2dec_uint(value, int_type=16):
        """
        辅助函数：将带符号的二进制表示的整数转换成负整数 （eg: -45的直接整型表达为65491，需要将其转换成-45）
        :value:     被转换的带符号的二进制其直接int化的整数
        :int_type:  二进制整数所表示的是int16、int32、还是int64
        :return:    最后还原的负整数
        """
        if int_type not in [16, 32, 64]:
            logger.error("int只能有int16 、 int32、 int64，输入参数错误")
            return False
        value_str = MChelper.filled_in_num(value, num_len=int_type)
        if value_str[0][0] == "1":
            # 表示为负数
            # step1. 二进制取反
            new_vaule_str = ''
            for i in value_str[0]:
                if i == '1':
                    new_vaule_str += '0'
                else:
                    new_vaule_str += '1'
            # step2. 二进制+1
            new_vaule_str = bin(int(new_vaule_str, 2) + 1)
            # step3. 转换成十进制*（-1）
            return -int(new_vaule_str, 2)
        else:
            return value

    # 负整数转换成带符号的二进制所表示的整数
    @staticmethod
    def dec2bin_uint(value, int_type=16):
        """
        辅助函数：将负整数转换成带符号的二进制所表示的整数
        :value:     负整数的值
        :int_type:  转换成int16、int32还是int64
        :return:    被转换后的整数(十进制)
        """
        if value < 0:
            if int_type not in [16, 32, 64]:
                logger.error("int只能有int16 、 int32、 int64，输入参数错误")
                return False
            if int_type == 16:
                value = bin(value & 0xffff)
            elif int_type == 32:
                value = bin(value & 0xffffffff)
            else:
                value = bin(value & 0xffffffffffffffff)
            return int(value, 2)
        else:
            return value

    # 辅助函数：补全函数
    @staticmethod
    def filled_in_num(data, num_len=8):
        """
        辅助函数，按给定的长度将数据用“0”补齐
        :data:          要补齐的数据，类型str
        :num_len:       要补齐后的最终长度，类型int
        :return_data:   补齐后的字符串，如“0110 1001”
        """
        if type(data) is int:
            data = [data]
        return_data = []
        for i_data in data:
            i_data = bin(i_data)[2:]
            i_data = i_data if len(i_data) == num_len else "0" * (num_len - len(i_data)) + i_data
            return_data.append(i_data)
        return return_data

    pass


# MC协议，当前适用于三菱、基恩士
class McNetBinary:
    def __init__(self, plc_type=None, ip=None, port=None):
        self.plc_type = plc_type
        self.net = NetWorkBase(ip, port)
        self.net.link()

    # (私有函数)建立发送命令
    def _bulid_read_command(self, command=None, subcommand=None, address=None, length=None):
        """
        建立发送命令
        :command:       [0x01, 0x04]--读                       (list)
        :subcommand:    子命令，根据具体的命令来看                  (list)
        :address:       寄存器地址                               (str)
        :length:        读 | 写长度                             (int)
        """
        # 如果是读命令，则命令长度为21
        if command != [0x01, 0x04]:
            logger.error("发送命令的命令参数错误，应为%s" % [0x01, 0x04])
        # 标头 + 子标头 + 网络标号 + PC编号 + I/O编号 + 请求目标单元 + 请求目标单元站号 + 请求数据长度 + CPU监控计时器 + 命令 + 子命令 + 请求数据
        # 标头 = 以太网标头 + IP标头 + TCP标头             不用关注，socket会保证
        # 子标头 = \0x50\0x00                           Qna 兼容3E帧 二进制格式
        _command = bytearray(21)
        _command[0] = 0x50  # 子标头L
        _command[1] = 0x00  # 子标头H
        _command[2] = 0x00  # 网络标号
        _command[3] = 0xff  # PC编号
        _command[4] = 0xff  # I/O编号
        _command[5] = 0x03  # 请求目标单元
        _command[6] = 0x00  # 请求目标单元站号
        # 请求数据的长度是从CPU监控计时器开始剩余的长度，故而读与写不一致
        _command[7] = 0x0c  # 读命令的请求数据长度L
        _command[8] = 0x00  # 读命令的请求数据长度H
        _command[9] = 0x0a  # CPU监控计时器L
        _command[10] = 0x00  # CPU监控计时器H
        _command[11] = command[0]  # 命令L
        _command[12] = command[1]  # 命令H
        _command[13] = subcommand[0]  # 子命令L
        _command[14] = subcommand[1]  # 子命令H
        address_data = int(address[1:]) if address[1].isdigit() else int(address[2:])
        _command[15] = address_data % 256  # 首软元件地址，这里表示寄存器地址L （低8位） 共24位
        _command[16] = address_data // 256  # 首软元件地址，这里表示寄存器地址M （中8位） 共24位
        _command[17] = 0x00  # 首软元件地址，这里表示寄存器地址H （高8位） 共24位
        _command[18] = self._anasynic_address(address)[0]  # 软元件代码
        _command[19] = length % 256  # 软元件个数L
        _command[20] = length // 256  # 软元件个数H
        # print(_command)
        return _command

    # (私有函数)建立发送命令
    def _bulid_write_command(self, command=None, subcommand=None, address=None, bit=False, value=None, int_type=16):
        """
        建立发送命令
        :command:       [0x01, 0x14]-写                          (list)
        :subcommand:    子命令，根据具体的命令来看                    (list)
        :address:       寄存器地址                                 (str)
        :length:        读 | 写长度                                (int)
        :bit:           以bit方式读写标志    True | False           (bool)
        :value:         写入的数据，仅命令为写时生效
        :int_type:      写入数据的int类型，是int16 、 int32 、int64  (int)
        """
        # 如果是写入bit位，此处的数据以4位(点)为一个bit位(即一个8位存在2个被写入数据),若为奇数个bit,则最后一个8点剩下的4点为伪数
        if bit:
            buffer = MChelper.bit2bytearray(value)
        else:
            buffer = MChelper.int2bytearray(value, int_type=int_type)
        # 标头 + 子标头 + 网络标号 + PC编号 + I/O编号 + 请求目标单元 + 请求目标单元站号 + 请求数据长度 + CPU监控计时器 + 命令 + 子命令 + 请求数据
        # 标头 = 以太网标头 + IP标头 + TCP标头             不用关注，socket会保证
        # 子标头 = \0x50\0x00                           Qna 兼容3E帧 二进制格式
        _command = bytearray(21 + len(buffer))
        _command[21:] = buffer
        address_data = int(address[1:]) if address[1].isdigit() else int(address[2:])
        _command[0] = 0x50  # 子标头L
        _command[1] = 0x00  # 子标头H
        _command[2] = 0x00  # 网络标号
        _command[3] = 0xff  # PC编号
        _command[4] = 0xff  # I/O编号
        _command[5] = 0x03  # 请求目标单元
        _command[6] = 0x00  # 请求目标单元站号
        # 请求数据的长度是从CPU监控计时器开始剩余的长度，故而读与写不一致
        _command[7] = (len(_command) - 9) % 256  # 写命令的请求数据长度L
        _command[8] = (len(_command) - 9) // 256  # 写命令请求数据的长度H
        _command[9] = 0x0a  # CPU监控计时器L
        _command[10] = 0x00  # CPU监控计时器H
        _command[11] = command[0]  # 命令L
        _command[12] = command[1]  # 命令H
        _command[13] = subcommand[0]  # 子命令L
        _command[14] = subcommand[1]  # 子命令H
        _command[15] = address_data % 256  # 首软元件地址，这里表示寄存器地址L （低8位） 共24位
        _command[16] = address_data // 256  # 首软元件地址，这里表示寄存器地址M （中8位） 共24位
        _command[17] = 0x00  # 首软元件地址，这里表示寄存器地址H （高8位） 共24位
        _command[18] = self._anasynic_address(address)[0]  # 软元件代码
        _command[19] = len(value) * (int_type // 16) % 256  # 软元件个数L
        _command[20] = len(value) * (int_type // 16) // 256  # 软元件个数H
        return _command

    # (私有函数)发送命令并初步分析返回结果
    def _reponse_anasynic(self, address=None, length=None, bit=False, value=None, int_type=16):
        """
        (私有函数)发送命令并初步分析返回结果
        :address:   读写寄存器地址，类型str
        :length:    读命令的长度，类型int
        :bit:       是否为按位读取，True时表示按位读
        :value:     写命令的写入值，int或者list
        :int_type:      写入数据的int类型，是int16 、 int32 、int64  (int)
        :return:    [False]-读写失败；   bytearray-读写成功后返回命令报文数据字段
        """
        # 标头 + 子标头 + 网络标号 + PC编号 + I/O编号 + 请求目标单元 + 请求目标单元站号 + 请求数据长度 + CPU监控计时器 + 命令 + 子命令 + 请求数据
        # 标头 = 以太网标头 + IP标头 + TCP标头             不用关注，socket会保证
        # 子标头 = \0xD0\0x00                           Qna 兼容3E帧 二进制格式
        # _command[0] = 0xd0                                       # 子标头L
        # _command[1] = 0x00                                       # 子标头H
        # _command[2] = 0x00                                       # 网络标号
        # _command[3] = 0xff                                       # PC编号
        # _command[4] = 0xff                                       # I/O编号
        # _command[5] = 0x03                                       # 请求目标单元
        # _command[6] = 0x00                                       # 请求目标单元站号
        # 如果长度为空则表示需要读|写的长度为1
        length = 1 if length is None else length
        # 如果写入数据为空，则表示为读取命令
        if value is None:
            command = self._read(address, length, bit)
        else:
            command = self._write(address=address, value=value, bit=bit, int_type=int_type)
        msg = self.net.send_and_rev(command)
        if msg is not False and len(msg) != 0:
            if msg[:7] == b'\xd0\x00\x00\xff\xff\x03\x00':
                # 返回的消息是正常的消息
                if msg[9] == 0 and msg[10] == 0:
                    # 写正常后的返回消息处理
                    if len(msg) == 11:
                        return True
                    # 读正常后的返回消息处理
                    else:
                        return msg[11:]
                else:
                    err_code = hex(msg[10])[2:] + hex(msg[9])[2:]
                    logger.error("PLC返回错误码%s,信息为%s" % (err_code, MCERRCODE[err_code]))
            else:
                logger.error("PLC返回命令异常,正确的开头应为%s，请检查" % b'\xd0\x00\x00\xff\xff\x03\x00')
        return False

    # (私有函数)读命令的基础命令
    def _read(self, address=None, length=None, bit=False):
        """
        读命令基础命令
        :address:       寄存器地址      (str)
        :length:        读长度         (int)
        :bit:           读bit与否的标志 (bool)
        """
        command = [0x01, 0x04]
        if bit:
            subcommand = [0x01, 0x00]
        else:
            subcommand = [0x00, 0x00]
        return self._bulid_read_command(command, subcommand, address, length)

    # (私有函数)写命令的基础命令
    def _write(self, address=None, value=None, bit=False, int_type=16):
        """
        写命令基础命令
        :address:       寄存器地址      (str)
        :length:        写长度         (int)
        :bit:           写bit与否的标志 (bool)
        :int_type:      写入数据的int类型，是int16 、 int32 、int64  (int)
        """
        if type(value) is int:
            value = [value]
        command = [0x01, 0x14]
        if bit:
            subcommand = [0x01, 0x00]
        else:
            subcommand = [0x00, 0x00]
        return self._bulid_write_command(command, subcommand, address, bit, value=value, int_type=int_type)

    # (私有函数)MC协议的PLC地址解析 适用于三菱、基恩士PLC的MC 3QnA 二进制通信
    def _anasynic_address(self, address=None):
        """
        MC协议的PLC地址解析 适用于三菱、基恩士PLC的MC 3QnA 二进制通信
        :adderss: 寄存器地址
        :return: [软元件二进制代码, 软元件ASCII代码, 进制标识， 特殊标识(基恩士PLC部分寄存器按32位表示，MC协议下超出16位范围时，读65535)]
        """
        if self.plc_type == "三菱":
            if address.startswith("X") or address.startswith("x"):
                return [0x9C, 'X*', 16, 1]
            elif address.startswith("Y") or address.startswith("y"):
                return [0x9D, 'Y*', 16, 1]
            elif address.startswith("B") or address.startswith("b"):
                return [0xA0, 'B*', 16, 1]
            elif address.startswith("M") or address.startswith("m"):
                return [0x90, 'M*', 10, 1]
            elif address.startswith("L") or address.startswith("l"):
                return [0x92, 'L*', 10, 1]
            elif address.startswith("SM") or address.startswith("sm"):
                return [0x91, 'SM', 10, 1]
            elif address.startswith("SD") or address.startswith("sd"):
                return [0xA9, 'SD', 10, 1]
            elif address.startswith("D") or address.startswith("d"):
                return [0xA8, 'D*', 10, 1]
            elif address.startswith("R") or address.startswith("r"):
                return [0xAF, 'R*', 10, 1]
            elif address.startswith("ZR") or address.startswith("zr"):
                return [0xB0, 'ZR', 16, 1]
            elif address.startswith("W") or address.startswith("w"):
                return [0xB4, 'W*', 16, 1]
            elif address.startswith("TN") or address.startswith("tn"):
                return [0xC2, 'TN', 10, 1]
            elif address.startswith("TS") or address.startswith("ts"):
                return [0xC1, 'TS', 10, 1]
            elif address.startswith("CN") or address.startswith("cn"):
                return [0xC5, 'CN', 10, 1]
            elif address.startswith("CS") or address.startswith("cs"):
                return [0xC4, 'CS', 10, 1]
            else:
                logger.error("当前三菱PLC仅开发了 X Y B M L SM SD D R ZR W TN TS CN CS寄存器，其他寄存器请联系姚文佩")
                quit()
        elif self.plc_type == "基恩士":
            if address.startswith("R") or address.startswith("r"):
                return [0x9C, 'X*', 16, 1]
            elif address.startswith("B") or address.startswith("b"):
                return [0xA0, 'B*', 16, 1]
            elif address.startswith("MR") or address.startswith("mr"):
                return [0x90, 'M*', 10, 1]
            elif address.startswith("LR") or address.startswith("lr"):
                return [0x92, 'L*', 10, 1]
            elif address.startswith("CR") or address.startswith("cr"):
                return [0x91, 'SM', 10, 1]
            elif address.startswith("CM") or address.startswith("cm"):
                return [0xA9, 'SD', 10, 1]
            elif address.startswith("DM") or address.startswith("dm"):
                return [0xA8, 'D*', 10, 1]
            elif address.startswith("EM") or address.startswith("em"):
                return [0xA8, 'D*', 10, 1]
            elif address.startswith("FM") or address.startswith("fm"):
                return [0xAF, 'R*', 10, 1]
            elif address.startswith("ZF") or address.startswith("zf"):
                return [0xB0, 'ZR', 16, 1]
            elif address.startswith("W") or address.startswith("w"):
                return [0xB4, 'W*', 16, 1]
            elif address.startswith("T") or address.startswith("t"):
                return [0xC2, 'TN', 10, 0]
            elif address.startswith("C") or address.startswith("c"):
                return [0xC5, 'CN', 10, 0]
            else:
                logger.error("当前基恩士PLC只开发了R B MR LR CR CM DM EM FM ZF W T C寄存器，其他寄存器请联系姚文佩")
                quit()
        else:
            logger.error("请联系姚文佩开发其他PLC")
            quit()

    # 读取int16
    def read_int16(self, address=None, length=None):
        """
        MC二进制通信：读取有符号16位
        :address:     寄存器地址                        (str)
        :length:      读取长度，可以不填，                (int)
        :return:      [False]-读取失败     [True, [……]]读取成功
        """
        reponse = self._reponse_anasynic(address, length)
        if reponse is not False:
            reponse = MChelper.bytearray2int(byte_array=reponse, int_type=16)
            return [reponse]
        else:
            return [False]

    # 读取uint16
    def read_uint16(self, address=None, length=None):
        """
        MC二进制通信：读取无符号16位
        :address:     寄存器地址                        (str)
        :length:      读取长度，可以不填，                (int)
        :return:      [False]-读取失败     [True, [……]]读取成功
        """
        reponse = self._reponse_anasynic(address, length)
        if reponse is not False:
            reponse = MChelper.bytearray2int(byte_array=reponse, int_type=16)
            return [reponse]
        else:
            return [False]

    # 读取bit
    def read_bit(self, address=None, length=None):
        """
        MC二进制通信：读取bit
        :address:     寄存器地址                        (str)
        :length:      读取长度，可以不填，                (int)
        :return:      [False]-读取失败     [True, [……]]读取成功
        """
        length = 1 if length is None else length
        # 正常的bit寄存器为M30这类，按照如下操作进行D300.1
        if "." not in address:
            reponse = self._reponse_anasynic(address, length, bit=True)
            if reponse is not False:
                reponse = MChelper.bytearray2bit(reponse, length)
                if reponse is not False:
                    return reponse
            return [False]
        # 如果bit寄存器中有.存在，如 FM40.1,则进行如下操作
        else:
            address_list = address.split(".")
            address, bit_start = address_list[0], int(address_list[1])
            if bit_start == 0:
                new_length = length // 16 if length % 16 == 0 else length // 16 + 1
            else:
                new_length = (length + bit_start) // 16 + 1
            reponse = self._reponse_anasynic(address=address, length=new_length, bit=False, int_type=16)
            if reponse:
                reponse = MChelper.bytearray2bit_from_byte(reponse)
                reponse = reponse[bit_start:(bit_start + length)]
                return reponse
            else:
                return [False]

    # 读取bool
    def read_bool(self, address=None, length=None):
        """
        MC协议二进制通信方式：读布尔值
        :address:   读写地址,类型str
        :value:     写入值，可以是bool类型，也可以是[bool, bool……]类型
        :return:    [True,[return_data_list……]] or [False]
        """
        rev_data = self.read_bit(address, length)
        if rev_data[0]:
            return_data = []
            for i in rev_data:
                i = True if i == 1 else False
                return_data.append(i)
            return [return_data]
        return [False]

    # 读取双字int32
    def read_int32(self, address=None, length=None):
        """
        MC协议二进制通信方式：读有符号int32
        :address:   读写地址,类型str
        :length:     度长度，可以是int类型，也可以是[int, int……]类型
        :return:    [True,[return_data_list……]] or [False]
        """
        reponse = self._reponse_anasynic(address=address, length=2 * length, bit=False)
        if reponse:
            reponse = MChelper.bytearray2int(reponse, int_type=32)
            return [reponse]
        else:
            return [False]

    # 读取uint32
    def read_uint32(self, address=None, length=None):
        """
        MC协议二进制通信方式：读无符号int32
        :address:   读写地址,类型str
        :value:     写入值，可以是int类型，也可以是[int, int……]类型
        :return:    [True,[return_data_list……]] or [False]
        """
        reponse = self._reponse_anasynic(address=address, length=2 * length)
        if reponse:
            reponse = MChelper.bytearray2int(reponse, int_type=32)
            return [reponse]
        else:
            return [False]

    # 写bit
    def write_bit(self, address=None, value=None):
        """
        MC协议二进制通信方式：写bit值
        :address:   读写地址,类型str
        :value:     写入值，可以是int类型，也可以是[int, int……]类型
        :return:    [True] or [False]
        """
        if type(value) is int:
            value = [value]
        # 如果是 M30此种寄存器类型，进行如下操作
        if "." not in address:
            reponse = self._reponse_anasynic(address, value=value, bit=True)
        # 如果是 FM30.1此种寄存器，进行如下操作
        else:
            new_address, bit_start = address.split(".")[0], int(address.split(".")[1])
            if bit_start == 0:
                if (len(value) + bit_start) % 16 == 0:
                    new_length = (len(value) + bit_start) // 16
                else:
                    new_length = (len(value) + bit_start) // 16 + 1
            else:
                new_length = (len(value) + bit_start) // 16 + 1
            old_value = self.read_int16(address=new_address, length=new_length)
            if old_value[0] is False:
                logger.error("读取原bit出现异常，请检查")
                return [False]
            old_value = old_value[1]
            old_value = MChelper.int2bit(old_value, int_type=16)
            old_value[bit_start: (bit_start + len(value))] = value
            new_value = MChelper.bit2int(old_value, int_type=16)
            reponse = self._reponse_anasynic(new_address, value=new_value, bit=False, int_type=16)
        if reponse:
            return [True]
        return [False]

    # 写int16
    def write_int16(self, address=None, value=None):
        """
        MC协议二进制通信方式：写有符号int16
        :address:   读写地址,类型str
        :value:     写入值，可以是int类型，也可以是[int, int……]类型
        :return:    [True] or [False]
        """
        reponse = self._reponse_anasynic(address=address, value=value, bit=False, int_type=16)
        if reponse:
            return [True]
        return [False]

    # 写uint16
    def write_uint16(self, address=None, value=None):
        """
        MC协议二进制通信方式：写无符号int16
        :address:   读写地址,类型str
        :value:     写入值，可以是int类型，也可以是[int, int……]类型
        :return:    [True] or [False]
        """
        # 由于写uint16,需要先将负整数转换成其补数
        return self.write_int16(address=address, value=value)

    # 写bool
    def write_bool(self, address=None, value=None):
        """
        MC协议二进制通信方式：写布尔值
        :address:   读写地址,类型str
        :value:     写入值，可以是bool类型，也可以是[bool, bool,……]类型
        :return:    [True] or [False]
        """
        if type(value) is int:
            value = [value]
        new_value = []
        for i in value:
            i = 1 if i else 0
            new_value.append(i)
        reponse = self.write_bit(address=address, value=new_value)
        if reponse:
            return [True]
        return [False]

    # 写uint32
    def write_uint32(self, address=None, value=None):
        """
        MC协议二进制通信方式：写无符号uint32
        :address:   读写地址,类型str
        :value:     写入值，可以是int类型，也可以是[int, int……]类型
        :return:    [True] or [False]
        """
        return self.write_int32(address=address, value=value)

    # 写 int32
    def write_int32(self, address=None, value=None):
        """
        MC协议二进制通信方式：写有符号int32
        :address:   读写地址,类型str
        :value:     写入值，可以是int类型，也可以是[int, int……]类型
        :return:    [True] or [False]
        """
        reponse = self._reponse_anasynic(address=address, value=value, bit=False, int_type=32)
        if reponse:
            return [True]
        else:
            return [False]

    pass


PLC_TYPE = ['汇川', 'H5U']  # PLC的品牌、类型

STATION = 0

# 支持MODBUS的PLC支持的各类型寄存器地址的起始位置
MODBUS_REG_START_ADDRESS = {
    "汇川": {
        "H5U": {
            'M': 0x0000,  # bit
            'B': 0x3000,  # bit
            'S': 0xE000,  # bit
            'X': 0xF800,  # bit 8进制
            'Y': 0xFC00,  # bit 8进制
            'D': 0x0000,  # 字 （int, uint, float, double）
            'R': 0x3000  # 字 （int, uint, float, double）
        }
    }
}

# PLC支持的寄存器的类型
PLC_SUPPORT_REG_MODE = {
    '汇川': {
        'H5U': {
            'bit': ['M', 'B', 'S', 'X', 'Y'],
            'word': ['D', 'R']
        }
    }
}

# PLC数据类型关系    与struct的格式复对应的
PLC_DATA_TYPE = {
    'int16': [2, 'h'],
    'uint16': [2, 'H'],
    'int32': [4, 'i'],
    'uint32': [4, 'I'],
    'int64': [8, 'q'],
    'uint64': [8, 'Q'],
    'float': [4, 'f'],
    'double': [8, 'd']
}


# ModBus协议，当前适用于 汇川，其余PLC需要继续进行适配
class ModbusNet:
    def __init__(self, plc_net='ModBus', ip=None, port=502):
        self.plc_net = plc_net
        self.ip = ip
        self.port = port
        self.net = NetWorkBase(ip, port)
        self.net.link()
        pass

    # 私有函数：创建命令
    @staticmethod
    def _build_command(address=None, bytearrays=None, length=None, func_code=None):
        """
        私有函数：创建写命令
        :param address:     寄存器地址, string
        :param bytearrays:      需要写入的值的hex，bytearray
        :param func_code:   功能码，int
        # :param reg_type:    寄存器类型
        :return: command    创建的命令
        """
        global STATION
        if STATION == 256:
            STATION = 0
        STATION += 1
        command = bytearray(12)  # 命令长度，读以及写单个寄存器命令长度均为12， 写连续寄存器时重构
        command[0] = STATION // 256  # 事务处理标识
        command[1] = STATION % 256  # 事务处理标识
        command[2] = 0x00  # 协议标识
        command[3] = 0x00  # 协议标识
        command[4] = 0x00  # 长度高8位
        command[5] = 0x06  # 长度低8位
        command[6] = 0x01  # 单元标识符
        command[7] = func_code  # 功能码
        command[8] = address // 256  # 起始地址高8位
        command[9] = address % 256  # 起始地址低8位
        # 读寄存器
        if func_code in [0x01, 0x02, 0x03, 0x04]:
            #                               Mbap报文头（长度7）                PDU(功能码+数据)
            # 格式为： 事务处理标识       协议标识    长度      单元标识符         功能码     起始地址   寄存器数量
            # 字节串：  00 00           00 00      00 06     01                04      00 7D     00 0A
            length = length if length is not None else 1
            command[10] = length // 256  # 寄存器数量高8位
            command[11] = length % 256  # 寄存器数量低8位
            return command
        # 写寄存器
        else:
            #                               Mbap报文头（长度7）                PDU(功能码+数据)
            # 格式为： 事务处理标识       协议标识    长度      单元标识符         功能码     起始地址   寄存器值
            # 字节串：  00 00           00 00      00 06     01                05      00 7D     00 0A
            # 写单个寄存器命令
            if func_code in [0x05, 0x06]:
                command[10] = bytearrays
            else:
                #                        Mbap报文头（长度7）                     PDU(功能码+数据)
                # 格式为： 事务处理标识  协议标识  长度   单元标识符        功能码 起始地址 写入数量 写入字节数  写入的数据
                # 字节串：  00 00      00 00    00 06  01               05    00 7D   00 02  00 04      01 00……
                command = bytearray(13 + len(bytearrays))
                command[0] = STATION // 256
                command[1] = STATION % 256
                command[2] = 0x00
                command[3] = 0x00
                command[4] = (7 + len(bytearrays)) // 256
                command[5] = (7 + len(bytearrays)) % 256
                command[6] = 0x01
                command[7] = func_code
                command[8] = address // 256
                command[9] = address % 256
                if func_code == 0x0F:
                    command[10] = length // 256
                    command[11] = length % 256
                else:
                    command[10] = int(len(bytearrays) / 2) // 256
                    command[11] = int(len(bytearrays) / 2) % 256
                command[12] = len(bytearrays)
                command[13:] = bytearrays
            return command

    # 私有函数：地址分析
    @staticmethod
    def _analysis_address(address=None):
        """
        私有函数： 地址分析
        :param address:     寄存器地址    string
        :return:            [地址头， 地址分析后的数据]
        """
        # step1.判断地址是否为D3000一个字母开头还是两个字母开头DM3000
        if address[1].isdigit():
            address_start_with = address[:1]
            address_no = int(address[1:])
        else:
            address_start_with = address[:2]
            address_no = int(address[2:])
        address_start_with = address_start_with.upper()  # 强制小写转大写
        # 获取各寄存器类型的地址起始位置，
        address_start = MODBUS_REG_START_ADDRESS[PLC_TYPE[0]][PLC_TYPE[1]][address_start_with]  # 地址的开始位置
        return [address_start_with, address_start + address_no]

    # 私有函数：发送命令并分析报文
    def _response_analysis(self, address=None, length=None, bytearrays=None, func_code=None, reg_type=None, point=1):
        """
        私有函数：返回值确认
        :param address: 寄存器地址
        :param length:  读长度
        :param bytearrays:  写入数据,字节串
        :param func_code:   功能码
        :param reg_type:   寄存器类型
        :param point:   精确到几位小数，仅当reg_type=float时生效
        :return:    True:   写正确
                    False:  读或写错误
                    list:   读正确
        """
        command = ModbusNet._build_command(address=address, bytearrays=bytearrays, func_code=func_code, length=length)
        # 发送命令并获取返回值
        msg = self.net.send_and_rev(command=command)
        if msg and len(msg) != 0:
            # 如果是写命令
            if func_code in [0x05, 0x06, 0x10, 0x0F]:
                # 因为发送的命令与返回值msg的长度不同，所以其第5个byte位不同；
                if msg[:5] == command[:5] and msg[6:11] == command[6:11]:
                    return True
                else:
                    logger.info("发送的命令为%s" % command)
                    logger.error("返回了错误的命令%s" % msg)
            # 读命令
            else:
                # 判断返回消息的头两位正确性(事务处理标识)
                bytearray_help = bytearray(2)
                bytearray_help[0] = STATION // 256
                bytearray_help[1] = STATION % 256
                # 头部事务标识正确，且功能码标识正确
                if msg[:2] == bytearray_help and msg[7] == func_code:
                    msg = msg[9:]  # 读取的数据值段从数组第10位开始
                    # 读线圈（输出类似Y） 或者 离散输入寄存器(类似X)
                    if func_code == 0x01 or func_code == 0x02:
                        return ModBusHelper.bytearray2bit(byte_array=msg, length=length)
                    # 读保持寄存器
                    else:
                        return ModBusHelper.hex2other(bytearrays=msg, reg_type=reg_type, point=point)
                else:
                    logger.info("发送的命令为%s:" % command)
                    logger.error("头部事务处理标识错误或者功能码错误%s" % msg)
        else:
            logger.error("1命令发送失败，发送的命令为%s" % command)
        return False

    # 私有函数：读命令
    def _read(self, address=None, length=None, is_read_input=False, reg_type='int16', point=1):
        """
        主要函数：读寄存器
        :param address: 寄存器地址，string, eg: D3000
        :param length:  读的长度，可以为空，或者为int
        :param is_read_input:   是否读输入型寄存器，一般默认False即可；（输入寄存器不可外部更改）
        :param reg_type: 寄存器的类型[int16, uint16 int32, uint32, int64, uint64, float, double]
        :param point:   精确到几位小数，仅当reg_type=float时生效
        :return: 值列表
        """
        # step1. 分析地址
        [address_start, address] = ModbusNet._analysis_address(address=address)
        # 读bit,则按bit方法来读
        if address_start in PLC_SUPPORT_REG_MODE[PLC_TYPE[0]][PLC_TYPE[1]]['bit']:
            # 读输入型寄存器， 一般为X / Y 寄存器
            if is_read_input:
                return self._response_analysis(address, length, func_code=0x02)
            # 读普通线圈或者继电器
            else:
                return self._response_analysis(address, length, func_code=0x01)
        # 读字节
        else:
            if reg_type in ["int16", "uint16"]:
                # 计算实际读取的长度(int16类型的长度)
                length = int(PLC_DATA_TYPE[reg_type][0] * length / 2)
            elif reg_type in ["float", "int32", "uint32"]:
                # 计算实际读取的长度(32位的长度)
                length = int(PLC_DATA_TYPE[reg_type][0] * length / 2)
            else:
                # 计算实际读取的长度(64位的长度)
                length = int(PLC_DATA_TYPE[reg_type][0] * length / 2)
            # 读输入寄存器，不可写，仅可读
            if is_read_input:
                return self._response_analysis(address=address, length=length, func_code=0x04,
                                               reg_type=reg_type, point=point)
            # 读保持寄存器，可读可写
            else:
                return self._response_analysis(address=address, length=length, func_code=0x03,
                                               reg_type=reg_type, point=point)

    # 私有函数：写命令
    def _write(self, address=None, values=None, reg_type='int16'):
        """
        主函数：写命令
        :param address: 寄存器地址
        :param values: 值 int / list
        :param reg_type: 寄存器的类型[int16, uint16 int32, uint32, int64, uint64, float, double]
        :return: True or False
        """
        # step1.分析地址
        [address_start, address] = ModbusNet._analysis_address(address=address)
        # 写bit
        values_bytearrays = b''
        if address_start in PLC_SUPPORT_REG_MODE[PLC_TYPE[0]][PLC_TYPE[1]]['bit']:
            # 写多个线圈
            if type(values) in [list, tuple] and len(values) > 1:
                func_code = 0x0F
                values_bytearrays = ModBusHelper.bit2hex(values=values)
                return self._response_analysis(address, bytearrays=values_bytearrays,
                                               func_code=func_code, length=len(values))
            # 写单个线圈
            else:
                func_code = 0x05
                for value in values:
                    if value == 0:
                        values_bytearrays = 0
                    else:
                        values_bytearrays = 255
        # 写字节
        else:
            values_bytearrays = ModBusHelper.other2hex(values=values, reg_type=reg_type)
            if type(values) in [list, tuple] or reg_type not in ['int16', 'uint16']:
                # 将int32、int64、float、double类型的值转换成int16型的值写入
                func_code = 0x10
            else:
                func_code = 0x06
        return self._response_analysis(address, bytearrays=values_bytearrays, func_code=func_code, reg_type=reg_type)

    # 写单个线圈
    def write_coil(self, address=None, value=None):
        """
        写单个线圈
        :param address: 寄存器地址
        :param value: 1 | 0
        :return: True | False
        """
        return self._write(address=address, values=[value])

    # 写多个线圈
    def write_coils(self, address=None, value=None):
        """
        写多个线圈
        :param address: 寄存器地址
        :param value: 值列表[1，0，1，1，1，0]
        :return: True | False
        """
        return self._write(address=address, values=value)

    # 写单个保持寄存器（word）
    def write_hold_reg(self, address=None, value=None, reg_type='int16'):
        """
        写单个保持寄存器
        :param address: 寄存器地址
        :param value: 写入值
        :param reg_type: 寄存器的类型[int16, uint16 int32, uint32, int64, uint64, float, double]
        :return: True | False
        """
        return self._write(address=address, values=[value], reg_type=reg_type)

    # 写多个保持寄存器(word)
    def write_hold_regs(self, address=None, value=None, reg_type='int16'):
        """
        写多个保持寄存器
        :param address: 寄存器地址
        :param value: 写入值列表 list
        :param reg_type: 寄存器的类型[int16, uint16 int32, uint32, int64, uint64, float, double]
        :return: True | False
        """
        return self._write(address=address, values=value, reg_type=reg_type)

    # 读多个线圈
    def read_coils(self, address=None, length=1):
        """
        读多个线圈
        :param address: 寄存器地址
        :param length: 读取长度  int
        :return: 读的值列表
        """
        return self._read(address=address, length=length)

    # 读离散输入寄存器 类型X(输入的I/O信号)
    def read_discrete_input(self, address=None, length=1):
        """
        读离散输入信号 I/O信号
        :param address: 寄存器地址
        :param length: 长度
        :return: 返回值列表
        """
        return self._read(address=address, is_read_input=True, length=length)

    # 读输入寄存器的值
    def read_input_reg(self, address, length=1, reg_type='int16', point=1):
        """
        读输入寄存器的值
        :param address: 寄存器地址
        :param length: 读的长度
        :param reg_type: 寄存器的类型[int16, uint16 int32, uint32, int64, uint64, float, double]
        :param point:   精确到几位小数，仅当reg_type=float时生效
        :return: 值列表
        """
        return self._read(address=address, length=length, is_read_input=True, reg_type=reg_type, point=point)

    # 读保持寄存器
    def read_hold_regs(self, address, length=1, reg_type='int16', point=1):
        """
        读保持寄存器
        :param address: 寄存器地址
        :param length: 寄存器长度
        :param reg_type: 寄存器的类型[int16, uint16 int32, uint32, int64, uint64, float, double]
        :param point:   精确到几位小数，仅当reg_type=float时生效
        :return: 读取的值列表
        """
        return self._read(address=address, length=length, reg_type=reg_type, point=point)

    pass


class ModBusHelper:
    @staticmethod
    def bytearray2bit(byte_array=None, length=None):
        """
        辅助函数：将byte字符串转换成[0,1,1,0,1……]型bit列表
        :param byte_array: bytearray
        :param length:
        :return:
        """
        return_list = []
        for byte in byte_array:
            byte = ModBusHelper.filled_in_num(byte)
            byte = byte[::-1]  # 将补全的字符串反转
            byte = [int(i) for i in byte]  # 将反转后的字符串变成列表
            return_list = return_list + byte
        return return_list[: length]

    @staticmethod
    def bit2hex(values=None):
        new_values = ''
        for i in values:
            new_values += str(i)
        if len(new_values) % 8 != 0:
            new_values += '0' * (8 - len(new_values) % 8)
        bytearrays = bytearray(len(new_values) // 8)
        for j in range(len(new_values) // 8):
            value1 = new_values[8 * j:8 * (j + 1)]
            value1 = value1[::-1]
            value1 = eval('0b' + value1)
            bytearrays[j] = value1
        return bytearrays

    @staticmethod
    def bytearray2int(bytearrays=None):
        """
        辅助函数： 将byte字符串转换成 int列表
        :param bytearrays:  bytearray
        :return:
        """
        # return_list = []
        # length = int(len(byte_array)/2)
        # for i in range(length):
        #     i_h = byte_array[2*i]                                                         # 高8位
        #     i_l = byte_array[2*i+1]                                                       # 低8位
        #     i = i_h * 256 + i_l                                                         # h * 256 + l
        #     return_list.append(i)
        byte_len = len(bytearrays) // 2
        return struct.unpack('<' + 'h' * byte_len, bytearrays)

    @staticmethod
    def filled_in_num(data):
        """
        辅助函数：填充数据
        :param data:
        :return:
        """
        data = bin(data)  # 将b'\x01\'类型的数据转换成‘0b111'二进制字符串
        data = data[2:]  # 截取’0b'
        data = data if len(data) == 8 else '0' * (8 - len(data)) + data  # 补全8位长度
        return data

    @staticmethod
    def hex2int(bytearrays, reg_type='int16'):
        if reg_type in ['int16', 'uint16']:
            n_int = len(bytearrays) // 2
            return_list = struct.unpack('>' + n_int * 'h', bytearrays)
        elif reg_type == 'int32':
            n_int = len(bytearrays) // 4
            return_list = struct.unpack('>' + n_int * 'i', bytearrays)
        else:
            n_int = len(bytearrays) // 8
            return_list = struct.unpack('>' + n_int * 'q', bytearrays)
        return return_list

    @staticmethod
    def int2hex(values, reg_type='int16'):
        if type(values) not in [list, tuple]:
            values = [values]
        return_list = b''
        for value in values:
            if reg_type == 'int16':
                value = struct.pack('>h', value)
            elif reg_type == 'int32':
                value = struct.pack('>i', value)
            else:
                value = struct.pack('>q', value)
            return_list += value
        return return_list

    @staticmethod
    def double2hex(values):
        if type(values) is not list or tuple:
            values = [values]
        return_list = b''
        for value in values:
            value = struct.pack('>d', value)
            return_list += value
        return return_list

    @staticmethod
    def hex2double(bytearrays):
        n_float = len(bytearrays) // 8
        return_list = struct.unpack('>' + n_float * 'f', bytearrays)
        return_list = [Decimal(i).quantize(Decimal("0.01"), rounding="ROUND_HALF_UP") for i in return_list]
        return return_list

    @staticmethod
    def other2hex(values, reg_type='int16'):
        if type(values) not in [list, tuple]:
            values = [values]
        return_bytearray = b''
        for value in values:
            value = struct.pack('>' + PLC_DATA_TYPE[reg_type][1], value)
            value1 = b''
            # 当为双字节时，即2个字节，4个byte,表示为前一个字节在后，后一个字节在前
            if len(value) == 4:
                value1 += value[2:]
                value1 += value[:2]
                return_bytearray += value1
            # 当为四字节时，暂不考虑
            # 当为单字节时，即2个byte,16位
            else:
                return_bytearray += value
        return return_bytearray

    @staticmethod
    def hex2other(bytearrays, reg_type='int16', point=1):
        # 单字节
        if reg_type in ['int16', 'uint16']:
            n_int = len(bytearrays) // 2
            values = struct.unpack('>' + n_int * 'h', bytearrays)
        # 双字节
        elif reg_type in ['int32', 'uint32', 'float']:
            n_no = len(bytearrays) // 4  # 浮点型数据 的长度
            # 由于浮点型为双字，前个字为高，后个字为低，需要将其位置置换后再unpack
            new_bytearrays = b''
            for i in range(n_no):
                byte_1 = bytearrays[4 * i: 4 * i + 2]
                byte_2 = bytearrays[4 * i + 2: 4 * i + 4]
                new_bytearrays += byte_2
                new_bytearrays += byte_1
            if reg_type == 'float':
                # 解码unpack
                values = struct.unpack('>' + n_no * 'f', new_bytearrays)
                # 将浮点型进行精度计算
                values = [Decimal(i).quantize(Decimal("0." + (point - 1) * "0" + "1"),
                                              rounding="ROUND_HALF_UP") for i in values]
                values = tuple(values)
            else:
                values = struct.unpack('>' + n_no * 'i', new_bytearrays)
        # 四字节
        else:
            print("int64、uint64、double还未开发")
            "具体规则还未知"
            n_no = len(bytearrays) // 8
            values = struct.unpack('>' + n_no * 'Q', bytearrays)
        return values

    pass


if __name__ == '__main__':
    '''MC协议使用指导'''
    mc = McNetBinary("三菱", ip="172.20.1.33", port=8001)
    # # mc = McNetBinary("三菱", ip="127.0.0.1", port=8712)
    # # mc.write_bit("D320", [False])
    # # print(mc.read_bool("M1", 9))
    # # print(mc.write_bit("D330.0", [1, 1, 1, 1, 1, 1, 1, 0]))
    # # mc.write_uint16("D320", [12, 23, -324])
    # # print(mc.read_bit("D335.0", 9))
    # # print(mc.read_int16("D320", 9))
    # # print(mc.read_uint16("D320", 9))
    # mc.write_int32("D1100", -12345)
    # print(mc.read_int32("D1100", 3))
    # # print(mc.read_uint32("D1100", 3))
    mc.net.close()
    # a1 = MChelper.bytearray2bit1(bytearrays=a, length=length)

    '''ModBus协议使用指导'''
    # mod = ModbusNet(ip='192.168.3.10')
    # d = mod.write_hold_regs(address='D44', value=[65536, -65536], reg_type='int32')
    # a = mod.read_hold_regs(address='R1024', length=1, reg_type='float', point=3)[0]
    # # a = mod.read_coils(address='X1', length=10)
    # mod.write_coil(address='D180', value=10)
    # a = mod.read_coils(address='D180', length=1)
    # mod.write_coil(address='M500', value=1)
    # a = mod.read_coils(address='M500', length=10)
    # print(a[0],a)
    # mod.net.close()
    # print(d)
    # print(a)
    # b = mod.write_coil(address="B1120", value=0)
    # a = mod.read_coils(address="B1120", length=1)
    # print(a)
