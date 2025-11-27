# animations/tile_hover.py
import pygame
import math

from core.hexmath import axial_to_pixel, hex_corners


class TileHoverAnim:
    """
    마우스를 올렸을 때 타일이 살짝 하얗게 밝아지는 애니메이션.
    - fade_in: 밝기가 0 → max_alpha까지 올라가는 시간(초)
    - max_alpha: 최종 밝기 (0~255, 값이 클수록 더 밝음)
    """
    __slots__ = ("q", "r", "elapsed", "fade_in", "max_alpha")

    def __init__(self, q, r, fade_in: float = 0.12, max_alpha: int = 90):
        self.q = int(q)
        self.r = int(r)
        self.elapsed = 0.0
        self.fade_in = float(fade_in)
        self.max_alpha = int(max_alpha)

    @property
    def progress(self) -> float:
        """0.0 ~ 1.0 사이. fade_in 동안 서서히 1로 올라감."""
        if self.fade_in <= 0:
            return 1.0
        t = self.elapsed / self.fade_in
        if t < 0.0:
            return 0.0
        if t > 1.0:
            return 1.0
        return t

    def update(self, dt: float):
        self.elapsed += dt


def draw_hover_anim(surface: pygame.Surface,
                    anim: TileHoverAnim,
                    board_center,
                    hex_size: int):
    """
    현재 hover 중인 타일 위에 반투명 흰 육각형을 덮어서
    '밝기가 살짝 올라간' 느낌을 만든다.
    """
    cx, cy = board_center

    tx, ty = axial_to_pixel(anim.q, anim.r, hex_size)
    tx += cx
    ty += cy

    corners = hex_corners((tx, ty), hex_size - 2)

    min_x = int(min(x for x, y in corners)) - 2
    max_x = int(max(x for x, y in corners)) + 2
    min_y = int(min(y for x, y in corners)) - 2
    max_y = int(max(y for x, y in corners)) + 2

    w = max_x - min_x
    h = max_y - min_y
    if w <= 0 or h <= 0:
        return

    local_corners = [(x - min_x, y - min_y) for (x, y) in corners]
    overlay = pygame.Surface((w, h), pygame.SRCALPHA)

    # 진행도에 따라 알파가 서서히 0 → max_alpha로
    p = anim.progress
    alpha = max(0, min(255, int(anim.max_alpha * p)))
    color = (255, 255, 255, alpha)

    pygame.draw.polygon(overlay, color, local_corners)

    surface.blit(overlay, (min_x, min_y))