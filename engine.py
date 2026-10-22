import weakref
import math
from pyray import *

PI = math.pi


# ---------------------------------------------------------------- helpers
def is_color(v):
    return all(hasattr(v, c) for c in "rgba") or (isinstance(v, (tuple, list)) and len(v) == 4)

def as_color(v):
    return v if hasattr(v, "r") else Color(*v)
def is_vec2(v):
    return hasattr(v, "x") and hasattr(v, "y")

def clamp255(v):
    return max(0, min(255, int(v)))

def rgba(r, g, b, a=255):
    return Color(int(r), int(g), int(b), int(a))

def lerp(a, b, t):
    if is_color(a) or is_color(b):
        # accept tuples like (255, 0, 0, 255) on either side
        if not is_color(a): a = Color(*a)
        if not is_color(b): b = Color(*b)
        return Color(clamp255(lerp(a.r, b.r, t)),
                     clamp255(lerp(a.g, b.g, t)),
                     clamp255(lerp(a.b, b.b, t)),
                     clamp255(lerp(a.a, b.a, t)))
    if is_vec2(a) or is_vec2(b):
        if not is_vec2(a): a = Vector2(*a)
        if not is_vec2(b): b = Vector2(*b)
        return Vector2(lerp(a.x, b.x, t), lerp(a.y, b.y, t))
    if isinstance(a, (tuple, list)):
        return tuple(lerp(x, y, t) for x, y in zip(a, b))
    return a + (b - a) * t

def add(a, b):
    if is_color(a):
        return Color(clamp255(a.r + b.r), clamp255(a.g + b.g),
                     clamp255(a.b + b.b), clamp255(a.a + b.a))
    if is_vec2(a):
        return Vector2(a.x + b.x, a.y + b.y)
    return a + b

def mul(a, k):
    if is_vec2(a):
        return Vector2(a.x * k, a.y * k)
    return a * k

def rotate_point(p, angle):
    c, s = math.cos(angle), math.sin(angle)
    return Vector2(p.x * c - p.y * s, p.x * s + p.y * c)
# ---------------------------------------------------------------- easings

# ---------------------------------------------------------------- animations
# ---------------------------------------------------------------- animations
class Animation:
    def __init__(self, duration, ease=lambda t: t, delay=0.0):
        self.duration = duration
        self.ease = ease or (lambda t: t)    # None from Lua falls back to linear
        self._delay = delay
        self.elapsed = 0.0
        self._wait = delay
        self._started = False
        self.cancelled = False
        self.on_finish = None    # settable after construction: anim.on_finish = fn

    @property
    def total(self):
        """Delay plus duration: how long until this animation is fully done."""
        return self._delay + self.duration

    def delay(self, seconds):
        """Chainable: circle.move_to(pos, 1).delay(0.5)"""
        self._delay = self._wait = seconds
        return self

    def begin(self):
        """Called by Scene.play (and groups). Resets state; starts now if there's no delay."""
        self.elapsed = 0.0
        self._wait = self._delay
        self._started = False
        self.cancelled = False
        if self._wait <= 0:
            self.start()
            self._started = True

    def start(self): pass
    def apply(self, t): pass
    def targets(self, obj): return False

    def cancel_for(self, obj):
        if self.targets(obj):
            self.cancelled = True

    def _tick_delay(self, dt):
        if self._wait > 0:
            self._wait -= dt
            if self._wait > 0:
                return None
            dt = -self._wait
            self._wait = 0.0
        return dt

    def update(self, dt):
        dt = self._tick_delay(dt)
        if dt is None:
            return False
        if not self._started:
            self.start()
            self._started = True
        self.elapsed += dt
        k = 1.0 if self.duration <= 0 else min(1.0, self.elapsed / self.duration)
        self.apply(self.ease(k))
        done = k >= 1.0
        if done and self.on_finish:
            self.on_finish()
        return done


class Tween(Animation):
    def __init__(self, obj, attr, to, duration, ease=lambda t: t, mode="to"):
        super().__init__(duration, ease)
        self.obj, self.attr, self.to, self.mode = obj, attr, to, mode

    def start(self):
        self.frm = getattr(self.obj, self.attr)
        if self.mode == "by":
            self.target = add(self.frm, self.to)
        elif self.mode == "scale":
            self.target = mul(self.frm, self.to)
        else:
            self.target = self.to

    def apply(self, t):
        setattr(self.obj, self.attr, lerp(self.frm, self.target, t))

    def targets(self, obj):
        return self.obj is obj


class Fade(Animation):
    def __init__(self, obj, to_alpha, duration, ease=lambda t: t, from_alpha=None):
        super().__init__(duration, ease)
        self.obj, self.to_alpha, self.from_alpha = obj, to_alpha, from_alpha

    def start(self):
        c = as_color(self.obj.color)
        self.frm = c.a if self.from_alpha is None else self.from_alpha
        self.obj.color = Color(c.r, c.g, c.b, clamp255(self.frm))

    def apply(self, t):
        c = as_color(self.obj.color)
        a = clamp255(lerp(self.frm, self.to_alpha, t))
        self.obj.color = Color(c.r, c.g, c.b, a)

    def targets(self, obj):
        return self.obj is obj


class Kill(Animation):
    def __init__(self, scene, obj):
        super().__init__(0)
        self.scene, self.obj = scene, obj

    def start(self):
        self.scene.kill_object(self.obj)


class Parallel(Animation):
    def __init__(self, *anims):
        super().__init__(max((a.total for a in anims), default=0))
        self.anims = list(anims)
        self._live = []

    def start(self):
        for a in self.anims:
            a.begin()
        self._live = list(self.anims)

    def update(self, dt):
        dt = self._tick_delay(dt)
        if dt is None:
            return False
        if not self._started:
            self.start()
            self._started = True
        self._live = [a for a in self._live if not a.cancelled and not a.update(dt)]
        done = not self._live
        if done and self.on_finish:
            self.on_finish()
        return done

    def cancel_for(self, obj):
        for a in self.anims:
            a.cancel_for(obj)


class Sequence(Animation):
    def __init__(self, *anims):
        super().__init__(sum(a.total for a in anims))
        self.anims = list(anims)
        self.i = 0

    def start(self):
        self.i = 0
        if self.anims:
            self.anims[0].begin()

    def update(self, dt):
        dt = self._tick_delay(dt)
        if dt is None:
            return False
        if not self._started:
            self.start()
            self._started = True
        while self.i < len(self.anims):
            a = self.anims[self.i]
            if not a.cancelled and not a.update(dt):
                return False
            self.i += 1
            if self.i < len(self.anims):
                self.anims[self.i].begin()
            dt = 0
        if self.on_finish:
            self.on_finish()
        return True

    def cancel_for(self, obj):
        for a in self.anims:
            a.cancel_for(obj)


class Repeat(Animation):
    def __init__(self, anim, times=None):
        total = 0 if times is None else times * anim.total
        super().__init__(total)
        self.anim = anim
        self.times = times
        self.count = 0

    def start(self):
        self.anim.begin()

    def update(self, dt):
        if not self._started:
            self.start()
            self._started = True
        if self.anim.update(dt):
            self.count += 1
            if self.times is not None and self.count >= self.times:
                if self.on_finish:
                    self.on_finish()
                return True
            self.anim.begin()
        return False

    def cancel_for(self, obj):
        self.anim.cancel_for(obj)
# ---------------------------------------------------------------- shapes
class Shape:
    instances = weakref.WeakSet()      # shared by all subclasses
    size_attr = None
    def __init__(self):
        Shape.instances.add(self)
        self.color = BLACK
        self.rotation = 0.0            # on every shape, so rotate works on circles too
        # Shape.__init__
        self.filled = True
        self.stroke_width = 0.002
        self.z=0
    # absolute
    def move_to(self, position, time, ease=lambda t: t):
        return Tween(self, "position", position, time, ease)
    def rotate_to(self, rotation, time, ease=lambda t: t):
        return Tween(self, "rotation", rotation, time, ease)
    def resize_to(self, value, time, ease=lambda t: t):
        return Tween(self, self.size_attr, value, time, ease)
    def recolor_to(self, color, time, ease=lambda t: t):
        return Tween(self, "color", color, time, ease)

    # relative (add to the value at start)
    def move_by(self, delta, time, ease=lambda t: t):
        return Tween(self, "position", delta, time, ease, mode="by")
    def rotate_by(self, angle, time, ease=lambda t: t):
        return Tween(self, "rotation", angle, time, ease, mode="by")
    def resize_by(self, amount, time, ease=lambda t: t):
        return Tween(self, self.size_attr, amount, time, ease, mode="by")
    def recolor_by(self, delta, time, ease=lambda t: t):
        return Tween(self, "color", delta, time, ease, mode="by")

    # relative (multiply the value at start)
    def scale_by(self, factor, time, ease=lambda t: t):
        return Tween(self, self.size_attr, factor, time, ease, mode="scale")

    # fades (alpha only)
    def fade_in(self, time, ease=lambda t: t, alpha=255):
        return Fade(self, alpha, time, ease, from_alpha=0)
    def fade_out(self, time, ease=lambda t: t):
        return Fade(self, 0, time, ease)
    def fade_to(self, alpha, time, ease=lambda t: t):
        return Fade(self, alpha, time, ease)


class Circle(Shape):
    size_attr = "r"
    def __init__(self, position, r):
        super().__init__()
        self.position = position
        self.r = r


class Square(Shape):
    size_attr = "size"
    def __init__(self, position, size):
        super().__init__()
        self.position = position
        self.size = size
        self.anchor=Vector2(0.5,0.5)
class Rect(Shape):
    size_attr = "size"
    def __init__(self, position, size):
        super().__init__()
        self.position = position
        self.size = size
        self.anchor=Vector2(0.5,0.5)
class Line(Shape):
    size_attr = "length"
    def __init__(self, position,length,stroke_width):
        super().__init__()
        self.position = position
        self.length=length
        self.stroke_width=stroke_width
        self.anchor=0.5

# ---------------------------------------------------------------- scene
class Scene:
    def __init__(self):
        self.objects = []
        self.active_anims = []
        self.time_scale = 1.0
        self.paused = False

    def spawn_object(self, obj):
        self.objects.append(obj)
        return obj

    def spawn(self, cls, *args, **kwargs):
        obj = cls(*args, **kwargs)     # call the class to make an instance
        self.objects.append(obj)
        return obj

    def kill_object(self, obj):
        """Remove obj from the scene and cancel animations targeting it."""
        self.objects = [o for o in self.objects if o is not obj]
        for a in self.active_anims:
            a.cancel_for(obj)          # flagged, not removed, so it's safe mid-update
        return obj

    def kill_all(self, cls=None):
        """Remove everything, or everything of one class (e.g. Circle)."""
        doomed = [o for o in self.objects if cls is None or isinstance(o, cls)]
        for o in doomed:
            self.kill_object(o)
        return len(doomed)

    def play(self, *anims):
        for a in anims:
            a.begin()
            self.active_anims.append(a)
        return max((a.total for a in anims), default=0)   # how long Lua should wait

    def update(self, dt):
        if self.paused:
            return
        dt *= self.time_scale
        alive = []
        for a in list(self.active_anims):
            if a.cancelled:
                continue
            if not a.update(dt):
                alive.append(a)
        self.active_anims = [a for a in alive if not a.cancelled]

    def count(self, cls):
        return sum(isinstance(o, cls) for o in self.objects)