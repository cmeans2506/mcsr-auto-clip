from dataclasses import dataclass
from datetime import datetime,timedelta
import time
from pathlib import Path
from typing import Callable, Optional
import obswebsocket
from config import config
import threading
import logging
from logger import setup_logger

logger = setup_logger(__name__)

setup_logger('obswebsocket', logging.WARNING)

class OBSController:

    @dataclass(slots=True)
    class ReplayItem:
        path: Path
        timestamp: float

        def is_expired(self) -> bool:
            return time.time() - self.timestamp > config.replay_threshold_seconds

    def __init__(self, host: str, port: int, on_disconnect: Callable[[obswebsocket.obsws], None]):
        self._host = host
        self._port = port

        self._ws = obswebsocket.obsws(host, port, on_disconnect=on_disconnect)

        self._replay_video_list: list[OBSController.ReplayItem] = []
        self._lock = threading.Lock()

        self.replay_path: Path = Path()
        self.replay_buffer_saved_event = threading.Event()

        try:
            self._ws.connect()
        except Exception as e:
            logger.warning("OBS websocket连接失败！请检查主机名和端口号是否配置正确！")
            logger.warning(e.args[0])
            input()
            exit()

        try:
            self.check_replay_status()
        except Exception as e:
            logger.warning(e.args[0])
            input()
            exit()

        self._ws.register(self.on_replay_saved, obswebsocket.events.ReplayBufferSaved)

        logger.info("OBSController检查通过！")


    def on_replay_saved(self, message):
        # message 是 OBS 返回的原始事件数据
        self.replay_path = Path(message.getSavedReplayPath())
        self.replay_buffer_saved_event.set()


    def save_replay(self, timeout=30) -> Optional[Path]:
        with self._lock:
            if self._replay_video_list:
                latest_item = self._replay_video_list[-1]
                if not latest_item.is_expired():
                    return latest_item.path
        self.replay_buffer_saved_event.clear()
        self._ws.call(obswebsocket.requests.SaveReplayBuffer())
        # 等待事件触发
        if self.replay_buffer_saved_event.wait(timeout):
            logger.info(f"回放已保存到: {self.replay_path}")
            with self._lock:
                self._replay_video_list.append(OBSController.ReplayItem(self.replay_path, time.time()))
            return self.replay_path
        else:
            logger.warning("等待回放保存超时")
            return None

        # # 注销事件监听
        # self._ws.unregister(self.on_replay_saved, obswebsocket.events.ReplayBufferSaved)

    def clean(self):
        with self._lock:
            for replay_item in self._replay_video_list.copy():
                if replay_item.is_expired():
                    replay_item.path.unlink()
                    self._replay_video_list.remove(replay_item)
                    logger.info(f"原始文件：{replay_item.path} 已删除")


    def check_replay_status(self) -> None:
        replay_status = self._ws.call(obswebsocket.requests.GetReplayBufferStatus())

        if replay_status.datain.get("outputActive") is None:
            raise Exception("OBS回放缓存未启用！")

        if not replay_status.datain["outputActive"]:
            logger.info("回放缓存未开启，尝试启动...")
            self._ws.call(obswebsocket.requests.StartReplayBuffer())
            logger.info("回放缓存已启动！")

if __name__ == "__main__":
    pass