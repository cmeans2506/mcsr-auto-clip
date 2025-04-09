# MCSR AUTO CLIP

本项目基于 Python 开发，整合 OBS websocket、biliup 和 FFmpeg，实现 Minecraft Speedrun（MCSR）视频的自动切片、封面生成及上传功能。


## 快速开始

### 1. 安装依赖组件
#### ① FFmpeg 安装
- 下载 [FFmpeg](https://github.com/BtbN/FFmpeg-Builds/releases) 选择 `ffmpeg-master-latest-win64-gpl.zip`

- 将 `ffmpeg.exe` 加入系统环境变量

#### ② OBS 配置
1. OBS 中开启WebSocket服务器
   ```
   OBS菜单栏 -> 工具 -> WebSocket服务器设置 -> 启用，身份验证关闭
   ```
2. 启用回放缓存：
   ```
   OBS控制按钮 -> 设置 -> 输出 -> 回放缓存 -> 启用，回放时长上限1200秒（建议）
   ```
3. 记录 websocket 连接信息（默认：`localhost:4455`）

#### ③ biliup 部署
- 下载 [biliup](https://github.com/ForgQi/biliup-rs) 到工作目录（参考下文配置说明）
- 登录哔哩哔哩账号

#### ④chromium 部署
- 下载 [chromium](https://www.googleapis.com/download/storage/v1/b/chromium-browser-snapshots/o/Win_x64%2F1135619%2Fchrome-win.zip?generation=1682469079864558&alt=media)
- 修改配置文件路径（参考下文配置说明）


### 2. 配置文件说明
 `./config/config.json` 文件：

```json
{
  "player": {
    "name": "Cmeans",
    "uuid": "3affdb407396456abcca42dbeb102331"
  },
  "clip_setting": {
    "RANKED_MATCH": {
      "max_time": 720000,
      "seed_type": ["BURIED_TREASURE", "SHIPWRECK", "VILLAGE", "DESERT_TEMPLE", "RUINED_PORTAL"],
      "bastion_type": ["BRIDGE", "STABLES", "HOUSING", "TREASURE"]
    }
    // 其他模式配置...
  },
  "upload_setting": {
    // 上传配置...
  },
  "base_dir": "D:/视频",
  "host": "localhost",
  "port": 4455,
  "browser_executable": "D:/Software/chrome-win/chrome.exe",
  "use_cover": true
}
```

#### 配置字段说明
| 字段 | 类型 | 说明 |
|------|------|------|
| `player` | Object | 玩家信息 |
| `player.name` | String | Minecraft 游戏昵称 |
| `player.uuid` | String | 玩家 UUID |
| `clip_setting` | Object | 视频切片规则 |
| `max_time` | Number | 最大允许时长（毫秒） |
| `seed_type` | Array | 有效主世界类型白名单 |
| `bastion_type` | Array | 有效猪堡类型白名单 |
| `base_dir` | String | 工作目录路径 |
| `host` | String | OBS websocket 主机地址 |
| `port` | Number | OBS websocket 端口 |
| `browser_executable` | String | Chromium 浏览器路径 |
| `use_cover` | Boolean | 是否生成视频封面 |

### 3. 目录结构
```
工作目录/
├── biliup.exe         # 上传工具
├── mcsr/              # 视频存储
│   └── YYYYMMDD/      # 按日期分类
│       ├── video.mp4  
│       └── cover.jpg  
├── up_history.json    # 上传记录
└── config.json        # 配置文件
```

## 功能特性
- **智能切片**：根据比赛时长自动切片和裁剪视频
- **封面生成**：利用 Chromium 自动生成视频封面
- **视频上传**：利用 biliup 自动上传视频
- **历史记录**：`up_history.json` 记录上传信息


## 注意事项
1. 确保 OBS 回放缓存时间 > 最大切片时长(一般20分钟足矣)
2. 首次使用需通过 biliup 登录 B 站账号
3. 不同比赛模式的配置参数需单独设置

