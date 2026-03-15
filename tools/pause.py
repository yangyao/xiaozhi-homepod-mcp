import asyncio
import traceback

from tool_context import clear_active_stream, close_atv, get_active_stream, get_connection, logger, resolve_device_name


def register(mcp) -> None:
    @mcp.tool()
    async def pause(device: str = None) -> dict:
        """
        暂停 HomePod 播放

        Args:
            device: 设备名称。不指定则使用第一个设备。
        """
        logger.info(f"[pause] Called with device='{device}'")
        try:
            from pyatv import connect

            device_name = resolve_device_name(device)
            if not device_name:
                logger.error("[pause] No device configured")
                return {"error": "No device configured"}

            active_stream = get_active_stream(device_name)
            if active_stream:
                await active_stream.atv.remote_control.pause()
                logger.info(f"[pause] Pause sent to active stream on '{device_name}'")
                active_stream.task.cancel()
                try:
                    await close_atv(active_stream.atv)
                finally:
                    clear_active_stream(device_name, active_stream.task)
                return {"success": True, "device": device_name, "action": "pause", "mode": "active_stream"}

            conf = await get_connection(device_name)
            loop = asyncio.get_event_loop()
            atv = await connect(conf, loop)

            await atv.remote_control.pause()
            logger.info(f"[pause] Pause command sent to '{device_name}'")
            await close_atv(atv)

            return {"success": True, "device": device_name, "action": "pause"}
        except Exception as exc:
            logger.error(f"[pause] Error: {exc}")
            logger.error(traceback.format_exc())
            return {"error": str(exc)}
