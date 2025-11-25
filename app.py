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


        # 사운드 관련
        self.SOUND_DIR = os.path.join(self.ASSET_DIR, "sounds")
        pygame.mixer.init()

        self.bgm_volume = 0.5
        self.sfx_volume = 0.8

                # BGM 파일 경로
        self.bgm_paths = {
            "main":          os.path.join(self.SOUND_DIR, "main.ogg"),
            "basic":         os.path.join(self.SOUND_DIR, "basic.ogg"),
            "intermediate_1":os.path.join(self.SOUND_DIR, "intermediate_1.ogg"),
            "intermediate_2":os.path.join(self.SOUND_DIR, "intermediate_2.ogg"),
            "advance_1":     os.path.join(self.SOUND_DIR, "advance_1.ogg"),
            "advance_2":     os.path.join(self.SOUND_DIR, "advance_2.ogg"),
            "advance_3":     os.path.join(self.SOUND_DIR, "advance_3.ogg"),
        }
        self.current_bgm_key = None

        # SFX 로드
        self.sfx_ui_click = pygame.mixer.Sound(
            os.path.join(self.SOUND_DIR, "ui_click.wav")
        )
        self.sfx_tile_correct = pygame.mixer.Sound(
            os.path.join(self.SOUND_DIR, "tile_click_correct.wav")
        )
        self.sfx_tile_false = pygame.mixer.Sound(
            os.path.join(self.SOUND_DIR, "tile_click_false.wav")
        )

        self.update_bgm_volume()
        self.update_sfx_volume()

        self.screen = pygame.display.set_mode((self.WIDTH, self.HEIGHT))
        pygame.display.set_caption("HEXFIELD")
        self.clock = pygame.time.Clock()

        self.current_scene = TitleScene(self)
        self.running = True

        # --- Button에서 UI 클릭 소리를 쓸 수 있도록 연결 ---
        from core import ui as ui_mod
        ui_mod.play_ui_click = self.play_ui_click

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

    # --- 사운드 유틸 ---
    def update_bgm_volume(self):
        pygame.mixer.music.set_volume(self.bgm_volume)

    def update_sfx_volume(self):
        vol = self.sfx_volume
        for snd in (self.sfx_ui_click, self.sfx_tile_correct, self.sfx_tile_false):
            if snd is not None:
                snd.set_volume(vol)

    def play_bgm(self, key: str):
        """지정한 키의 BGM을 loop 재생 (같은 키면 재로딩 없이 볼륨만)."""
        path = self.bgm_paths.get(key)
        if not path:
            return

        # 이미 같은 곡이면 볼륨만 맞추고 끝
        if self.current_bgm_key == key:
            self.update_bgm_volume()
            return

        try:
            pygame.mixer.music.load(path)
            pygame.mixer.music.set_volume(self.bgm_volume)
            pygame.mixer.music.play(-1)  # 무한 루프
            self.current_bgm_key = key
        except pygame.error as e:
            print("[WARN] BGM 재생 실패:", e)

    def stop_bgm(self):
        pygame.mixer.music.stop()
        self.current_bgm_key = None

    def play_ui_click(self):
        """모든 UI 버튼(타일 제외) 클릭 시 호출."""
        if self.sfx_ui_click is not None:
            self.sfx_ui_click.play()

    def play_tile_click(self, ok: bool):
        """타일 클릭: 옳으면 True, 실수면 False."""
        snd = self.sfx_tile_correct if ok else self.sfx_tile_false
        if snd is not None:
            snd.play()

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