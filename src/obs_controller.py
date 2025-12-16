from datetime import datetime,timedelta
import time
from pathlib import Path
import obswebsocket
from config import config
import threading

from logger import setup_logger

logger = setup_logger(__name__)

class OBSController:
    def __init__(self, host:str , port:int):
        self._host = host
        self._port = port

        self._ws = obswebsocket.obsws(host, port)

        self._replay_video_list: list[Path] = []
        self._lock = threading.Lock()
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

        logger.info("OBSController检查通过！")

    @staticmethod
    def is_file_recent(file_path: Path):
        try:
            file_name = file_path.stem
            if not (file_name.startswith(config.replay_prefix) and file_name.endswith(config.replay_suffix)):
                return False
            date_time_str = file_name[len(config.replay_prefix):]
            if len(config.replay_suffix) != 0:
                date_time_str = date_time_str[:-len(config.replay_suffix)]
            file_time = datetime.strptime(date_time_str, config.filename_formatting)
            current_time = datetime.now()
            return current_time - file_time <= timedelta(seconds=config.replay_threshold_seconds)
        except (IndexError, ValueError):
            # 如果文件名格式错误，返回 False
            return False

    def replay_save(self) -> Path:
        with self._lock:
            if self._replay_video_list and self.is_file_recent(self._replay_video_list[-1]):
                return self._replay_video_list[-1]
        self._ws.call(obswebsocket.requests.SaveReplayBuffer())
        while 1:
            time.sleep(1)
            last_replay_buffer = self._ws.call(obswebsocket.requests.GetLastReplayBufferReplay())
            video_path: str = last_replay_buffer.datain["savedReplayPath"]
            if self.is_file_recent(Path(video_path)):
                logger.info(f"回放已经保存到{video_path}")
                with self._lock:
                    self._replay_video_list.append(Path(video_path))
                return Path(video_path)

    def clean(self):
        with self._lock:
            for replay_file in self._replay_video_list.copy():
                if not self.is_file_recent(replay_file):
                    replay_file.unlink()
                    self._replay_video_list.remove(replay_file)
                    logger.info(f"原始文件：{replay_file} 已删除")


    def check_replay_status(self) -> None:
        replay_status = self._ws.call(obswebsocket.requests.GetReplayBufferStatus())

        if replay_status.datain.get("outputActive") is None:
            raise Exception("OBS回放缓存未启用！")

        if not replay_status.datain["outputActive"]:
            logger.info("回放缓存未开启，尝试启动...")
            self._ws.call(obswebsocket.requests.StartReplayBuffer())
            logger.info("回放缓存已启动！")

obs_controller = OBSController(config.host, config.port)
if __name__ == "__main__":
    pass