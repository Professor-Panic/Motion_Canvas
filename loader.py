from pathlib import Path
import json
from lupa import LuaRuntime
from engine import *
from pyray import Vector2,RED,BLUE,WHITE,RAYWHITE,GREEN
from easings import *
def load_script(lua, path):
    p = Path(path).expanduser().resolve()      # works for any path, absolute or relative
    code = p.read_text(encoding="utf-8")
    chunk = lua.eval("function(src, name) return load(src, name) end")(code, "@" + str(p))
    if chunk is None:
        raise RuntimeError(f"could not compile {p}")
    return chunk()                              # runs it and returns whatever the file returns
LUARC_PATH = Path(__file__).parent / ".luarc.json"   # put this next to your .lua scripts

def sync_luarc(names, path=LUARC_PATH):
    """Add the given global names to .luarc.json without touching other settings."""
    try:
        cfg = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        cfg = {}

    existing = set(cfg.get("diagnostics.globals", []))
    merged = sorted(existing | set(names))

    if merged != cfg.get("diagnostics.globals"):     # only write when something changed
        cfg["diagnostics.globals"] = merged
        path.write_text(json.dumps(cfg, indent=4), encoding="utf-8")

def Load_Lua():
    lua = LuaRuntime(unpack_returned_tuples=True)
    g = lua.globals()

    exports = {
        "Circle": Circle,
        "Square": Square,
        "Rect": Rect,
        "Line": Line,
        "Vector2": Vector2,
        "rgba": rgba,
        "EaseOutBounce": ease_out_bounce,
        "EaseInSine": ease_in_sine,
        "EaseInOutQuad": ease_in_out_quad,
        "EaseInCubic": ease_in_cubic,
        "EaseOutCubic": ease_out_cubic,
        "EaseInOutBack": ease_in_out_back,
        "EaseOutElastic": ease_out_elastic,
        "Scene": Scene(),
        "RED": RED,
        "GREEN": GREEN,
        "BLUE": BLUE,
        "WHITE": WHITE,
        "Kill": Kill,
        "PI": math.pi,
        "TAU": 2 * math.pi,
        "Parallel": Parallel,
        "Sequence": Sequence,
        "Repeat": Repeat,
        "Tween":Tween
    }

    for name, value in exports.items():
        g[name] = value

    sync_luarc(exports.keys())
    return lua