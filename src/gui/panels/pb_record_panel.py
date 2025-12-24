from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
                             QLabel, QPushButton, QLineEdit, QGroupBox,
                             QTimeEdit, QDateEdit, QSpinBox, QMessageBox)
from PyQt6.QtCore import QTime, QDate
from auto_clip import auto_clip
from datetime import datetime
from logger import setup_logger

logger = setup_logger(__name__)

class PBRecordPanel(QWidget):
    """RSG PB设置标签页"""

    # PB类型配置
    PB_TYPES = [
        {
            "key": "rsg.first_portal",
            "title": "盲传",
            "grid_pos": (0, 0)
        },
        {
            "key": "rsg.enter_stronghold",
            "title": "隔墙有眼",
            "grid_pos": (0, 1)
        },
        {
            "key": "rsg.enter_end",
            "title": "进入末地",
            "grid_pos": (1, 0)
        },
        {
            "key": "rsg.credits",
            "title": "结束",
            "grid_pos": (1, 1)
        }
    ]

    # 默认配置
    DEFAULT_CONFIG = {
        "rsg.first_portal": {
            "id": 0,
            "igt": 0,
            "bvid": "",
            "time": 0
        },
        "rsg.enter_stronghold": {
            "id": 0,
            "igt": 0,
            "bvid": "",
            "time": 0
        },
        "rsg.enter_end": {
            "id": 0,
            "igt": 0,
            "bvid": "",
            "time": 0
        },
        "rsg.credits": {
            "id": 0,
            "igt": 0,
            "bvid": "",
            "time": 0
        }
    }

    # 界面文本常量
    LABEL_DATE = "打出日期"
    LABEL_IGT = "游戏内时间(IGT)"
    LABEL_BVID = "B站视频BV号"
    BTN_SAVE = "保存"
    BTN_RESET = "恢复默认"

    def __init__(self):
        super().__init__()
        # 存储所有PB记录的控件
        self.pb_widgets = {}
        self._init_ui()
        # 初始化时加载数据
        self._load_from_rsg_pb()

    def _init_ui(self):
        """初始化用户界面"""
        layout = QVBoxLayout()

        # 创建2x2网格布局
        grid_layout = QGridLayout()

        # 动态创建所有PB组
        for pb_type in self.PB_TYPES:
            row, col = pb_type["grid_pos"]
            group = self._create_pb_group(pb_type)
            grid_layout.addWidget(group, row, col)

        layout.addLayout(grid_layout)

        # 操作按钮
        layout.addWidget(self._create_action_buttons())

        self.setLayout(layout)

    def _create_pb_group(self, pb_type):
        """创建单个PB记录组"""
        key = pb_type["key"]
        title = pb_type["title"]

        group = QGroupBox(title)
        layout = QVBoxLayout()

        # 打出日期
        layout.addWidget(QLabel(self.LABEL_DATE))
        date_edit = QDateEdit()
        date_edit.setDisplayFormat("yyyy-MM-dd")
        date_edit.setCalendarPopup(True)
        date_edit.setDate(QDate.currentDate())
        layout.addWidget(date_edit)

        # IGT时间(分:秒.毫秒)
        layout.addWidget(QLabel(self.LABEL_IGT))
        time_layout, time_edit, ms_spin = self._create_time_input()
        layout.addLayout(time_layout)

        # BV号
        layout.addWidget(QLabel(self.LABEL_BVID))
        bvid_input = QLineEdit()
        bvid_input.setPlaceholderText("如: BV1TdNRzwEfX")
        layout.addWidget(bvid_input)

        group.setLayout(layout)

        # 存储控件引用
        self.pb_widgets[key] = {
            "date_edit": date_edit,
            "time_edit": time_edit,
            "ms_spin": ms_spin,
            "bvid_input": bvid_input
        }

        return group

    def _create_time_input(self):
        """创建时间输入控件(分:秒.毫秒)"""
        layout = QHBoxLayout()

        # 时间编辑器(分:秒)
        time_edit = QTimeEdit()
        time_edit.setDisplayFormat("mm:ss")
        time_edit.setTime(QTime(0, 0, 0))
        time_edit.setMinimumTime(QTime(0, 0, 0))
        time_edit.setMaximumTime(QTime(0, 59, 59))
        layout.addWidget(time_edit)

        # 点号
        layout.addWidget(QLabel("."))

        # 毫秒输入框
        ms_spin = QSpinBox()
        ms_spin.setRange(0, 999)
        ms_spin.setValue(0)
        ms_spin.setSingleStep(1)
        layout.addWidget(ms_spin)

        return layout, time_edit, ms_spin

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

    def _load_from_rsg_pb(self):
        """从rsg_pb.pb_info加载数据到界面"""
        for key, widgets in self.pb_widgets.items():
            if key not in auto_clip.rsg_pb.pb_info:
                continue

            record = auto_clip.rsg_pb.pb_info[key]

            # 加载日期(从unix时间戳)
            timestamp = record.time
            if timestamp > 0:
                date = datetime.fromtimestamp(timestamp)
                widgets["date_edit"].setDate(date)
            else:
                widgets["date_edit"].setDate(QDate.currentDate())

            # 加载IGT时间
            igt = record.igt
            minutes, seconds, ms = self._ms_to_time(igt)
            widgets["time_edit"].setTime(QTime(0, minutes, seconds))
            widgets["ms_spin"].setValue(ms)

            # 加载BV号
            bvid = record.bvid
            widgets["bvid_input"].setText(bvid)

    def _on_reset(self):
        """处理恢复默认设置事件"""
        reply = QMessageBox.question(
            self,
            "确认",
            "确定要清空所有PB记录吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self._reset_to_defaults()
            QMessageBox.information(self, "成功", "已清空所有PB记录")
            logger.info(f"已清空所有PB记录")

    def _reset_to_defaults(self):
        """重置所有PB记录为默认值"""
        for key, widgets in self.pb_widgets.items():
            # 重置日期为当前日期
            widgets["date_edit"].setDate(QDate.currentDate())

            # 重置IGT为0
            widgets["time_edit"].setTime(QTime(0, 0, 0))
            widgets["ms_spin"].setValue(0)

            # 清空BV号
            widgets["bvid_input"].clear()

    def _on_save(self):
        """处理保存事件"""
        # 验证配置
        valid, errors = self.validate_config()
        if not valid:
            error_msg = "\n".join(errors)
            QMessageBox.warning(self, "验证失败", error_msg)
            logger.warning(f"验证失败: \n{error_msg}")
            return

        # 保存到rsg_pb.pb_info
        self._save_to_rsg_pb()
        QMessageBox.information(self, "成功", "PB记录已保存")
        logger.info(f"rsg_pb已成功保存")

    def _save_to_rsg_pb(self):
        """保存界面数据到rsg_pb.pb_info"""
        for key, widgets in self.pb_widgets.items():
            # 获取日期(转为unix时间戳)
            date = widgets["date_edit"].date()
            timestamp = int(date.startOfDay().toSecsSinceEpoch())

            # 获取IGT时间(转为毫秒)
            igt = self._time_to_ms(widgets["time_edit"], widgets["ms_spin"])

            # 获取BV号
            bvid = widgets["bvid_input"].text().strip()

            # 保存到rsg_pb.pb_info
            # 保持原有的id,如果不存在则为0
            current_id = 0
            if key in auto_clip.rsg_pb.pb_info:
                current_id = auto_clip.rsg_pb.pb_info[key].id

            auto_clip.rsg_pb.pb_info[key] = {
                "id": current_id,
                "igt": igt,
                "bvid": bvid,
                "time": timestamp
            }

        # 调用rsg_pb的保存方法(如果有)

        auto_clip.rsg_pb.write_back()

    def _time_to_ms(self, time_edit, ms_spin):
        """将时间转换为毫秒"""
        time = time_edit.time()
        total_ms = time.minute() * 60 * 1000
        total_ms += time.second() * 1000
        total_ms += ms_spin.value()
        return total_ms


    def _ms_to_time(self, milliseconds):
        """将毫秒转换为(分, 秒, 毫秒)"""
        total_seconds = milliseconds // 1000
        ms = milliseconds % 1000
        minutes = total_seconds // 60
        seconds = total_seconds % 60
        return (minutes, seconds, ms)


    def validate_config(self):
        """验证配置是否有效"""
        errors = []

        for pb_config in self.PB_TYPES:
            key = pb_config["key"]
            title = pb_config["title"]
            widgets = self.pb_widgets[key]

            bvid = widgets["bvid_input"].text().strip()
            igt = self._time_to_ms(widgets["time_edit"], widgets["ms_spin"])

            # 如果填写了BV号但IGT为0，报错
            if igt == 0:
                errors.append(f"{title}: IGT时间为0")

            # 验证BV号格式(如果填写了)
            if bvid and not bvid.startswith("BV"):
                errors.append(f"{title}: BV号格式错误，应以'BV'开头")

        return len(errors) == 0, errors
