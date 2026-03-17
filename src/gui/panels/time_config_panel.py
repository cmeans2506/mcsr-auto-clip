from PyQt6.QtWidgets import (QApplication, QMainWindow, QTabWidget,
                             QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
                             QLineEdit, QTextEdit, QListWidget, QFileDialog, QCheckBox, QFormLayout, QSpinBox,
                             QGroupBox, QComboBox, QTimeEdit, QGridLayout, QDateEdit, QMessageBox)
from PyQt6.QtCore import Qt, QTime, QDate, QObject, pyqtSignal, QTimer
from PyQt6.QtCore import QCoreApplication

from config import config, Config, Setting
from logger import setup_logger
from ranked.ranked_service import MatchType, SeedType, BastionType
from rsg.paceman_service import EventIdType

logger = setup_logger(__name__)


class TimeConfigPanel(QWidget):
    def __init__(self):
        super().__init__()
        self._has_unsaved_changes = False
        self._init_ui()
        self._connect_signals()
        self._connect_change_signals()


    def _init_ui(self):
        """初始化用户界面"""
        layout = QVBoxLayout()

        # 模式选择
        mode_group = QGroupBox(self.tr("MODE"))
        self.mode_combo = QComboBox()
        self.mode_combo.addItem(self.tr("Clip Setting"))
        self.mode_combo.addItem(self.tr("Upload Setting"))
        self.mode_combo.setCurrentIndex(0)

        mode_layout = QVBoxLayout()
        mode_layout.addWidget(self.mode_combo)
        mode_group.setLayout(mode_layout)

        layout.addWidget(mode_group)

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

    def _connect_change_signals(self):
        """连接所有输入控件的变化信号（在创建所有控件后调用）"""
        # 模式和匹配类型切换
        self.mode_combo.currentIndexChanged.connect(self._mark_unsaved)
        self.match_type_combo.currentIndexChanged.connect(self._mark_unsaved)

        # RANKED时间设置
        self.ranked_time_edit.timeChanged.connect(self._mark_unsaved)

        # 种子类型复选框
        for cb in self.seed_checkboxes.values():
            cb.stateChanged.connect(self._mark_unsaved)

        # 猪堡类型复选框
        for cb in self.bastion_checkboxes.values():
            cb.stateChanged.connect(self._mark_unsaved)

        # RSG时间编辑器
        for time_edit in self.rsg_time_edits.values():
            time_edit.timeChanged.connect(self._mark_unsaved)

    def _mark_unsaved(self):
        """标记有未保存的更改"""
        self._has_unsaved_changes = True


    def _create_ranked_group(self):
        """创建RANKED设置组"""
        group = QGroupBox(self.tr("RANKED"))
        layout = QVBoxLayout()

        # 匹配类型选择
        self.match_type_combo = QComboBox()
        for member in MatchType:
            self.match_type_combo.addItem(member.label, member)
        self.match_type_combo.setCurrentIndex(self.match_type_combo.findText(MatchType.RANKED_MATCH.label))
        # self.match_type_combo.setCurrentIndex(1)
        layout.addWidget(self.match_type_combo)

        # 最大允许时间
        time_layout = QFormLayout()
        self.ranked_time_edit = self._create_time_edit()
        time_layout.addRow(self.tr("Max Time"), self.ranked_time_edit)
        layout.addLayout(time_layout)

        # 种子类型筛选
        layout.addWidget(QLabel(self.tr("Seed Type")))
        layout.addLayout(self._create_seed_type_checkboxes())

        # 猪堡类型筛选
        layout.addWidget(QLabel(self.tr("Bastion Type")))
        layout.addLayout(self._create_bastion_type_checkboxes())

        group.setLayout(layout)
        return group

    def _create_seed_type_checkboxes(self):
        """创建种子类型复选框"""
        layout = QHBoxLayout()

        self.seed_checkboxes = {}

        for member in SeedType:
            cb = QCheckBox(member.label)
            self.seed_checkboxes[member] = cb
            layout.addWidget(cb)

        return layout

    def _create_bastion_type_checkboxes(self):
        """创建猪堡类型复选框"""
        layout = QHBoxLayout()

        self.bastion_checkboxes = {}
        for member in BastionType:
            cb = QCheckBox(member.label)
            self.bastion_checkboxes[member] = cb
            layout.addWidget(cb)

        return layout

    def _create_rsg_group(self):
        """创建RSG设置组"""
        group = QGroupBox("RSG")
        layout = QVBoxLayout()

        form_layout = QFormLayout()

        # 创建所有RSG时间编辑器
        self.rsg_time_edits = {}

        for member in EventIdType:
            # We don't use the SECOND_PORTAL, so skip
            if member == EventIdType.SECOND_PORTAL:
                continue
            time_edit = self._create_time_edit()
            self.rsg_time_edits[member] = time_edit
            form_layout.addRow(member.label, time_edit)

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
        self.reset_btn = QPushButton(self.tr("Reset"))
        self.reset_btn.clicked.connect(self._on_reset)
        layout.addWidget(self.reset_btn)

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
        match_type: MatchType = self.match_type_combo.currentData()
        setting = config.clip_setting if self.mode_combo.currentIndex() == 0 else config.upload_setting

        ranked_config = setting.ranked[match_type.name]
        rsg_config = setting.rsg

        # 加载RANKED配置
        self.ranked_time_edit.setTime(self._ms_to_time(ranked_config.max_time))

        # 加载种子类型
        for seed_type, cb in self.seed_checkboxes.items():
            cb.setChecked(seed_type in ranked_config.seed_type)

        # 加载猪堡类型
        for en_name, cb in self.bastion_checkboxes.items():
            cb.setChecked(en_name in ranked_config.bastion_type)

        # 加载RSG配置
        for event_id_type, time_edit in self.rsg_time_edits.items():
            time_edit.setTime(self._ms_to_time(rsg_config[event_id_type]))

    def _save_current_match_config(self):
        """保存当前匹配类型配置到内存"""
        setting = config.clip_setting if self.mode_combo.currentIndex() == 0 else config.upload_setting
        match_type: MatchType = self.match_type_combo.currentData()

        # 保存RANKED配置
        setting.ranked[match_type.name].max_time = self._time_to_ms(self.ranked_time_edit)
        setting.ranked[match_type.name].seed_type = [
            seed_type for seed_type, cb in self.seed_checkboxes.items() if cb.isChecked()
        ]
        setting.ranked[match_type.name].bastion_type = [
            bastion_type for bastion_type, cb in self.bastion_checkboxes.items() if cb.isChecked()
        ]

        # 保存RSG配置
        for key, time_edit in self.rsg_time_edits.items():
            setting.rsg[key] = self._time_to_ms(time_edit)

    def _on_reset(self):
        """处理恢复默认设置事件"""
        reply = QMessageBox.question(
            self,
            self.tr("Reset"),
            self.tr("Are you sure to reset the time settings to default?"),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self._reset_to_defaults()
            QMessageBox.information(self, self.tr("Success"), self.tr("The system settings has been reset to default"))

    def _reset_to_defaults(self):
        """重置所有设置为默认值"""
        config.clip_setting = Config.model_fields["clip_setting"].default_factory()
        config.upload_setting = Config.model_fields["upload_setting"].default_factory()
        self.mode_combo.setCurrentIndex(0)
        self.match_type_combo.setCurrentIndex(1)
        logger.info("Reset clip_setting and upload_setting to default values.")
        self._load_current_match_config()

        # 标记为未保存
        self._mark_unsaved()


    def _save_config(self, silent=False):
        """保存配置

        Args:
            silent: 是否静默保存(不显示成功消息框)
        """
        # 先保存当前界面的配置
        self._save_current_match_config()
        config.save()

        # 重置未保存标记
        self._has_unsaved_changes = False

        if not silent:
            QMessageBox.information(self, self.tr("Success"), self.tr("The Configuration has been saved"))

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