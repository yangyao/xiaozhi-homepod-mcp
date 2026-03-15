import asyncio

from tool_context import close_atv, get_connection, normalize_volume_input, resolve_device_name


def register(mcp) -> None:
    @mcp.tool()
    async def set_volume(device: str = None, level: float = 0.5) -> dict:
        """
        设置 HomePod 音量

        Args:
            device: 设备名称。不指定则使用第一个设备。
            level: 音量级别 (0.0 - 1.0)，默认 0.5
        """
        try:
            from pyatv import connect

            device_name = resolve_device_name(device)
            if not device_name:
                return {"error": "No device configured"}

            normalized_level = normalize_volume_input(level)

            conf = await get_connection(device_name)
            loop = asyncio.get_event_loop()
            atv = await connect(conf, loop)

            await atv.audio.set_volume(normalized_level)
            await close_atv(atv)

            return {
                "success": True,
                "device": device_name,
                "volume": normalized_level,
                "input_volume": level,
            }
        except Exception as exc:
            return {"error": str(exc)}

    @mcp.tool()
    async def get_volume(device: str = None) -> dict:
        """
        获取 HomePod 当前音量

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

            volume = atv.audio.volume
            await close_atv(atv)

            return {"device": device_name, "volume": volume}
        except Exception as exc:
            return {"error": str(exc)}
