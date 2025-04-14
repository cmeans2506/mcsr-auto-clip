import os
from datetime import datetime,timedelta
import time
from pathlib import Path
import obswebsocket
from config import config


class OBSController:
    def __init__(self, host:str , port:int):
        self._host = host
        self._port = port

        self._ws = obswebsocket.obsws(host, port)
        try:
            self._ws.connect()
        except Exception as e:
            print("OBS websocket连接失败！请检查主机名和端口号是否配置正确！")
            input(e.args[0])
            exit()

        try:
            self.check_replay_status()
        except Exception as e:
            input(e.args[0])
            exit()

        print("OBSController检查通过！")

    def replay_save(self) -> Path:
        self._ws.call(obswebsocket.requests.SaveReplayBuffer())

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
                return current_time - file_time <= timedelta(seconds=30)
            except (IndexError, ValueError):
                # 如果文件名格式错误，返回 False
                return False

        while 1:
            time.sleep(1)
            last_replay_buffer = self._ws.call(obswebsocket.requests.GetLastReplayBufferReplay())
            video_path: str = last_replay_buffer.datain["savedReplayPath"]
            if is_file_recent(Path(video_path)):
                print(f"回放已经保存到{video_path}")
                return Path(video_path)

    def check_replay_status(self) -> None:
        replay_status = self._ws.call(obswebsocket.requests.GetReplayBufferStatus())

        if replay_status.datain.get("outputActive") is None:
            raise Exception("OBS回放缓存未启用！")

        if not replay_status.datain["outputActive"]:
            print("回放缓存未开启，尝试启动...")
            self._ws.call(obswebsocket.requests.StartReplayBuffer())
            print("回放缓存已启动！")

obs_controller = OBSController(config.host, config.port)
if __name__ == "__main__":
    pass