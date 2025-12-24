import logging
import sys

from PyQt6.QtGui import QColor, QTextCursor
from PyQt6.QtWidgets import (QApplication, QMainWindow, QTabWidget,
                             QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
                             QLineEdit, QTextEdit, QListWidget, QFileDialog, QCheckBox, QFormLayout, QSpinBox,
                             QGroupBox, QComboBox, QTimeEdit, QGridLayout, QDateEdit, QMessageBox)
from PyQt6.QtCore import Qt, QTime, QDate, QObject, pyqtSignal
import os

from config import config, Config, Setting
from translator import translator
from logger import setup_logger

logger = setup_logger(__name__)

class TimeConfigPanel(QWidget):
    """时间设置标签页"""
    # 界面文本常量
    MODE_OPTIONS = ["切片设置", "上传设置"]
    MATCH_TYPES = list(translator.match_type_map.values())

    LABEL_MAX_TIME = "最大允许时间："
    LABEL_SEED_FILTER = "种子类型筛选"
    LABEL_BASTION_FILTER = "猪堡类型筛选"

    # RSG标签
    LABEL_ENTER_NETHER = "进地狱："
    LABEL_ENTER_BASTION = "进猪堡："
    LABEL_ENTER_FORTRESS = "进地狱堡垒："
    LABEL_FIRST_PORTAL = "盲传："
    LABEL_ENTER_STRONGHOLD = "进要塞："
    LABEL_ENTER_END = "进末地："
    LABEL_CREDITS = "结束："

    BTN_SAVE = "保存"
    BTN_RESET = "恢复默认"

    def __init__(self):
        super().__init__()
        self._init_ui()
        self._connect_signals()

    def _init_ui(self):
        """初始化用户界面"""
        layout = QVBoxLayout()

        # 模式选择
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(self.MODE_OPTIONS)
        self.mode_combo.setCurrentIndex(0)
        layout.addWidget(self.mode_combo)


        # RANKED和RSG分组横向布局
        groups_layout = QHBoxLayout()
        groups_layout.addWidget(self._create_ranked_group())
        groups_layout.addWidget(self._create_rsg_group())
        layout.addLayout(groups_layout)

        # 操作按钮
        layout.addWidget(self._create_action_buttons())

        self._load_current_match_config()

        self.setLayout(layout)

    def _connect_signals(self):
        """连接信号"""
        # 模式切换时加载对应配置
        self.mode_combo.currentIndexChanged.connect(self._on_mode_changed)
        # 匹配类型切换时加载对应配置
        self.match_type_combo.currentIndexChanged.connect(self._on_match_type_changed)

    def _create_ranked_group(self):
        """创建RANKED设置组"""
        group = QGroupBox("RANKED")
        layout = QVBoxLayout()

        # 匹配类型选择
        self.match_type_combo = QComboBox()
        self.match_type_combo.addItems(self.MATCH_TYPES)
        self.match_type_combo.setCurrentIndex(1)
        layout.addWidget(self.match_type_combo)

        # 最大允许时间
        time_layout = QFormLayout()
        self.ranked_time_edit = self._create_time_edit()
        time_layout.addRow(self.LABEL_MAX_TIME, self.ranked_time_edit)
        layout.addLayout(time_layout)

        # 种子类型筛选
        layout.addWidget(QLabel(self.LABEL_SEED_FILTER))
        layout.addLayout(self._create_seed_type_checkboxes())

        # 猪堡类型筛选
        layout.addWidget(QLabel(self.LABEL_BASTION_FILTER))
        layout.addLayout(self._create_bastion_type_checkboxes())

        group.setLayout(layout)
        return group

    def _create_seed_type_checkboxes(self):
        """创建种子类型复选框"""
        layout = QHBoxLayout()

        self.seed_checkboxes = {}
        for en_name, cn_name in translator.seedtype_map.items():
            cb = QCheckBox(cn_name)
            self.seed_checkboxes[en_name] = cb
            layout.addWidget(cb)

        return layout

    def _create_bastion_type_checkboxes(self):
        """创建猪堡类型复选框"""
        layout = QHBoxLayout()

        self.bastion_checkboxes = {}
        for en_name, cn_name in translator.bastion_map.items():
            cb = QCheckBox(cn_name)
            self.bastion_checkboxes[en_name] = cb
            layout.addWidget(cb)

        return layout

    def _create_rsg_group(self):
        """创建RSG设置组"""
        group = QGroupBox("RSG")
        layout = QVBoxLayout()

        form_layout = QFormLayout()

        # 创建所有RSG时间编辑器
        self.rsg_time_edits = {}

        for key, label in translator.event_map.items():
            time_edit = self._create_time_edit()
            self.rsg_time_edits[key] = time_edit
            form_layout.addRow(label, time_edit)

        layout.addLayout(form_layout)
        group.setLayout(layout)
        return group

    def _create_time_edit(self):
        """创建配置好的时间编辑器"""
        time_edit = QTimeEdit()
        time_edit.setDisplayFormat("mm:ss")
        time_edit.setTime(QTime(0, 0, 0))
        time_edit.setMinimumTime(QTime(0, 0, 0))
        time_edit.setMaximumTime(QTime(0, 59, 59))
        return time_edit

    def _create_action_buttons(self):
        """创建操作按钮"""
        widget = QWidget()
        layout = QHBoxLayout()

        # 恢复默认按钮
        self.reset_btn = QPushButton(self.BTN_RESET)
        self.reset_btn.clicked.connect(self._on_reset)
        layout.addWidget(self.reset_btn)

        # 保存按钮
        self.save_btn = QPushButton(self.BTN_SAVE)
        self.save_btn.clicked.connect(self._on_save)
        layout.addWidget(self.save_btn)

        widget.setLayout(layout)
        return widget

    def _on_mode_changed(self):
        """模式切换时加载配置"""
        self._load_current_match_config()

    def _on_match_type_changed(self):
        """匹配类型切换时加载配置"""
        self._load_current_match_config()

    def _load_current_match_config(self):
        """加载当前选中的匹配类型配置"""
        match_type = translator.match_type_map_rev[self.match_type_combo.currentText()]
        setting = config.clip_setting if self.mode_combo.currentIndex() == 0 else config.upload_setting

        ranked_config = setting.ranked[match_type]
        rsg_config = setting.rsg

        # 加载RANKED配置
        self.ranked_time_edit.setTime(self._ms_to_time(ranked_config.max_time))

        # 加载种子类型
        for en_name, cb in self.seed_checkboxes.items():
            cb.setChecked(en_name in ranked_config.seed_type)

        # 加载猪堡类型
        for en_name, cb in self.bastion_checkboxes.items():
            cb.setChecked(en_name in ranked_config.bastion_type)

        # 加载RSG配置
        for key, time_edit in self.rsg_time_edits.items():
            time_edit.setTime(self._ms_to_time(rsg_config[key]))

    def _save_current_match_config(self):
        """保存当前匹配类型配置到内存"""
        setting = config.clip_setting if self.mode_combo.currentIndex() == 0 else config.upload_setting
        match_type = translator.match_type_map_rev[self.match_type_combo.currentText()]

        # 保存RANKED配置
        setting.ranked[match_type].max_time = self._time_to_ms(self.ranked_time_edit)
        setting.ranked[match_type].seed_type = [
            en_name for en_name, cb in self.seed_checkboxes.items() if cb.isChecked()
        ]
        setting.ranked[match_type].bastion_type = [
            en_name for en_name, cb in self.bastion_checkboxes.items() if cb.isChecked()
        ]

        # 保存RSG配置
        for key, time_edit in self.rsg_time_edits.items():
            setting.rsg[key] = self._time_to_ms(time_edit)

        logger.info(f"保存配置:\n{self.MODE_OPTIONS[self.mode_combo.currentIndex()]} "
                    f"ranked {match_type}: {setting.ranked[match_type]}"
                    f"rsg: {setting.rsg}")

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
        config.clip_setting = Config.model_fields["clip_setting"].default_factory()
        config.upload_setting = Config.model_fields["upload_setting"].default_factory()
        self.mode_combo.setCurrentIndex(0)
        self.match_type_combo.setCurrentIndex(1)
        logger.info("已将 clip_setting 和 upload_setting 恢复至默认")
        self._load_current_match_config()

    def _on_save(self):
        """处理保存事件"""
        # 先保存当前界面的配置
        self._save_current_match_config()
        config.save()
        QMessageBox.information(self, "成功", "设置已保存")

    def _time_to_ms(self, time_edit):
        """将QTimeEdit转换为毫秒"""
        time = time_edit.time()
        total_seconds = time.minute() * 60 + time.second()
        return total_seconds * 1000

    def _ms_to_time(self, milliseconds):
        """将毫秒转换为QTime"""
        total_seconds = milliseconds // 1000
        minutes = total_seconds // 60
        seconds = total_seconds % 60
        return QTime(0, minutes, seconds)

