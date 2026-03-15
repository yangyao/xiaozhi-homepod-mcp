from tools.devices import register as register_devices_tools
from tools.library import register as register_library_tools
from tools.next_track import register as register_next_track_tool
from tools.now_playing import register as register_now_playing_tool
from tools.pause import register as register_pause_tool
from tools.play import register as register_play_tool
from tools.play_album import register as register_play_album_tool
from tools.previous_track import register as register_previous_track_tool
from tools.scan_devices import register as register_scan_devices_tool
from tools.stop import register as register_stop_tool
from tools.stream_file import register as register_stream_file_tool
from tools.volume import register as register_volume_tools


def register_tools(mcp) -> None:
    register_devices_tools(mcp)
    register_scan_devices_tool(mcp)
    register_play_tool(mcp)
    register_pause_tool(mcp)
    register_stop_tool(mcp)
    register_volume_tools(mcp)
    register_now_playing_tool(mcp)
    register_next_track_tool(mcp)
    register_previous_track_tool(mcp)
    register_library_tools(mcp)
    register_stream_file_tool(mcp)
    register_play_album_tool(mcp)
