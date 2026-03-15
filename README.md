# MCP HomePod Controller

[中文说明](README_ZH.md)

Control HomePod through MCP (Model Context Protocol). This project supports browsing a local music library, streaming local audio files to HomePod, and basic playback control.

## Features

### Playback Control
- Play / pause / stop
- Volume control
- Read current playback info
- Previous / next track

### Local Music
- Browse local music library
- Search music files
- Stream local audio to HomePod
- Play an album

### Device Management
- Scan AirPlay devices on the local network
- List configured devices

## Quick Start

### 1. Fork or Clone the Repository

```bash
git clone https://github.com/yangyao/xiaozhi-homepod-mcp.git
cd xiaozhi-homepod-mcp
```

If you plan to customize this project, fork it first and then clone your own repository.

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables

Edit `.env`:

```bash
# MCP endpoint
MCP_ENDPOINT=wss://api.xiaozhi.me/mcp/?token=your_token

# HomePod devices (name=ip)
HOMEPOD_DEVICES=Living Room=192.168.1.100

# Local music library path
MUSIC_LIBRARY=/Users/jiao/Music
```

### 4. Pair the Device First if Needed

```bash
python pair.py
```

### 5. Start the Service

```bash
python mcp_pipe.py
```

If you want to debug the MCP server locally, you can also run:

```bash
python -m homepod
```

## Docker

This project can run in Docker on Linux, NAS, or other non-macOS hosts, but HomePod discovery and AirPlay control work best when the container has direct access to the local network.

The container entrypoint is `mcp_pipe`, which is the mode used by XiaoZhi. It is not meant to start `homepod` directly as a standalone MCP process.

Recommended runtime:

```bash
docker run -d \
  --name xiaozhi-homepod-mcp \
  --network host \
  --env-file .env \
  -v /path/to/music:/music:ro \
  yangyao/xiaozhi-homepod-mcp:latest
```

Recommended `.env` values for Docker:

```bash
MCP_ENDPOINT=wss://api.xiaozhi.me/mcp/?token=your_token
HOMEPOD_DEVICES=Living Room=192.168.1.100
MUSIC_LIBRARY=/music
```

Build locally:

```bash
docker build -t yangyao/xiaozhi-homepod-mcp:latest .
```

Notes:
- Prefer fixed HomePod IPs in `HOMEPOD_DEVICES` instead of relying on automatic discovery.
- On Linux, `--network host` is strongly recommended for AirPlay and device discovery.
- On macOS Docker, host networking is more limited, so Linux deployment is the better target for stable streaming.
- The default startup command inside the container is `python -m mcp_pipe`.

## Available Tools

### Device Management
| Tool | Description |
|------|-------------|
| `list_devices` | List configured devices |
| `scan_devices` | Scan devices on the local network |

### Playback Control
| Tool | Description | Parameters |
|------|-------------|------------|
| `play` | Resume the current resumable playback context | `device` (optional) |
| `pause` | Pause playback | `device` (optional) |
| `stop` | Stop playback | `device` (optional) |
| `set_volume` | Set volume | `device`, `level` |
| `get_volume` | Get volume | `device` (optional) |
| `now_playing` | Get current playback info | `device` (optional) |
| `next_track` | Skip to the next track | `device` (optional) |
| `previous_track` | Return to the previous track | `device` (optional) |

### Local Music
| Tool | Description | Parameters |
|------|-------------|------------|
| `list_music` | List music files | `path`, `recursive` |
| `search_music` | Search music files | `keyword` |
| `stream_file` | Stream a local audio file | `file_path`, `device` |
| `play_album` | Play an album directory | `album_path`, `device` |

## Usage Examples

```text
# Browse music
list_music(path="Pop", recursive=true)

# Search music
search_music(keyword="Coldplay")

# Play a file
stream_file(file_path="Pop/Coldplay/Viva La Vida.mp3", device="Living Room")

# Play an album
play_album(album_path="Pop/Coldplay/Viva La Vida or Death and All His Friends", device="Living Room")

# Set volume to 50%
set_volume(device="Living Room", level=0.5)
```

`set_volume` accepts both styles:
- `0.5` is treated as `50%`
- `50` is also treated as `50%`

## Behavior Notes

### Difference Between `play` and `stream_file`

- `play` resumes an existing playback context on HomePod
- `stream_file` explicitly starts playing a local audio file

If the device does not currently have resumable content, `play` may not actually start playback. In that case, `stream_file` is the correct tool to use.

### Pause and Stop for Local Streaming

For local audio sessions started by `stream_file` or `play_album`, `pause` and `stop` will first try to control the active streaming session. This avoids cases where the command is accepted but the local stream keeps playing.

## Supported Audio Formats

- MP3 (`.mp3`)
- AAC / M4A (`.m4a`, `.aac`)
- FLAC (`.flac`)
- WAV (`.wav`)
- OGG (`.ogg`)
- WMA (`.wma`)
- ALAC

## Notes

1. AirPlay must be enabled on the HomePod.
2. Local music streaming requires AirPlay to be available. On some device or system versions, pairing may be required first.
3. The computer and HomePod must be on the same local network.
4. `play`, `pause`, and `stop` do not behave exactly the same for native system playback and locally streamed audio. Check the current playback source when debugging.

## Project Structure

```text
mcp-homepod/
├── homepod.py       # MCP entry point
├── tool_context.py  # Shared config, logging, and connection helpers
├── tools/           # One file per MCP tool
│   ├── play.py
│   ├── pause.py
│   ├── stop.py
│   ├── stream_file.py
│   └── ...
├── pair.py          # Pairing helper
├── mcp_pipe.py      # WebSocket bridge
├── mcp_config.json  # MCP config
├── .env             # Environment variables
└── requirements.txt # Dependencies
```
