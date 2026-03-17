<p align="center">English ｜ <a href="./readme_zh_CN.md" >简体中文</a></p>

# MCSR AUTO CLIP

This is a script for automatically clipping 1.16 RSG and Ranked Minecraft speedruns. Once conditions are met, it automatically clips and uploads the video, saving time.

  * **Demo:** [Bilibili Space](https://space.bilibili.com/1578160350)
  * **Tutorial:** [Bilibili Video](https://www.bilibili.com/video/BV1zDBXBkETV)

This project is built using **Python 3.13**, **OBS WebSocket**, **biliup**, and **FFmpeg**.

-----

## Quick Start

### 1\. Download Executable

Download `mcsr auto clip.zip` from the Releases page. Extract it to find the `main` folder, which contains the main program.

### 2\. OBS Configuration

1.  **Enable WebSocket Server:**
      * Go to OBS Menu -\> Tools -\> WebSocket Server Settings.
      * Check **Enable WebSocket Server**.
      * Set **Server Port** (default: `4455`).
      * Disable **Enable Authentication**.
2.  **Enable Replay Buffer:**
      * Go to Settings -\> Output -\> Replay Buffer.
      * Check **Enable Replay Buffer**.
      * Set a **Maximum Replay Time** (this is the source duration for clips; ensure it is longer than your desired final clip length).

### 3\. Launch the Script

Double-click the `main.exe` in the `main` folder. Enter your Minecraft **In-Game Name**, set the **Video Folder** (where final clips will be saved), and click **Start**.

For advanced settings, refer to the `Configuration Guide` below. Good luck with your pace\!

### 4\. Notes

  * **Uploading:** If the upload feature is enabled, the script will prompt you to log in to Bilibili. **QR Code Login** is recommended.
  * **Bug Reports:** If you meet bugs, please describe the reproduction steps in detail and provide log files if possible.

-----

## Build from Source

### 1\. Requirements & Setup

#### OBS Configuration

Follow the same steps above.

#### Dependency Installation

  * Double-click `./src/install-requirements.bat` to install necessary Python packages.
  * Ensure an `assets` folder exists in the same directory as `src` with the following structure:

```text
assets
├───biliup
│─────  biliup.exe
│
└───ffmpeg
    ├── bin
    │─────  ffmpeg.exe
    │─────  ffplay.exe
    └─────  ffprobe.exe
```

#### Running

  * Double-click `./src/start.bat`.

-----

### 2\. Configuration Guide

The `config.json` file is located at:
`C:\Users\<Username>\AppData\Roaming\mcsr auto clip`

#### JSON Structure Example

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
      // other mode settings
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
    // upload setting is the same as above...
  },
  "base_dir": "<desktop>/mcsr videos",
  "lang": "en",

  "host": "localhost",
  "port": 4455,

  "auto_start": true,
  "use_cover": false, 
  "use_description": false,
  "use_upload": false,
  "use_rsg_pb": false,
  "extra_seconds_ranked": 15,
  "extra_seconds_rsg": 0,
  "wait_for_datapack": 20,
  
  "clean_raw_file": true,
  "use_death_clip": true, 
  "ranked_job": true,
  "rsg_job": true,
  "death_clip_duration": 20,
  "death_clip_ahead_seconds": 0
}
```

### Configuration Field Descriptions

| Field                            | Type    | Description                                                                                                           |
|:---------------------------------|:--------|:----------------------------------------------------------------------------------------------------------------------|
| `player`                         | Object  | Player information.                                                                                                   |
| `player.name`                    | String  | Minecraft in-game nickname.                                                                                           |
| `player.uuid`                    | String  | Player UUID (without hyphens `-`). Can be retrieved from: `https://mcsrranked.com/api/users/{your_name}`              |
| `clip_setting`                   | Object  | Rules for video clipping.                                                                                             |
| `upload_setting`                 | Object  | Rules for video uploading.                                                                                            |
| `ranked.MATCH_TYPE.max_time`     | Number  | Maximum allowed time (ms).                                                                                            |
| `ranked.MATCH_TYPE.seed_type`    | Array   | Whitelist of valid Overworld seed types.                                                                              |
| `ranked.MATCH_TYPE.bastion_type` | Array   | Whitelist of valid Bastion types.                                                                                     |
| `rsg.rsg.enter_nether`           | Number  | RSG: Max allowed time to enter the Nether (ms).                                                                       |
| `rsg.rsg.enter_bastion`          | Number  | RSG: Max allowed time to enter the Bastion (ms).                                                                      |
| `rsg.rsg.enter_fortress`         | Number  | RSG: Max allowed time to enter the Fortress (ms).                                                                     |
| `rsg.rsg.first_portal`           | Number  | RSG: Max allowed time blind (ms).                                                                                     |
| `rsg.rsg.enter_stronghold`       | Number  | RSG: Max allowed time to enter the Stronghold (ms).                                                                   |
| `rsg.rsg.enter_end`              | Number  | RSG: Max allowed time to enter the End (ms).                                                                          |
| `rsg.rsg.credits`                | Number  | RSG: Max allowed time to finish the run (ms).                                                                         |
| `base_dir`                       | String  | Path to the working directory.                                                                                        |
| `lang`                           | String  | language，`zh_CN` is supported now                                                                                       |
| `host`                           | String  | OBS WebSocket host address.                                                                                           |
| `port`                           | Number  | OBS WebSocket port.                                                                                                   |
| `auto_start`                     | Boolean | Whether to automatically start the script.                                                                            |
| `use_cover`                      | Boolean | Whether to generate a video cover/thumbnail.                                                                          |
| `use_description`                | Boolean | Whether to generate a video description.                                                                              |
| `use_upload`                     | Boolean | Whether to enable video uploading to bilibili.                                                                        |
| `use_rsg_pb`                     | Boolean | Whether to enable the RSG PB detection feature.                                                                       |
| `extra_seconds_ranked`           | Number  | Clipping starts from the end; duration is `RTA + extra_seconds`. Default is 15s; increase if clips are cut too short. |
| `extra_seconds_rsg`              | Number  | Clipping starts from the end; duration is `RTA + extra_seconds`. Default is 0s; increase if clips are cut too short.  |
| `wait_for_datapack`              | Number  | Seconds to wait after an RSG run before stopping the recording (to show seeds, datapack lists, etc.). Default is 30s. |
| `clean_raw_file`                 | Boolean | Whether to delete the original raw video files after processing.                                                      |
| `use_death_clip`                 | Boolean | Whether to enable clipping for player deaths in mcsr ranked.                                                          |
| `ranked_job`                     | Boolean | Whether to enable the Ranked clipping task.                                                                           |
| `rsg_job`                        | Boolean | Whether to enable the RSG clipping task.                                                                              |
| `death_clip_duration`            | Number  | Duration of the death clip (seconds).                                                                                 |
| `death_clip_ahead_seconds`       | Number  | Time lead-in for the start of the death clip (seconds).                                                               |

---
> **Note:** Fields in `clip_setting` and `upload_setting` correspond to each other. Values in `upload_setting` must be less than or equal to `clip_setting` values.

-----
* `./scripts/concat.bat` is a script used to merge all death clips. 
Double-click the script in the `death_clip` folder to run; it will generate `output.mp4`.

---

### `pb.json` 
This file stores your Personal Best information and is located in the `C:\Users\<Username>\AppData\Roaming\mcsr auto clip` folder.

```json
{
   "rsg.first_portal": {
        "id": 0,
        "igt": 0,
        "bvid": null,
        "time": 0
   }
   // Other configurations...
}
```

#### Field Descriptions
| Field | Type | Description |
| :--- | :--- | :--- |
| `id` | int | The World ID of this run in Paceman. |
| `igt` | int | In-game time (IGT) in milliseconds (Default: 0). |
| `bvid` | String | The Bilibili video ID (BVID) corresponding to this PB. |
| `time` | int | The timestamp (in seconds) when this PB was achieved. |

---

### 3. Directory Structure
After the project starts, the following folders and files will be generated in the working directory:

* **`logs/`**: Stores script output log files.
* **`rsg/`**: Stores all 1.16 any% speedrun videos, categorized by date. Files are named `world[<World ID>].mp4`.
* **`ranked/`**: Stores all Ranked speedrun match videos, categorized by date. Files are named `match[<Match ID>].mp4`.
* **`death_clip/`**: Stores all death clips categorized by date. Files are named `match[<Match ID>]<Timestamp>.mp4`. A `filelist.txt` is generated in the same directory for merging purposes.
* **`up_history.json`**: Upload history record.

#### Visual Structure:
```text
Working Directory/
├── logs/                  # Logs folder
│   └── mcsr_auto_clip_YYYYMMDD.log
├── rsg/                   # RSG video storage
│   └── YYYYMMDD/          # Categorized by date
│       ├── world[<World ID>].mp4  
│       ├── bg[<World ID>].webp 
│       ├── cover[<World ID>].jpg 
│       ├── cover[<World ID>].html 
│       ├── desc[<World ID>].txt 
│       └── title[<World ID>].txt 
├── ranked/                # Ranked video storage
│   └── YYYYMMDD/          # Categorized by date
│       ├── match[<Match ID>].mp4  
│       ├── bg[<Match ID>].webp 
│       ├── cover[<Match ID>].jpg 
│       ├── cover[<Match ID>].html 
│       ├── desc[<Match ID>].txt 
│       └── title[<Match ID>].txt 
├── death_clip/            # Death clips
│   └── YYYYMMDD/          # Categorized by date
│       ├── match[<Match ID>]<Timestamp>.mp4  
│       ├── concat.bat     # Script for video merging  
│       └── filelist.txt   # List used for fast video merging
└── up_history.json        # Upload history record
```

---
