# animations/scene_transition.py
import pygame

class SceneFadeTransition:
    """
    씬 전환용 페이드 인/아웃 애니메이션.
    - fade_out: 이전 화면을 어둡게 덮어가며 사라짐
    - fade_in : 새 화면 위에서 어둠이 걷히며 나타남
    """
    def __init__(self, app, to_scene, fade_out=0.25, fade_in=0.25):
        self.app = app
        self.to_scene = to_scene
        self.fade_out = float(fade_out)
        self.fade_in = float(fade_in)

        self.time = 0.0
        self.phase = "fade_out"   # "fade_out" -> "fade_in"
        self.finished = False

        self.from_surface = None  # 이전 화면 캡처
        self.switched = False     # 실제 씬 교체 완료 여부

    def capture_from(self, from_scene):
        """현재 씬을 한 프레임 그려서 Surface로 캡처."""
        size = self.app.screen.get_size()
        surf = pygame.Surface(size).convert_alpha()
        # 배경 + UI 전부 한 번 그리기
        from_scene.draw(surf)
        self.from_surface = surf

    def update(self, dt):
        self.time += dt

        if self.phase == "fade_out":
            if self.time >= self.fade_out:
                # 페이드 아웃 끝나는 시점에 실제 씬 교체
                if not self.switched:
                    self.app.current_scene = self.to_scene
                    self.switched = True
                self.phase = "fade_in"
                self.time = 0.0

        elif self.phase == "fade_in":
            if self.time >= self.fade_in:
                self.finished = True

    def draw(self, screen):
        if self.phase == "fade_out":
            # 이전 씬 캡처 화면 위에 어두운 오버레이
            if self.from_surface is not None:
                screen.blit(self.from_surface, (0, 0))

            t = max(0.0, min(1.0, self.time / max(self.fade_out, 1e-6)))
            alpha = int(255 * t)

            overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, alpha))
            screen.blit(overlay, (0, 0))

        elif self.phase == "fade_in":
            # 새 씬을 먼저 그린 다음, 남은 어둠을 걷어내는 느낌
            self.app.current_scene.draw(screen)

            t = max(0.0, min(1.0, self.time / max(self.fade_in, 1e-6)))
            alpha = int(255 * (1.0 - t))   # 점점 밝아짐

            if alpha > 0:
                overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
                overlay.fill((0, 0, 0, alpha))
                screen.blit(overlay, (0, 0))