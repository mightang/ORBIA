# animations/tile_reveal.py
import math
import pygame

from core.hexmath import axial_to_pixel, hex_corners  # 헥스 좌표 → 픽셀 변환 :contentReference[oaicite:0]{index=0}
from settings import COL_COVERED                      # 덮인 타일 색상 :contentReference[oaicite:1]{index=1}


class TileRevealAnim:
    """
    단일 타일에 대한 '중앙에서부터 원형으로 사라지는' 애니메이션.
    - elapsed: 시작 후 경과 시간
    - duration: 한 타일이 완전히 열리는 데 걸리는 시간(초)
    - delay: 애니메이션 시작까지의 대기 시간(초)
    """
    __slots__ = ("q", "r", "elapsed", "duration", "delay", "finished")

    def __init__(self, q, r, duration: float = 0.25, delay: float = 0.0):
        self.q = int(q)
        self.r = int(r)
        self.elapsed = 0.0
        self.duration = float(duration)
        self.delay = float(delay)
        self.finished = False

    @property
    def progress(self) -> float:
        if self.duration <= 0:
            return 1.0

        # delay 이전에는 진행도 0
        if self.elapsed <= self.delay:
            return 0.0

        t = (self.elapsed - self.delay) / self.duration
        if t < 0.0:
            return 0.0
        if t > 1.0:
            return 1.0
        return t

    def update(self, dt: float):
        if self.finished:
            return
        self.elapsed += dt
        if self.elapsed >= self.delay + self.duration:
            self.finished = True



def _draw_single_reveal(surface: pygame.Surface,
                        anim: TileRevealAnim,
                        board_center,
                        hex_size: int):
    """
    실제 그리기:
    1) 현재 타일 위치 주변에 작은 서피스를 하나 만들고
    2) 그 위에 '덮인 타일 색(COL_COVERED)' 육각형을 그림
    3) 중앙에서부터 투명한 원(circle)을 BLEND_RGBA_MIN으로 뚫어 줌
    4) 결과를 메인 surface에 blit
    """
    if anim.finished:
        return

    # 진행도 (0.0 ~ 1.0)
    t = anim.progress

    cx, cy = board_center
    tx, ty = axial_to_pixel(anim.q, anim.r, hex_size)
    tx += cx
    ty += cy

    # 해당 타일 육각형 좌표
    corners = hex_corners((tx, ty), hex_size - 1)

    min_x = int(min(p[0] for p in corners)) - 2
    max_x = int(max(p[0] for p in corners)) + 2
    min_y = int(min(p[1] for p in corners)) - 2
    max_y = int(max(p[1] for p in corners)) + 2

    w = max_x - min_x
    h = max_y - min_y
    if w <= 0 or h <= 0:
        return

    local_center = (tx - min_x, ty - min_y)
    local_corners = [(x - min_x, y - min_y) for (x, y) in corners]

    overlay = pygame.Surface((w, h), pygame.SRCALPHA)

    # 1) 전체 육각형을 '덮인 타일' 색으로 채움 (완전히 덮인 상태)
    pygame.draw.polygon(overlay, (*COL_COVERED, 255), local_corners)

    # 2) 육각형 기준 최대 반지름 계산
    max_r = 0.0
    lx0, ly0 = local_center
    for (lx, ly) in local_corners:
        d = math.hypot(lx - lx0, ly - ly0)
        if d > max_r:
            max_r = d
    if max_r <= 0.0:
        return

    # 3) 현재 프레임의 구멍 반지름 (0 → max_r)
    radius = int(max_r * t)
    if radius > 0:
        # 중앙에서부터 투명한 원으로 뚫기:
        # 1) hole 서피스를 만들고
        # 2) 그 위에 알파 255짜리 원을 그림
        # 3) overlay에 BLEND_RGBA_SUB로 빼서, 해당 영역의 알파를 0으로 만듦
        hole = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.circle(
            hole,
            (0, 0, 0, 255),  # rgba: 알파 255
            (int(local_center[0]), int(local_center[1])),
            radius,
        )
        overlay.blit(hole, (0, 0), special_flags=pygame.BLEND_RGBA_SUB)

    # 4) 메인 surface에 블릿
    surface.blit(overlay, (min_x, min_y))


def draw_reveal_anims(surface: pygame.Surface,
                      anims,
                      board_center,
                      hex_size: int):
    """
    현재 살아있는 TileRevealAnim들을 한 번에 그려주는 헬퍼.
    GameplayScene.draw에서 draw_board 이후에 호출하면 된다.
    """
    for anim in anims:
        if not anim.finished:
            _draw_single_reveal(surface, anim, board_center, hex_size)