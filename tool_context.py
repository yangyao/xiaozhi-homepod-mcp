"""
Shared MCP HomePod configuration and helpers.
"""

import asyncio
import inspect
import logging
import os
import traceback
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("/tmp/homepod_mcp.log", mode="a", encoding="utf-8"),
    ],
)
logger = logging.getLogger("HomePod")
logger.setLevel(logging.DEBUG)

pyatv_logger = logging.getLogger("pyatv")
pyatv_logger.setLevel(logging.DEBUG)

logger.info("=" * 60)
logger.info("HomePod MCP Server Starting...")
logger.info(f"Python version: {os.sys.version}")
logger.info(f"Working directory: {os.getcwd()}")
logger.info("=" * 60)

AUDIO_EXTENSIONS = {".mp3", ".m4a", ".flac", ".wav", ".aac", ".ogg", ".wma", ".alac"}


def get_music_libraries() -> list[str]:
    """Get music library paths from environment."""
    libs = os.environ.get("MUSIC_LIBRARY", "")
    result = [p.strip() for p in libs.split(",") if p.strip()]
    logger.debug(f"Music libraries from env: {result}")
    return result


def parse_devices() -> dict[str, str]:
    """Parse HOMEPOD_DEVICES env var: 名称=IP,名称=IP."""
    devices = {}
    devices_str = os.environ.get("HOMEPOD_DEVICES", "")
    logger.debug(f"Parsing HOMEPOD_DEVICES: '{devices_str}'")
    for pair in devices_str.split(","):
        if "=" in pair:
            name, ip = pair.strip().split("=", 1)
            devices[name.strip()] = ip.strip()
            logger.debug(f"  Parsed device: '{name.strip()}' -> '{ip.strip()}'")
    logger.info(f"Configured devices: {devices}")
    return devices


MUSIC_LIBRARIES = get_music_libraries()
DEVICES = parse_devices()
logger.info(f"Music libraries: {MUSIC_LIBRARIES}")

_connections: dict[str, object] = {}


@dataclass
class ActiveStream:
    device: str
    atv: Any
    task: asyncio.Task
    file_path: str


_active_streams: dict[str, ActiveStream] = {}


def resolve_device_name(device: str | None) -> str | None:
    """Resolve a requested device or fall back to the first configured device."""
    return device or (list(DEVICES.keys())[0] if DEVICES else None)


def resolve_music_file(file_path: str) -> Path | None:
    """Resolve an absolute path or search the configured music libraries."""
    path = Path(file_path)
    if path.is_absolute() and path.exists():
        return path

    for library in MUSIC_LIBRARIES:
        candidate = Path(library) / file_path
        if candidate.exists():
            return candidate
    return None


async def close_atv(atv: Any) -> None:
    """Close a pyatv connection with sync/async compatibility."""
    close_result = atv.close()
    if inspect.isawaitable(close_result):
        await close_result


def get_active_stream(device_name: str) -> ActiveStream | None:
    """Return active stream for a device if one is still alive."""
    stream = _active_streams.get(device_name)
    if stream and stream.task.done():
        _active_streams.pop(device_name, None)
        return None
    return stream


def set_active_stream(device_name: str, stream: ActiveStream) -> None:
    """Store active stream state for a device."""
    _active_streams[device_name] = stream


def clear_active_stream(device_name: str, task: asyncio.Task | None = None) -> None:
    """Remove active stream state for a device."""
    stream = _active_streams.get(device_name)
    if not stream:
        return
    if task is not None and stream.task is not task:
        return
    _active_streams.pop(device_name, None)


def normalize_volume_input(level: float) -> float:
    """Normalize user volume input to pyatv's 0-100 range.

    Values in [0, 1] are treated as fractional input for backward compatibility.
    Values above 1 are treated as percent input.
    """
    if 0.0 <= level <= 1.0:
        return max(0.0, min(100.0, level * 100.0))
    return max(0.0, min(100.0, level))


async def get_connection(device_name: str):
    """Get or create pyatv device config for a HomePod."""
    logger.info("[get_connection] ========== GETTING CONNECTION ==========")
    logger.info(f"[get_connection] Requested device: '{device_name}'")
    logger.debug(f"[get_connection] Current cached connections: {list(_connections.keys())}")
    logger.debug(f"[get_connection] Available devices: {DEVICES}")

    if device_name in _connections:
        logger.info(f"[get_connection] Using cached connection for '{device_name}'")
        return _connections[device_name]

    if device_name not in DEVICES:
        logger.error(f"[get_connection] Unknown device: '{device_name}'")
        logger.error(f"[get_connection] Available devices: {list(DEVICES.keys())}")
        raise ValueError(f"Unknown device: {device_name}. Available: {list(DEVICES.keys())}")

    try:
        import pyatv

        ip = DEVICES[device_name]
        logger.info(f"[get_connection] Device '{device_name}' maps to IP: {ip}")

        loop = asyncio.get_event_loop()
        logger.info(f"[get_connection] Starting device scan at {ip}...")

        scan_start = loop.time()
        atvs = await pyatv.scan(loop, hosts=[ip])
        scan_duration = loop.time() - scan_start
        logger.info(f"[get_connection] Scan completed in {scan_duration:.2f}s, found {len(atvs)} device(s)")

        if not atvs:
            logger.error(f"[get_connection] Cannot find HomePod at {ip}")
            logger.error("[get_connection] Possible issues: device offline, wrong IP, firewall blocking")
            raise RuntimeError(f"Cannot find HomePod at {ip}")

        atv_conf = atvs[0]
        logger.info(f"[get_connection] Found device: name='{atv_conf.name}', identifier='{atv_conf.identifier}'")
        logger.debug(f"[get_connection] Device address: {atv_conf.address}")
        logger.debug(f"[get_connection] Device deep sleep: {atv_conf.deep_sleep}")

        logger.info(f"[get_connection] Device services ({len(atv_conf.services)}):")
        for i, service in enumerate(atv_conf.services):
            svc_type = getattr(service, "service_type", None) or getattr(service, "protocol", None) or str(type(service))
            svc_port = getattr(service, "port", "N/A")
            svc_id = getattr(service, "identifier", "N/A")
            logger.info(f"[get_connection]   Service #{i + 1}: type='{svc_type}', port={svc_port}, identifier='{svc_id}'")

        _connections[device_name] = atv_conf
        logger.info(f"[get_connection] Successfully cached config for '{device_name}'")
        logger.info("[get_connection] ========== CONNECTION READY ==========")
        return atv_conf
    except Exception as exc:
        logger.error(f"[get_connection] Failed to connect to {device_name}: {exc}")
        logger.error(traceback.format_exc())
        raise RuntimeError(f"Failed to connect to {device_name}: {exc}") from exc
