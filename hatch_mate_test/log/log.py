import logging,os,time
from datetime import datetime

class Logger():
    def get_logger(name):
        logger = logging.getLogger(name)
        # 创建一个handler，用于写入日志文件
        fh = logging.FileHandler(name, mode='a+', encoding='utf-8')
        # 再创建一个handler用于输出到控制台
        ch = logging.StreamHandler()
        # 定义输出格式(可以定义多个输出格式例formatter1，formatter2)
        formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
        # 定义日志输出层级
        logger.setLevel(logging.DEBUG)
        # 定义控制台输出层级
        # logger.setLevel(logging.DEBUG)
        # 为文件操作符绑定格式（可以绑定多种格式例fh.setFormatter(formatter2)）
        fh.setFormatter(formatter)
        # 为控制台操作符绑定格式（可以绑定多种格式例ch.setFormatter(formatter2)）
        ch.setFormatter(formatter)
        # 给logger对象绑定文件操作符
        logger.addHandler(fh)
        # 给logger对象绑定文件操作符
        logger.addHandler(ch)
        return logger



# if __name__ == "__main__":
    # log1 = get_logger('logger1')
    # log2 = get_logger('logger2')
    #
    # log1.debug("This is a debug log.")
    # log1.info("This is a info log.")
    # log1.warning("This is a warning log.")
    # log1.error("This is a error log.")
    # log1.critical("This is a critical log.")
    #
    # log2.debug("This is a debug log.")
    # log2.info("This is a info log.")
    # log2.warning("This is a warning log.")
    # log2.error("This is a error log.")
    # log2.critical("This is a critical log.")