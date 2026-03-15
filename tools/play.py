import asyncio
import traceback

from tool_context import DEVICES, close_atv, get_connection, logger, resolve_device_name


async def _wait_for_resume(atv, attempts: int = 4, delay: float = 0.5):
    """Poll playback state briefly after sending play."""
    last_playing = None
    for attempt in range(attempts):
        if attempt > 0:
            await asyncio.sleep(delay)
        last_playing = await atv.metadata.playing()
        if str(last_playing.device_state) == "DeviceState.Playing":
            return last_playing
    return last_playing


def register(mcp) -> None:
    @mcp.tool()
    async def play(device: str = None) -> dict:
        """
        在 HomePod 上播放音乐

        Args:
            device: 设备名称，如 "客厅"、"卧室"。不指定则使用第一个设备。
        """
        logger.info("[play] ========== PLAY COMMAND ==========")
        logger.info(f"[play] Input: device='{device}'")
        logger.info(f"[play] Available devices: {list(DEVICES.keys())}")

        try:
            from pyatv import connect

            device_name = resolve_device_name(device)
            if not device_name:
                logger.error("[play] No device configured")
                return {"error": "No device configured", "configured_devices": list(DEVICES.keys())}

            logger.info(f"[play] Target device: '{device_name}'")

            conf = await get_connection(device_name)
            loop = asyncio.get_event_loop()

            logger.info("[play] Establishing connection...")
            atv = await connect(conf, loop)
            logger.info("[play] Connected, sending play command...")

            if not hasattr(atv, "remote_control"):
                logger.error("[play] No remote_control interface available")
                await close_atv(atv)
                return {"error": "Metadata interface not available"}

            logger.debug(f"[play] Remote control interface: {type(atv.remote_control)}")
            await atv.remote_control.play()
            logger.info(f"[play] Play command sent to '{device_name}', verifying state...")

            playing = await _wait_for_resume(atv)
            state = str(playing.device_state) if playing and playing.device_state else None
            if state != "DeviceState.Playing":
                logger.warning(
                    f"[play] Device '{device_name}' did not enter playing state after play command; state={state}"
                )
                await close_atv(atv)
                logger.info("[play] Connection closed")
                return {
                    "error": "No active content to resume",
                    "device": device_name,
                    "action": "play",
                    "state": state,
                    "title": playing.title if playing else None,
                    "artist": playing.artist if playing else None,
                    "album": playing.album if playing else None,
                }

            logger.info(f"[play] Playback resumed successfully on '{device_name}'")

            await close_atv(atv)
            logger.info("[play] Connection closed")

            return {
                "success": True,
                "device": device_name,
                "action": "play",
                "state": state,
                "title": playing.title,
                "artist": playing.artist,
                "album": playing.album,
            }
        except Exception as exc:
            logger.error(f"[play] ERROR: {exc}")
            logger.error(traceback.format_exc())
            return {"error": str(exc), "error_type": type(exc).__name__}
