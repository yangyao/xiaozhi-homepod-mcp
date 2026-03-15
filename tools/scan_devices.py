import asyncio
import traceback

from tool_context import logger


def register(mcp) -> None:
    @mcp.tool()
    async def scan_devices() -> dict:
        """扫描局域网内的所有 AirPlay 设备"""
        try:
            import pyatv

            loop = asyncio.get_event_loop()
            atvs = await pyatv.scan(loop)

            devices = []
            for atv in atvs:
                services = []
                for service in atv.services:
                    svc_type = getattr(service, "service_type", None) or getattr(service, "protocol", None) or str(type(service))
                    services.append(str(svc_type))

                devices.append(
                    {
                        "name": atv.name,
                        "ip": str(atv.address),
                        "identifier": atv.identifier,
                        "services": services,
                    }
                )

            return {"devices": devices, "count": len(devices)}
        except Exception as exc:
            logger.error(f"[scan_devices] Error: {exc}")
            logger.error(traceback.format_exc())
            return {"error": str(exc)}
