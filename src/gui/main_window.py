import sys

from PyQt6.QtCore import Qt, QRect, QTimer
from PyQt6.QtWidgets import QMainWindow, QTabWidget, QWidget, QVBoxLayout, QLabel, QApplication, QMessageBox, QStatusBar

from gui.panels.game_config_panel import GameConfigPanel
from gui.panels.pb_record_panel import PBRecordPanel
from gui.panels.system_config_panel import SystemConfigPanel
from gui.panels.time_config_panel import TimeConfigPanel
from gui.panels.log_viewer_panel import LogViewerPanel

from gui.status_notifier import status_notifier

from auto_clip import auto_clip, scheduler_error_notifier

from config import VERSION, config
from logger import setup_logger

logger = setup_logger(__name__)


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

        self.tabs.addTab(self.tab1, self.tr("Home"))
        self.tabs.addTab(self.tab2, self.tr("Launch Settings"))
        self.tabs.addTab(self.tab3, self.tr("System Settings"))
        self.tabs.addTab(self.tab4, self.tr("Time Settings"))
        self.tabs.addTab(self.tab5, self.tr("RSG PB Settings"))
        self.tabs.addTab(self.tab6, self.tr("Logs"))

        # 创建状态栏
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_label = QLabel()
        self.status_bar.addPermanentWidget(self.status_label)

        # 初始化状态显示
        self._update_status()

        scheduler_error_notifier.signal.connect(self._on_job_error)
        status_notifier.message_signal.connect(self._show_status_message)

        if config.auto_start:
            self.tab2._on_start()

        self.auto_save_timer = QTimer(self)
        self.auto_save_timer.timeout.connect(self._auto_save)
        self.auto_save_timer.start(500)

        # 状态更新定时器
        self.status_update_timer = QTimer(self)
        self.status_update_timer.timeout.connect(self._update_status)
        self.status_update_timer.start(1000)  # 每秒更新一次状态

    def create_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()

        label = QLabel(self.tr("Welcome to MCSR AUTO CLIP"))
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet("font-size: 24px; font-weight: bold;")

        desc = QLabel(f'{self.tr("Author: Cmeans")} <br>'
                      f'<a href="https://discord.gg/WtWYRjQB">Discord</a>&nbsp; | &nbsp;'
                      f'<a href="https://qm.qq.com/q/ZrPnhF9JcW">QQ</a>')
        desc.setOpenExternalLinks(True)
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc.setStyleSheet("font-size: 14px; margin-top: 20px;")

        layout.addStretch()
        layout.addWidget(label)
        layout.addWidget(desc)
        layout.addStretch()

        tab.setLayout(layout)
        return tab

    def _update_status(self):
        """更新状态栏显示"""
        if auto_clip.is_running:
            self.status_label.setText(self.tr("Status: Running"))
            self.status_label.setStyleSheet("color: #10b981;")
        else:
            self.status_label.setText(self.tr("Status: Stopped"))
            self.status_label.setStyleSheet("color: #71717a;")


    def _show_status_message(self, message: str, timeout: int = 3000):
        """在状态栏左侧显示临时消息"""
        self.status_bar.showMessage(message, timeout)


    def _auto_save(self):
        """自动保存配置"""
        if self.tab2._has_unsaved_changes:
            self.tab2._save_config(silent=True)
            logger.info("Auto-saved game configuration")

        if self.tab3._has_unsaved_changes:
            self.tab3._save_config(silent=True)
            logger.info("Auto-saved system configuration")

        if self.tab4._has_unsaved_changes:
            self.tab4._save_config(silent=True)
            logger.info("Auto-saved time configuration")

        if self.tab5._has_unsaved_changes:
            self.tab5._save_config(silent=True)
            logger.info("Auto-saved PB records")

    def _on_job_error(self, text: str):
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Icon.Critical)
        msg.setWindowTitle(self.tr("Error"))
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