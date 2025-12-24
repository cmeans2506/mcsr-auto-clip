import logging
from datetime import datetime
from PyQt6.QtCore import QObject, pyqtSignal

from config import config

formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

class LogSignalHub(QObject):
    log_signal = pyqtSignal(str, int)

log_signal_hub = LogSignalHub()

class QtLoggingHandler(logging.Handler):
    def __init__(self):
        super().__init__()
        self.setFormatter(formatter)
        self.setLevel(logging.INFO)

    def emit(self, record):
        msg = self.format(record)
        # 信号发射是线程安全的
        log_signal_hub.log_signal.emit(msg, record.levelno)


def setup_logger(name=None, log_level=logging.DEBUG):
    # 获取或创建 logger
    logger = logging.getLogger(name or 'main')

    # 避免重复添加 handler
    if logger.handlers:
        return logger

    logger.setLevel(log_level)

    # 控制台输出
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # 文件输出 - 所有日志
    log_file = config.log_dir / f"mcsr_auto_clip_{datetime.now().strftime('%Y%m%d')}.log"
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    qt_logging_handler = QtLoggingHandler()
    logger.addHandler(qt_logging_handler)

    return logger
