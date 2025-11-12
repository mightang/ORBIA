import os, sys, pygame
import settings
from core.scenes import TitleScene

class App:
    def __init__(self):
        pygame.init()

        self.BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        self.ASSET_DIR = os.path.join(self.BASE_DIR, "assets")

        self.WIDTH, self.HEIGHT = settings.WIDTH, settings.HEIGHT
        self.FPS = settings.FPS
        self.screen = pygame.display.set_mode((self.WIDTH, self.HEIGHT))
        pygame.display.set_caption("HEXFIELD")
        self.clock = pygame.time.Clock()

        self.current_scene = TitleScene(self)

    def load_font(self, size):
        # assets 폴더에 폰트 파일이 있다면 여기서 불러오기
        font_path = os.path.join(self.ASSET_DIR, "fonts", "Pretendard-Regular.ttf")
        if os.path.exists(font_path):
            return pygame.font.Font(font_path, size)
        else:
            # 폰트 파일이 없을 경우 기본 시스템 폰트로 대체
            print("[WARN] 폰트 파일을 찾을 수 없어 시스템 폰트를 사용합니다.")
            return pygame.font.SysFont("malgungothic,arial", size)

    def change_scene(self, scene_obj):
        self.current_scene = scene_obj

    def run(self):
        running = True
        while running:
            dt = self.clock.tick(self.FPS) / 1000.0
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    running = False
                else:
                    self.current_scene.handle_event(e)
            self.current_scene.update(dt)
            self.current_scene.draw(self.screen)
            pygame.display.flip()
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    App().run()