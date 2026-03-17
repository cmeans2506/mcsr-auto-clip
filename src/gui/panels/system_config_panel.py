from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton, QLineEdit, QCheckBox, QFormLayout, QSpinBox, \
    QMessageBox, QComboBox
from PyQt6.QtCore import QTimer

from config import config, Config
from auto_clip import auto_clip

from logger import setup_logger

logger = setup_logger(__name__)


class SystemConfigPanel(QWidget):

    def __init__(self):
        super().__init__()
        self._has_unsaved_changes = False
        self._init_ui()
        self._connect_change_signals()

    def _init_ui(self):
        """初始化用户界面"""
        layout = QFormLayout()

        self._create_language_settings(layout)

        # OBS设置
        self._create_obs_settings(layout)

        # 时间设置
        self._create_time_settings(layout)

        # 功能开关
        self._create_feature_toggles(layout)

        # 保存和重置按钮
        self._create_action_buttons(layout)

        self.setLayout(layout)


    def _connect_change_signals(self):
        """连接所有输入控件的变化信号"""
        self.lang_combo.currentIndexChanged.connect(self._mark_unsaved)

        # 文本输入
        self.obs_host_input.textChanged.connect(self._mark_unsaved)

        # 数字输入
        self.obs_port_spin.valueChanged.connect(self._mark_unsaved)
        self.extra_seconds_ranked_spin.valueChanged.connect(self._mark_unsaved)
        self.extra_seconds_rsg_spin.valueChanged.connect(self._mark_unsaved)
        self.wait_seed_spin.valueChanged.connect(self._mark_unsaved)
        self.death_clip_duration_spin.valueChanged.connect(self._mark_unsaved)
        self.death_clip_ahead_spin.valueChanged.connect(self._mark_unsaved)

        # 复选框
        self.auto_start_checkbox.stateChanged.connect(self._mark_unsaved)
        self.use_cover_checkbox.stateChanged.connect(self._mark_unsaved)
        self.use_description_checkbox.stateChanged.connect(self._mark_unsaved)
        self.use_upload_checkbox.stateChanged.connect(self._mark_unsaved)
        self.use_rsg_pb_checkbox.stateChanged.connect(self._mark_unsaved)

    def _mark_unsaved(self):
        """标记有未保存的更改"""
        self._has_unsaved_changes = True


    def _create_language_settings(self, layout):
        self.lang_combo = QComboBox()
        self.lang_combo.addItem("English", "en")
        self.lang_combo.addItem("中文", "zh_CN")
        self.lang_combo.setCurrentIndex(self.lang_combo.findData(config.lang))

        layout.addRow("language: ", self.lang_combo)

    def _create_obs_settings(self, layout):
        """创建OBS相关设置"""
        # OBS主机名
        self.obs_host_input = QLineEdit()
        self.obs_host_input.setText(config.host)
        layout.addRow(self.tr("OBS Host: "), self.obs_host_input)

        # OBS端口
        self.obs_port_spin = self._create_spinbox(
            min_val=0,
            max_val=65535,
            default=config.port
        )
        layout.addRow(self.tr("OBS Port: "), self.obs_port_spin)

    def _create_time_settings(self, layout):
        """创建时间相关设置"""
        # 录像额外秒数
        self.extra_seconds_ranked_spin = self._create_spinbox(
            min_val=0,
            max_val=60,
            default=config.extra_seconds_ranked
        )
        layout.addRow(self.tr("RANKED Video Extra Seconds: "), self.extra_seconds_ranked_spin)

        self.extra_seconds_rsg_spin = self._create_spinbox(
            min_val=-30,
            max_val=30,
            default=config.extra_seconds_rsg
        )
        layout.addRow(self.tr("RSG Video Extra Seconds: "), self.extra_seconds_rsg_spin)

        # 等待\seed秒数
        self.wait_seed_spin = self._create_spinbox(
            min_val=0,
            max_val=60,
            default=config.wait_for_datapack
        )
        layout.addRow(self.tr(r"Seconds waiting for \seed: "), self.wait_seed_spin)

        # 死亡切片时长
        self.death_clip_duration_spin = self._create_spinbox(
            min_val=0,
            max_val=120,
            default=config.death_clip_duration
        )
        layout.addRow(self.tr("Death Clip Duration: "), self.death_clip_duration_spin)

        # 死亡切片提前量
        self.death_clip_ahead_spin = self._create_spinbox(
            min_val=-20,
            max_val=20,
            default=config.death_clip_ahead_seconds
        )
        layout.addRow(self.tr("Death Clip Ahead Seconds: "), self.death_clip_ahead_spin)

    def _create_feature_toggles(self, layout):
        """创建功能开关复选框"""
        # 创建复选框
        self.auto_start_checkbox = QCheckBox(self.tr("Auto Launch"))
        self.auto_start_checkbox.setChecked(config.auto_start)

        self.use_cover_checkbox = QCheckBox(self.tr("Use Generated Cover"))
        self.use_cover_checkbox.setChecked(config.use_cover)

        self.use_description_checkbox = QCheckBox(self.tr("Use Generated Description"))
        self.use_description_checkbox.setChecked(config.use_description)

        self.use_upload_checkbox = QCheckBox(self.tr("Bilibili Upload"))
        self.use_upload_checkbox.setChecked(config.use_upload)

        self.use_rsg_pb_checkbox = QCheckBox(self.tr("Use Rsg PB"))
        self.use_rsg_pb_checkbox.setChecked(config.use_rsg_pb)

        # 横向布局
        toggle_layout = QHBoxLayout()
        toggle_layout.addWidget(self.auto_start_checkbox)
        toggle_layout.addWidget(self.use_cover_checkbox)
        toggle_layout.addWidget(self.use_description_checkbox)
        toggle_layout.addWidget(self.use_upload_checkbox)
        toggle_layout.addWidget(self.use_rsg_pb_checkbox)

        layout.addRow(toggle_layout)

    def _create_action_buttons(self, layout):
        """创建操作按钮(保存、恢复默认)"""
        button_layout = QHBoxLayout()

        # 恢复默认按钮
        self.reset_btn = QPushButton(self.tr("Reset"))
        self.reset_btn.clicked.connect(self._on_reset)
        button_layout.addWidget(self.reset_btn)

        layout.addRow(button_layout)

    def _create_spinbox(self, min_val, max_val, default):
        """创建配置好的SpinBox"""
        spinbox = QSpinBox()
        spinbox.setRange(min_val, max_val)
        spinbox.setValue(default)
        spinbox.setSingleStep(1)
        return spinbox

    def _on_reset(self):
        """处理恢复默认设置事件"""
        reply = QMessageBox.question(
            self,
            self.tr("Reset"),
            self.tr("Are you sure to reset the system settings to default?"),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self._reset_to_defaults()
            QMessageBox.information(self, self.tr("Success"), self.tr("The system settings has been reset to default"))

    def _reset_to_defaults(self):
        """重置所有设置为默认值"""
        self.lang_combo.setCurrentIndex(0)
        # OBS设置
        self.obs_host_input.setText(Config.model_fields["host"].default)
        self.obs_port_spin.setValue(Config.model_fields["port"].default)

        # 时间设置
        self.extra_seconds_ranked_spin.setValue(Config.model_fields["extra_seconds_ranked"].default)
        self.extra_seconds_rsg_spin.setValue(Config.model_fields["extra_seconds_rsg"].default)
        self.wait_seed_spin.setValue(Config.model_fields["wait_for_datapack"].default)
        self.death_clip_duration_spin.setValue(Config.model_fields["death_clip_duration"].default)
        self.death_clip_ahead_spin.setValue(Config.model_fields["death_clip_ahead_seconds"].default)

        # 功能开关
        self.auto_start_checkbox.setChecked(Config.model_fields["auto_start"].default)
        self.use_cover_checkbox.setChecked(Config.model_fields["use_cover"].default)
        self.use_description_checkbox.setChecked(Config.model_fields["use_description"].default)
        self.use_upload_checkbox.setChecked(Config.model_fields["use_upload"].default)
        self.use_rsg_pb_checkbox.setChecked(Config.model_fields["use_rsg_pb"].default)

        # 标记为未保存
        self._mark_unsaved()

    def _save_config(self, silent=False):
        """保存配置

        Args:
            silent: 是否静默保存(不显示成功消息框)
        """

        config.lang = self.lang_combo.currentData()

        # 验证OBS主机名
        if not self.obs_host_input.text().strip():
            if not silent:
                QMessageBox.warning(self, self.tr("Warning"), self.tr("OBS host cannot be empty"))
            return

        old_host = config.host
        old_port = config.port

        config.host = self.obs_host_input.text().strip()
        config.port = self.obs_port_spin.value()

        config.extra_seconds_ranked = self.extra_seconds_ranked_spin.value()
        config.extra_seconds_rsg = self.extra_seconds_rsg_spin.value()
        config.wait_for_datapack = self.wait_seed_spin.value()
        config.death_clip_duration = self.death_clip_duration_spin.value()
        config.death_clip_ahead_seconds = self.death_clip_ahead_spin.value()
        config.auto_start = self.auto_start_checkbox.isChecked()
        config.use_cover = self.use_cover_checkbox.isChecked()
        config.use_description = self.use_description_checkbox.isChecked()
        config.use_upload = self.use_upload_checkbox.isChecked()
        config.use_rsg_pb = self.use_rsg_pb_checkbox.isChecked()

        if config.host != old_host or config.port != old_port:
            if auto_clip.obs_controller is not None:
                auto_clip.obs_controller.stop()
                auto_clip.obs_controller = None

        config.save()

        # 重置未保存标记
        self._has_unsaved_changes = False

        if not silent:
            QMessageBox.information(self, self.tr("Success"), self.tr("The Configuration has been saved"))