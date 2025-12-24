import logging

from PyQt6.QtCore import pyqtSlot
from PyQt6.QtGui import QColor, QTextCharFormat, QTextCursor
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPlainTextEdit

from logger import log_signal_hub


class LogViewer(QPlainTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setMaximumBlockCount(1000)  # 性能关键：限制最大行数，防止内存溢出

        # 颜色映射 (使用标准 Level 数值)
        self.color_map = {
            logging.DEBUG: QColor("gray"),
            logging.INFO: QColor("black"),
            logging.WARNING: QColor("darkorange"),
            logging.ERROR: QColor("red"),
            logging.CRITICAL: QColor("darkred"),
        }

    @pyqtSlot(str, int)
    def append_log(self, message, level):
        # 设置特定级别的颜色
        color = self.color_map.get(level, QColor("black"))

        fmt = QTextCharFormat()
        fmt.setForeground(color)

        self.moveCursor(QTextCursor.MoveOperation.End)
        self.setCurrentCharFormat(fmt)
        self.appendPlainText(message)
        self.moveCursor(QTextCursor.MoveOperation.End)



class LogViewerPanel(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()

        self.log_viewer = LogViewer()
        layout.addWidget(self.log_viewer)
        self.setLayout(layout)
        log_signal_hub.log_signal.connect(self.log_viewer.append_log)

