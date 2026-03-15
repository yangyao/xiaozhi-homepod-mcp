import asyncio

from tool_context import close_atv, get_connection, resolve_device_name


def register(mcp) -> None:
    @mcp.tool()
    async def now_playing(device: str = None) -> dict:
        """
        获取 HomePod 当前播放信息

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

            playing = await atv.metadata.playing()
            await close_atv(atv)

            return {
                "device": device_name,
                "title": playing.title,
                "artist": playing.artist,
                "album": playing.album,
                "state": str(playing.device_state) if playing.device_state else None,
                "position": playing.position,
                "total_time": playing.total_time,
            }
        except Exception as exc:
            return {"error": str(exc)}
