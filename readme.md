# MCSR AUTO CLIP

这是一个用于自动切片1.16rsg和ranked的脚本， 符合预设的条件就可以自动切片上传，省去后期的时间。
效果可参考：https://space.bilibili.com/1578160350

本项目基于 Python3.13、OBS websocket、biliup 和 FFmpeg 等技术实现 


## 快速开始

### ① 下载可执行文件

从release中下载 `mcsr auto clip.zip`，解压后会得到两个文件夹 `installer` 和 `main`。`installer`文件中的文件使用来安装相关的依赖工具的。`main`文件夹中的文件是主程序。

### ② 相关依赖的安装

依次运行 `biliup_installer.exe`（上传工具） `chromium_installer.exe`（封面生成工具） `ffmpeg_installer.exe`（剪辑工具），这三个软件的下载都需要科学上网，请确保你的网络状况。

### ③ OBS 配置

1. OBS 中开启WebSocket服务器
   ```
   OBS菜单栏 -> 工具 -> WebSocket服务器设置 -> 启用，身份验证关闭
   ```
2. 启用回放缓存：
   ```
   OBS控制按钮 -> 设置 -> 输出 -> 回放缓存 -> 启用，设置一个合理的回放时长（这个时长是用于剪辑的原素材文件时长，因此需要大于你剪辑成片的长度）
   ```
3. 记录 websocket 连接信息（默认：`localhost:4455`）

### ④ 启动切片脚本

填写游戏名称，修改视频文件夹（将你的剪辑成片输出的位置）

保存好后，点击启动，开启脚本。

**请记住！任何修改需要点击保存才能生效！**

大约每10秒钟就在日志中输出paceman和ranked信息就是正常运行了。

关于其他设置，可以在下文的的配置文件说明中找到更详细的解释。

尽力打出你的pace吧！

### ⑤ 备注

- 如果启用了上传功能，脚本会让你登录一个bilibili账号，这个账号是你用于上传视频的账号，推荐使用**扫码登录**，最方便。

- 任何修改需要点击保存才能生效！

- 如果点击启动后显示未找到biliup或未找到ffmpeg，可能是安装失败了或者你的电脑需要重启

- 如果遇到了任何bug，请尽量详细地描述复现这个bug的流程，如果能提供日志是更好的

- 如果想要删除在 `① 下载可执行文件` 中安装的文件，请来到 `C:\Users\<用户名>` 文件夹下，删除 `biliup` 、`chromium` 和 `ffmpeg` 文件夹。此外，还要去系统环境变量中删除`biliup`和`ffmpeg` 可执行文件所在的目录。

---

## 从源代码开始

### 1. 安装依赖组件
#### ① OBS 配置
1. OBS 中开启WebSocket服务器
   ```
   OBS菜单栏 -> 工具 -> WebSocket服务器设置 -> 启用，身份验证关闭
   ```
2. 启用回放缓存：
   ```
   OBS控制按钮 -> 设置 -> 输出 -> 回放缓存 -> 启用，设置一个合理的回放时长（这个时长是用于剪辑的原素材文件时长，因此需要大于你剪辑成片的长度）
   ```
3. 记录 websocket 连接信息（默认：`localhost:4455`）


#### ②安装相关依赖
- 双击 `./src/install-requirements.bat` ，脚本会自动安装python包，biliup，chromium，ffmpeg

#### ③运行
- 双击 `./src/start.bat`

### 2. 配置文件说明
 `config.json` 文件：

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
  "base_dir": "<桌面>/mcsr videos",

  "host": "localhost",
  "port": 4455,

  "browser_executable": "C:/Users/<用户名>/chromium/chrome-win/chrome.exe",
  "use_cover": false, 
  "use_description": false,
  "use_upload": false,
  "use_rsg_pb": false,
  "extra_seconds": 15, 
  "wait_for_datapack": 20,
  "replay_threshold_seconds": 20,
  
  "clean_raw_file": true,
  "use_death_clip": true, 
  "ranked_job": true,
  "rsg_job": true,
  "death_clip_duration": 20,
  "death_clip_ahead_seconds": 0
}
```
该文件位于 `C:\Users\<用户名>\AppData\Roaming\mcsr auto clip` 文件夹中

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
| `browser_executable`             | String  | Chromium 浏览器路径，注意正斜杠'/'与反斜杠'\\'                                          |
| `use_cover`                      | Boolean | 是否生成视频封面                                                                 |
| `use_description`                | Boolean | 是否生成视频简介                                                                 |
| `use_upload`                     | Boolean | 是否启用上传                                                                   |
| `use_rsg_pb`                     | Boolean | 是否启用rsg_pb检测功能                                                           |
| `extra_seconds`                  | Number  | 视频是从末尾开始剪辑的，剪辑时长为 `RTA + extra_seconds`<br/>默认值为15，如果剪漏了可以适当调大（秒）        |
| `wait_for_datapack`              | Number  | rsg完成一场速通后，会等待一段时间再结束录像，期间可以输入种子、datapack list等。默认值为30（秒）                |
| `replay_threshold_seconds`       | Number  | 在该数值范围内的录像请求都会共用同一个原始文件                                                  |
| `clean_raw_file`                 | Boolean | 是否要清理原始文件                                                                |
| `use_death_clip`                 | Boolean | 是否启用死亡切片                                                                 |
| `ranked_job`                     | Boolean | 是否启用ranked切片功能                                                           |
| `rsg_job`                        | Boolean | 是否启用rsg切片功能                                                              |
| `death_clip_duration`            | Number  | 死亡切片时长（秒）                                                                |
| `death_clip_ahead_seconds`       | Number  | 切片起始点的提前时间量                                                              |

 - `clip_setting` 和 `upload_setting` 中的字段是相互对应的
 - 其中，`upload_setting` 中的最大允许时长一定是小于等于 `clip_setting` 中的最大允许时长，否则没有意义（有切片才能上传对吧）

---

 - `./scripts/concat.bat` 是用于合并所有死亡切片的脚本，将他放到视频的同级目录下(YYYYMMDD/中，文件夹需要包含filelist.txt)，双击运行，会产生`output.mp4`

---

 `pb.json` 文件：
存储你的pb信息
```json
{
   "rsg.first_portal": {
        "id": 0,
        "igt": 0,
        "bvid": "",
        "time": 0
   }
   // 其他配置...
}
```
该文件位于 `C:\Users\<用户名>\AppData\Roaming\mcsr auto clip` 文件夹中
#### 配置字段说明
| 字段     | 类型     | 说明                 |
|--------|--------|--------------------|
| `id`   | int    | paceman中，本场速通的世界id |
| `igt`  | int    | igt，单位毫秒，默认0       |
| `bvid` | String | 本次pb对应的视频          |
| `time` | int    | 打出本次pb的时间，时间戳，单位秒  |


### 3. 目录结构
项目启动后。会在目录中产生
- `logs`文件夹，用于脚本输出日志文件
- `rsg`文件夹，存储所有 1.16 any% 速通视频。在这个文件夹中，视频会根据日期进行分类。`world[<世界ID>].mp4`
- `ranked`文件夹，存储所有 ranked 速通比赛视频。在这个文件夹中，视频会根据日期进行分类。`match[<比赛ID>].mp4`
- `death_clip`文件夹，用于存储所有死亡切片。在这个文件夹中，视频会根据日期进行分类。只切片不上传。产生`match[<比赛ID>]<时间节点>.mp4`文件。同时同目录下还会产生`filelist.txt`文件，这是用于合并所有切片用到的文件，不要乱动。
- `up_history.json`上传记录
```
工作目录/
├── logs/                  # 日志文件夹
│   └── mcsr_auto_clip_YYYYMMDD.log
├── rsg/                   # 视频存储
│   └── YYYYMMDD/          # 按日期分类
│       ├── world[<世界ID>].mp4  
│       ├── BG world[<世界ID>].jpg 
│       ├── cover world[<世界ID>].jpg 
│       ├── cover world[<世界ID>].html 
│       ├── desc world[<世界ID>].txt 
│       └── title world[<世界ID>].txt 
├── ranked/                # 视频存储
│   └── YYYYMMDD/          # 按日期分类
│       ├── match[<比赛ID>].mp4  
│       ├── BG match[<比赛ID>].jpg 
│       ├── cover match[<比赛ID>].jpg 
│       ├── cover match[<比赛ID>].html 
│       ├── desc match[<比赛ID>].txt 
│       └── title match[<比赛ID>].txt 
├── death_clip/            # 死亡切片
│   └── YYYYMMDD/          # 按日期分类
│       ├── match[<比赛ID>]<时间节点>.mp4  
│       └── filelist.txt   # 视频列表，用于快速合并视频
└── up_history.json        # 上传记录
```

## 功能点
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

## 备用方案
如果上述安装方法无法成功，请尝试以下的方法
#### ① FFmpeg 安装
- 下载 [FFmpeg](https://github.com/BtbN/FFmpeg-Builds/releases) 选择 `ffmpeg-master-latest-win64-gpl.zip`
- 将 `ffmpeg.exe` 和 `ffprobe.exe` 加入系统环境变量

#### ② biliup 部署
- 下载 [biliup](https://github.com/biliup/biliup) 选择 `biliupR-v1.1.28-x86_64-windows.zip` 
- 解压后把 `biliup.exe` 加入系统环境变量
- 在工作目录打开终端，输入 `biliup login` 登录哔哩哔哩账号，推荐使用扫码登录

#### ③chromium 部署
- 下载 [chromium](https://www.googleapis.com/download/storage/v1/b/chromium-browser-snapshots/o/Win_x64%2F1135619%2Fchrome-win.zip?generation=1682469079864558&alt=media)
- 修改配置文件路径（参考下文配置说明），把 `config.json` 中 `browser_executable` 字段的值改为 `chrome.exe` 所在的路径，注意 `\` 与 `/`