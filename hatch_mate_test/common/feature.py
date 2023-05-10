from common.action import *
from common import my_threading as thread


class Test(Action):
    def __init__(self):
        super().__init__()
        self.stop_tag = 0
        pass

    # 挑管
    def move_tube(self, loops=None, action_id=None, tube_nu=None, tube_id_a=None, tube_id_b=None, box_id_a=None,
                  box_id_b=None, random_flag=None, start=None):
        """
        Args:
            loops: 挑管循环次数
            action_id: 动作指令 => 通常都为 1
            tube_nu: 移动管子数量
            tube_id_a: 移动管子时A盒内的类型
            tube_id_b: 移动管子时B盒内的类型
            box_id_a: A位置盒子类型
            box_id_b: B位置盒子类型
            random_flag: 随机挑管标志
            start: 单盒内挑管时的方向，参数为1：盒子内管子位置小的一方；参数为2：盒子内管子位置大的一方
        Returns:

        """
        box_flag = 0        # 内部A、B位置盒子参数交换指令
        for i in range(loops):
            if self.stop_tag != 1:
                start = time.time()
                # 执行挑管
                result = self.run_tube(action_id=action_id, tube_nu=tube_nu, tube_id_a=tube_id_a, tube_id_b=tube_id_b,
                                       box_id_a=box_id_a, box_id_b=box_id_b, random_flag=random_flag, start=start, box_flag=box_flag)
                if result[0] != 1:
                    return -65535
                # 在两盒间挑管时，需要转移冻存盒
                if action_id == 1:
                    self.move_box(box_flag=box_flag, box_id_a=box_id_a, box_id_b=box_id_b)
                    # 更改A、B两个位置的盒子参数
                    if i % 2 == 0:
                        box_flag = 1
                    else:
                        box_flag = 0
                end = time.time()
                # 计算消耗的时间
                minute = round(end - start) // 60
                second = round(end - start) % 60
                action_flag = '完成第 %d 次挑管，耗时 %d 分 %d 秒（包含移盒的时间）' if action_id == 1 else '完成第 %d 次挑管，耗时 %d 分 %d 秒'
                logger.info(action_flag % (i+1, minute, second))
            else:
                logger.info('收到停止指令，停止完成')
                break
        pass

    # 在操作区移盒
    def move_box(self, box_flag=None, box_id_a=None, box_id_b=None):
        if box_flag == 0:
            box_a = box_id_a
            box_b = box_id_b
        else:
            box_a = box_id_b
            box_b = box_id_a
        # 从源位移动到转移位
        result_move_box = super()._move_box(box_id=box_a, source="挑管区", dest="挑管区", source_box=1, dest_box=3)
        if result_move_box[0] != 1:
            return -65535
        # 从目标位移动到源位
        result_move_box = super()._move_box(box_id=box_b, source="挑管区", dest="挑管区", source_box=2, dest_box=1)
        if result_move_box[0] != 1:
            return -65535
        # 从转移位移动到目标位
        result_move_box = super()._move_box(box_id=box_a, source="挑管区", dest="挑管区", source_box=3, dest_box=2)
        if result_move_box[0] != 1:
            return -65535

    # 挑管执行
    def run_tube(self, action_id=None, tube_nu=None, tube_id_a=None, tube_id_b=None, box_id_a=None, box_id_b=None,
                 random_flag=None, start=None, box_flag=None):
        """
        Args:
            action_id: 动作指令 => 通常都为 1
            tube_nu: 移动管子数量
            tube_id_a: 移动管子时A盒内的类型
            tube_id_b: 移动管子时B盒内的类型
            box_id_a: A位置盒子类型
            box_id_b: B位置盒子类型
            random_flag: 随机挑管标志
            start: 单盒内挑管时的方向，参数为1：盒子内管子位置小的一方；参数为2：盒子内管子位置大的一方
            box_flag： 移盒标记：0和1，再循环挑管中如果是转板，则存在两种不同的盒子，移盒后A、B两个位置的参数互换
        Returns:

        """
        # 挑管函数，参数依次为挑管方式，挑管数量，管子类型，盒子类型，是否随机，开始方向
        args_tube = (action_id, tube_nu, tube_id_a, tube_id_b, box_id_a, box_id_b, random_flag, start, box_flag)
        thread_tube = thread.MyThread(super()._move_tube, args=args_tube)
        thread_read = thread.MyThread(super().tube_site, args=(tube_nu,))  # 参数为挑管的数量
        thread_read.setDaemon(True)
        thread_read.start()
        time.sleep(2)
        thread_tube.start()
        thread_tube.join()
        thread_read.join()
        thread_result = thread_tube.get_result()
        time.sleep(5)
        if thread_result[0] == 1:
            return thread_result
        else:
            return -65536

    # 机构整体执行
    def move_action(self, loops=None, tube_nu=None, tube_id_a=None, tube_id_b=None, box_id_a=None, box_id_b=None,
                    random_flag=None):
        for i in range(1, loops):
            start = time.time()
            if self.stop_tag != 1:
                # 传送带接收桶
                result = self._belt(action_id=1)
                if result[0] != 1:
                    return -65535
                # 收回交接机构
                result = self._platform(action_id =2)
                if result[0] != 1:
                    return -65535

                # 顶升和开桶盖
                result = self._cap(action_id=1)
                if result[0] != 1:
                    return -65535
                # 开挑管区保温盖
                result = self._insulation(action_id=1)
                if result[0] != 1:
                    return -65535
                if i%2 == 1:
                    # 从转运桶移动冻存盒到挑管区A
                    result = self._move_box(box_id=box_id_a,source='转运桶', dest='挑管区', source_box=1, dest_box=1)
                    if result[0] != 1:
                        return -65535
                elif i%2 == 0:
                    # 从转运桶移动冻存盒到挑管区B
                    result = self._move_box(box_id=box_id_a,source='转运桶', dest='挑管区', source_box=1, dest_box=3)
                    if result[0] != 1:
                        return -65535
                    # 从挑管区3号位移动挑管区2号位
                    result = self._move_box(box_id=box_id_a,source='挑管区', dest='挑管区', source_box=3, dest_box=1)
                    if result[0] != 1:
                        return -65535

                # 关桶盖和下降
                result = self._cap(action_id=2)
                if result[0] != 1:
                    return -65535

                # 在挑管区内挑管
                # print('在挑管区内挑管')
                result = self._move_tube(action_id=1, tube_nu=tube_nu, box_id_a=box_id_a, box_id_b=box_id_b,
                                              tube_id_a=tube_id_a, tube_id_b=tube_id_b, random_flag=random_flag)
                if result[0] != 1:
                    return -65535

                # 顶升和开桶盖
                result = self._cap(action_id=1)
                if result[0] != 1:
                    return -65535
                # 从挑管区移动冻存盒到转运桶
                result = self._move_box(box_id=box_id_b,source='挑管区', dest='转运桶', source_box=2, dest_box=1)
                if result[0] != 1:
                    return -65535

                # 在挑管区内将盒子从1号位置移动到2号位置
                result = self._move_box(box_id=box_id_a,source='挑管区', dest='挑管区', source_box=1, dest_box=2)
                if result[0] != 1:
                    return -65535

                # 关闭挑管区保温盖
                result = self._insulation(action_id=2)
                if result[0] != 1:
                    return -65535

                # 关桶盖和下降
                result = self._cap(action_id=2)
                if result[0] != 1:
                    return -65535
                # 推出交接机构
                result = self._platform(action_id=1)
                if result[0] != 1:
                    return -65535

                # 皮带送出桶
                # result = self._belt(action_id=2)
                # if result[0] != 1:
                #     return -65535
                end = time.time()
                minute = round(end - start) // 60
                second = round(end - start) % 60
                logger.info('完成第 %d 次流程，耗时 %d 分 %d 秒' % (i, minute, second))
            else:
                logger.info('收到停止指令')
