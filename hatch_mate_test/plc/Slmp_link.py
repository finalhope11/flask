# -*- coding: utf-8 -*-
# ------------------------------------
# @Project   :  04.kiosk
# @Time      :  2020/5/9 11:04
# @Auth      :  yaowenpei
# @File      :  Slmp_link.py.py
# @IDE       :  PyCharm
# 用于SLMP通信的二次封装库
# -----------------------------------
from Common.Plc.HslCommunication import MelsecMcNet
import time


# SLMP通信协议，创建链接
class SlmpTcpLink:
    def __init__(self, ip, port):
        self.ip = ip
        self.port = port
        pass

    # 建立链接
    # @staticmethod
    def create_link(self):
        """
        建立TCP链接
        return: 链路连接状态  -1 表示连接失败
        """
        link_flag = 0
        # 最多重新连接三次，如果一次连接成功，直接退出循环
        while link_flag < 3:
            link_flag += 1
            tcp_link = MelsecMcNet(self.ip, self.port)
            if tcp_link.ConnectServer().IsSuccess is True:
                print("connect success!,servers ip is %s ,port is %s" % (self.ip, self.port))
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
        relink_file.write("触发重新链接，链接时间为%s" % (time.strftime("%Y%m%d%H%M%S")))
        relink_file.close()
        return result

    # 断开链接
    # @staticmethod
    def close_link(self, link=None):
        """
        断开TCP链接
        """
        link.ConnectClose()
        print("connect is close, close time is %s" % (time.strftime('%Y%m%d%H%M%S')))
        pass

    pass


# SLMP通信协议：读写寄存器
class SlmpPlcAction(SlmpTcpLink):
    """
    SLMP 协议的通讯，适用于三菱、基恩士
    规则1： 基恩士的 'FM'类型的寄存器使用 'R'类型的读取
    """
    def __init__(self, ip, port):
        SlmpTcpLink.__init__(self, ip, port)
        self.link = self.create_link()
        pass

    # 读取bit位
    def read_bit(self, reg=None, bit=None, length=1):
        """
        读取bit位数字                    读取失败时会重新读取1次，还是失败会重连后再读取；重复5次；
        args:
                reg:  寄存器地址位置
                bit:  读取的比特位，[0~15]
                length: 默认为1
        return:
                result 为[-65535]时表示获取网络异常，关闭链接；为0或者1时即为读取的bit位的值
        """
        loops = 0
        while loops < 5:
            loops += 1
            time.sleep(0.15)
            result = self.link.Read(reg, length)
            if result.IsSuccess is False:
                # 隔1s重读
                time.sleep(1)
                result = self.link.Read(reg, length)
            if result.IsSuccess is True:
                result_list = result.Content
                bit_list = []
                for i in result_list:
                    result3 = str(bin(i))
                    result4 = result3[2:]
                    if len(result4) < 16:
                        los = 16 - len(result4)
                        result5 = '0' * los + result4
                        result_1 = int(result5[(15 - bit)])
                    else:
                        result_1 = int(result4[(15 - bit)])
                    bit_list.append(int(result_1))
                return bit_list
            else:
                # 重读失败，间隔5s重新链接
                time.sleep(5)
                # 先关闭链接再建立链接
                self.close_link(self.link)
                self.link = self.relink()
                continue
        # 重连5次还是失败，关闭链接
        self.close_link(self.link)
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
            time.sleep(0.15)
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
                self.close_link(self.link)
                time.sleep(0.1)
                self.link = self.relink()
                continue
        self.close_link(self.link)
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
            time.sleep(0.15)
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
                self.close_link(self.link)
                time.sleep(0.1)
                self.link = self.relink()
                continue
        self.close_link(self.link)
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
            time.sleep(0.15)
            result = self.link.ReadInt32(reg, length)
            if result.IsSuccess is False:
                # 等待1s后重读
                time.sleep(1)
                result = self.link.ReadInt32(reg, length)
            if result.IsSuccess is True:
                result_list = result.Content
                result_1 = []
                for i in result_list:
                    result_1.append(int(i))
                return result_1
            else:
                # 等待3s后先关闭链接再重建链接
                time.sleep(5)
                self.close_link(self.link)
                time.sleep(0.1)
                self.link = self.relink()
                continue
        self.close_link(self.link)
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
            time.sleep(0.15)
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
                self.close_link(self.link)
                time.sleep(0.1)
                self.link = self.relink()
                continue
        self.close_link(self.link)
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
            time.sleep(0.15)
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
                self.close_link(self.link)
                time.sleep(0.1)
                self.link = self.relink()
                continue
        self.close_link(self.link)
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
            time.sleep(0.15)
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
                self.close_link(self.link)
                time.sleep(0.1)
                self.link = self.relink()
                continue
        self.close_link(self.link)
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
            time.sleep(0.15)
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
                self.close_link(self.link)
                time.sleep(0.1)
                self.link = self.relink()
                continue
        self.close_link(self.link)
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
            time.sleep(0.15)
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
                self.close_link(self.link)
                time.sleep(0.1)
                self.link = self.relink()
                continue
        self.close_link(self.link)
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
            time.sleep(0.15)
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
                self.close_link(self.link)
                time.sleep(0.1)
                self.link = self.relink()
                continue
        self.close_link(self.link)
        return [-65535]

    # 写入bit位
    def write_bit(self, reg=None, bit=None, value=None):
        """
        写入bit位
        ：args:
                :reg: 寄存器地址
                :bit: bit位，第几个bit  0~15
                :value: 将要写入的值    0 / 1
        ：return:
                0表示写入成功
                -65535表示写入失败， 一般多为网络链路问题
        """
        time.sleep(0.2)
        source_result = self.read_int16(reg, 1)
        if source_result[0] != -65535:
            # 将获取到的值转换成二进制流字符串  eg: ‘ob11001’
            source_result1 = str(bin(source_result[0]))
            # 补齐到16个bit位
            source_result1 = source_result1[2:]
            if len(source_result1) < 16:
                los = 16 - len(source_result1)
                source_result1 = '0' * los + source_result1
            # bit位在补齐后的二进制流中的位置
            r_bit = 15 - bit
            # 如果将目标bit位的值置为1则 + 2**bit； 置为0则 -2**bit
            if int(source_result1[r_bit]) != int(value):
                if int(value) == 0:
                    write_value = int(source_result[0]) - 2 ** int(bit)
                else:
                    write_value = int(source_result[0]) + 2 ** int(bit)
            else:
                write_value = int(source_result[0])
            # 写入bit位到寄存器
            i_times = 0
            while i_times < 5:
                time.sleep(0.15)
                write_result = self.link.WriteInt16(reg, write_value)
                if write_result.IsSuccess is False:
                    time.sleep(1)
                    write_result = self.link.WriteInt16(reg, write_value)
                if write_result.IsSuccess is True:
                    time.sleep(0.1)
                    read_result = self.read_int16(reg, 1)
                    if read_result[0] != -65535:
                        if read_result[0] == write_value:
                            return [0]
                    else:
                        return [-65535]
                else:
                    time.sleep(5)
                    self.close_link(self.link)
                    time.sleep(0.1)
                    self.link = self.relink()
                i_times += 1
        self.close_link(self.link)
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
        time.sleep(0.15)
        times = 0
        while times < 5:
            write_result = self.link.WriteInt16(address=reg, value=value)
            if write_result.IsSuccess is False:
                time.sleep(1)
                write_result = self.link.WriteInt16(address=reg, value=value)
            if write_result.IsSuccess is True:
                time.sleep(0.1)
                read_result = self.read_int16(reg, 1)
                if read_result[0] != -65535:
                    if read_result[0] == int(value):
                        return [0]
                return [-65535]
            else:
                self.close_link(self.link)
                time.sleep(5)
                self.link = self.relink()
            time.sleep(0.1)
            times += 1
        self.close_link(self.link)
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
        time.sleep(0.2)
        times = 0
        while times < 5:
            write_result = self.link.WriteInt32(address=reg, value=value)
            if write_result.IsSuccess is False:
                time.sleep(1)
                write_result = self.link.WriteInt32(address=reg, value=value)
            if write_result.IsSuccess is True:
                time.sleep(0.1)
                read_result = self.read_int32(reg, 1)
                if read_result[0] != -65535:
                    if read_result[0] == int(value):
                        return [0]
                return [-65535]
            else:
                self.close_link(self.link)
                time.sleep(5)
                self.link = self.relink()
            time.sleep(0.1)
            times += 1
        self.close_link(self.link)
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
        time.sleep(0.15)
        times = 0
        while times < 5:
            write_result = self.link.WriteInt64(address=reg, value=value)
            if write_result.IsSuccess is False:
                time.sleep(1)
                write_result = self.link.WriteInt64(address=reg, value=value)
            if write_result.IsSuccess is True:
                time.sleep(0.1)
                read_result = self.read_int64(reg, 1)
                if read_result[0] != -65535:
                    if read_result[0] == int(value):
                        return [0]
                return [-65535]
            else:
                self.close_link(self.link)
                time.sleep(5)
                self.link = self.relink()
            time.sleep(1)
            times += 1
        self.close_link(self.link)
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
        time.sleep(0.15)
        times = 0
        while times < 5:
            write_result = self.link.WriteUInt16(address=reg, value=value)
            if write_result.IsSuccess is False:
                time.sleep(1)
                write_result = self.link.WriteUInt16(address=reg, value=value)
            if write_result.IsSuccess is True:
                time.sleep(0.1)
                read_result = self.read_uint16(reg, 1)
                if read_result[0] != -65535:
                    if read_result[0] == int(value):
                        return [0]
                return [-65535]
            else:
                self.close_link(self.link)
                time.sleep(5)
                self.link = self.relink()
            time.sleep(1)
            times += 1
        self.close_link(self.link)
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
        time.sleep(0.15)
        times = 0
        while times < 5:
            write_result = self.link.WriteUInt32(address=reg, value=int(value))
            if write_result.IsSuccess is False:
                time.sleep(1)
                write_result = self.link.WriteUInt32(address=reg, value=int(value))
            if write_result.IsSuccess is True:
                time.sleep(0.1)
                read_result = self.read_uint32(reg, 1)
                if read_result[0] != -65535:
                    if read_result[0] == int(value):
                        return [0]
                return [-65535]
            else:
                self.close_link(self.link)
                time.sleep(5)
                self.link = self.relink()
            time.sleep(1)
            times += 1
        self.close_link(self.link)
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
        time.sleep(0.15)
        times = 0
        while times < 5:
            write_result = self.link.WriteUInt64(address=reg, value=value)
            if write_result.IsSuccess is False:
                time.sleep(1)
                write_result = self.link.WriteUInt64(address=reg, value=value)
            if write_result.IsSuccess is True:
                time.sleep(0.1)
                read_result = self.read_uint64(reg, 1)
                if read_result[0] != -65535:
                    if read_result[0] == int(value):
                        return [0]
                return [-65535]
            else:
                self.close_link(self.link)
                time.sleep(5)
                self.link = self.relink()
            time.sleep(1)
            times += 1
        self.close_link(self.link)
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
        time.sleep(0.15)
        times = 0
        while times < 5:
            write_result = self.link.WriteFloat(address=reg, value=value)
            if write_result.IsSuccess is False:
                time.sleep(1)
                write_result = self.link.WriteFloat(address=reg, value=value)
            if write_result.IsSuccess is True:
                time.sleep(0.1)
                read_result = self.read_float(reg, 1)
                if read_result[0] != -65535:
                    if read_result[0] == value:
                        return [0]
                return [-65535]
            else:
                self.close_link(self.link)
                time.sleep(5)
                self.link = self.relink()
            time.sleep(1)
            times += 1
        self.close_link(self.link)
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
        time.sleep(0.15)
        times = 0
        while times < 5:
            write_result = self.link.WriteDouble(address=reg, value=value)
            if write_result.IsSuccess is False:
                time.sleep(1)
                write_result = self.link.WriteDouble(address=reg, value=value)
            if write_result.IsSuccess is True:
                time.sleep(0.1)
                read_result = self.read_double(reg, 1)
                if read_result[0] != -65535:
                    if read_result[0] == value:
                        return [0]
                return [-65535]
            else:
                self.close_link(self.link)
                time.sleep(5)
                self.link = self.relink()
            time.sleep(1)
            times += 1
        self.close_link(self.link)
        return [-65535]

    pass
