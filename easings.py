import math
def ease_in_out_quad(t):
    return 2*t*t if t < 0.5 else 1 - pow(-2*t + 2, 2) / 2

def ease_in_cubic(t):
    return t * t * t

def ease_out_cubic(t):
    return 1 - pow(1 - t, 3)

def ease_in_out_back(t, c=1.70158):
    c2 = c * 1.525
    if t < 0.5:
        return (pow(2*t, 2) * ((c2+1)*2*t - c2)) / 2
    return (pow(2*t-2, 2) * ((c2+1)*(t*2-2)+c2) + 2) / 2

def ease_out_elastic(t):
    c4 = (2 * math.pi) / 3
    if t == 0 or t == 1: return t
    return pow(2, -10*t) * math.sin((t*10-0.75)*c4) + 1
def ease_in_sine(t):
    return 1 - math.cos((t * math.pi) / 2)

def ease_out_bounce(x):
    n1 = 7.5625
    d1 = 2.75
    if x < 1 / d1:
        return n1 * x * x
    elif x < 2 / d1:
        x -= 1.5 / d1
        return n1 * x * x + 0.75
    elif x < 2.5 / d1:
        x -= 2.25 / d1
        return n1 * x * x + 0.9375
    else:
        x -= 2.625 / d1
        return n1 * x * x + 0.984375

