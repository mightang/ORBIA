# animations/game_hex_bg.py
import random
import pygame
from core.hexmath import hex_corners


class GameHexBackground:
    """
    인게임 전용 배경:
    - 검은 바탕 위에
    - 크기 / 투명도 / 속도가 서로 다른 흰색 육각형들이
      아주 천천히 떠다니는 느낌
    - 윤곽선 없이 '흐릿하게 채워진' 육각형만 보이게
    """

    def __init__(self, size, num_hex=40):
        self.size = size  # (w, h)
        self.num_hex = num_hex
        self.hexes = []
        self._init_hexes()

    # -----------------------
    # 육각형 스폰 / 초기화
    # -----------------------
    def _spawn_hex(self, *, from_bottom=False):
        """새 육각형 하나 생성해서 dict로 돌려줌."""
        w, h = self.size

        # 크기/속도/투명도 그룹을 좀 더 세분화 (5단계)
        band = random.random()

        if band < 0.2:
            # 1단계: 아주 작은 육각형 (가장 빠름)
            radius = random.uniform(10, 18)
            speed = random.uniform(14, 24)   # px/sec

        elif band < 0.4:
            # 2단계: 작은 육각형
            radius = random.uniform(18, 28)
            speed = random.uniform(10, 20)

        elif band < 0.6:
            # 3단계: 중간 크기
            radius = random.uniform(28, 42)
            speed = random.uniform(7, 14)

        elif band < 0.8:
            # 4단계: 좀 큰 육각형
            radius = random.uniform(42, 60)
            speed = random.uniform(5, 10)

        else:
            # 5단계: 아주 큰 육각형 (가장 느리고 가장 흐릿해질 대상)
            radius = random.uniform(60, 86)
            speed = random.uniform(3, 7)

        if from_bottom:
            y = random.uniform(h, h + h * 0.5)   # 화면 아래에서 새로 등장
        else:
            y = random.uniform(0, h)

        x = random.uniform(-0.15 * w, 1.15 * w)

        drift = random.uniform(-6, 6)            # 좌우로 아주 살짝만 흐르게

        # 크기에 따라 투명도도 조금 다르게 (큰 애는 더 연하게)
        base_alpha = 120 - int(radius * 0.7) + random.randint(-10, 10)
        alpha = max(30, min(130, base_alpha))

        return {
            "x": x,
            "y": y,
            "r": radius,
            "speed": speed,
            "drift": drift,
            "alpha": alpha,
        }

    def _init_hexes(self):
        self.hexes = [self._spawn_hex() for _ in range(self.num_hex)]

    def resize(self, size):
        """해상도 바뀔 때 전체 재생성."""
        self.size = size
        self._init_hexes()

    # -----------------------
    # 업데이트 / 그리기
    # -----------------------
    def update(self, dt):
        """위로 천천히 떠오르게."""
        w, h = self.size
        for hx in self.hexes:
            hx["y"] -= hx["speed"] * dt
            hx["x"] += hx["drift"] * dt

            # 화면 완전히 벗어나면 다시 스폰
            if hx["y"] + hx["r"] < -20:
                new = self._spawn_hex(from_bottom=True)
                hx.update(new)
            elif hx["x"] < -0.3 * w or hx["x"] > 1.3 * w:
                new = self._spawn_hex()
                hx.update(new)

    def draw(self, surface):
        """검은 배경 + 윤곽선 없는 흐릿한 육각형들 (겹칠수록 더 밝게)."""
        w, h = surface.get_size()

        # 1) 배경
        surface.fill((4, 6, 12))

        # 2) 각 육각형을 '작은 SRCALPHA 서피스'에 그린 뒤,
        #    메인 surface에 하나씩 blit → 겹치는 부분이 실제로 더 밝아짐
        for hx in self.hexes:
            cx, cy = hx["x"], hx["y"]
            r = hx["r"]
            alpha = hx["alpha"]

            # 이 육각형의 꼭짓점 (월드 좌표)
            world_poly = hex_corners((cx, cy), r)

            # 육각형을 담을 박스 크기 (조금 여유)
            box_r = int(r) + 3
            box_size = box_r * 2

            # 이 육각형만을 위한 작은 투명 서피스
            hex_surf = pygame.Surface((box_size, box_size), pygame.SRCALPHA)

            # 월드 좌표 → 로컬 좌표로 옮기기 (박스 중앙 기준)
            local_poly = []
            for x, y in world_poly:
                lx = x - cx + box_r
                ly = y - cy + box_r
                local_poly.append((lx, ly))

            # 전체 밝기(투명도)를 더 낮추고 싶으면 FADE 조절
            FADE = 0.4  # 0.4 = 원래보다 40% 정도만 보이게
            draw_alpha = max(0, min(255, int(alpha * FADE)))

            fill_color = (255, 255, 255, draw_alpha)
            pygame.draw.polygon(hex_surf, fill_color, local_poly, 0)

            # 메인 surface에 알파 블렌딩으로 합치기
            surface.blit(hex_surf, (cx - box_r, cy - box_r))