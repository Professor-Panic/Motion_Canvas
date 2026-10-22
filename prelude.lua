function Play(...)
    local args = {...}
    if #args == 1 and type(args[1]) == "table" then
        args = args[1]                      -- a bundle: use its contents
    end
    coroutine.yield(Scene.play(table.unpack(args)))
end

function Wait(seconds)
    coroutine.yield(seconds)
end