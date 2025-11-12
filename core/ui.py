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


def draw_label_center(surf, text, font, center, color=(234,242,255)):
    img = font.render(text, True, color)
    surf.blit(img, img.get_rect(center=center))