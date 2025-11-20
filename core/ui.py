# core/ui.py
import pygame

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
                if self.on_click: self.on_click()

    def draw(self, surf):
        color = (58, 66, 86) if self.hover else self.bg
        pygame.draw.rect(surf, color, self.rect, border_radius=10)
        label = self.font.render(self.text, True, self.fg)
        surf.blit(label, label.get_rect(center=self.rect.center))

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