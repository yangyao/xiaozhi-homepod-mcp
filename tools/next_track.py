import asyncio

from tool_context import close_atv, get_connection, resolve_device_name


def register(mcp) -> None:
    @mcp.tool()
    async def next_track(device: str = None) -> dict:
        """
        播放下一曲

        Args:
            device: 设备名称。不指定则使用第一个设备。
        """
        try:
            from pyatv import connect

            device_name = resolve_device_name(device)
            if not device_name:
                return {"error": "No device configured"}

            conf = await get_connection(device_name)
            loop = asyncio.get_event_loop()
            atv = await connect(conf, loop)

            await atv.remote_control.next()
            await close_atv(atv)

            return {"success": True, "device": device_name, "action": "next"}
        except Exception as exc:
            return {"error": str(exc)}
