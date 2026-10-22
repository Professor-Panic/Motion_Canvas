from lupa import LuaRuntime,LuaError
import raylib as rl
from loader import *
from pyray import *
lua=Load_Lua()
lua.execute(Path(__file__).with_name("prelude.lua").read_text(encoding="utf-8"))
load_script(lua=lua,path="test.lua")

g=lua.globals()
def Draw_Scene_Objects(scene, width, height):
    m = min(width, height)
    for obj in sorted(scene.objects,key=lambda obj:obj.z):
        px, py = obj.position.x * width, obj.position.y * height
        if isinstance(obj, Circle):
            draw_circle_v(Vector2(px, py), obj.r * m / 2, obj.color)
        elif isinstance(obj, Square):
            side = obj.size * m
            origin = Vector2(side * obj.anchor.x, side * obj.anchor.y)
            draw_rectangle_pro(
                Rectangle(px, py, side, side),     # x, y = where the origin point lands on screen
                Vector2(side / 2, side / 2),       # origin in pixels, relative to the rect's top-left
                obj.rotation*360/(2*math.pi),                      # degrees
                obj.color,
            )
        elif isinstance(obj, Rect):
            side =Vector2(obj.size.x*width,obj.size.y*height)
            origin = Vector2(side * obj.anchor.x, side * obj.anchor.y)
            draw_rectangle_pro(
                Rectangle(px, py,side.x,side.y),     # x, y = where the origin point lands on screen
                origin,       # origin in pixels, relative to the rect's top-left
                obj.rotation*360/(2*math.pi),                      # degrees
                obj.color,
            )
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
    rl.InitWindow(1200,800,"Motion_Engine")
    set_target_fps(60)
    while not window_should_close():
        dt=get_frame_time()
        g.Scene.update(dt)
        if is_key_pressed(rl.KEY_SPACE):
            g.Scene.paused=not g.Scene.paused
        runner.update(dt)
        rl.BeginDrawing()
        rl.ClearBackground(rl.BLACK)
        Draw_Scene_Objects(g.Scene,1200,800)
        rl.EndDrawing()
    close_window()
run()