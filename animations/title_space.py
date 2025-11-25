# animations/title_space.py
import math
import random
import pygame
from core.hexmath import hex_corners


class TitleBackground:
    """
    미니멀 우주 느낌 타이틀용 배경.
    - 세로 그라디언트
    - 여러 레이어의 별
    - 중앙 위쪽 헥사곤 링
    """
    def __init__(self, size, num_stars=80):
        self.w, self.h = size
        self.num_stars = num_stars
        self.time = 0.0
        self.stars = []
        self._make_gradient()
        self._init_stars()

    def resize(self, size):
        self.w, self.h = size
        self._make_gradient()
        self._init_stars()

    def _make_gradient(self):
        self.bg = pygame.Surface((self.w, self.h))
        for y in range(self.h):
            t = y / max(1, self.h - 1)
            r = int(6 + 10 * t)
            g = int(10 + 25 * t)
            b = int(20 + 55 * t)
            pygame.draw.line(self.bg, (r, g, b), (0, y), (self.w, y))

    def _init_stars(self):
        self.stars = []
        for _ in range(self.num_stars):
            layer = random.choice([0, 1, 2])
            if layer == 0:
                speed = random.uniform(8, 18)
                radius = 1
                alpha = 80
            elif layer == 1:
                speed = random.uniform(15, 30)
                radius = 1.5
                alpha = 120
            else:
                speed = random.uniform(25, 40)
                radius = 2
                alpha = 180

            x = random.uniform(0, self.w)
            y = random.uniform(0, self.h)
            self.stars.append({
                "x": x,
                "y": y,
                "speed": speed,
                "radius": radius,
                "alpha": alpha,
            })

    def update(self, dt):
        self.time += dt
        for s in self.stars:
            s["y"] += s["speed"] * dt
            if s["y"] > self.h:
                s["y"] -= self.h
                s["x"] = random.uniform(0, self.w)

    def draw(self, surf):
        # 배경 그라디언트
        surf.blit(self.bg, (0, 0))

        # 별
        star_surf = pygame.Surface((self.w, self.h), pygame.SRCALPHA)
        for s in self.stars:
            flicker = 0.5 + 0.5 * math.sin(self.time * 2.0 + s["x"] * 0.01)
            alpha = int(s["alpha"] * (0.7 + 0.3 * flicker))
            color = (230, 238, 255, max(40, min(255, alpha)))
            pygame.draw.circle(
                star_surf,
                color,
                (int(s["x"]), int(s["y"])),
                int(s["radius"])
            )
        surf.blit(star_surf, (0, 0))

        # 중앙 헥사곤 링
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