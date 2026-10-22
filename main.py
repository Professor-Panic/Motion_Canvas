from lupa import LuaRuntime,LuaError
import raylib as rl
from loader import *
from pyray import *
lua=Load_Lua()
lua.execute(Path(__file__).with_name("prelude.lua").read_text(encoding="utf-8"))
load_script(lua=lua,path="test.lua")

g=lua.globals()
def draw_rect_lines_rotated(px, py, w, h, origin, rotation_rad, thickness, color):
    local_corners = [Vector2(0, 0), Vector2(w, 0), Vector2(w, h), Vector2(0, h)]
    pts = []
    for c in local_corners:
        rel = Vector2(c.x - origin.x, c.y - origin.y)
        r = rotate_point(rel, rotation_rad)
        pts.append(Vector2(px + r.x, py + r.y))

    half = thickness / 2.0
    for i in range(4):
        a = pts[i]
        b = pts[(i + 1) % 4]
        dx, dy = b.x - a.x, b.y - a.y
        length = math.hypot(dx, dy)
        if length == 0:
            continue
        ux, uy = dx / length, dy / length
        ext_a = Vector2(a.x - ux * half, a.y - uy * half)
        ext_b = Vector2(b.x + ux * half, b.y + uy * half)
        draw_line_ex(ext_a, ext_b, thickness, color)
def Draw_Scene_Objects(scene, width, height):
    m = min(width, height)
    for obj in sorted(scene.objects,key=lambda obj:obj.z):
        px, py = obj.position.x * width, obj.position.y * height
        if isinstance(obj, Circle):
            if obj.filled:
                draw_circle_v(Vector2(px, py), obj.r * m / 2, obj.color)
            else:
                draw_circle_lines_v(Vector2(px, py), int(obj.r * m / 2), obj.color)
        elif isinstance(obj, Square):
            side = obj.size * m
            origin = Vector2(side * obj.anchor.x, side * obj.anchor.y)
            if obj.filled:
                draw_rectangle_pro(
                    Rectangle(px, py, side, side),
                    origin,
                    obj.rotation * 360 / (2 * math.pi),
                    obj.color,
                )
            else:
                draw_rect_lines_rotated(px, py, side, side, origin, obj.rotation, obj.stroke_width * m, obj.color)

        elif isinstance(obj, Rect):
            side = Vector2(obj.size.x * width, obj.size.y * height)
            origin = Vector2(side.x * obj.anchor.x, side.y * obj.anchor.y)
            if obj.filled:
                draw_rectangle_pro(
                    Rectangle(px, py, side.x, side.y),
                    origin,
                    obj.rotation * 360 / (2 * math.pi),
                    obj.color,
                )
            else:
                draw_rect_lines_rotated(px, py, side.x, side.y, origin, obj.rotation, obj.stroke_width * m, obj.color)
                
        elif isinstance(obj, Line):
            offset = obj.length * m * obj.anchor
            start = Vector2(px - math.cos(obj.rotation) * offset,
                            py - math.sin(obj.rotation) * offset)
            end = Vector2(start.x + math.cos(obj.rotation) * obj.length * m,
                        start.y + math.sin(obj.rotation) * obj.length * m)
            draw_line_ex(start, end, obj.stroke_width * m, obj.color)
class Runner:
    def __init__(self, func):
        self.co = func.coroutine()         # lupa wraps a Lua function as a coroutine
        self.wait = 0.0
        self.done = False

    def update(self, dt):
        if self.done:
            return
        self.wait -= dt
        if self.wait <= 0:
            try:
                self.wait = next(self.co) or 0.0   # runs Lua until next yield
            except StopIteration:
                self.done = True
            except LuaError as e:
                import traceback
                print("Lua error:", e, e.args)
                traceback.print_exc()
                raise

runner = Runner(g.Main)
def run():
    init_window(1200,800,"Motion_Engine")
    set_target_fps(60)
    while not window_should_close():
        dt=get_frame_time()
        g.Scene.update(dt)
        if is_key_pressed(rl.KEY_SPACE):
            g.Scene.paused=not g.Scene.paused
        runner.update(dt)
        rl.BeginDrawing()
        rl.ClearBackground(BLACK)
        Draw_Scene_Objects(g.Scene,1200,800)
        draw_fps(20,20)
        rl.EndDrawing()
    close_window()
run()