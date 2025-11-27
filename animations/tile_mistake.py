# animations/tile_mistake.py
import math
import pygame

from core.hexmath import axial_to_pixel, hex_corners
from settings import COL_MINE


# 흔들림 기본 주파수(크게 할수록 더 떨림이 촘촘해짐)
SHAKE_FREQ = 28.0  # rad/sec 정도 느낌


class TileShakeAnim:
    """
    '실수한 타일'이 제자리에서 살짝 떨리는 애니메이션.
    - duration: 전체 재생 시간(초)
    - amplitude: 흔들림 세기(픽셀)
    """
    __slots__ = ("q", "r", "elapsed", "duration", "amplitude", "finished")

    def __init__(self, q, r, duration: float = 0.25, amplitude: float = 5.0):
        self.q = int(q)
        self.r = int(r)
        self.elapsed = 0.0
        self.duration = float(duration)
        self.amplitude = float(amplitude)
        self.finished = False

    @property
    def progress(self) -> float:
        if self.duration <= 0:
            return 1.0
        t = self.elapsed / self.duration
        if t < 0.0:
            return 0.0
        if t > 1.0:
            return 1.0
        return t

    def update(self, dt: float):
        if self.finished:
            return
        self.elapsed += dt
        if self.elapsed >= self.duration:
            self.finished = True


def _draw_single_shake(surface: pygame.Surface,
                       anim: TileShakeAnim,
                       board_center,
                       hex_size: int):
        if anim.finished:
            return

        cx, cy = board_center
        tx, ty = axial_to_pixel(anim.q, anim.r, hex_size)
        tx += cx
        ty += cy

        # 진행도에 따라 감쇠되는 흔들림
        p = anim.progress
        # 끝으로 갈수록 진폭이 줄어들도록 (linear falloff)
        amp = anim.amplitude * (1.0 - p)

        # 간단한 사인파 기반 좌우/상하 흔들림
        phase = anim.elapsed * SHAKE_FREQ
        dx = math.sin(phase) * amp
        dy = math.sin(phase * 1.7) * amp * 0.4

        jitter_center = (tx + dx, ty + dy)
        corners = hex_corners(jitter_center, hex_size - 1)

        min_x = int(min(x for x, y in corners)) - 3
        max_x = int(max(x for x, y in corners)) + 3
        min_y = int(min(y for x, y in corners)) - 3
        max_y = int(max(y for x, y in corners)) + 3

        w = max_x - min_x
        h = max_y - min_y
        if w <= 0 or h <= 0:
            return

        local_corners = [(x - min_x, y - min_y) for (x, y) in corners]
        overlay = pygame.Surface((w, h), pygame.SRCALPHA)

        # COL_MINE은 RGB만 들어 있으니까 알파 추가
        r, g, b = COL_MINE
        border_color = (r, g, b, 230)

        # 살짝 두꺼운 붉은 테두리만 그려서 "타일이 떨리는 느낌" 내기
        pygame.draw.polygon(overlay, (0, 0, 0, 0), local_corners)
        pygame.draw.polygon(overlay, border_color, local_corners, width=3)

        surface.blit(overlay, (min_x, min_y))


def draw_shake_anims(surface: pygame.Surface,
                     anims,
                     board_center,
                     hex_size: int):
    """
    실수 애니메이션 전부 그려 주는 헬퍼.
    GameplayScene.draw에서 draw_board 이후에 호출하면 된다.
    """
    for anim in anims:
        if not anim.finished:
            _draw_single_shake(surface, anim, board_center, hex_size)