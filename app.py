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
        self.stage_best_stars = {}   # ← 추가: 스테이지별 최고 별 개수
        self.load_progress()

        self.WIDTH, self.HEIGHT = settings.WIDTH, settings.HEIGHT
        self.FPS = settings.FPS

        # 해상도 프리셋/인덱스
        self.resolutions = getattr(settings, "RESOLUTIONS", [(self.WIDTH, self.HEIGHT)])
        self.res_index = getattr(settings, "DEFAULT_RES_INDEX", 0)
        if 0 <= self.res_index < len(self.resolutions):
            self.WIDTH, self.HEIGHT = self.resolutions[self.res_index]

        # 디스플레이 모드 정의 (3가지)
        # kind: "window" / "max_window" / "fullscreen"
        self.display_modes = [
            {"name": "창 모드",          "kind": "window"},
            {"name": "전체 화면",        "kind": "fullscreen"},
        ]
        self.display_mode_index = 0   # 기본: 창 모드

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
        self.sfx_tile_hover = pygame.mixer.Sound(
            os.path.join(self.SOUND_DIR, "tile_hover.wav")
        )

        self.update_bgm_volume()
        self.update_sfx_volume()

        # --- Button에서 UI 클릭 소리를 쓸 수 있도록 연결 ---
        from core import ui as ui_mod
        ui_mod.play_ui_click = self.play_ui_click

        self.screen = pygame.display.set_mode((self.WIDTH, self.HEIGHT))
        pygame.display.set_caption("HEXFIELD")
        self.clock = pygame.time.Clock()

        self.current_scene = TitleScene(self)
        self.running = True  # ← 루프 제어 플래그

        self.transition = None

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
        # 기본값
        self.max_unlocked_stage = 1
        self.stage_best_stars = {}

        try:
            with open(self.save_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            self.max_unlocked_stage = int(data.get("max_unlocked_stage", 1))

            raw_stars = data.get("stage_best_stars", {})
            stars = {}
            if isinstance(raw_stars, dict):
                for k, v in raw_stars.items():
                    try:
                        idx = int(k)
                        sc = int(v)
                    except (TypeError, ValueError):
                        continue
                    if sc > 0:
                        stars[idx] = max(0, min(3, sc))  # 0~3 범위로 클램프
            self.stage_best_stars = stars

        except (FileNotFoundError, json.JSONDecodeError, ValueError):
            # 파일이 없거나 깨졌으면 기본값
            self.max_unlocked_stage = 1
            self.stage_best_stars = {}
    
    def save_progress(self):
        # 키는 문자열로 저장 (JSON에서 보기도 편함)
        stars_out = {
            str(idx): int(sc)
            for idx, sc in getattr(self, "stage_best_stars", {}).items()
            if int(sc) > 0
        }

        data = {
            "max_unlocked_stage": int(self.max_unlocked_stage),
            "stage_best_stars": stars_out,
        }

        try:
            with open(self.save_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except OSError as e:
            print("[WARN] 진행도 저장 실패:", e)

    def unlock_stage(self, cleared_index: int,
                     total_stages: int = 37,
                     star_count: int | None = None):
        """
        cleared_index 스테이지를 클리어했을 때:
          - 최고 별 기록을 갱신하고
          - 필요하면 다음 스테이지를 연다.
        """
        if cleared_index < 1:
            return

        # 1) 별 기록 갱신 (이미 깨 본 스테이지도 갱신 가능)
        if star_count is not None:
            try:
                sc = max(0, min(3, int(star_count)))
            except (TypeError, ValueError):
                sc = None
            if sc is not None:
                prev = getattr(self, "stage_best_stars", {}).get(cleared_index, 0)
                if sc > prev:
                    self.stage_best_stars[cleared_index] = sc

        # 2) 스테이지 잠금 해제
        if cleared_index >= total_stages:
            # 마지막 스테이지는 '다음'이 없으니 자기 자신까지만
            self.max_unlocked_stage = max(self.max_unlocked_stage, cleared_index)
        elif cleared_index >= self.max_unlocked_stage:
            # 그 외에는 cleared_index + 1까지 오픈
            self.max_unlocked_stage = max(self.max_unlocked_stage, cleared_index + 1)

        self.save_progress()


    def reset_progress(self):
        """진행도 초기화: 1스테이지만 열어 두고 다시 저장."""
        self.max_unlocked_stage = 1
        self.stage_best_stars = {}   # ← 추가
        self.save_progress()

    def change_scene(self, scene_obj, use_transition=True):
        """
        씬 교체.
        - use_transition=True 이면 페이드 아웃/인 애니메이션을 사용
        - False 이면 바로 교체
        """
        if not use_transition or self.current_scene is None:
            self.current_scene = scene_obj
            return

        # 이미 전환 중이면 그냥 즉시 교체해 버림 (중첩 방지)
        if self.transition is not None:
            self.current_scene = scene_obj
            self.transition = None
            return

        from animations.scene_transition import SceneFadeTransition

        trans = SceneFadeTransition(self, scene_obj,
                                    fade_out=0.25,
                                    fade_in=0.25)
        trans.capture_from(self.current_scene)
        self.transition = trans

    # 해상도 변경 메서드
    def set_resolution(self, index:int):
        if 0 <= index < len(self.resolutions):
            self.res_index = index
            self.WIDTH, self.HEIGHT = self.resolutions[index]
            self.screen = pygame.display.set_mode((self.WIDTH, self.HEIGHT))

    def set_display_mode(self, index: int):
        """표시 모드 변경: 창 / 큰 창 / 전체 화면."""
        if not (0 <= index < len(self.display_modes)):
            return

        self.display_mode_index = index
        mode = self.display_modes[index]
        kind = mode.get("kind", "window")

        # 기준 비율은 settings 기준
        base_w, base_h = settings.WIDTH, settings.HEIGHT
        ratio = base_w / base_h

        info = pygame.display.Info()
        desktop_w, desktop_h = info.current_w, info.current_h

        flags = 0

        if kind == "window":
            # 기본 작은 창
            w, h = base_w, base_h

        elif kind == "fullscreen":
            flags = pygame.FULLSCREEN
            w, h = desktop_w, desktop_h

        else:
            w, h = base_w, base_h

        self.WIDTH, self.HEIGHT = w, h
        self.screen = pygame.display.set_mode((w, h), flags)

    # --- 사운드 유틸 ---
    def update_bgm_volume(self):
        pygame.mixer.music.set_volume(self.bgm_volume)

    def update_sfx_volume(self):
        vol = self.sfx_volume
        for snd in (self.sfx_ui_click,
                    self.sfx_tile_correct,
                    self.sfx_tile_false,
                    self.sfx_tile_hover):
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

    def play_tile_hover(self):
        """타일 위로 마우스를 처음 올렸을 때 한 번만 호출."""
        if getattr(self, "sfx_tile_hover", None) is not None:
            self.sfx_tile_hover.play()

    def run(self):
        self.running = True
        while self.running:
            dt = self.clock.tick(self.FPS) / 1000.0

            # --- 이벤트 처리 ---
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    self.running = False
                else:
                    # 전환 중에는 입력을 씬에 넘기지 않음
                    if self.transition is None and self.current_scene is not None:
                        self.current_scene.handle_event(e)

            # --- 업데이트 & 그리기 ---
            if self.transition is not None:
                # fade-in 단계에 들어간 이후에는 새 씬도 같이 update 해 준다
                if self.transition.phase == "fade_in" and self.current_scene is not None:
                    self.current_scene.update(dt)

                self.transition.update(dt)
                self.transition.draw(self.screen)

                if self.transition.finished:
                    self.transition = None
            else:
                if self.current_scene is not None:
                    self.current_scene.update(dt)
                    self.current_scene.draw(self.screen)

            pygame.display.flip()

        pygame.quit()
        sys.exit()

    def quit(self):
        self.running = False

if __name__ == "__main__":
    App().run()