from pathlib import Path
import traceback

from tool_context import AUDIO_EXTENSIONS, MUSIC_LIBRARIES, logger
from tools.stream_file import stream_file_impl


def register(mcp) -> None:
    @mcp.tool()
    async def play_album(album_path: str, device: str = None) -> dict:
        """
        播放专辑（播放目录下所有音乐）

        Args:
            album_path: 专辑目录的相对路径
            device: 设备名称。不指定则使用第一个设备。
        """
        logger.info(f"[play_album] Called with album_path='{album_path}', device='{device}'")
        try:
            if not MUSIC_LIBRARIES:
                logger.error("[play_album] MUSIC_LIBRARY not configured")
                return {"error": "MUSIC_LIBRARY not configured in .env"}

            album_dir = None
            for library in MUSIC_LIBRARIES:
                candidate = Path(library) / album_path
                logger.debug(f"[play_album] Checking: {candidate}")
                if candidate.exists() and candidate.is_dir():
                    album_dir = candidate
                    logger.info(f"[play_album] Found album directory: {album_dir}")
                    break

            if not album_dir:
                logger.error(f"[play_album] Album directory not found: {album_path}")
                return {"error": f"Album directory not found: {album_path}"}

            tracks = []
            for track in sorted(album_dir.iterdir()):
                if track.is_file() and track.suffix.lower() in AUDIO_EXTENSIONS:
                    tracks.append(track)

            logger.debug(f"[play_album] Found {len(tracks)} tracks")

            if not tracks:
                logger.error(f"[play_album] No audio files found in: {album_path}")
                return {"error": f"No audio files found in: {album_path}"}

            first_track = tracks[0]
            logger.info(f"[play_album] Playing first track: {first_track.name}")
            result = await stream_file_impl(str(first_track), device)

            return {
                **result,
                "album": album_path,
                "total_tracks": len(tracks),
                "playing_track": first_track.name,
                "track_list": [track.name for track in tracks],
            }
        except Exception as exc:
            logger.error(f"[play_album] Error: {exc}")
            logger.error(traceback.format_exc())
            return {"error": str(exc)}
