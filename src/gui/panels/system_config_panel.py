import logging
import sys
from pathlib import Path

from PyQt6.QtGui import QColor, QTextCursor
from PyQt6.QtWidgets import (QApplication, QMainWindow, QTabWidget,
                             QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
                             QLineEdit, QTextEdit, QListWidget, QFileDialog, QCheckBox, QFormLayout, QSpinBox,
                             QGroupBox, QComboBox, QTimeEdit, QGridLayout, QDateEdit, QMessageBox)
from PyQt6.QtCore import Qt, QTime, QDate, QObject, pyqtSignal
import os

from config import config, Config
from auto_clip import auto_clip

from logger import setup_logger

logger = setup_logger(__name__)

class SystemConfigPanel(QWidget):
    """其他设置标签页"""

    # 默认值常量
    DEFAULT_OBS_HOST = "localhost"
    DEFAULT_OBS_PORT = 4455
    DEFAULT_EXTRA_SECONDS = 15
    DEFAULT_WAIT_SEED = 20
    DEFAULT_REPLAY_THRESHOLD = 20
    DEFAULT_DEATH_CLIP_DURATION = 20
    DEFAULT_DEATH_CLIP_AHEAD = 0

    # 界面文本常量
    LABEL_OBS_HOST = "OBS主机名："
    LABEL_OBS_PORT = "OBS端口号："
    LABEL_EXTRA_SECONDS = "录像额外秒数："
    LABEL_WAIT_SEED = r"等待\seed秒数："
    LABEL_REPLAY_THRESHOLD = "回放共用时长秒数："
    LABEL_DEATH_CLIP_DURATION = "死亡切片时长："
    LABEL_DEATH_CLIP_AHEAD = "死亡切片提前量："
    LABEL_BROWSER_PATH = "浏览器可执行文件路径：{}"

    BTN_SELECT_FILE = "选择文件"
    BTN_SAVE = "保存"
    BTN_RESET = "恢复默认"

    FILE_FILTER = "可执行文件 (*.exe)"
    FILE_EMPTY = "空"

    def __init__(self):
        super().__init__()
        self.browser_executable = config.browser_executable.as_posix()
        self._init_ui()

    def _init_ui(self):
        """初始化用户界面"""
        layout = QFormLayout()

        # OBS设置
        self._create_obs_settings(layout)

        # 时间设置
        self._create_time_settings(layout)

        # 浏览器设置
        self._create_browser_settings(layout)

        # 功能开关
        self._create_feature_toggles(layout)

        # 保存和重置按钮
        self._create_action_buttons(layout)

        self.setLayout(layout)

    def _create_obs_settings(self, layout):
        """创建OBS相关设置"""
        # OBS主机名
        self.obs_host_input = QLineEdit()
        self.obs_host_input.setText(config.host)
        layout.addRow(self.LABEL_OBS_HOST, self.obs_host_input)

        # OBS端口
        self.obs_port_spin = self._create_spinbox(
            min_val=0,
            max_val=65535,
            default=config.port
        )
        layout.addRow(self.LABEL_OBS_PORT, self.obs_port_spin)

    def _create_time_settings(self, layout):
        """创建时间相关设置"""
        # 录像额外秒数
        self.extra_seconds_spin = self._create_spinbox(
            min_val=0,
            max_val=60,
            default=config.extra_seconds
        )
        layout.addRow(self.LABEL_EXTRA_SECONDS, self.extra_seconds_spin)

        # 等待\seed秒数
        self.wait_seed_spin = self._create_spinbox(
            min_val=0,
            max_val=60,
            default=config.wait_for_datapack
        )
        layout.addRow(self.LABEL_WAIT_SEED, self.wait_seed_spin)

        # 回放共用时长秒数
        self.replay_threshold_spin = self._create_spinbox(
            min_val=0,
            max_val=60,
            default=config.replay_threshold_seconds
        )
        layout.addRow(self.LABEL_REPLAY_THRESHOLD, self.replay_threshold_spin)

        # 死亡切片时长
        self.death_clip_duration_spin = self._create_spinbox(
            min_val=0,
            max_val=120,
            default=config.death_clip_duration
        )
        layout.addRow(self.LABEL_DEATH_CLIP_DURATION, self.death_clip_duration_spin)

        # 死亡切片提前量
        self.death_clip_ahead_spin = self._create_spinbox(
            min_val=-20,
            max_val=20,
            default=config.death_clip_ahead_seconds
        )
        layout.addRow(self.LABEL_DEATH_CLIP_AHEAD, self.death_clip_ahead_spin)

    def _create_browser_settings(self, layout):
        """创建浏览器相关设置"""
        # 浏览器路径显示
        self.browser_path_label = QLabel(self._get_browser_path_text())
        self.browser_path_label.setWordWrap(True)
        layout.addRow(self.browser_path_label)

        # 选择文件按钮
        self.select_browser_btn = QPushButton(self.BTN_SELECT_FILE)
        self.select_browser_btn.clicked.connect(self._on_select_browser)
        layout.addRow(self.select_browser_btn)

    def _create_feature_toggles(self, layout):
        """创建功能开关复选框"""
        # 创建复选框
        self.use_cover_checkbox = QCheckBox("使用自动生成的封面")
        self.use_cover_checkbox.setChecked(config.use_cover)

        self.use_description_checkbox = QCheckBox("使用自动生成的简介")
        self.use_description_checkbox.setChecked(config.use_description)

        self.use_upload_checkbox = QCheckBox("使用上传功能")
        self.use_upload_checkbox.setChecked(config.use_upload)

        self.use_rsg_pb_checkbox = QCheckBox("使用rsg_pb功能")
        self.use_rsg_pb_checkbox.setChecked(config.use_rsg_pb)

        # 横向布局
        toggle_layout = QHBoxLayout()
        toggle_layout.addWidget(self.use_cover_checkbox)
        toggle_layout.addWidget(self.use_description_checkbox)
        toggle_layout.addWidget(self.use_upload_checkbox)
        toggle_layout.addWidget(self.use_rsg_pb_checkbox)

        layout.addRow(toggle_layout)

    def _create_action_buttons(self, layout):
        """创建操作按钮(保存、恢复默认)"""
        button_layout = QHBoxLayout()

        # 恢复默认按钮
        self.reset_btn = QPushButton(self.BTN_RESET)
        self.reset_btn.clicked.connect(self._on_reset)
        button_layout.addWidget(self.reset_btn)

        # 保存按钮
        self.save_btn = QPushButton(self.BTN_SAVE)
        self.save_btn.clicked.connect(self._on_save)
        button_layout.addWidget(self.save_btn)

        layout.addRow(button_layout)

    def _create_spinbox(self, min_val, max_val, default):
        """创建配置好的SpinBox"""
        spinbox = QSpinBox()
        spinbox.setRange(min_val, max_val)
        spinbox.setValue(default)
        spinbox.setSingleStep(1)
        return spinbox

    def _get_browser_path_text(self):
        """获取浏览器路径显示文本"""
        return self.LABEL_BROWSER_PATH.format(
            str(self.browser_executable) or self.FILE_EMPTY
        )

    def _update_browser_path_label(self):
        """更新浏览器路径显示"""
        self.browser_path_label.setText(self._get_browser_path_text())

    def _on_select_browser(self):
        """处理选择浏览器可执行文件事件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择浏览器可执行文件",
            "",
            self.FILE_FILTER
        )

        if file_path:
            self.browser_executable = Path(file_path)
            logger.info(f'选择的文件: {file_path}')

        self._update_browser_path_label()

    def _on_reset(self):
        """处理恢复默认设置事件"""
        reply = QMessageBox.question(
            self,
            "确认",
            "确定要恢复所有设置为默认值吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self._reset_to_defaults()
            QMessageBox.information(self, "成功", "已恢复默认设置")

    def _reset_to_defaults(self):
        """重置所有设置为默认值"""
        # OBS设置
        self.obs_host_input.setText(Config.model_fields["host"].default)
        self.obs_port_spin.setValue(Config.model_fields["port"].default)

        # 时间设置
        self.extra_seconds_spin.setValue(Config.model_fields["extra_seconds"].default)
        self.wait_seed_spin.setValue(Config.model_fields["wait_for_datapack"].default)
        self.replay_threshold_spin.setValue(Config.model_fields["replay_threshold_seconds"].default)
        self.death_clip_duration_spin.setValue(Config.model_fields["death_clip_duration"].default)
        self.death_clip_ahead_spin.setValue(Config.model_fields["death_clip_ahead_seconds"].default)

        # 浏览器设置
        self.browser_executable = Config.model_fields["browser_executable"].default
        self._update_browser_path_label()

        # 功能开关
        self.use_cover_checkbox.setChecked(Config.model_fields["use_cover"].default)
        self.use_description_checkbox.setChecked(Config.model_fields["use_description"].default)
        self.use_upload_checkbox.setChecked(Config.model_fields["use_upload"].default)
        self.use_rsg_pb_checkbox.setChecked(Config.model_fields["use_rsg_pb"].default)

    def _on_save(self):
        """处理保存事件"""
        # 验证OBS主机名
        if not self.obs_host_input.text().strip():
            QMessageBox.warning(self, "警告", "OBS主机名不能为空")
            return

        old_host = config.host
        old_port = config.port

        config.host = self.obs_host_input.text().strip()
        config.port = self.obs_port_spin.value()

        config.extra_seconds = self.extra_seconds_spin.value()
        config.wait_for_datapack = self.wait_seed_spin.value()
        config.replay_threshold_seconds = self.replay_threshold_spin.value()
        config.death_clip_duration = self.death_clip_duration_spin.value()
        config.death_clip_ahead_seconds = self.death_clip_ahead_spin.value()
        config.browser_executable = self.browser_executable
        config.use_cover = self.use_cover_checkbox.isChecked()
        config.use_description = self.use_description_checkbox.isChecked()
        config.use_upload = self.use_upload_checkbox.isChecked()
        config.use_rsg_pb = self.use_rsg_pb_checkbox.isChecked()

        if config.host != old_host or config.port != old_port:
            if auto_clip.obs_controller is not None:
                auto_clip.obs_controller.stop()
                auto_clip.obs_controller = None

        changed_fields = {
            "host": config.host,
            "port": config.port,
            "extra_seconds": config.extra_seconds,
            "wait_for_datapack": config.wait_for_datapack,
            "replay_threshold_seconds": config.replay_threshold_seconds,
            "death_clip_duration": config.death_clip_duration,
            "death_clip_ahead_seconds": config.death_clip_ahead_seconds,
            "browser_executable": config.browser_executable,
            "use_cover": config.use_cover,
            "use_description": config.use_description,
            "use_upload": config.use_upload,
            "use_rsg_pb": config.use_rsg_pb,
        }
        logger.info(f"保存配置: {changed_fields}")
        QMessageBox.information(self, "成功", "设置已保存")

        config.save()

    def get_config(self):
        """获取当前配置"""
        return {
            'obs_host': self.obs_host_input.text().strip(),
            'obs_port': self.obs_port_spin.value(),
            'extra_seconds': self.extra_seconds_spin.value(),
            'wait_seed': self.wait_seed_spin.value(),
            'replay_threshold': self.replay_threshold_spin.value(),
            'death_clip_duration': self.death_clip_duration_spin.value(),
            'death_clip_ahead': self.death_clip_ahead_spin.value(),
            'browser_executable': self.browser_executable,
            'use_cover': self.use_cover_checkbox.isChecked(),
            'use_description': self.use_description_checkbox.isChecked(),
            'use_upload': self.use_upload_checkbox.isChecked(),
            'use_rsg_pb': self.use_rsg_pb_checkbox.isChecked()
        }

