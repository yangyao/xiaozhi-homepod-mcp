import asyncio
import traceback

from tool_context import DEVICES, close_atv, get_connection, logger, resolve_device_name


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
            logger.info(f"[play] Play command sent successfully to '{device_name}'")

            await close_atv(atv)
            logger.info("[play] Connection closed")

            return {"success": True, "device": device_name, "action": "play"}
        except Exception as exc:
            logger.error(f"[play] ERROR: {exc}")
            logger.error(traceback.format_exc())
            return {"error": str(exc), "error_type": type(exc).__name__}
