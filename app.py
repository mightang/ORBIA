import os, sys, pygame
import json
import settings
from core.scenes import TitleScene

class App:
    def __init__(self):
        pygame.init()

        self.BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        self.ASSET_DIR = os.path.join(self.BASE_DIR, "assets")

        self.SAVE_DIR = os.path.join(self.BASE_DIR, "saves")
        os.makedirs(self.SAVE_DIR, exist_ok=True)  # 폴더가 없으면 생성

        self.save_path = os.path.join(self.SAVE_DIR, "save.json")

        self.max_unlocked_stage = 1
        self.load_progress()

        self.WIDTH, self.HEIGHT = settings.WIDTH, settings.HEIGHT
        self.FPS = settings.FPS

        # 해상도 프리셋/인덱스
        self.resolutions = getattr(settings, "RESOLUTIONS", [(self.WIDTH, self.HEIGHT)])
        self.res_index = getattr(settings, "DEFAULT_RES_INDEX", 0)
        if 0 <= self.res_index < len(self.resolutions):
            self.WIDTH, self.HEIGHT = self.resolutions[self.res_index]

        # 볼륨 상태 (0.0 ~ 1.0)
        self.bgm_volume = 0.5
        self.sfx_volume = 0.8

        self.screen = pygame.display.set_mode((self.WIDTH, self.HEIGHT))
        pygame.display.set_caption("HEXFIELD")
        self.clock = pygame.time.Clock()

        self.current_scene = TitleScene(self)
        self.running = True  # ← 루프 제어 플래그

    def load_font(self, size):
        # assets 폴더에 폰트 파일이 있다면 여기서 불러오기
        font_path = os.path.join(self.ASSET_DIR, "fonts", "PretendardVariable.ttf")
        if os.path.exists(font_path):
            return pygame.font.Font(font_path, size)
        else:
            # 폰트 파일이 없을 경우 기본 시스템 폰트로 대체
            print("[WARN] 폰트 파일을 찾을 수 없어 시스템 폰트를 사용합니다.")
            return pygame.font.SysFont("malgungothic,arial", size)
        
        # --- 진행도 저장/로드 ---
    def load_progress(self):
        try:
            with open(self.save_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.max_unlocked_stage = int(data.get("max_unlocked_stage", 1))
        except (FileNotFoundError, json.JSONDecodeError, ValueError):
            # 파일이 없거나 깨졌으면 1스테이지만 오픈
            self.max_unlocked_stage = 1

    def save_progress(self):
        data = {"max_unlocked_stage": int(self.max_unlocked_stage)}
        try:
            with open(self.save_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except OSError as e:
            print("[WARN] 진행도 저장 실패:", e)

    def unlock_stage(self, cleared_index: int, total_stages: int = 37):
        """
        cleared_index 스테이지를 클리어했을 때 다음 스테이지를 연다.
        예) 1 클리어 -> 2 오픈, 2 클리어 -> 3 오픈 ...
        """
        if cleared_index < 1:
            return

        # 이미 더 높은 스테이지까지 열려 있으면 무시
        if cleared_index < self.max_unlocked_stage:
            return

        # 마지막 스테이지는 '다음'이 없으니 그냥 현재 값 유지
        if cleared_index >= total_stages:
            self.max_unlocked_stage = max(self.max_unlocked_stage, cleared_index)
        else:
            self.max_unlocked_stage = max(self.max_unlocked_stage, cleared_index + 1)

        self.save_progress()

    def reset_progress(self):
        """진행도 초기화: 1스테이지만 열어 두고 다시 저장."""
        self.max_unlocked_stage = 1
        self.save_progress()


    def change_scene(self, scene_obj):
        self.current_scene = scene_obj

    # 해상도 변경 메서드
    def set_resolution(self, index:int):
        if 0 <= index < len(self.resolutions):
            self.res_index = index
            self.WIDTH, self.HEIGHT = self.resolutions[index]
            self.screen = pygame.display.set_mode((self.WIDTH, self.HEIGHT))

    def run(self):
        self.running = True
        while self.running:
            dt = self.clock.tick(self.FPS) / 1000.0
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    self.running = False
                else:
                    self.current_scene.handle_event(e)
            self.current_scene.update(dt)
            self.current_scene.draw(self.screen)
            pygame.display.flip()
        pygame.quit()
        sys.exit()

    def quit(self):
        self.running = False

if __name__ == "__main__":
    App().run()