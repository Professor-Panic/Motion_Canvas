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
    local line = Line(Vector2(0.5, 0.5), 1.0, 0.005)
    line.color = WHITE
    line.z = 1
    Scene.spawn_object(line)

    local spin = Repeat(line.rotate_by(TAU/2, 1.0), 5)
    spin.on_finish = function() line.color = BLUE end
    Play(spin)

    local circle = Circle(Vector2(0.5, 0.5), 0.05)
    circle.color = RED
    circle.z = 2
    Scene.spawn_object(circle)

    local grow = Parallel(circle.resize_to(0.15, 1.5, EaseOutBounce), circle.fade_in(1.5))
    grow.on_finish = function() circle.color = GREEN end
    Play(grow)

    Wait(1.5)

    local moves = Sequence(
        circle.move_to(Vector2(0.2, 0.2), 1.0),
        circle.move_to(Vector2(0.8, 0.2), 1.0),
        circle.move_to(Vector2(0.5, 0.8), 1.0)
    )
    moves.on_finish = function() circle.color = BLUE end
    Play(moves)
end