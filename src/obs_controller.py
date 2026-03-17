from pathlib import Path
from typing import Callable, Optional
import obswebsocket
import threading
import logging

from my_exceptions import OBSConnectionException, OBSReplayNotEnableError
from logger import setup_logger

logger = setup_logger(__name__)

setup_logger('obswebsocket', logging.WARNING)

class OBSController:
    def __init__(self, host: str, port: int, on_disconnect: Callable[[obswebsocket.obsws], None]):
        self._host = host
        self._port = port

        self._ws = obswebsocket.obsws(host, port, on_disconnect=on_disconnect)

        self.replay_path: Path = Path()
        self.replay_buffer_saved_event = threading.Event()

        # self.start()

        self._ws.register(self.on_replay_saved, obswebsocket.events.ReplayBufferSaved)


    def start(self):
        try:
            logger.info("Attempting to connect to OBS...")
            self._ws.connect()
        except Exception as e:
            raise OBSConnectionException()

        logger.info("Connected to OBS successfully!")
        self.check_replay_status()


    def stop(self):
        if self._ws.ws:
            self._ws.disconnect()


    def on_replay_saved(self, message):
        # 'message' contains the raw event data returned by OBS
        self.replay_path = Path(message.getSavedReplayPath())
        self.replay_buffer_saved_event.set()


    # no race conditions guaranteed.
    def save_replay(self, timeout=30) -> Optional[Path]:
        self.replay_buffer_saved_event.clear()
        self._ws.call(obswebsocket.requests.SaveReplayBuffer())

        # Wait for the ReplayBufferSaved event to trigger
        if not self.replay_buffer_saved_event.wait(timeout):
            logger.warning("Timed out waiting for replay buffer to save.")
            return None
        logger.info(f"Replay saved to: {self.replay_path}")
        return self.replay_path

        # # 注销事件监听
        # self._ws.unregister(self.on_replay_saved, obswebsocket.events.ReplayBufferSaved)


    def check_replay_status(self) -> None:
        replay_status = self._ws.call(obswebsocket.requests.GetReplayBufferStatus())

        if replay_status.datain.get("outputActive") is None:
            raise OBSReplayNotEnableError()

        if not replay_status.datain["outputActive"]:
            logger.info("Replay Buffer is not active. Attempting to start...")
            self._ws.call(obswebsocket.requests.StartReplayBuffer())
            logger.info("Replay Buffer started successfully!")

if __name__ == "__main__":
    pass