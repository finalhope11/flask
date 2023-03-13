from common.feature import Test
import traceback,time
from common.action import logger
class action_():
    def __init__(self):
        global link
        self.stop_move_rack = 0
    def con(self):
        try:
            link = Test()
            link.close_tcp_link()
            return 'connect success'
        except:
            return 'connect failed'

    def tube_move(self,Loops,action_id,TUBE_NU,BOX_ID_A,BOX_ID_B,TUBE_ID_A,TUBE_ID_B,random_flag,start):
        global link
        link = Test()
        try:
            print('正在执行')
            link.move_tube(loops=Loops, action_id=action_id, tube_nu=TUBE_NU, box_id_a=BOX_ID_A, box_id_b=BOX_ID_B,
                           tube_id_a=TUBE_ID_A, tube_id_b=TUBE_ID_B, random_flag=random_flag, start=start)
        except Exception as e:
            print('traceback.format_exc\t', traceback.format_exc(e))
            print('traceback.print_exc\t', traceback.print_exc(e))
        finally:
            link.close_tcp_link()
            time.sleep(0.1)
            print('执行完成')
        pass

    def stop(self):
        global link
        link.stop_tag = 1

    def all_test(self,Loops,TUBE_NU,BOX_ID,TUBE_ID,random_flag):
        global link
        link = Test()
        try:
            link.move_action(loops=Loops, tube_nu=TUBE_NU, box_id=BOX_ID, tube_id=TUBE_ID,
                             random_flag=random_flag)
        except Exception as e:
            print('traceback.format_exc\t', traceback.format_exc(e))
            print('traceback.print_exc\t', traceback.print_exc(e))
        finally:
            link.close_tcp_link()
            time.sleep(0.1)
            print('执行完成')
        pass

    def rack_move(self,BOX_ID_A,BOX_ID_B):
        link = Test()
        number = 0
        while self.stop_move_rack !=1:
            link.move_box(box_flag=number%2, box_id_a=BOX_ID_A, box_id_b=BOX_ID_B)
            time.sleep(1)
            logger.info("第{}次".format(number+1))
            number += 1
        logger.info('收到停止指令')

    def stop_move(self):
        self.stop_move_rack = 1
