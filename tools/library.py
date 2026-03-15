from pathlib import Path
import traceback

from tool_context import AUDIO_EXTENSIONS, MUSIC_LIBRARIES, logger


def register(mcp) -> None:
    @mcp.tool()
    async def list_music(path: str = None, recursive: bool = False) -> dict:
        """
        列出音乐库中的音乐文件

        Args:
            path: 相对路径，不指定则列出根目录。如 "流行音乐/周杰伦"
            recursive: 是否递归搜索子目录，默认 False
        """
        logger.info("[list_music] ========== LIST MUSIC ==========")
        logger.info(f"[list_music] Input: path='{path}', recursive={recursive}")
        logger.info(f"[list_music] MUSIC_LIBRARIES: {MUSIC_LIBRARIES}")
        logger.info(f"[list_music] AUDIO_EXTENSIONS: {AUDIO_EXTENSIONS}")

        try:
            if not MUSIC_LIBRARIES:
                logger.error("[list_music] MUSIC_LIBRARY not configured")
                return {"error": "MUSIC_LIBRARY not configured in .env", "configured_libraries": []}

            results = []
            library_stats = []

            for library in MUSIC_LIBRARIES:
                logger.info(f"[list_music] --- Processing library: {library} ---")
                base_path = Path(library)
                logger.debug(f"[list_music] Base path: {base_path}")
                logger.debug(f"[list_music] Exists: {base_path.exists()}")

                if not base_path.exists():
                    logger.warning(f"[list_music] Library path does not exist: {library}")
                    library_stats.append({"library": library, "exists": False, "file_count": 0})
                    continue

                search_path = base_path / path if path else base_path
                logger.info(f"[list_music] Search path: {search_path}")
                logger.debug(f"[list_music] Search path exists: {search_path.exists()}")

                if not search_path.exists():
                    logger.warning(f"[list_music] Search path does not exist: {search_path}")
                    library_stats.append({"library": library, "path": str(search_path), "exists": False, "file_count": 0})
                    continue

                pattern = "**/*" if recursive else "*"
                file_count = 0
                dir_count = 0
                first_files = []

                for file_path in search_path.glob(pattern):
                    if file_path.is_dir():
                        dir_count += 1
                        if dir_count <= 5:
                            logger.debug(f"[list_music] Found directory: {file_path.name}")
                        continue

                    if file_path.is_file() and file_path.suffix.lower() in AUDIO_EXTENSIONS:
                        rel_path = file_path.relative_to(base_path)
                        results.append(
                            {
                                "name": file_path.stem,
                                "filename": file_path.name,
                                "path": str(rel_path),
                                "library": library,
                                "size_mb": round(file_path.stat().st_size / (1024 * 1024), 2),
                            }
                        )
                        file_count += 1
                        if len(first_files) < 5:
                            first_files.append(file_path.name)

                logger.info(f"[list_music] Library '{library}': found {file_count} audio files, {dir_count} directories")
                if first_files:
                    logger.debug(f"[list_music] First files: {first_files}")

                library_stats.append(
                    {
                        "library": library,
                        "path": str(search_path),
                        "exists": True,
                        "file_count": file_count,
                        "dir_count": dir_count,
                    }
                )

            results.sort(key=lambda item: item["path"])

            logger.info("[list_music] ========== LIST COMPLETE ==========")
            logger.info(f"[list_music] Total files found: {len(results)}")
            logger.info(f"[list_music] Library stats: {library_stats}")

            return {
                "libraries": MUSIC_LIBRARIES,
                "library_stats": library_stats,
                "count": len(results),
                "files": results[:100],
            }
        except Exception as exc:
            logger.error(f"[list_music] ERROR: {exc}")
            logger.error(traceback.format_exc())
            return {"error": str(exc), "error_type": type(exc).__name__}

    @mcp.tool()
    async def search_music(keyword: str) -> dict:
        """
        搜索音乐文件

        Args:
            keyword: 搜索关键词（文件名）
        """
        logger.info("[search_music] ========== START SEARCH ==========")
        logger.info(f"[search_music] Input keyword: '{keyword}' (type: {type(keyword)})")
        logger.info(f"[search_music] Keyword length: {len(keyword) if keyword else 0}")
        logger.info(f"[search_music] MUSIC_LIBRARIES: {MUSIC_LIBRARIES}")
        logger.info(f"[search_music] AUDIO_EXTENSIONS: {AUDIO_EXTENSIONS}")

        try:
            if not keyword or not keyword.strip():
                logger.warning("[search_music] Empty keyword provided")
                return {"error": "Search keyword cannot be empty", "keyword": keyword, "count": 0, "files": []}

            if not MUSIC_LIBRARIES:
                logger.error("[search_music] MUSIC_LIBRARY not configured")
                return {"error": "MUSIC_LIBRARY not configured in .env"}

            keyword_lower = keyword.lower().strip()
            logger.info(f"[search_music] Searching for: '{keyword_lower}'")
            results = []
            total_scanned = 0
            total_directories = 0

            for library in MUSIC_LIBRARIES:
                logger.info(f"[search_music] --- Processing library: {library} ---")
                base_path = Path(library)
                logger.debug(f"[search_music] Base path resolved to: {base_path}")
                logger.debug(f"[search_music] Path exists: {base_path.exists()}")
                logger.debug(f"[search_music] Is directory: {base_path.is_dir() if base_path.exists() else 'N/A'}")

                if not base_path.exists():
                    logger.warning(f"[search_music] Library path does not exist: {library}")
                    continue

                library_file_count = 0
                library_match_count = 0
                library_dir_count = 0

                try:
                    for file_path in base_path.rglob("*"):
                        total_scanned += 1

                        if file_path.is_dir():
                            total_directories += 1
                            library_dir_count += 1
                            if library_dir_count <= 5:
                                logger.debug(f"[search_music] Found directory: {file_path.name}")
                            continue

                        if file_path.is_file() and file_path.suffix.lower() in AUDIO_EXTENSIONS:
                            library_file_count += 1
                            stem = file_path.stem.lower()

                            if library_file_count <= 10:
                                logger.debug(f"[search_music] Audio file #{library_file_count}: stem='{stem}', ext='{file_path.suffix.lower()}'")

                            if keyword_lower in stem:
                                rel_path = file_path.relative_to(base_path)
                                results.append(
                                    {
                                        "name": file_path.stem,
                                        "filename": file_path.name,
                                        "path": str(rel_path),
                                        "library": library,
                                        "size_mb": round(file_path.stat().st_size / (1024 * 1024), 2),
                                    }
                                )
                                library_match_count += 1
                                logger.info(f"[search_music] MATCH #{library_match_count}: '{file_path.name}' at '{rel_path}'")

                    logger.info(
                        f"[search_music] Library '{library}' summary: scanned {total_scanned} items, "
                        f"{library_file_count} audio files, {library_match_count} matches"
                    )
                except PermissionError as exc:
                    logger.error(f"[search_music] Permission denied accessing {library}: {exc}")
                except Exception as exc:
                    logger.error(f"[search_music] Error scanning library {library}: {exc}")
                    logger.error(traceback.format_exc())

            results.sort(key=lambda item: item["path"])

            logger.info("[search_music] ========== SEARCH COMPLETE ==========")
            logger.info(f"[search_music] Total scanned: {total_scanned} items ({total_directories} directories)")
            logger.info(f"[search_music] Total matches: {len(results)}")
            logger.info(f"[search_music] Returning top {min(50, len(results))} results")

            return {"keyword": keyword, "count": len(results), "files": results[:50]}
        except Exception as exc:
            logger.error(f"[search_music] FATAL ERROR: {exc}")
            logger.error(traceback.format_exc())
            return {"error": str(exc), "keyword": keyword, "count": 0, "files": []}
