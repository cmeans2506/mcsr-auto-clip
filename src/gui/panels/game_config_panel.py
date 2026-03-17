from pathlib import Path
from typing import Callable, Any

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
                             QLineEdit, QFileDialog, QCheckBox, QMessageBox)
from PyQt6.QtCore import Qt, QTime, QDate, QObject, pyqtSignal, QThread, QTimer
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

    def __init__(self):
        super().__init__()
        self.folder_path = config.base_dir.as_posix()
        self._has_unsaved_changes = False
        self._init_ui()
        self._connect_change_signals()

    def _init_ui(self):
        """初始化用户界面"""
        main_layout = QVBoxLayout()

        # 游戏名称输入区域
        main_layout.addWidget(QLabel(self.tr("Minecraft Nickname: ")))
        self.nickname_input = QLineEdit()
        self.nickname_input.setPlaceholderText(self.tr("Please enter your minecraft nickname..."))
        self.nickname_input.setText(config.player.name)
        main_layout.addWidget(self.nickname_input)

        # 文件夹路径显示
        self.path_label = QLabel(self._get_folder_label_text())
        self.path_label.setWordWrap(True)
        main_layout.addWidget(self.path_label)

        # 文件夹操作按钮
        main_layout.addLayout(self._create_folder_buttons())

        main_layout.addStretch(1)

        # 处理选项复选框
        main_layout.addLayout(self._create_process_options())

        # 开始/停止按钮
        main_layout.addLayout(self._create_control_buttons())

        main_layout.addStretch(1)

        self.setLayout(main_layout)


    def _connect_change_signals(self):
        """连接所有输入控件的变化信号"""
        # 昵称输入
        self.nickname_input.textChanged.connect(self._mark_unsaved)

        # 处理选项复选框
        self.ranked_checkbox.stateChanged.connect(self._mark_unsaved)
        self.rsg_checkbox.stateChanged.connect(self._mark_unsaved)
        self.death_clip_checkbox.stateChanged.connect(self._mark_unsaved)
        self.obs_clean_checkbox.stateChanged.connect(self._mark_unsaved)


    def _mark_unsaved(self):
        """标记有未保存的更改"""
        self._has_unsaved_changes = True


    def _create_folder_buttons(self):
        """创建文件夹操作按钮"""
        layout = QHBoxLayout()

        self.open_folder_btn = QPushButton(self.tr("Open Folder"))
        self.open_folder_btn.clicked.connect(self._on_open_folder)

        self.select_folder_btn = QPushButton(self.tr("Select Folder"))
        self.select_folder_btn.clicked.connect(self._on_select_folder)

        layout.addWidget(self.open_folder_btn)
        layout.addWidget(self.select_folder_btn)

        return layout

    def _create_process_options(self):
        """创建处理选项复选框"""
        layout = QHBoxLayout()

        self.ranked_checkbox = QCheckBox(self.tr("RANKED"))
        self.ranked_checkbox.setChecked(config.ranked_job)
        self.rsg_checkbox = QCheckBox(self.tr("RSG"))
        self.rsg_checkbox.setChecked(config.rsg_job)
        self.death_clip_checkbox = QCheckBox(self.tr("Death Clip"))
        self.death_clip_checkbox.setChecked(config.use_death_clip)
        self.obs_clean_checkbox = QCheckBox(self.tr("Clean Raw File"))
        self.obs_clean_checkbox.setChecked(config.clean_raw_file)

        layout.addWidget(self.ranked_checkbox)
        layout.addWidget(self.rsg_checkbox)
        layout.addWidget(self.death_clip_checkbox)
        layout.addWidget(self.obs_clean_checkbox)

        return layout

    def _create_control_buttons(self):
        """创建开始/停止控制按钮"""
        layout = QHBoxLayout()

        self.start_btn = QPushButton(self.tr("Start"))
        self.start_btn.clicked.connect(self._on_start)

        self.stop_btn = QPushButton(self.tr("Stop"))
        self.stop_btn.clicked.connect(self._on_stop)

        layout.addWidget(self.start_btn)
        layout.addWidget(self.stop_btn)

        return layout

    def _get_folder_label_text(self):
        """获取文件夹标签文本"""
        return f'{self.tr("Video Folder")}: {self.folder_path or self.tr("None")}'

    def _update_folder_label(self):
        """更新文件夹路径显示"""
        self.path_label.setText(self._get_folder_label_text())

    def _on_select_folder(self):
        """处理选择文件夹事件"""
        folder_path = QFileDialog.getExistingDirectory(
            self,
            self.tr("Select Folder"),
            "",
            QFileDialog.Option.ShowDirsOnly
        )

        if not folder_path:
            return

        self.folder_path = folder_path
        logger.info(f'Selected video folder: {folder_path}')

        self._update_folder_label()

        # 文件夹路径改变，标记为未保存
        self._mark_unsaved()

    def _on_open_folder(self):
        """处理打开文件夹事件"""
        if not self.folder_path or not os.path.isdir(self.folder_path):
            QMessageBox.warning(self, self.tr("Warning"), self.tr("Please select a valid folder."))
            return

        try:
            os.startfile(self.folder_path)
        except Exception as e:
            QMessageBox.critical(self, self.tr("Error"), self.tr("Failed to open the folder."))

    def _on_save(self):
        """处理保存事件（手动保存）"""
        self._save_config(silent=False)

    def _save_config(self, silent=False):
        """保存配置

        Args:
            silent: 是否静默保存(不显示成功消息框)
        """
        nickname = self.nickname_input.text().strip()

        if not nickname:
            if not silent:
                QMessageBox.warning(self, self.tr("Warning"), self.tr("Please enter a valid nickname."))
            return

        if not self.folder_path or not os.path.isdir(self.folder_path):
            if not silent:
                QMessageBox.warning(self, self.tr("Warning"), self.tr("Please select a valid folder."))
            return

        # 保存配置
        config.player.name = nickname
        config.base_dir = Path(self.folder_path)
        config.ranked_job = self.ranked_checkbox.isChecked()
        config.rsg_job = self.rsg_checkbox.isChecked()
        config.use_death_clip = self.death_clip_checkbox.isChecked()
        config.clean_raw_file = self.obs_clean_checkbox.isChecked()

        config.save()

        # 重置未保存标记
        self._has_unsaved_changes = False

    def _on_start(self):
        if hasattr(self, "_start_worker") and self._start_worker.isRunning() or auto_clip.is_running:
            QMessageBox.warning(self, self.tr("Failed to start"), self.tr("mcsr auto clip is running"))
            return

        def _on_start_success():
            QMessageBox.information(self, self.tr("Started successfully"), self.tr("mcsr auto clip is running"))

        def _on_start_error(detail):
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Icon.Critical)
            msg.setWindowTitle(self.tr("Failed to start"))
            msg.setText(f'{self.tr("Errors during launching")}: \n{detail}')
            msg.exec()

        self._on_save()
        self._start_worker = Worker(auto_clip.start)
        self._start_worker.success.connect(_on_start_success)
        self._start_worker.error.connect(_on_start_error)
        self._start_worker.start()

    def _on_stop(self):
        if (hasattr(self, "_stop_worker") and self._stop_worker.isRunning()) or not auto_clip.is_running:
            QMessageBox.warning(self, self.tr("Failed to stop"), self.tr("mcsr auto clip has been stopped"))
            return

        def _on_stop_success():
            QMessageBox.information(self, self.tr("Stopped successfully"), self.tr("mcsr auto clip has been stopped"))

        def _on_stop_error(detail):
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Icon.Critical)
            msg.setWindowTitle(self.tr("Failed to stop"))
            msg.setText(f'{self.tr("Errors during stopping")}: \n{detail}')
            msg.exec()

        self._stop_worker = Worker(auto_clip.stop)
        self._stop_worker.success.connect(_on_stop_success)
        self._stop_worker.error.connect(_on_stop_error)
        self._stop_worker.start()