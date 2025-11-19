import math

SQRT3 = math.sqrt(3) # 3의 제곱근

# 픽셀 변환
def axial_to_pixel(q, r, size):
    x = size * (1.5 * q)
    y = size * (SQRT3 * (r + q * 0.5))
    return (x, y)

def pixel_to_axial(x, y, size):
    q = (2.0 / 3.0 * x) / size
    r = ((-1.0 / 3.0) * x + (SQRT3 / 3.0) * y) / size
    cx, cy, cz = cube_round(axial_to_cube(q, r))
    aq, ar = cube_to_axial(cx, cy, cz)
    return (aq, ar)

def axial_to_cube(q, r):
    x = q
    z = r
    y = -x - z
    return (x, y, z)

def cube_to_axial(x, y, z):
    return (x, z)

def cube_round(cube):
    (x, y, z) = cube
    rx, ry, rz = round(x), round(y), round(z)
    dx, dy, dz = abs(rx - x), abs(ry - y), abs(rz - z)
    if dx > dy and dx > dz:
        rx = -ry - rz
    elif dy > dz:
        ry = -rx - rz
    else:
        rz = -rx - ry
    return (rx, ry, rz)

def hex_corners(center_xy, size):
    cx, cy = center_xy
    corners = []
    for i in range(6):
        angle = math.radians(60 * i)
        corners.append((cx + size * math.cos(angle), cy + size * math.sin(angle)))
    return corners