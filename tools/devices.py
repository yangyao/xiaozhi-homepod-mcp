from tool_context import DEVICES


def register(mcp) -> None:
    @mcp.tool()
    async def list_devices() -> dict:
        """列出所有配置的 HomePod 设备"""
        return {
            "devices": [
                {"name": name, "ip": ip}
                for name, ip in DEVICES.items()
            ]
        }
