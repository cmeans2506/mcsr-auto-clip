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

#### ⑤安装python包
- 在`./src` 文件夹下，运行 `pip install -r requirements.txt`

#### ⑥运行
- 运行 `python ./src/main.py`

### 2. 配置文件说明
 `./config/config.json` 文件：

```json
{
  "player": {
    "name": "Cmeans",
    "uuid": "3affdb407396456abcca42dbeb102331"
  },
  "clip_setting": {
    "ranked": {
      "RANKED_MATCH": {
        "max_time": 720000,
        "seed_type": ["BURIED_TREASURE", "SHIPWRECK", "VILLAGE", "DESERT_TEMPLE", "RUINED_PORTAL"],
        "bastion_type": ["BRIDGE", "STABLES", "HOUSING", "TREASURE"]
      }
       // 其他模式配置...
    },
    "rsg": {
      "rsg.enter_nether": 0,
      "rsg.enter_bastion": 0,
      "rsg.enter_fortress": 0,
      "rsg.first_portal": 540000,
      "rsg.enter_stronghold": 660000,
      "rsg.enter_end": 720000,
      "rsg.credits": 900000
    }
  },
  "upload_setting": {
    // 上传配置同上...
  },
  "base_dir": "D:/视频",

  "host": "localhost",
  "port": 4455,

  "browser_executable": "D:/Software/chrome-win/chrome.exe",
  "use_cover": true,
  "extra_seconds": 15,
  "replay_prefix": "Replay ",
  "replay_suffix": "",
  "output_format": "mp4",
  "filename_formatting": "%Y-%m-%d %H-%M-%S",

  "replay_threshold_seconds": 20,
  "clean_raw_file": true,
  "use_death_clip": true,
  "death_clip_duration": 25,
  "death_clip_ahead_seconds": 0,

  "use_messagebox": true
}
```

#### 配置字段说明
| 字段                               | 类型      | 说明                                                                       |
|----------------------------------|---------|--------------------------------------------------------------------------|
| `player`                         | Object  | 玩家信息                                                                     |
| `player.name`                    | String  | Minecraft 游戏昵称                                                           |
| `player.uuid`                    | String  | 玩家 UUID(不要带'-')，可以从这里查：<br/>https://mcsrranked.com/api/users/{your_name} |
| `clip_setting`                   | Object  | 视频切片规则                                                                   |
| `upload_setting`                 | Object  | 视频上传规则                                                                   |
| `ranked.MATCH_TYPE.max_time`     | Number  | 最大允许时长（毫秒）                                                               |
| `ranked.MATCH_TYPE.seed_type`    | Array   | 有效主世界类型白名单                                                               |
| `ranked.MATCH_TYPE.bastion_type` | Array   | 有效猪堡类型白名单                                                                |
| `rsg.rsg.enter_nether`           | Number  | rsg进地狱最大允许时长（毫秒）                                                         |
| `rsg.rsg.enter_bastion`          | Number  | rsg进猪堡最大允许时长（毫秒）                                                         |
| `rsg.rsg.enter_fortress`         | Number  | rsg阴森的要塞最大允许时长（毫秒）                                                       |
| `rsg.rsg.first_portal`           | Number  | rsg盲传最大允许时长（毫秒）                                                          |
| `rsg.rsg.enter_stronghold`       | Number  | rsg隔墙有眼最大允许时长（毫秒）                                                        |
| `rsg.rsg.enter_end`              | Number  | rsg进末地最大允许时长（毫秒）                                                         |
| `rsg.rsg.credits`                | Number  | rsg结束最大允许时长（毫秒）                                                          |
| `base_dir`                       | String  | 工作目录路径                                                                   |
| `host`                           | String  | OBS websocket 主机地址                                                       |
| `port`                           | Number  | OBS websocket 端口                                                         |
| `browser_executable`             | String  | Chromium 浏览器路径，注意用正斜杠'/'，而不是反斜杠'\\'                                      |
| `use_cover`                      | Boolean | 是否生成视频封面                                                                 |
| `extra_seconds`                  | Number  | 视频是从末尾开始剪辑的，剪辑时长为 `RTA + extra_seconds`<br/>默认值为15，如果剪漏了可以适当调大           |
| `replay_prefix`                  | String  | 回放文件名前缀，在OBS设置-录制-高级中可以修改                                                |
| `replay_suffix`                  | String  | 回放文件名后缀，在OBS设置-录制-高级中可以修改                                                |
| `filename_formatting`            | String  | 文件名格式，在OBS设置-录制-高级中可以修改                                                  |
| `output_format`                  | String  | 剪辑后的视频格式，请与录像格式保持一致，否则剪辑时可能出现问题，在OBS设置-输出-录制-录像格式中可以修改                   |
| `replay_threshold_seconds`       | Number  | 在该数值范围内的录像请求都会共用同一个原始文件                                                  |
| `clean_raw_file`                 | Boolean | 是否要清理原始文件                                                                |
| `use_death_clip`                 | Boolean | 是否启用死亡切片                                                                 |
| `death_clip_duration`            | Number  | 死亡切片时长（秒）                                                                |
| `death_clip_ahead_seconds`       | Number  | 切片起始点的提前时间量                                                              |
| `use_messagebox`                 | Bool    | 上传成功或失败的时候是否需要消息框提示                                                      |

 - `clip_setting` 和 `upload_setting` 中的字段是相互对应的
 - 其中，`upload_setting` 中的最大允许时长一定是小于等于 `clip_setting` 中的最大允许时长，否则没有意义（有切片才能上传对吧）

---

 - `./scripts/concat.bat` 是用于合并所有死亡切片的脚本，将他放到视频的同级目录下(YYYYMMDD/中，文件夹需要包含filelist.txt)，双击运行，会产生`output.mp4`

---

 `./config/pb.json` 文件：
存储你的pb信息
```json
{
   "rsg.first_portal": {
        "id": 0,
        "igt": 1200000,
        "bvid": "",
        "time": 0
   }
   // 其他配置...
}
```

#### 配置字段说明
| 字段     | 类型     | 说明                 |
|--------|--------|--------------------|
| `id`   | int    | paceman中，本场速通的世界id |
| `igt`  | int    | igt，单位毫秒，默认20分钟    |
| `bvid` | String | 本次pb对应的视频          |
| `time` | int    | 打出本次pb的时间，时间戳，单位秒  |


### 3. 目录结构
项目启动后。会在目录中产生
- `mcsr`文件夹，存储所有 any% 速通比赛视频及相关素材。在这个文件夹中，视频会根据日期进行分类。
- `death_clip`文件夹，用于存储所有死亡切片。在这个文件夹中，视频会根据日期进行分类。只切片不上传。产生`match[<比赛ID>]<时间节点>.mp4`文件。同时同目录下还会产生`filelist.txt`文件，这是用于合并所有切片用到的文件，不要乱动。
- `up_history.json`上传记录
```
工作目录/
├── biliup.exe             # 上传工具
├── mcsr/                  # 视频存储
│   └── YYYYMMDD/          # 按日期分类
         # ranked
│       ├── match[<比赛ID>].mp4  
│       ├── BG match[<比赛ID>].jpg 
│       ├── cover match[<比赛ID>].jpg 
│       ├── cover match[<比赛ID>].html 
│       ├── desc match[<比赛ID>].txt 
│       ├── title match[<比赛ID>].txt 
         # rsg
│       ├── world[<比赛ID>].mp4  
│       ├── BG world[<比赛ID>].jpg 
│       ├── cover world[<比赛ID>].jpg 
│       ├── cover world[<比赛ID>].html 
│       ├── desc world[<比赛ID>].txt 
│       └── title world[<比赛ID>].txt 
├── death_clip/            # 死亡切片
│   └── YYYYMMDD/          # 按日期分类
│       ├── match[<比赛ID>]<时间节点>.mp4  
│       └── filelist.txt   # 视频列表，用于快速合并视频
└── up_history.json        # 上传记录
```

## 功能特性
- **智能切片**：根据比赛时长自动切片和裁剪视频
- **封面生成**：利用 Chromium 自动生成视频封面
- **视频上传**：利用 biliup 自动上传视频
- **历史记录**：`up_history.json` 记录上传信息
- **死亡切片**：根据比赛timeline信息自动生成死亡切片


## 注意事项
1. 确保 OBS 回放缓存时间 > 最大切片时长(一般20分钟足矣)
2. 首次使用需通过 biliup 登录 B 站账号
3. 不同比赛模式的配置参数需单独设置
4. 目前只负责Any%项目速通
5. 私人房间如果未设置'当有人完成时比赛结束'则可能剪辑不准确！
6. OBS录像路径无要求

