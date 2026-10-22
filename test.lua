function Pow(a,b)
    local ans=a;
    if b==0 then
        return 1
    else
        for i=1,b-1 do
            ans=ans*a
        end
        return ans
    end
end
function Play(...)
    local args = {...}
    -- if the only argument is a plain Lua table (a bundle), use its contents
    if #args == 1 and type(args[1]) == "table" then
        args = args[1]
    end
    coroutine.yield(Scene.play(table.unpack(args)))
end
function Wait(seconds)
    coroutine.yield(seconds)
end
local function done()
    print("Done with animations")
end
function Main()
    -- an unfilled square whose stroke_width animates, so the outline visibly thickens
    local square = Square(Vector2(0.3, 0.5), 0.3)
    square.color = WHITE
    square.filled = false
    square.stroke_width = 0.002
    square.z = 1
    Scene.spawn_object(square)

    -- tween stroke_width directly -- it's just an attribute, so Tween handles it for free
    Play(Sequence(
        Tween(square, "stroke_width", 0.05, 1.0),
        Tween(square, "stroke_width", 0.002, 0.5)
    ))

    Wait(3.0)

    -- a rotating outlined rect to confirm draw_rect_lines_rotated tracks rotation correctly
    local rect = Rect(Vector2(0.7, 0.5), Vector2(0.4, 0.2))
    rect.color = GREEN
    rect.filled = false
    rect.stroke_width = 0.01
    rect.z = 2
    Scene.spawn_object(rect)

    Play(Repeat(rect.rotate_by(TAU, 2.0), 3))
end