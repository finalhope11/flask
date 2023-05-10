
from plc.Plc_Link import *
from common.base_method import get_all_config
# from common.writelog import *
from log import log
import random,os
path = os.path.dirname(os.path.dirname(__file__)) + '/report/'
if not os.path.exists(path):
    os.mkdir(path)
log_path = path + time.strftime('%Y%m%d')+ 'plc.txt'
logger = log.Logger.get_logger(log_path)

class Action:
    def __init__(self):
        self.link = PlcAction(get_all_config['plc_config']['PLC_IP'], int(get_all_config['plc_config']['PLC_PORT']),
                            get_all_config['plc_config']['PLC_AGREEMENT'])

    # 接桶平台推出收回
    def _platform(self, action_id):
        """
        接桶平台推出收回
        Args:
            action_id: 1, 2 分别为机构推出和收回的指令

        Returns:

        """
        if action_id == 1:
            logger.info('推出交接机构')
        else:
            logger.info('收回交接机构')
        # 将执行指令写入寄存器
        self.link.write_uint16('D349', action_id)
        time.sleep(0.05)
        # 触发指令
        self.link.write_int16('D344', 1)
        time.sleep(0.1)
        # 触发清零
        self.link.write_int16('D344', 0)
        # 获取结束寄存器状态， 1 表示结束， 0 表示未结束
        while True:
            rec_value = self.link.read_int16('D346', 1)
            if rec_value[0] == 1:
                break
            else:
                time.sleep(0.2)
        # 返回状态寄存器值
        return self.link.read_int16('D346', 1)

    # 传送带运动
    def _belt(self, action_id=None):
        """
        传送带运动
        Args:
            action_id: 运动指令，1表示接收桶，2表示送出桶

        Returns:

        """
        # self.link.write_int16('D364', 0)
        result = self.link.read_uint16('D369', 1)
        if result[0] == 0:
            self.link.write_uint16('D370', action_id)
            time.sleep(0.05)
            # 触发
            self.link.write_int16('D364', 1)
            # 获取结束寄存器状态 1 表示结束， 0 表示未结束
            while True:
                rec_value = self.link.read_int16('D366', 1)
                if rec_value[0] == 1:
                    break
                else:
                    time.sleep(0.05)

        # 返回状态寄存器值
        return self.link.read_int16('D366', 1)

    # 桶顶升/下降和开关盖
    def _cap(self, action_id=None):
        """
        桶顶升/下降和开关盖
        Args:
            action_id: 运动指令

        Returns:

        """
        # self.link.write_int16('D384', 0)
        self.link.write_uint16('D389', action_id)
        if action_id ==2:
            logger.info('关桶盖和下降')
        else:
            logger.info('顶升和开桶盖')
        time.sleep(0.05)
        # 触发
        self.link.write_int16('D384', 1)
        while True:
            read_value = self.link.read_int16('D386')
            if read_value[0] == 1:
                break
            else:
                time.sleep(0.2)

        # 返回状态寄存器值
        return self.link.read_int16('D386', 1)

    # 打开/关闭挑管区保温盖
    def _insulation(self, action_id=None):
        """
        打开/关闭挑管区保温盖
        Args:
            action_id: 动作指令

        Returns:

        """
        if action_id == 2:
            logger.info('关闭挑管区保温盖')
        else:
            logger.info('开挑管区保温盖')
        self.link.write_uint16('D409', action_id)  # 写入命令
        time.sleep(0.05)
        # 触发
        self.link.write_int16('D404', 1)

        while True:
            rec_value = self.link.read_int16('D406')
            if rec_value[0] == 1:
                break
            else:
                time.sleep(0.2)

        # 返回状态寄存器值
        return self.link.read_int16('D406')

    # 移动冻存盒
    def _move_box(self, box_id=2, source=None, dest=None, source_box=None, dest_box=None):
        """
        移动冻存盒
        Args:
            box_id: 盒子类型
            source: 起始移动区域 => 转运桶：1，挑管区：2
            dest: 目标移动区域 => 转运桶：1，挑管区：2
            source_box: 起始位置 => 转运桶：1，挑管区：1，2，3
            dest_box: 目标位置 => 转运桶：1，挑管区：1，2，3

        Returns: 结束寄存器值
        """
        if source == dest:
            logger.info("正在挑管区内移盒，从%s移动到%s" % (get_all_config['plc_config']['BOX_AREA'][source_box],
                                               get_all_config['plc_config']['BOX_AREA'][dest_box]))
        else:
            if source=='转运桶':
                logger.info("正在从转运桶移盒至挑管区，从%s移动到%s" % (get_all_config['plc_config']['BOX_AREA'][source_box],
                                               get_all_config['plc_config']['BOX_AREA'][dest_box]))
            else:
                logger.info("正在从挑管区移盒至转运桶，从%s移动到%s" % (get_all_config['plc_config']['BOX_AREA'][source_box],
                                                       get_all_config['plc_config']['BOX_AREA'][dest_box]))
        if source not in get_all_config['plc_config']['BOX_PLACE'].keys() or dest not in get_all_config['plc_config']['BOX_PLACE'].keys():
            print("盒子位置参数设置错误")
            return -65535
        source_place, dest_place = get_all_config['plc_config']['BOX_PLACE'][source], get_all_config['plc_config']['BOX_PLACE'][dest]
        source = str(bin(source_place))[2:]
        dest = str(bin(dest_place))[2:]
        source = "0" * (8 - len(source)) + source
        dest = "0" * (8 - len(dest)) + dest
        action_id = eval('0b' + source + dest)
        # action_id = 514

        # D489动作指令， D490盒子类型， D491源盒位， D492目标盒位
        self.link.write_uint16('D489', [action_id, box_id, source_box, dest_box])
        time.sleep(0.05)

        # 触发
        self.link.write_int16('D484', 1)

        time.sleep(0.5)
        while True:
            result = self.link.read_int16('D486', 1)
            if result[0] == 1:
                break
            time.sleep(0.2)

        return self.link.read_int16('D486', 1)

    # 挑管
    def _move_tube(self, action_id=None, tube_nu=None, tube_id_a=None, tube_id_b=None, box_id_a=None, box_id_b=None,
                   random_flag=None, start=None, box_falg=None):
        """
        移动冻存管
        Args:
            action_id: 动作指令 => 通常都为 1
            tube_nu: 移动管子数量
            tube_id_a: 移动管子时A盒内的类型
            tube_id_b: 移动管子时B盒内的类型
            box_id_a: A位置盒子类型
            box_id_b: B位置盒子类型
            random_flag: 随机挑管标志
            start: 单盒内挑管时的方向，参数为1：盒子内管子位置小的一方；参数为2：盒子内管子位置大的一方
            box_falg: 移盒标记：0和1，再循环挑管中如果是转板，则存在两种不同的盒子，移盒后A、B两个位置的参数互换
        Returns: 结束寄存器值
        """
        tube = {48: 8, 96: 12, 100: 10, 126: 14, 196: 14}  # 盒子管子总数对应的每行管子数量
        # print('正在写入寄存器')
        self.link.write_uint16("D509", 0)  # 将指令寄存器归零
        self.link.write_int16("D504", 0)  # 将触发寄存器归零
        # print('写入已完成')
        logger.info('挑管数据已写入')
        time.sleep(0.5)
        # 写入
        tube_nu = tube_nu if action_id == 1 else tube_nu / 2
        # 向寄存器写入动作类型
        self.link.write_uint16("D509", action_id)
        # box_flag为0时，还未移盒，此时A、B盒子参数未变
        if box_falg == 0:
            # 向寄存器写入A盒参数（源位置）
            self.link.write_uint16("D510", [box_id_a, tube_id_a])
            # 向寄存器写入B盒参数（源位置）
            self.link.write_uint16("D494", [box_id_b, tube_id_b])
        # box_flag不为0时，A、B两个位置的盒子互换
        else:
            # 向寄存器写入A盒参数（源位置）
            self.link.write_uint16("D510", [box_id_b, tube_id_b])
            # 向寄存器写入B盒参数（源位置）
            self.link.write_uint16("D494", [box_id_a, tube_id_a])
        # 向寄存器写入挑管数量
        self.link.write_uint16("D512", tube_nu)
        tube_pos_list = []
        # action_id为1，即在两盒间挑管，位置也
        if action_id == 1:
            source = list(range(1, (tube_nu + 1)))  # 起始位置列表
            dest = list(range(1, (tube_nu + 1)))  # 目标位置列表
            # 是否随机挑管
            if random_flag == 1:
                random.shuffle(source)  # 将源盒位置打乱
                random.shuffle(dest)  # 将目标盒位置打乱
            # 将源位与目标位写入一个列表中
            for i in range(len(source)):
                tube_pos_list.append([source[i], dest[i]])
        else:
            # action_id为2，即在单盒内挑管，采取一半挑到另一半
            if tube_nu not in tube.keys():
                print("暂不支持%s管的单盒挑管（当前只支持48,96,100,126,196管单盒挑管）")
            # 将每行的坐标写入一个列表，最后形成一个嵌套列表的列表，内部的每个列表都是一行盒子内的管子位置参数
            pos = [[i for i in range(1 + j, tube[tube_nu] + j + 1)] for j in
                   range(0, int(tube[tube_nu] * (tube_nu / tube[tube_nu])), tube[tube_nu])]
            # 盒子中编号较小的管子位置
            first_half = sorted([pos[i][j] for j in range(int(tube[tube_nu] / 2)) for i in range(len(pos))])
            # 盒子中编号较大的管子位置
            second_half = sorted(
                [pos[i][j] for j in range(int(tube[tube_nu] / 2), tube[tube_nu]) for i in range(len(pos))])
            # 根据挑管方向确定起始位和目标位
            source = first_half if start == 1 else second_half
            dest = second_half if start == 1 else first_half
            # 是否随机挑管
            if random_flag == 1:
                random.shuffle(source)  # 将源盒位置打乱
                random.shuffle(dest)  # 将目标盒位置打乱
            # 将源位与目标位写入一个列表中，方便计算
            for i in range(len(source)):
                tube_pos_list.append([source[i], dest[i]])
        move_tube_pos_list = []
        # 将源位与目标位转换成位置参数
        for tube_pos in tube_pos_list:
            source, dest = tube_pos[0], tube_pos[1]
            source, dest = str(bin(source))[2:], str(bin(dest))[2:]
            source = '0' * (8 - len(source)) + source if len(source) < 8 else source
            dest = '0' * (8 - len(dest)) + dest if len(dest) < 8 else dest
            tube_site = eval('0b' + source + dest)
            move_tube_pos_list.append(tube_site)
        # 将位置信息写入寄存器
        self.link.write_uint16('D600', move_tube_pos_list)
        time.sleep(0.1)
        # 触发挑管
        self.link.write_int16('D504', 1)
        while True:
            rec_value = self.link.read_int16('D506', 1)  # 获取结束寄存器状态  0 表示未结束
            if rec_value[0] == 1:
                break
            else:
                time.sleep(0.2)
        # 返回结束寄存器值
        return self.link.read_int16('D506', 1)

    def tube_site(self, tube_nu=None):
        """
        实时显示挑管信息
        Args:
            tube_nu: 挑管的数量
        Returns:

        """
        while True:
            result = self.link.read_uint16("D506", 1)[0]
            time.sleep(0.05)
            if result == 0:  # 通过挑管的结束寄存器值改变来开始记录
                break
        self.link.write_uint16("D1501", 0)  # 将位置信息寄存器置零
        time.sleep(0.01)
        while True:
            tube_start = self.link.read_uint16('D1501', 1)[0]  # 获取当前执行的管子编号
            time.sleep(0.02)
            if tube_start != 0:
                break
        i = 1
        tube = bin(int(tube_start))[2:]
        source = eval('0b' + tube[:-8]) - 1
        dest = eval('0b' + tube[-8:]) - 1
        logger.info("开始挑第%3d只管,起始位:%3d，目标位:%3d" % (i, source, dest))
        start_time = time.time()
        while True:
            if i == tube_nu:
                tube_start = 0
            tube_end = self.link.read_uint16('D1501', 1)[0]
            time.sleep(0.1)
            if i == tube_nu:
                time.sleep(1)
                while True:
                    if self.link.read_int16('D506', 1)[0] == 1:
                        tube = bin(int(tube_end))[2:]
                        source = eval('0b' + tube[:-8]) - 1
                        dest = eval('0b' + tube[-8:]) - 1
                        end_time = time.time()
                        logger.info('第%3d只管完成，总%d只=> 起始位:%3d, 目标位:%3d，耗时 %.2f秒' % (
                            i, tube_nu, source, dest, round((end_time - start_time), 2)))
                        i += 1
                        break
                    else:
                        time.sleep(0.01)
            if i > tube_nu:
                break
            if tube_end == tube_start:
                continue
            else:
                tube = bin(int(tube_start))[2:]
                source = eval('0b' + tube[:-8]) - 1
                dest = eval('0b' + tube[-8:]) - 1
                end_time = time.time()
                logger.info('第%3d只管完成，总%d只=> 起始位:%3d, 目标位:%3d，耗时 %.2f秒' % (
                    i, tube_nu, source, dest, round((end_time - start_time), 2)))
                i += 1
            tube_start = self.link.read_uint16('D1501', 1)[0]
            tube = bin(int(tube_start))[2:]
            source = eval('0b' + tube[:-8]) - 1
            dest = eval('0b' + tube[-8:]) - 1
            logger.info("开始第%3d只挑管,起始位:%3d，目标位:%3d" % (i, source, dest))
            start_time = time.time()

    def read_torque(self, tube_nu=None):
        """
        读取挑管时，夹爪反馈的转矩值
        Args:
            tube_nu: 挑管的管子数量
        Returns:

        """
        i = 0
        while True:
            if i >= tube_nu:
                break
            result = self.link.read_int16('D318', 1)  # 读取夹管时的最大扭矩
            if result != 0:
                logger.info('扭矩为：%f' % result)
                self.link.write_int16('D318', 0)
            else:
                continue
            i += 1

    # 关闭链接
    def close_tcp_link(self):
        self.link.close_link()

    pass

    if __name__=='__main__':
        print(get_all_config['plc_config']['BOX_PLACE'].values())
        source_place, dest_place = get_all_config['plc_config']['BOX_PLACE']['转运桶'], get_all_config['plc_config']['BOX_PLACE']['挑管区']
        if 1 not in get_all_config['plc_config']['BOX_PLACE'].keys() or 2 not in get_all_config['plc_config']['BOX_PLACE'].keys():
            print("盒子位置参数设置错误")