class PlayerNotFoundException(Exception):
    def __init__(self, nickname):
        self.nickname = nickname
        super().__init__(f"未找到玩家： {self.nickname} ")

class RankedAPIUnavailableError(Exception):
    def __init__(self, url: str, original: Exception | None = None):
        super().__init__(f"Ranked API 请求失败: {url}")
        self.url = url
        self.original = original

class PacemanAPIUnavailableError(Exception):
    def __init__(self, url: str, original: Exception | None = None):
        super().__init__(f"Paceman API 请求失败: {url}")
        self.url = url
        self.original = original

class OBSConnectionException(Exception):
    def __init__(self):
        super().__init__(f"OBS websocket连接失败！请检查主机名和端口号是否配置正确！")

class OBSReplayNotEnableError(Exception):
    def __init__(self):
        super().__init__(f'OBS回放缓存未启用！')

class BiliupNotConfiguredException(Exception):
    def __init__(self):
        super().__init__(f"未找到biliup，请确保已安装biliup并将biliup添加到系统环境变量！")

class BiliupLogInError(Exception):
    def __init__(self, returncode, stderr):
        super().__init__(f"biliup登录失败！退出码: {returncode}, stderr：{stderr}")

class BiliupUploadError(Exception):
    def __init__(self, returncode, stderr):
        super().__init__(f"biliup视频上传失败！退出码: {returncode}, stderr：{stderr}")

class FfmpegNotConfiguredException(Exception):
    def __init__(self):
        super().__init__(f"未找到ffmpeg/ffprobe，请确保已安装FFmpeg并将ffmpeg/ffprobe添加到系统环境变量！"
                                   "（https://github.com/BtbN/FFmpeg-Builds/releases）")

