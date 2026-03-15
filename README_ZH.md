# MCP HomePod Controller

[English README](README.md)

通过 MCP (Model Context Protocol) 控制 HomePod，支持浏览本地音乐库、把本地音频推流到 HomePod 播放，以及执行基础播放控制。

## 功能

### 播放控制
- 播放 / 暂停 / 停止
- 音量控制
- 获取当前播放信息
- 上一曲 / 下一曲

### 本地音乐
- 浏览本地音乐库
- 搜索音乐文件
- 推送本地音频到 HomePod
- 播放专辑

### 设备管理
- 扫描局域网 AirPlay 设备
- 列出已配置设备

## 快速开始

### 1. 安装依赖

```bash
cd /Users/jiao/www/play/mcp-homepod
pip install -r requirements.txt
```

### 2. 配置环境变量

编辑 `.env` 文件：

```bash
# MCP 接入点地址
MCP_ENDPOINT=wss://api.xiaozhi.me/mcp/?token=your_token

# HomePod 设备 (名称=IP地址)
HOMEPOD_DEVICES=客厅=192.168.1.100

# 本地音乐库路径
MUSIC_LIBRARY=/Users/jiao/Music
```

### 3. 首次配对（如需要）

```bash
python pair.py
```

### 4. 启动服务

```bash
python mcp_pipe.py
```

如果你是直接本地调试 MCP server，也可以运行：

```bash
python -m homepod
```

## 可用工具

### 设备管理
| 工具 | 说明 |
|------|------|
| `list_devices` | 列出配置的设备 |
| `scan_devices` | 扫描局域网设备 |

### 播放控制
| 工具 | 说明 | 参数 |
|------|------|------|
| `play` | 恢复当前可恢复的播放上下文 | `device`（可选） |
| `pause` | 暂停 | `device`（可选） |
| `stop` | 停止 | `device`（可选） |
| `set_volume` | 设置音量 | `device`, `level` |
| `get_volume` | 获取音量 | `device`（可选） |
| `now_playing` | 当前播放 | `device`（可选） |
| `next_track` | 下一曲 | `device`（可选） |
| `previous_track` | 上一曲 | `device`（可选） |

### 本地音乐
| 工具 | 说明 | 参数 |
|------|------|------|
| `list_music` | 列出音乐文件 | `path`, `recursive` |
| `search_music` | 搜索音乐 | `keyword` |
| `stream_file` | 推送音乐播放 | `file_path`, `device` |
| `play_album` | 播放专辑 | `album_path`, `device` |

## 使用示例

```text
# 浏览音乐库
list_music(path="流行音乐", recursive=true)

# 搜索音乐
search_music(keyword="周杰伦")

# 播放指定文件
stream_file(file_path="流行音乐/周杰伦/青花瓷.mp3", device="客厅")

# 播放专辑
play_album(album_path="流行音乐/周杰伦/范特西", device="客厅")

# 设置音量 50%
set_volume(device="客厅", level=0.5)
```

`set_volume` 兼容两种写法：
- `0.5` 会被当作 `50%`
- `50` 也会被当作 `50%`

## 行为说明

### `play` 和 `stream_file` 的区别

- `play` 用于恢复 HomePod 当前已有的播放上下文
- `stream_file` 用于明确播放一首本地音乐文件

如果设备当前没有可恢复的播放内容，`play` 可能不会真正开始播放；这种场景下应优先使用 `stream_file`。

### 本地推流的暂停/停止

对通过 `stream_file` 或 `play_album` 发起的本地音频推流，`pause` 和 `stop` 会优先控制当前活跃的推流会话。这样可以避免“命令发送成功，但没有停掉本地推流”的问题。

## 支持的音频格式

- MP3 (`.mp3`)
- AAC / M4A (`.m4a`, `.aac`)
- FLAC (`.flac`)
- WAV (`.wav`)
- OGG (`.ogg`)
- WMA (`.wma`)
- ALAC

## 注意事项

1. HomePod 需要开启 AirPlay 功能
2. 本地音乐推流需要 AirPlay 可用；部分设备或系统版本下可能需要先完成配对
3. 电脑和 HomePod 需在同一局域网
4. `play` / `pause` / `stop` 对系统原生播放器和本地推流的行为不完全相同，排查问题时请先确认当前播放来源

## 项目结构

```text
mcp-homepod/
├── homepod.py       # MCP 入口
├── tool_context.py  # 共享配置、日志、连接逻辑
├── tools/           # 每个 MCP tool 一个文件
│   ├── play.py
│   ├── pause.py
│   ├── stop.py
│   ├── stream_file.py
│   └── ...
├── pair.py          # 配对工具
├── mcp_pipe.py      # WebSocket 管道
├── mcp_config.json  # MCP 配置
├── .env             # 环境变量
└── requirements.txt # 依赖列表
```
