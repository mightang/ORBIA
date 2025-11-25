# core/ui.py
import pygame

play_ui_click = None

class Button:
    def __init__(self, rect, text, font, on_click, bg=(40, 46, 60), fg=(234, 242, 255)):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.font = font
        self.on_click = on_click
        self.bg = bg
        self.fg = fg
        self.hover = False

    def handle_event(self, e):
        if e.type == pygame.MOUSEMOTION:
            self.hover = self.rect.collidepoint(e.pos)
        elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            if self.rect.collidepoint(e.pos):
                # 먼저 UI 클릭 사운드
                if play_ui_click is not None:
                    play_ui_click()
                # 그 다음 실제 버튼 동작
                if self.on_click:
                    self.on_click()

    def draw(self, surf):
        # 1) 드롭 섀도우
        shadow_offset = 3
        shadow_rect = self.rect.move(0, shadow_offset)
        pygame.draw.rect(
            surf,
            (5, 8, 16),      # 아주 어두운 남색 계열 그림자
            shadow_rect,
            border_radius=14
        )

        # 2) 버튼 본체를 별도 Surface에 그림
        btn_surf = pygame.Surface(self.rect.size, pygame.SRCALPHA)
        btn_rect = btn_surf.get_rect()

        # 기본 배경색 + hover 시 살짝 밝게
        bg = self.bg
        if self.hover:
            lighten = 18
            r = min(bg[0] + lighten, 255)
            g = min(bg[1] + lighten, 255)
            b = min(bg[2] + lighten, 255)
            bg = (r, g, b)

        # 2-1) 기본 바탕 (둥근 사각형)
        corner_radius = 14
        pygame.draw.rect(btn_surf, bg, btn_rect, border_radius=corner_radius)

        # 2-2) 테두리 (은은한 라인)
        border_color = (
            min(bg[0] + 20, 255),
            min(bg[1] + 25, 255),
            min(bg[2] + 40, 255),
        )
        pygame.draw.rect(btn_surf, border_color, btn_rect, width=2, border_radius=corner_radius)

        # 2-3) 위쪽에만 살짝 하이라이트 그라디언트 (모서리 안쪽으로만)
        grad = pygame.Surface(self.rect.size, pygame.SRCALPHA)
        h = self.rect.height
        for y in range(h // 2):
            t = y / max(1, (h // 2) - 1)
            alpha = int(60 * (1.0 - t))  # 위쪽이 더 밝음

            # 좌우를 corner_radius만큼 깎아서, 네 모서리 밖은 건드리지 않음
            pygame.draw.line(
                grad,
                (255, 255, 255, alpha),
                (corner_radius, y),
                (self.rect.width - corner_radius, y),
            )
        btn_surf.blit(grad, (0, 0))

        # 3) 텍스트
        label = self.font.render(self.text, True, self.fg)
        btn_surf.blit(label, label.get_rect(center=btn_rect.center))

        # 4) 최종 blit
        surf.blit(btn_surf, self.rect.topleft)

class Slider:
    def __init__(self, rect, min_val, max_val, value, on_change=None,
                 track_color=(80, 86, 100), fill_color=(180, 200, 255),
                 knob_color=(234, 242, 255)):
        self.rect = pygame.Rect(rect)
        self.min_val = float(min_val)
        self.max_val = float(max_val)
        self.value = float(value)
        self.on_change = on_change
        self.track_color = track_color
        self.fill_color = fill_color
        self.knob_color = knob_color
        self.dragging = False

    def _value_to_x(self):
        t = (self.value - self.min_val) / (self.max_val - self.min_val or 1.0)
        return self.rect.left + int(t * self.rect.width)

    def _x_to_value(self, x):
        t = (x - self.rect.left) / (self.rect.width or 1.0)
        t = max(0.0, min(1.0, t))
        return self.min_val + t * (self.max_val - self.min_val)

    def handle_event(self, e):
        if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            if self.rect.collidepoint(e.pos):
                self.dragging = True
                self.value = self._x_to_value(e.pos[0])
                if self.on_change:
                    self.on_change(self.value)
        elif e.type == pygame.MOUSEBUTTONUP and e.button == 1:
            self.dragging = False
        elif e.type == pygame.MOUSEMOTION and self.dragging:
            self.value = self._x_to_value(e.pos[0])
            if self.on_change:
                self.on_change(self.value)

    def draw(self, surf):
        y = self.rect.centery
        # 트랙
        pygame.draw.line(surf, self.track_color,
                         (self.rect.left, y), (self.rect.right, y), 4)
        # 채워진 부분
        knob_x = self._value_to_x()
        pygame.draw.line(surf, self.fill_color,
                         (self.rect.left, y), (knob_x, y), 6)
        # 노브
        pygame.draw.circle(surf, self.knob_color, (knob_x, y), 8)

def draw_label_center(surf, text, font, center, color=(234,242,255)):
    img = font.render(text, True, color)
    surf.blit(img, img.get_rect(center=center))