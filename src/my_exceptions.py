from PyQt6.QtCore import QCoreApplication


class PlayerNotFoundException(Exception):
    def __init__(self, nickname):
        self.nickname = nickname
        super().__init__(QCoreApplication.translate("PlayerNotFoundException", f"Player not found: {self.nickname}"))

class RankedAPIUnavailableError(Exception):
    def __init__(self, url: str, original: Exception | None = None):
        super().__init__(QCoreApplication.translate("RankedAPIUnavailableError", f"Ranked API request failed: {url}"))
        self.url = url
        self.original = original

class PacemanAPIUnavailableError(Exception):
    def __init__(self, url: str, original: Exception | None = None):
        super().__init__(QCoreApplication.translate("PacemanAPIUnavailableError", f"Paceman API request failed: {url}"))
        self.url = url
        self.original = original

class OBSConnectionException(Exception):
    def __init__(self):
        super().__init__(QCoreApplication.translate("OBSConnectionException", "OBS WebSocket connection failed! Please check if the hostname and port are configured correctly."))

class OBSReplayNotEnableError(Exception):
    def __init__(self):
        super().__init__(QCoreApplication.translate("OBSReplayNotEnableError", "OBS Replay Buffer is not enabled!"))

class BiliupNotConfiguredException(Exception):
    def __init__(self):
        super().__init__(QCoreApplication.translate("BiliupNotConfiguredException", "biliup not found. Please ensure biliup is installed."))

class BiliupLogInError(Exception):
    def __init__(self, returncode, stderr):
        super().__init__(QCoreApplication.translate("BiliupLogInError", f"biliup login failed! Exit code: {returncode}, stderr: {stderr}"))

class BiliupUploadError(Exception):
    def __init__(self, returncode, stderr):
        super().__init__(QCoreApplication.translate("BiliupUploadError", f"biliup video upload failed! Exit code: {returncode}, stderr: {stderr}"))

class FfmpegNotConfiguredException(Exception):
    def __init__(self):
        super().__init__(QCoreApplication.translate("FfmpegNotConfiguredException", "ffmpeg/ffprobe not found. Please ensure FFmpeg is installed."
                         "(Download: https://github.com/BtbN/FFmpeg-Builds/releases)"))

