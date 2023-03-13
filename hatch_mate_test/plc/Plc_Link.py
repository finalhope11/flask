# -*- coding: utf-8 -*-
# ------------------------------------
# @Project   :  04.kiosk
# @Time      :  2020/5/28 10:57
# @Auth      :  yaowenpei
# @File      :  Plc_Link.py
# @IDE       :  PyCharm
# 用于SLMP / ModBus通信的二次封装库
# -----------------------------------

from plc.HslCommunication import ModbusTcpNet
from plc.HslCommunication import MelsecMcNet
import time


bit_type = 1  # 1 表示为16个bit位的比特寄存器（基恩士PLC）； 2表示8个bit位的比特寄存器(三菱FN-5X)



class TcpLink:
    def __init__(self, ip, port, agreement):
        self.ip = ip
        self.port = port
        self.agreement = agreement
        pass

    # 建立链接
    def create_link(self):
        """
        建立TCP链接
        return: 链路连接状态  -1 表示连接失败
        """
        link_flag = 0
        # 最多重新连接三次，如果一次连接成功，直接退出循环
        while link_flag < 3:
            time.sleep(0.001)
            link_flag += 1
            if self.agreement == 'SLMP':
                tcp_link = MelsecMcNet(self.ip, self.port)
            else:
                tcp_link = ModbusTcpNet(self.ip, self.port)
            if tcp_link.ConnectServer().IsSuccess is True:
                print("connect success!,servers ip is %s ,port is %s, net is %s" % (self.ip, self.port, self.agreement))
                return tcp_link
            time.sleep(link_flag * 2)
            if link_flag == 3:
                print("%s times reconnect fail!" % link_flag)
                tcp_link.ConnectClose()
                return -1

    # 断链重连
    def relink(self):
        relink_file = open("relink.ini", "a+")
        result = self.create_link()
        relink_file.write("触发重新链接，链接时间为%s\n" % (time.strftime("%Y%m%d%H%M%S")))
        relink_file.close()
        return result

    pass


class PlcAction(
    TcpLink):
    """
    SLMP/ ModBus 协议的通讯，适用于三菱、基恩士
    规则1： 基恩士的 'FM'类型的寄存器使用 'R'类型的读取
    """
    def __init__(self, ip, port, agreement):
        TcpLink.__init__(self, ip, port, agreement)
        self.link = self.create_link()
        pass

    def close_link(self):
        """
        断开TCP链接
        """
        self.link.ConnectClose()
        print("connect is close, close time is %s" % (time.strftime('%Y%m%d%H%M%S')))
        pass

    # 读取bit位
    def read_bit(self, reg=None, length=1):
        """
        读取bit位数字                    读取失败时会重新读取1次，还是失败会重连后再读取；重复5次；
        args:
                reg:  寄存器地址位置   eg: D101.1
                length: 默认为1
        return:
                result 为[-65535]时表示获取网络异常，关闭链接；为0或者1时即为读取的bit位的值
        """
        loops = 0
        while loops < 5:
            loops += 1
            time.sleep(0.04)
            reg_str_list = reg.split(".")
            reg_new, bit_start = reg_str_list[0], eval(reg_str_list[1])                               # 获取寄存器要处理的比特位
            plc_bit_len = 16 if bit_type == 1 else 8  # 一个寄存器占的比特位的大小  ， 基恩士的是16位， 三菱FNX 为8位
            if bit_start + length > plc_bit_len:
                print('最多只支持从一个16位或者8位寄存器中读取bit位')
                return [-65535]
            else:
                result = self.link.ReadUInt16(reg_new, 1)
                if result.IsSuccess is True:
                    result = result.Content
                    read = (str(bin(result[0])))[2:]  # eg 将 '0b10000010' 转换成 ‘10000010’  最高位为1，最低位为0
                    read = read if len(read) == plc_bit_len else '0' * (plc_bit_len - len(read)) + read
                    read = list(read)  # eg [1,0,0,0,0,0,1,0]
                    read.reverse()
                    read = read[bit_start: bit_start + length]
                    read_new = []
                    for i in read:
                        read_new.append(int(i))
                    return read_new
                else:
                    # 重读失败，间隔5s重新链接
                    time.sleep(5)
                    # 先关闭链接再建立链接
                    self.close_link()
                    self.link = self.relink()
                    continue
            # 重连5次还是失败，关闭链接
        self.close_link()
        return [-65535]

    # 读取int16型寄存器
    def read_int16(self, reg=None, length=1):
        """
        读取 int16型寄存器  （有符号）
        args:
                reg:寄存器地址
                length: 默认1
        return:
                result_1：列表   [-65535]时表示链接异常(读取失败时会重新读取1次，还是失败会重连后再读取；重复5次；)；
        """
        loops = 0
        while loops < 5:
            loops += 1
            time.sleep(0.04)
            result = self.link.ReadInt16(reg, length)
            if result.IsSuccess is False:
                # 等待1s后重读
                time.sleep(1)
                print(result.ToMessageShowString())
                result = self.link.ReadInt16(reg, length)
            if result.IsSuccess is True:
                result_list = result.Content
                result_1 = []
                for i in result_list:
                    result_1.append(int(i))
                return result_1
            else:
                # 等待3s后先关闭链接再重建链接
                time.sleep(5)
                self.close_link()
                time.sleep(0.1)
                self.link = self.relink()
                continue
        self.close_link()
        return [-65535]

    # 读取uint16型寄存器
    def read_uint16(self, reg=None, length=1):
        """
        读取 Uint16型寄存器  （无符号）
        args:
                reg:寄存器地址
                length: 默认1
        return:
                result_1：列表 [-65535]时表示链接异常(读取失败时会重新读取1次，还是失败会重连后再读取；重复5次；)；
        """
        loops = 0
        while loops < 5:
            loops += 1
            time.sleep(0.04)
            result = self.link.ReadUInt16(reg, length)
            if result.IsSuccess is False:
                # 等待1s后重读
                time.sleep(1)
                result = self.link.ReadUInt16(reg, length)
            if result.IsSuccess is True:
                result_list = result.Content
                result_1 = []
                for i in result_list:
                    result_1.append(int(i))
                return result_1
            else:
                # 等待3s后先关闭链接再重建链接
                time.sleep(5)
                self.close_link()
                time.sleep(0.1)
                self.link = self.relink()
                continue
        self.close_link()
        return [-65535]

    # 读取int32型寄存器
    def read_int32(self, reg=None, length=1):
        """
        读取 int32型寄存器  （有符号）
        args:
                reg:寄存器地址
                length: 默认1
        return:
                 result_1：列表 [-65535]时表示链接异常(读取失败时会重新读取1次，还是失败会重连后再读取；重复5次；)；
        """
        loops = 0
        while loops < 5:
            loops += 1
            time.sleep(0.04)
            result = self.link.ReadInt32(reg, length)
            if result.IsSuccess is False:
                # 等待1s后重读
                time.sleep(1)
                result = self.link.ReadInt32(reg, length)
                print(result.ToMessageShowString())
            if result.IsSuccess is True:
                result_list = result.Content
                result_1 = []
                for i in result_list:
                    result_1.append(int(i))
                return result_1
            else:
                # 等待3s后先关闭链接再重建链接
                time.sleep(5)
                self.close_link()
                time.sleep(0.1)
                self.link = self.relink()
                continue
        self.close_link()
        return [-65535]

    # 读取uint32型寄存器
    def read_uint32(self, reg=None, length=1):
        """
        读取 uint32型寄存器  （无符号）
        args:
                reg:寄存器地址
                length: 默认1
        return:
                 result_1：列表 [-65535]时表示链接异常(读取失败时会重新读取1次，还是失败会重连后再读取；重复5次；)；
        """
        loops = 0
        while loops < 5:
            loops += 1
            time.sleep(0.04)
            result = self.link.ReadUInt32(reg, length)
            if result.IsSuccess is False:
                # 等待1s后重读
                time.sleep(1)
                result = self.link.ReadUInt32(reg, length)
            if result.IsSuccess is True:
                result_list = result.Content
                result_1 = []
                for i in result_list:
                    result_1.append(int(i))
                return result_1
            else:
                # 等待3s后先关闭链接再重建链接
                time.sleep(5)
                self.close_link()
                time.sleep(0.1)
                self.link = self.relink()
                continue
        self.close_link()
        return [-65535]

    # 读取bool型寄存器
    def read_bool(self, reg=None, length=1):
        """
        读取 bool型寄存器
        args:
                reg:寄存器地址
                length: 默认1
        return:
                 result_1：列表 [-65535]时表示链接异常(读取失败时会重新读取1次，还是失败会重连后再读取；重复5次；)；
        """
        loops = 0
        while loops < 5:
            loops += 1
            time.sleep(0.04)
            if 'X' in reg:                           # 屏幕显示出来的X63等等都是八进制数据， 而read_bit表现的为十六进制数据，所以需要将其转换一次
                reg1 = eval('0o' + reg[1:])
                reg = 'X' + str(hex(reg1))[2:]
            result = self.link.ReadBool(reg, length)
            if result.IsSuccess is False:
                # 等待1s后重读
                time.sleep(1)
                result = self.link.ReadBool(reg, length)
            if result.IsSuccess is True:
                result_list = result.Content
                result_1 = []
                for i in result_list:
                    result_1.append(eval(i))
                return result_1
            else:
                # 等待3s后先关闭链接再重建链接
                time.sleep(5)
                self.close_link()
                time.sleep(0.1)
                self.link = self.relink()
                continue
        self.close_link()
        return [-65535]

    # 读取int64型寄存器
    def read_int64(self, reg=None, length=1):
        """
        读取 int64型寄存器  （有符号）
        args:
                reg:寄存器地址
                length: 默认1
        return:
                 result_1：列表 [-65535]时表示链接异常(读取失败时会重新读取1次，还是失败会重连后再读取；重复5次；)；
        """
        loops = 0
        while loops < 5:
            loops += 1
            time.sleep(0.04)
            result = self.link.ReadInt64(reg, length)
            if result.IsSuccess is False:
                # 等待1s后重读
                time.sleep(1)
                result = self.link.ReadInt64(reg, length)
            if result.IsSuccess is True:
                result_list = result.Content
                result_1 = []
                for i in result_list:
                    result_1.append(int(i))
                return result_1
            else:
                # 等待3s后先关闭链接再重建链接
                time.sleep(5)
                self.close_link()
                time.sleep(0.1)
                self.link = self.relink()
                continue
        self.close_link()
        return [-65535]

    # 读取uint64型寄存器
    def read_uint64(self, reg=None, length=1):
        """
        读取 uint64型寄存器  （无符号）
        args:
                reg:寄存器地址
                length: 默认1
        return:
                 result_1：列表 [-65535]时表示链接异常(读取失败时会重新读取1次，还是失败会重连后再读取；重复5次；)；
        """
        loops = 0
        while loops < 5:
            loops += 1
            time.sleep(0.04)
            result = self.link.ReadUInt64(reg, length)
            if result.IsSuccess is False:
                # 等待1s后重读
                time.sleep(1)
                result = self.link.ReadUInt64(reg, length)
            if result.IsSuccess is True:
                result_list = result.Content
                result_1 = []
                for i in result_list:
                    result_1.append(int(i))
                return result_1
            else:
                # 等待3s后先关闭链接再重建链接
                time.sleep(5)
                self.close_link()
                time.sleep(0.1)
                self.link = self.relink()
                continue
        self.close_link()
        return [-65535]

    # 读取单精度浮点型寄存器   >= 3个小数点
    def read_float(self, reg=None, length=1):
        """
        读取 浮点型寄存器  （3位小数点）
        args:
                reg:寄存器地址
                length: 默认1
        return:
                 result_1：列表 [-65535]时表示链接异常(读取失败时会重新读取1次，还是失败会重连后再读取；重复5次；)；
        """
        loops = 0
        while loops < 5:
            loops += 1
            time.sleep(0.04)
            result = self.link.ReadFloat(reg, length)
            if result.IsSuccess is False:
                # 等待1s后重读
                time.sleep(1)
                result = self.link.ReadFloat(reg, length)
            if result.IsSuccess is True:
                result_list = result.Content
                result_1 = []
                for i in result_list:
                    result_1.append(eval(i))
                return result_1
            else:
                # 等待3s后先关闭链接再重建链接
                time.sleep(5)
                self.close_link()
                time.sleep(0.1)
                self.link = self.relink()
                continue
        self.close_link()
        return [-65535]

    # 读取多精度浮点型寄存器   >= 4个小数点
    def read_double(self, reg=None, length=1):
        """
        读取 双精度浮点型型寄存器
        args:
                reg:寄存器地址
                length: 默认1
        return:
                 result_1：列表 [-65535]时表示链接异常(读取失败时会重新读取1次，还是失败会重连后再读取；重复5次；)；
        """
        loops = 0
        while loops < 5:
            loops += 1
            time.sleep(0.04)
            result = self.link.ReadDouble(reg, length)
            if result.IsSuccess is False:
                # 等待1s后重读
                time.sleep(1)
                result = self.link.ReadDouble(reg, length)
            if result.IsSuccess is True:
                result_list = result.Content
                result_1 = []
                for i in result_list:
                    result_1.append(eval(i))
                return result_1
            else:
                # 等待3s后先关闭链接再重建链接
                time.sleep(5)
                self.close_link()
                time.sleep(0.1)
                self.link = self.relink()
                continue
        self.close_link()
        return [-65535]

    # 写入bit位
    def write_bit(self, reg=None, value=None):
        """
        写入bit位  （只支持写一个大bit位的长度的值）
        ：args:
                :reg: 寄存器地址 D1010.1
                :bit: bit位，第几个bit  0~15
                :value: 将要写入的值    0 / 1
        ：return:
                0表示写入成功
                -65535表示写入失败， 一般多为网络链路问题
        """
        time.sleep(0.04)
        # step1. 读取需要写入的寄存器的值
        # # step1.1 先计算需要写几个寄存器的值
        reg_str_list = reg.split('.')                                           # 找到bit位所在的寄存器的位置， . 号前面为寄存器， 后面的为位号
        reg_new, bit_start = reg_str_list[0], int(reg_str_list[1])              # 比特位所在的寄存器，比特位位号
        bit_num = len(value) if type(value) is list else 1                      # 需要写入的bit位的数量
        plc_bit_len = 16 if bit_type == 1 else 8                                # 一个寄存器占的比特位的大小  ， 基恩士的是16位， 三菱FNX 为8位
        if bit_num + bit_start > plc_bit_len:
            print('仅支持在一个16位或者8位寄存器中写入')
            return [-65535]
        else:
            source_read = self.link.ReadUInt16(reg_new, 1)
            source_read = int((source_read.Content)[0])
            read = (str(bin(source_read)))[2:]         # eg 将 '0b10000010' 转换成 ‘10000010’  最高位为1，最低位为0
            read = read if len(read) == plc_bit_len else '0' * (plc_bit_len - len(read)) + read
            read = list(read)                                              # eg [1,0,0,0,0,0,1,0]
            read.reverse()
            if bit_num == 1:
                read[bit_start] = value
            else:
                read = read[:(bit_start + 1)] + value
            read.reverse()
            new_value = '0b'
            for i in read:
                new_value += str(i)                      # '0b000111101101'
            new_value = eval(new_value)
            # step2. 写入寄存器值
            times = 0
            while times < 3:
                time.sleep(0.001)
                write_result = self.link.WriteInt16(reg_new, new_value)
                if write_result.IsSuccess is False:
                    time.sleep(1)
                    write_result = self.link.WriteInt16(reg_new, new_value)
                if write_result.IsSuccess is True:
                    return [0]
                else:
                    self.close_link()
                    time.sleep(5)
                    self.link = self.relink()
                time.sleep(0.04)
                times += 1
            # 失败返回错误
            self.close_link()
            return [-65535]

    # 写int16型寄存器
    def write_int16(self, reg=None, value=None):
        """
        写int16型寄存器
        ：args:
                :reg:寄存器地址
                :value:寄存器值
        ：return:
                : -65535表示失败，一般多为链路故障或者拥塞； 0表示设置成功
        """
        time.sleep(0.04)
        times = 0
        while times < 3:
            time.sleep(0.001)
            write_result = self.link.WriteInt16(address=reg, value=value)
            if write_result.IsSuccess is False:
                time.sleep(1)
                write_result = self.link.WriteInt16(address=reg, value=value)
            if write_result.IsSuccess is True:
                return [0]
            else:
                self.close_link()
                time.sleep(5)
                self.link = self.relink()
            time.sleep(0.04)
            times += 1
        self.close_link()
        return [-65535]

    # 写int32型寄存器
    def write_int32(self, reg=None, value=None):
        """
        写int32型寄存器
        ：args:
                :reg:寄存器地址
                :value:寄存器值
        ：return:
                : -65535表示失败，一般多为链路故障或者拥塞； 0表示设置成功
        """
        time.sleep(0.04)
        times = 0
        while times < 3:
            time.sleep(0.001)
            write_result = self.link.WriteInt32(address=reg, value=value)
            if write_result.IsSuccess is False:
                time.sleep(1)
                write_result = self.link.WriteInt32(address=reg, value=value)
            if write_result.IsSuccess is True:
                return [0]
            else:
                self.close_link()
                time.sleep(5)
                self.link = self.relink()
            time.sleep(0.1)
            times += 1
        self.close_link()
        return [-65535]

    # 写int64型寄存器
    def write_int64(self, reg=None, value=None):
        """
        写int64型寄存器
        ：args:
                :reg:寄存器地址
                :value:寄存器值
        ：return:
                : -65535表示失败，一般多为链路故障或者拥塞； 0表示设置成功
        """
        time.sleep(0.04)
        times = 0
        while times < 3:
            time.sleep(0.001)
            write_result = self.link.WriteInt64(address=reg, value=value)
            if write_result.IsSuccess is False:
                time.sleep(1)
                write_result = self.link.WriteInt64(address=reg, value=value)
            if write_result.IsSuccess is True:
                return [0]
            else:
                self.close_link()
                time.sleep(5)
                self.link = self.relink()
            time.sleep(1)
            times += 1
        self.close_link()
        return [-65535]

    # 写uint16型寄存器
    def write_uint16(self, reg=None, value=None):
        """
        写uint16型寄存器
        ：args:
                :reg:寄存器地址
                :value:寄存器值
        ：return:
                : -65535表示失败，一般多为链路故障或者拥塞； 0表示设置成功
        """
        time.sleep(0.04)
        times = 0
        while times < 3:
            time.sleep(0.001)
            write_result = self.link.WriteUInt16(address=reg, value=value)
            if write_result.IsSuccess is False:
                time.sleep(1)
                write_result = self.link.WriteUInt16(address=reg, value=value)
            if write_result.IsSuccess is True:
                return [0]
            else:
                self.close_link()
                time.sleep(5)
                self.link = self.relink()
            time.sleep(1)
            times += 1
        self.close_link()
        return [-65535]

    # 写uint32型寄存器
    def write_uint32(self, reg=None, value=None):
        """
        写Uint32型寄存器
        ：args:
                :reg:寄存器地址
                :value:寄存器值
        ：return:
                : -65535表示失败，一般多为链路故障或者拥塞； 0表示设置成功
        """
        time.sleep(0.04)
        times = 0
        while times < 3:
            time.sleep(0.001)
            write_result = self.link.WriteUInt32(address=reg, value=int(value))
            if write_result.IsSuccess is False:
                time.sleep(1)
                write_result = self.link.WriteUInt32(address=reg, value=int(value))
            if write_result.IsSuccess is True:
                return [0]
            else:
                self.close_link()
                time.sleep(5)
                self.link = self.relink()
            time.sleep(1)
            times += 1
        self.close_link()
        return [-65535]

    # 写uint64型寄存器
    def write_uint64(self, reg=None, value=None):
        """
        写uint64型寄存器
        ：args:
                :reg:寄存器地址
                :value:寄存器值
        ：return:
                : -65535表示失败，一般多为链路故障或者拥塞； 0表示设置成功
        """
        time.sleep(0.04)
        times = 0
        while times < 3:
            time.sleep(0.001)
            write_result = self.link.WriteUInt64(address=reg, value=value)
            if write_result.IsSuccess is False:
                time.sleep(1)
                write_result = self.link.WriteUInt64(address=reg, value=value)
            if write_result.IsSuccess is True:
                return [0]
            else:
                self.close_link()
                time.sleep(5)
                self.link = self.relink()
            time.sleep(1)
            times += 1
        self.close_link()
        return [-65535]

    # 写单精度浮点型寄存器
    def write_float(self, reg=None, value=None):
        """
        写单精度浮点型寄存器
        ：args:
                :reg:寄存器地址
                :value:寄存器值
        ：return:
                : -65535表示失败，一般多为链路故障或者拥塞； 0表示设置成功
        """
        time.sleep(0.04)
        times = 0
        while times < 3:
            time.sleep(0.001)
            write_result = self.link.WriteFloat(address=reg, value=value)
            if write_result.IsSuccess is False:
                time.sleep(1)
                write_result = self.link.WriteFloat(address=reg, value=value)
            if write_result.IsSuccess is True:
                return [0]
            else:
                self.close_link()
                time.sleep(5)
                self.link = self.relink()
            time.sleep(1)
            times += 1
        self.close_link()
        return [-65535]

    # 写双精度浮点型寄存器
    def write_double(self, reg=None, value=None):
        """
        写单精度浮点型寄存器
        ：args:
                :reg:寄存器地址
                :value:寄存器值
        ：return:
                : -65535表示失败，一般多为链路故障或者拥塞； 0表示设置成功
        """
        time.sleep(0.04)
        times = 0
        while times < 3:
            time.sleep(0.001)
            write_result = self.link.WriteDouble(address=reg, value=value)
            if write_result.IsSuccess is False:
                time.sleep(1)
                write_result = self.link.WriteDouble(address=reg, value=value)
            if write_result.IsSuccess is True:
                return [0]
            else:
                self.close_link()
                time.sleep(5)
                self.link = self.relink()
            time.sleep(1)
            times += 1
        self.close_link()
        return [-65535]

    pass

