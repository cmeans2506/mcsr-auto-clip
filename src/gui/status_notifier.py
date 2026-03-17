from PyQt6.QtCore import QObject, pyqtSignal


class StatusNotifier(QObject):
    message_signal = pyqtSignal(str, int)  # (消息, 显示毫秒数)

# 全局单例
status_notifier = StatusNotifier()