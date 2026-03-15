import asyncio
import traceback
from pathlib import Path

from tool_context import (
    AUDIO_EXTENSIONS,
    DEVICES,
    MUSIC_LIBRARIES,
    ActiveStream,
    clear_active_stream,
    close_atv,
    get_active_stream,
    logger,
    resolve_device_name,
    resolve_music_file,
    set_active_stream,
)


async def _stream_in_background(device_name: str, atv, actual_path: Path) -> None:
    current_task = asyncio.current_task()
    try:
        logger.debug(f"[stream_file] Background task streaming '{actual_path}'")
        await atv.stream.stream_file(str(actual_path))
        logger.info(f"[stream_file] Background stream completed for '{device_name}'")
    except asyncio.CancelledError:
        logger.info(f"[stream_file] Background stream cancelled for '{device_name}'")
        raise
    except Exception as exc:
        logger.error(f"[stream_file] Background stream failed for '{device_name}': {exc}")
        logger.error(traceback.format_exc())
    finally:
        try:
            await close_atv(atv)
            logger.info(f"[stream_file] Background connection closed for '{device_name}'")
        except Exception as exc:
            logger.warning(f"[stream_file] Error closing background stream for '{device_name}': {exc}")
        clear_active_stream(device_name, current_task)


async def _wait_for_stream_start(stream_task: asyncio.Task, timeout: float = 1.0) -> str | None:
    """Wait briefly to detect immediate stream startup failures.

    Returns an error message if the background task fails immediately, else None.
    """
    done, _ = await asyncio.wait({stream_task}, timeout=timeout)
    if stream_task not in done:
        return None

    try:
        await stream_task
    except asyncio.CancelledError:
        return "Stream was cancelled during startup"
    except Exception as exc:
        return str(exc)
    return "Stream ended unexpectedly during startup"


async def stream_file_impl(file_path: str, device: str = None) -> dict:
    logger.info("[stream_file] ========== START STREAM ==========")
    logger.info(f"[stream_file] Input: file_path='{file_path}', device='{device}'")
    logger.info(f"[stream_file] Configured devices: {DEVICES}")
    logger.info(f"[stream_file] Music libraries: {MUSIC_LIBRARIES}")

    try:
        import pyatv
        from pyatv import conf, connect

        logger.debug(f"[stream_file] pyatv version: {pyatv.__version__ if hasattr(pyatv, '__version__') else 'unknown'}")

        actual_path = resolve_music_file(file_path)
        path = Path(file_path)
        logger.info(f"[stream_file] Resolving path: '{file_path}'")
        logger.debug(f"[stream_file] Path object: {path}")
        logger.debug(f"[stream_file] Is absolute: {path.is_absolute()}")
        logger.debug(f"[stream_file] Absolute path would be: {path.absolute()}")

        if not actual_path:
            logger.error(f"[stream_file] File not found: {file_path}")
            logger.error(f"[stream_file] Searched libraries: {MUSIC_LIBRARIES}")
            return {"error": f"File not found: {file_path}", "searched_libraries": MUSIC_LIBRARIES}

        logger.info(f"[stream_file] File found: {actual_path}")
        file_stat = actual_path.stat()
        logger.debug(f"[stream_file] File size: {file_stat.st_size / (1024 * 1024):.2f} MB")
        logger.debug(f"[stream_file] File extension: {actual_path.suffix}")
        logger.debug(f"[stream_file] File stem: {actual_path.stem}")

        if actual_path.suffix.lower() not in AUDIO_EXTENSIONS:
            logger.warning(f"[stream_file] File extension '{actual_path.suffix}' may not be supported. Supported: {AUDIO_EXTENSIONS}")

        device_name = resolve_device_name(device)
        if not device_name:
            logger.error("[stream_file] No device configured in DEVICES")
            return {"error": "No device configured", "configured_devices": list(DEVICES.keys())}

        ip = DEVICES[device_name]
        logger.info(f"[stream_file] Target device: '{device_name}' at {ip}")

        loop = asyncio.get_event_loop()
        logger.debug(f"[stream_file] Event loop: {loop}")

        logger.info(f"[stream_file] Scanning for device at {ip}...")
        scan_start = loop.time()

        try:
            atvs = await asyncio.wait_for(pyatv.scan(loop, hosts=[ip]), timeout=10.0)
            scan_duration = loop.time() - scan_start
            logger.info(f"[stream_file] Scan completed in {scan_duration:.2f}s, found {len(atvs)} device(s)")
        except asyncio.TimeoutError:
            logger.error(f"[stream_file] Scan timeout for {ip}")
            return {"error": f"Scan timeout for {ip}"}
        except Exception as exc:
            logger.error(f"[stream_file] Scan error: {exc}")
            logger.error(traceback.format_exc())
            return {"error": f"Scan error: {exc}"}

        if not atvs:
            logger.error(f"[stream_file] Cannot find HomePod at {ip}")
            return {"error": f"Cannot find HomePod at {ip}", "ip": ip}

        atv_conf = atvs[0]
        logger.info(f"[stream_file] Found device: name='{atv_conf.name}', identifier='{atv_conf.identifier}', address='{atv_conf.address}'")

        logger.info(f"[stream_file] Device has {len(atv_conf.services)} service(s):")
        for i, service in enumerate(atv_conf.services):
            svc_type = getattr(service, "service_type", None) or getattr(service, "protocol", None) or str(type(service))
            svc_port = getattr(service, "port", "N/A")
            svc_id = getattr(service, "identifier", "N/A")
            logger.info(f"[stream_file]   Service #{i + 1}: type='{svc_type}', port={svc_port}, identifier='{svc_id}'")
            logger.debug(f"[stream_file]   Service #{i + 1} attributes: {[a for a in dir(service) if not a.startswith('_')]}")

        airplay_service = None
        for service in atv_conf.services:
            svc_type = str(getattr(service, "service_type", "") or getattr(service, "protocol", "")).lower()
            logger.debug(f"[stream_file] Checking service: {svc_type}")
            if "airplay" in svc_type or "raop" in svc_type:
                airplay_service = service
                logger.info("[stream_file] Found AirPlay/RAOP service!")
                logger.info(f"[stream_file]   Port: {getattr(service, 'port', 'N/A')}")
                logger.info(f"[stream_file]   Identifier: {getattr(service, 'identifier', 'N/A')}")
                if hasattr(service, "credentials"):
                    creds = service.credentials
                    logger.debug(f"[stream_file]   Credentials: {creds[:20] if creds else 'None'}...")
                break

        if not airplay_service:
            logger.error("[stream_file] No AirPlay service found on device")
            svc_types = [str(getattr(service, "service_type", "") or getattr(service, "protocol", "")) for service in atv_conf.services]
            logger.error(f"[stream_file] Available service types: {svc_types}")
            return {"error": "HomePod does not support AirPlay streaming", "available_services": svc_types}

        airplay_id = getattr(airplay_service, "identifier", None)
        airplay_port = getattr(airplay_service, "port", 7000)
        airplay_creds = getattr(airplay_service, "credentials", None)

        logger.debug(f"[stream_file] AirPlay identifier: {airplay_id}")
        logger.debug(f"[stream_file] AirPlay port: {airplay_port}")
        logger.debug(f"[stream_file] AirPlay credentials: {airplay_creds}")

        try:
            airplay_conf = conf.AirPlayService(airplay_id, airplay_port, credentials=airplay_creds)
            atv_conf.add_service(airplay_conf)
            logger.info("[stream_file] AirPlay config added to device configuration")
        except Exception as exc:
            logger.error(f"[stream_file] Failed to create AirPlay config: {exc}")
            logger.error(traceback.format_exc())
            return {"error": f"Failed to create AirPlay config: {exc}"}

        logger.info(f"[stream_file] Connecting to device '{device_name}'...")
        connect_start = loop.time()

        try:
            atv = await asyncio.wait_for(connect(atv_conf, loop), timeout=15.0)
            connect_duration = loop.time() - connect_start
            logger.info(f"[stream_file] Connected successfully in {connect_duration:.2f}s")
        except asyncio.TimeoutError:
            logger.error("[stream_file] Connection timeout")
            return {"error": "Connection timeout"}
        except Exception as exc:
            logger.error(f"[stream_file] Connection failed: {exc}")
            logger.error(traceback.format_exc())
            return {"error": f"Connection failed: {exc}"}

        logger.debug(f"[stream_file] Connection object: {type(atv)}")
        logger.debug(f"[stream_file] Available interfaces: {[m for m in dir(atv) if not m.startswith('_')]}")

        if not hasattr(atv, "stream"):
            logger.error("[stream_file] Connection does not have 'stream' interface")
            await close_atv(atv)
            return {"error": "Stream interface not available"}

        logger.debug(f"[stream_file] Stream interface: {type(atv.stream)}")
        logger.debug(f"[stream_file] Stream methods: {[m for m in dir(atv.stream) if not m.startswith('_')]}")

        logger.info("[stream_file] ========== STARTING STREAM ==========")
        logger.info(f"[stream_file] File: {actual_path}")
        logger.info(f"[stream_file] Size: {file_stat.st_size / (1024 * 1024):.2f} MB")
        existing_stream = get_active_stream(device_name)
        if existing_stream:
            logger.info(f"[stream_file] Existing active stream found on '{device_name}', stopping it first")
            try:
                await existing_stream.atv.remote_control.stop()
            except Exception as exc:
                logger.warning(f"[stream_file] Failed to stop previous stream cleanly: {exc}")
            existing_stream.task.cancel()
            try:
                await close_atv(existing_stream.atv)
            except Exception as exc:
                logger.warning(f"[stream_file] Failed to close previous stream cleanly: {exc}")
            clear_active_stream(device_name, existing_stream.task)

        stream_task = asyncio.create_task(_stream_in_background(device_name, atv, actual_path))
        set_active_stream(
            device_name,
            ActiveStream(
                device=device_name,
                atv=atv,
                task=stream_task,
                file_path=str(actual_path),
            ),
        )

        startup_error = await _wait_for_stream_start(stream_task)
        if startup_error:
            logger.error(f"[stream_file] Stream startup failed: {startup_error}")
            clear_active_stream(device_name, stream_task)
            return {"error": f"Stream startup failed: {startup_error}"}

        return {
            "success": True,
            "device": device_name,
            "device_ip": ip,
            "file": str(actual_path),
            "file_size_mb": round(file_stat.st_size / (1024 * 1024), 2),
            "action": "stream_started",
        }
    except Exception as exc:
        logger.error(f"[stream_file] FATAL ERROR: {exc}")
        logger.error(traceback.format_exc())
        return {"error": str(exc), "error_type": type(exc).__name__}


def register(mcp) -> None:
    @mcp.tool()
    async def stream_file(file_path: str, device: str = None) -> dict:
        """
        推送本地音乐文件到 HomePod 播放

        Args:
            file_path: 音乐文件的相对路径或绝对路径
            device: 设备名称。不指定则使用第一个设备。
        """
        return await stream_file_impl(file_path, device)
