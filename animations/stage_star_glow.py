# animations/stage_star_glow.py
import math
import pygame

def draw_stage_star_glow(surface, center, poly, t, base_color=(255, 230, 160)):
    """
    레벨 선택 화면에서 '별 3개 클리어' 스테이지 타일 위에 그리는
    은은한 펄스 하이라이트.

    - surface: 메인 화면 Surface
    - center : (cx, cy) 타일 중심 좌표
    - poly   : 육각형 꼭짓점 리스트
    - t      : 누적 시간(초)
    """
    cx, cy = center

    # 0~1 사이로 진동하는 펄스 값
    SPEED = 0.7  # 1.0 = 기본, 작게 하면 느려짐, 크게 하면 빨라짐
    phase = (math.sin(t * SPEED * 2.0 * math.pi) + 1.0) * 0.5
    alpha = int(60 + 80 * phase)    # 밝기
    scale = 1.03 + 0.05 * phase     # 살짝 커졌다 작아지는 크기

    # 육각형을 중심 기준으로 scale 배만큼 키운다
    scaled = []
    for (x, y) in poly:
        sx = cx + (x - cx) * scale
        sy = cy + (y - cy) * scale
        scaled.append((sx, sy))

    w, h = surface.get_size()
    overlay = pygame.Surface((w, h), pygame.SRCALPHA)

    color = (*base_color, alpha)
    # 테두리만 그려서 기존 타일을 가리지 않게
    pygame.draw.polygon(overlay, color, scaled, width=3)

    surface.blit(overlay, (0, 0))