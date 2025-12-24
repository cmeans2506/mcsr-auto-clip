import logging
import sys

from pathlib import Path
from typing import Callable, Any

from PyQt6.QtGui import QColor, QTextCursor
from PyQt6.QtWidgets import (QApplication, QMainWindow, QTabWidget,
                             QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
                             QLineEdit, QTextEdit, QListWidget, QFileDialog, QCheckBox, QFormLayout, QSpinBox,
                             QGroupBox, QComboBox, QTimeEdit, QGridLayout, QDateEdit, QMessageBox)
from PyQt6.QtCore import Qt, QTime, QDate, QObject, pyqtSignal, QThread
import os
import traceback

from auto_clip import auto_clip
from config import config
from my_exceptions import (PlayerNotFoundException, RankedAPIUnavailableError, PacemanAPIUnavailableError,
                           OBSConnectionException, OBSReplayNotEnableError, BiliupNotConfiguredException,
                           BiliupLogInError, FfmpegNotConfiguredException)
from logger import setup_logger

logger = setup_logger(__name__)


class Worker(QThread):
    success = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, func: Callable[[], Any]):
        super().__init__()
        self.func = func

    def run(self):
        try:
            self.func()
            self.success.emit()
        except (PlayerNotFoundException, RankedAPIUnavailableError, PacemanAPIUnavailableError,
                OBSConnectionException, OBSReplayNotEnableError, BiliupNotConfiguredException,
                BiliupLogInError, FfmpegNotConfiguredException) as e:
            self.error.emit(str(e))
            logger.warning(str(e))
        except Exception:
            self.error.emit(traceback.format_exc())
            logger.warning(traceback.format_exc())


class GameConfigPanel(QWidget):
    """游戏视频处理标签页"""

    # 界面文本常量
    LABEL_NICKNAME = "游戏名称:"
    LABEL_VIDEO_FOLDER = "视频文件夹：{}"
    PLACEHOLDER_NICKNAME = "请输入游戏名"
    FOLDER_EMPTY = "空"

    BTN_SELECT_FOLDER = "选择文件夹"
    BTN_OPEN_FOLDER = "打开文件夹"
    BTN_SAVE = "保存"
    BTN_START = "开始"
    BTN_STOP = "停止"

    def __init__(self):
        super().__init__()
        self.folder_path = config.base_dir.as_posix()
        self._init_ui()

    def _init_ui(self):
        """初始化用户界面"""
        main_layout = QVBoxLayout()

        # 游戏名称输入区域
        main_layout.addWidget(QLabel(self.LABEL_NICKNAME))
        self.nickname_input = QLineEdit()
        self.nickname_input.setPlaceholderText(self.PLACEHOLDER_NICKNAME)
        self.nickname_input.setText(config.player.name)
        main_layout.addWidget(self.nickname_input)

        # 文件夹路径显示
        self.path_label = QLabel(self._get_folder_label_text())
        self.path_label.setWordWrap(True)
        main_layout.addWidget(self.path_label)

        # 文件夹操作按钮
        main_layout.addLayout(self._create_folder_buttons())

        # 保存按钮
        self.save_btn = QPushButton(self.BTN_SAVE)
        self.save_btn.clicked.connect(self._on_save)
        main_layout.addWidget(self.save_btn)

        main_layout.addStretch(1)

        # 处理选项复选框
        main_layout.addLayout(self._create_process_options())

        # 开始/停止按钮
        main_layout.addLayout(self._create_control_buttons())

        main_layout.addStretch(1)

        self.setLayout(main_layout)

    def _create_folder_buttons(self):
        """创建文件夹操作按钮"""
        layout = QHBoxLayout()

        self.open_folder_btn = QPushButton(self.BTN_OPEN_FOLDER)
        self.open_folder_btn.clicked.connect(self._on_open_folder)

        self.select_folder_btn = QPushButton(self.BTN_SELECT_FOLDER)
        self.select_folder_btn.clicked.connect(self._on_select_folder)

        layout.addWidget(self.open_folder_btn)
        layout.addWidget(self.select_folder_btn)

        return layout

    def _create_process_options(self):
        """创建处理选项复选框"""
        layout = QHBoxLayout()

        self.ranked_checkbox = QCheckBox("ranked")
        self.ranked_checkbox.setChecked(config.ranked_job)
        self.rsg_checkbox = QCheckBox("rsg")
        self.rsg_checkbox.setChecked(config.rsg_job)
        self.death_clip_checkbox = QCheckBox("死亡切片")
        self.death_clip_checkbox.setChecked(config.use_death_clip)
        self.obs_clean_checkbox = QCheckBox("源文件清理")
        self.obs_clean_checkbox.setChecked(config.clean_raw_file)

        layout.addWidget(self.ranked_checkbox)
        layout.addWidget(self.rsg_checkbox)
        layout.addWidget(self.death_clip_checkbox)
        layout.addWidget(self.obs_clean_checkbox)

        return layout

    def _create_control_buttons(self):
        """创建开始/停止控制按钮"""
        layout = QHBoxLayout()

        self.start_btn = QPushButton(self.BTN_START)
        self.start_btn.clicked.connect(self._on_start)

        self.stop_btn = QPushButton(self.BTN_STOP)
        self.stop_btn.clicked.connect(self._on_stop)

        layout.addWidget(self.start_btn)
        layout.addWidget(self.stop_btn)

        return layout

    def _get_folder_label_text(self):
        """获取文件夹标签文本"""
        return self.LABEL_VIDEO_FOLDER.format(
            self.folder_path or self.FOLDER_EMPTY
        )

    def _update_folder_label(self):
        """更新文件夹路径显示"""
        self.path_label.setText(self._get_folder_label_text())

    def _on_select_folder(self):
        """处理选择文件夹事件"""
        folder_path = QFileDialog.getExistingDirectory(
            self,
            "选择文件夹",
            "",
            QFileDialog.Option.ShowDirsOnly
        )

        if not folder_path:
            return

        self.folder_path = folder_path
        logger.info(f'选择的视频文件夹: {folder_path}')

        self._update_folder_label()

    def _on_open_folder(self):
        """处理打开文件夹事件"""
        if not self.folder_path or not os.path.isdir(self.folder_path):
            QMessageBox.warning(self, "警告", "请先选择有效的文件夹")
            return

        try:
            os.startfile(self.folder_path)
        except Exception as e:
            QMessageBox.critical(self, "错误", f"无法打开文件夹: {str(e)}")

    def _on_save(self):
        """处理保存事件"""
        nickname = self.nickname_input.text().strip()

        if not nickname:
            QMessageBox.warning(self, "警告", "请输入游戏名称")
            return

        if not self.folder_path or not os.path.isdir(self.folder_path):
            QMessageBox.warning(self, "警告", "请选择有效的视频文件夹")
            return

        # TODO: 实现保存逻辑
        config.player.name = nickname
        config.base_dir = Path(self.folder_path)
        config.ranked_job = self.ranked_checkbox.isChecked()
        config.rsg_job = self.rsg_checkbox.isChecked()
        config.use_death_clip = self.death_clip_checkbox.isChecked()
        config.clean_raw_file = self.obs_clean_checkbox.isChecked()

        logger.info(f"保存配置 - 游戏名称: {nickname}, 文件夹: {self.folder_path}")
        logger.info(f"处理选项 - ranked: {self.ranked_checkbox.isChecked()}, "
              f"rsg: {self.rsg_checkbox.isChecked()}, "
              f"死亡切片: {self.death_clip_checkbox.isChecked()}, "
              f"源文件清理: {self.obs_clean_checkbox.isChecked()}")

        config.save()

    def _on_start(self):
        if hasattr(self, "_start_worker") and self._start_worker.isRunning() or auto_clip.is_running:
            QMessageBox.warning(self, "启动错误", "mcsr auto clip正在运行")
            return

        def _on_start_success():
            QMessageBox.information(self, "启动成功", "mcsr auto clip已启动")

        def _on_start_error(detail):
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Icon.Critical)
            msg.setWindowTitle("启动失败")
            msg.setText("启动时出现错误：\n" + detail)
            msg.exec()


        self._start_worker = Worker(auto_clip.start)
        self._start_worker.success.connect(_on_start_success)
        self._start_worker.error.connect(_on_start_error)
        self._start_worker.start()


    def _on_stop(self):
        if (hasattr(self, "_stop_worker") and self._stop_worker.isRunning()) or not auto_clip.is_running:
            QMessageBox.warning(self, "停止错误", "mcsr auto clip已停止")
            return

        def _on_stop_success():
            QMessageBox.information(self, "停止成功", "mcsr auto clip已停止")

        def _on_stop_error(detail):
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Icon.Critical)
            msg.setWindowTitle("停止失败")
            msg.setText("停止时出现错误：\n" + detail)
            msg.exec()


        self._stop_worker = Worker(auto_clip.stop)
        self._stop_worker.success.connect(_on_stop_success)
        self._stop_worker.error.connect(_on_stop_error)
        self._stop_worker.start()

    def get_config(self):
        """获取当前配置"""
        return {
            'game_name': self.nickname_input.text().strip(),
            'folder_path': self.folder_path,
            'ranked': self.ranked_checkbox.isChecked(),
            'rsg': self.rsg_checkbox.isChecked(),
            'death_clip': self.death_clip_checkbox.isChecked(),
            'obs_clean': self.obs_clean_checkbox.isChecked()
        }

    def set_config(self, config):
        """设置配置"""
        self.nickname_input.setText(config.get('game_name', ''))
        self.folder_path = config.get('folder_path', '')
        self._update_folder_label()

        self.ranked_checkbox.setChecked(config.get('ranked', False))
        self.rsg_checkbox.setChecked(config.get('rsg', False))
        self.death_clip_checkbox.setChecked(config.get('death_clip', False))
        self.obs_clean_checkbox.setChecked(config.get('obs_clean', False))