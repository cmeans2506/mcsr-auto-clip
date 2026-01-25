import sys

from PyQt6.QtCore import Qt, QRect
from PyQt6.QtWidgets import QMainWindow, QTabWidget, QWidget, QVBoxLayout, QLabel, QApplication, QMessageBox

from gui.panels.game_config_panel import GameConfigPanel
from gui.panels.pb_record_panel import PBRecordPanel
from gui.panels.system_config_panel import SystemConfigPanel
from gui.panels.time_config_panel import TimeConfigPanel
from gui.panels.log_viewer_panel import LogViewerPanel

from auto_clip import auto_clip, scheduler_error_notifier

from config import VERSION, config


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"MCSR AUTO CLIP {VERSION}")

        geometry = QRect(0, 0, 800, 450)
        center_point = QApplication.primaryScreen().geometry().center()
        geometry.moveCenter(center_point)
        self.setGeometry(geometry)

        # 创建标签页控件
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        self.tab1 = self.create_tab()
        self.tab2 = GameConfigPanel()
        self.tab3 = SystemConfigPanel()
        self.tab4 = TimeConfigPanel()
        self.tab5 = PBRecordPanel()
        self.tab6 = LogViewerPanel()

        self.tabs.addTab(self.tab1, "首页")
        self.tabs.addTab(self.tab2, "启动设置")
        self.tabs.addTab(self.tab3, "系统设置")
        self.tabs.addTab(self.tab4, "时间设置")
        self.tabs.addTab(self.tab5, "rsg_pb设置")
        self.tabs.addTab(self.tab6, "日志")

        scheduler_error_notifier.signal.connect(self._on_job_error)

        if config.auto_start:
            self.tab2._on_start()

    def create_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()

        label = QLabel("欢迎使用MCSR AUTO CLIP")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet("font-size: 24px; font-weight: bold;")

        desc = QLabel(f"作者: Cmeans \n反馈交流群: 1035220689\n{VERSION}")
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc.setStyleSheet("font-size: 14px; margin-top: 20px;")

        layout.addStretch()
        layout.addWidget(label)
        layout.addWidget(desc)
        layout.addStretch()

        tab.setLayout(layout)
        return tab

    def _on_job_error(self, text: str):
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Icon.Critical)
        msg.setWindowTitle("任务出错")
        msg.setText(text)
        msg.exec()

    def closeEvent(self, event):
        # 停止调度器，wait=False 表示不等待当前任务执行完立即停止
        # 如果有重要任务需要跑完，可以设置 wait=True
        if auto_clip.background_scheduler.running:
            auto_clip.background_scheduler.shutdown(wait=False)

        event.accept()  # 允许窗口关闭

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
