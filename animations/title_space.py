# animations/title_space.py
import math
import random
import pygame
from core.hexmath import hex_corners


class TitleBackground:
    """
    미니멀 우주 느낌 타이틀용 배경.
    - 세로 그라디언트
    - 제자리에서 깜빡이는 별
    - 중앙 위쪽 헥사곤 링(옵션)
    """
    def __init__(self, size, num_stars=160, show_hex=True):
        self.w, self.h = size
        self.num_stars = num_stars
        self.show_hex = show_hex

        self.time = 0.0
        self.stars = []

        self._make_gradient()
        self._init_stars()

    # 해상도 바뀔 때 호출
    def resize(self, size):
        self.w, self.h = size
        self._make_gradient()
        self._init_stars()   # 화면 크기에 맞게 별 재배치

    # 배경 세로 그라디언트
    def _make_gradient(self):
        self.bg = pygame.Surface((self.w, self.h))
        for y in range(self.h):
            t = y / max(1, self.h - 1)
            r = int(6 + 10 * t)
            g = int(10 + 25 * t)
            b = int(20 + 55 * t)
            pygame.draw.line(self.bg, (r, g, b), (0, y), (self.w, y))

    # 별 초기화 (위치는 고정, 밝기만 깜빡이게)
    def _init_stars(self):
        self.stars = []
        for _ in range(self.num_stars):
            layer = random.choice([0, 1, 2])

            if layer == 0:
                radius = 1
                base_alpha = 70
            elif layer == 1:
                radius = 1.5
                base_alpha = 120
            else:
                radius = 2
                base_alpha = 190

            x = random.uniform(0, self.w)
            y = random.uniform(0, self.h)

            flicker_speed = random.uniform(0.8, 1.6)   # 별마다 다른 깜빡임 속도
            phase = random.uniform(0, math.tau)        # 시작 위상 다르게

            self.stars.append({
                "x": x,
                "y": y,
                "radius": radius,
                "base_alpha": base_alpha,
                "flicker_speed": flicker_speed,
                "phase": phase,
            })

    # 프레임별 업데이트 (별 위치는 안 움직이고, 시간만 흐름)
    def update(self, dt):
        self.time += dt

    # 별 그리기
    def _draw_stars(self, surf):
        star_surf = pygame.Surface((self.w, self.h), pygame.SRCALPHA)
        for s in self.stars:
            flicker = 0.5 + 0.5 * math.sin(
                self.time * 2.0 * s["flicker_speed"] + s["phase"]
            )
            alpha = int(s["base_alpha"] * (0.6 + 0.4 * flicker))
            color = (230, 238, 255, max(30, min(255, alpha)))

            pygame.draw.circle(
                star_surf,
                color,
                (int(s["x"]), int(s["y"])),
                int(s["radius"])
            )
        surf.blit(star_surf, (0, 0))

    # 중앙 헥사곤 장식 링
    def _draw_hex_ring(self, surf):
        overlay = pygame.Surface((self.w, self.h), pygame.SRCALPHA)
        cx, cy = self.w // 2, int(self.h * 0.32)

        base_radius = min(self.w, self.h) * 0.12
        radii = [base_radius * r for r in (0.9, 1.2, 1.5)]

        for i, r in enumerate(radii):
            pulse = 0.5 + 0.5 * math.sin(self.time * 0.9 + i * 1.4)
            alpha = int(40 + 40 * pulse)
            width = 1 + int(1 * pulse)
            color = (140, 180, 255, alpha)
            pts = hex_corners((cx, cy), r)
            pygame.draw.polygon(overlay, color, pts, width=width)

        surf.blit(overlay, (0, 0))

    # 최종 그리기
    def draw(self, surf):
        # 배경 그라디언트
        surf.blit(self.bg, (0, 0))

        # 별
        self._draw_stars(surf)

        # 중앙 헥사곤 장식 (옵션)
        if self.show_hex:
            self._draw_hex_ring(surf)