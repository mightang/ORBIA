# core/scenes.py
import os, json, re, math
import pygame
from core.ui import Button, draw_label_center, Slider
from core import render as render_mod
from core.board import Board, C_REVEALED, C_BLOCKED
from core.grid import HexGrid, cube_len
from core.hexmath import pixel_to_axial, hex_corners, axial_to_pixel
from settings import COL_FLAG_TILE, COL_COVERED, HEX_SIZE

from animations.title_space import TitleBackground
from animations.tile_reveal import TileRevealAnim, draw_reveal_anims
from animations.tile_mistake import TileShakeAnim, draw_shake_anims
from animations.tile_hover import TileHoverAnim, draw_hover_anim
from animations.stage_star_glow import draw_stage_star_glow
from animations.game_hex_bg import GameHexBackground

TOTAL_STAGES = 37
MAJOR_STEP_LAST_INDICES = {1, 7, 19, 37}

def stage_index_to_relpath(idx: int) -> str:
    num = int(idx)
    if num < 1 or num > TOTAL_STAGES:
        raise ValueError(f"invalid stage index: {idx}")

    if num == 1:
        subdir = "tutorial"
    elif 2 <= num <= 7:
        subdir = "basic"
    elif 8 <= num <= 19:
        subdir = "intermediate"
    else:  # 20~37
        subdir = "advance"

    return os.path.join("stages", subdir, f"{num:03d}.json")


def path_to_stage_index(path: str):
    """
    .../012.json 같은 경로에서 12를 int로 뽑아낸다.
    """
    m = re.search(r"(\d+)\.json$", path)
    return int(m.group(1)) if m else None

def stage_difficulty_index(idx: int) -> int:
    """
    0: 튜토리얼(1번)
    1: basic (2~7)
    2: intermediate (8~19)
    3: advance (20~37)
    """
    num = int(idx)
    if num == 1:
        return 0
    elif 2 <= num <= 7:
        return 1
    elif 8 <= num <= 19:
        return 2
    else:
        return 3


# 공통 Scene 인터페이스
class Scene:
    def __init__(self, game):
        self.game = game
    def handle_event(self, e): pass
    def update(self, dt): pass
    def draw(self, screen): pass

# 1) 메인 타이틀
class TitleScene(Scene):
    def __init__(self, game):
        super().__init__(game)
        W, H = self.game.WIDTH, self.game.HEIGHT
        self.title_font = self.game.load_font(48)
        self.ui_font = self.game.load_font(26)
        self.small_font = self.game.load_font(22)

        # 배경 로드
        self.bg = TitleBackground((W, H))

        # 타이틀 이미지 로드
        logo_path = os.path.join(self.game.ASSET_DIR, "images", "game_title.png")

        # 원본 로고 로드
        orig_logo = pygame.image.load(logo_path).convert_alpha()

        # 원하는 배율 (예: 0.8 = 80% 크기)
        scale = 0.55

        w, h = orig_logo.get_size()
        new_size = (int(w * scale), int(h * scale))

        # 부드럽게 축소
        self.title_img = pygame.transform.smoothscale(orig_logo, new_size)

        # 큰 시작 버튼
        start_w, start_h = 260, 60
        start_x = (W - start_w) // 2
        start_y = int(H * 0.42)

        # 아래 작은 버튼들
        sub_w, sub_h = 200, 46
        sub_gap = 10
        sub_block_top = start_y + start_h + 24  # 시작 버튼 아래 약간 띄움

        self.start_btn = Button(
            rect=(start_x, start_y, start_w, start_h),
            text="시작하기",
            font=self.ui_font,
            on_click=self.go_level_select
        )

        sub_x = (W - sub_w) // 2

        self.option_btn = Button(
            rect=(sub_x, sub_block_top + 0 * (sub_h + sub_gap), sub_w, sub_h),
            text="옵션",
            font=self.small_font,
            on_click=self.go_options
        )
        self.credit_btn = Button(
            rect=(sub_x, sub_block_top + 1 * (sub_h + sub_gap), sub_w, sub_h),
            text="크레딧",
            font=self.small_font,
            on_click=self.go_credits
        )
        self.quit_btn = Button(
            rect=(sub_x, sub_block_top + 2 * (sub_h + sub_gap), sub_w, sub_h),
            text="게임 종료",
            font=self.small_font,
            on_click=self.quit_game
        )

        # 타이틀 전용 버튼 색상 조정
        # 시작 버튼: 포인트 컬러 (조금 더 밝고 푸른 톤)
        self.start_btn.bg = (70, 92, 160)
        self.start_btn.fg = (240, 245, 255)

        # 나머지 보조 버튼들: 조금 더 어두운 남색
        sub_bg = (40, 50, 96)
        sub_fg = (220, 230, 245)
        self.option_btn.bg = sub_bg
        self.option_btn.fg = sub_fg
        self.credit_btn.bg = sub_bg
        self.credit_btn.fg = sub_fg
        self.quit_btn.bg = sub_bg
        self.quit_btn.fg = sub_fg


        self.last_size = None
        self.relayout(game.screen.get_size())

        # 처음 실행 시에만 메인 BGM 재생.
        # 이미 다른 BGM이 재생 중이면 건드리지 않는다.
        if getattr(self.game, "current_bgm_key", None) is None:
            if hasattr(self.game, "play_bgm"):
                self.game.play_bgm("main")

    def relayout(self, size):
        W, H = size
        self.last_size = size
        start_w, start_h = 260, 60
        start_x = (W - start_w) // 2
        start_y = int(H * 0.55)
        self.start_btn.rect.update(start_x, start_y, start_w, start_h)

        sub_w, sub_h = 200, 46
        sub_gap = 10
        sub_block_top = start_y + start_h + 24
        sub_x = (W - sub_w) // 2
        self.option_btn.rect.update(sub_x, sub_block_top + 0 * (sub_h + sub_gap), sub_w, sub_h)
        self.credit_btn.rect.update(sub_x, sub_block_top + 1 * (sub_h + sub_gap), sub_w, sub_h)
        self.quit_btn.rect.update(sub_x, sub_block_top + 2 * (sub_h + sub_gap), sub_w, sub_h)

    def go_level_select(self):
        # 아직 튜토리얼(1번 스테이지)만 열린 상태라면 → 바로 1번 스테이지 진입
        if getattr(self.game, "max_unlocked_stage", 1) <= 1:
            stage_path = stage_index_to_relpath(1)
            self.game.change_scene(GameplayScene(self.game, stage_path))
        else:
            # 튜토리얼을 한 번이라도 깨서 2번 이상 열려 있으면 → 레벨 선택 화면
            self.game.change_scene(LevelSelectScene(self.game))


    def go_options(self):
        self.game.change_scene(OptionsScene(self.game))

    def go_credits(self):
        self.game.change_scene(CreditsScene(self.game))

    def quit_game(self):
        self.game.quit()

    def handle_event(self, e):
        self.start_btn.handle_event(e)
        self.option_btn.handle_event(e)
        self.credit_btn.handle_event(e)
        self.quit_btn.handle_event(e)

    def update(self, dt):
        if hasattr(self, "bg"):
            self.bg.update(dt)

    def draw(self, screen):
        size = screen.get_size()
        if size != self.last_size:
            self.relayout(size)
            if hasattr(self, "bg"):
                self.bg.resize(size)

        if hasattr(self, "bg"):
            self.bg.draw(screen)
        else:
            screen.fill((14, 18, 32))

        W, H = size
        # 타이틀 이미지 그리기
        img = self.title_img
        rect = img.get_rect()
        rect.center = (W // 2, int(H * 0.32))
        screen.blit(img, rect)

        self.start_btn.draw(screen)
        self.option_btn.draw(screen)
        self.credit_btn.draw(screen)
        self.quit_btn.draw(screen)


class OptionsScene(Scene):
    def __init__(self, game):
        super().__init__(game)
        W, H = self.game.WIDTH, self.game.HEIGHT
        self.title_font = self.game.load_font(40)
        self.ui_font = self.game.load_font(22)
        self.small_font = self.game.load_font(18)

        # 슬라이더 영역 설정
        margin_x = 120
        slider_w = W - margin_x * 2
        y_base = int(H * 0.3)
        gap_y = 80

        # BGM 슬라이더
        self.bgm_slider = Slider(
            rect=(margin_x, y_base, slider_w, 24),
            min_val=0.0, max_val=1.0,
            value=self.game.bgm_volume,
            on_change=self.on_bgm_change
        )

        # SFX 슬라이더
        self.sfx_slider = Slider(
            rect=(margin_x, y_base + gap_y, slider_w, 24),
            min_val=0.0, max_val=1.0,
            value=self.game.sfx_volume,
            on_change=self.on_sfx_change
        )

        # 해상도 버튼들
        self.res_buttons = []
        res_y = y_base + gap_y * 2
        btn_w, btn_h = 160, 40
        gap = 20

        modes = getattr(self.game, "display_modes", [])
        count = len(modes)
        total_w = count * btn_w + (count - 1) * gap
        start_x = (W - total_w) // 2

        for i, mode in enumerate(modes):
            x = start_x + i * (btn_w + gap)
            label = mode.get("name", f"모드 {i+1}")

            def make_cb(idx=i):
                def cb():
                    self.select_resolution(idx)  # 함수 이름은 그대로 둬도 됨
                return cb

            self.res_buttons.append(
                Button((x, res_y, btn_w, btn_h), label, self.small_font, make_cb())
            )

        # 뒤로가기 버튼
        self.back_btn = Button(
            rect=(20, 20, 100, 40),
            text="뒤로가기",
            font=self.small_font,
            on_click=self.back_to_title
        )

        # 진행도 초기화 관련 상태
        self.reset_modal_active = False
        self.reset_modal_btns = {}

        # 오른쪽 아래 데이터 초기화 버튼
        btn_w, btn_h = 140, 40
        self.reset_btn = Button(
            rect = (W - btn_w - 20, H - btn_h - 20, btn_w, btn_h),
            text = "데이터 초기화",
            font = self.small_font,
            on_click = self.open_reset_modal
        )

    def open_reset_modal(self):
        self.reset_modal_active = True
        self.reset_modal_btns = {}

    def confirm_reset(self):
        # App에 있는 reset_progress 호출
        if hasattr(self.game, "reset_progress"):
            self.game.reset_progress()
        self.reset_modal_active = False
        self.reset_modal_btns = {}

    def cancel_reset(self):
        self.reset_modal_active = False
        self.reset_modal_btns = {}

    def on_bgm_change(self, value):
        self.game.bgm_volume = float(value)
        if hasattr(self.game, "update_bgm_volume"):
            self.game.update_bgm_volume()

    def on_sfx_change(self, value):
        self.game.sfx_volume = float(value)
        if hasattr(self.game, "update_sfx_volume"):
            self.game.update_sfx_volume()

    def select_resolution(self, idx):
        if hasattr(self.game, "set_display_mode"):
            self.game.set_display_mode(idx)
        # 해상도 바꾸는 건 즉시 반영하는 게 자연스러우니 전환 끄기
        self.game.change_scene(OptionsScene(self.game), use_transition=False)

    def back_to_title(self):
        # 타이틀을 새로 생성하면 버튼 위치도 새 해상도 기준으로 재배치됨
        self.game.change_scene(TitleScene(self.game))

    def handle_event(self, e):
        # 🔹 초기화 확인 모달이 떠 있을 때는 그쪽만 처리
        if self.reset_modal_active:
            if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                self.cancel_reset()
                return
            
            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1 and self.reset_modal_btns:
                mx, my = e.pos
                if self.reset_modal_btns["ok"].collidepoint(mx, my):
                    if hasattr(self.game, "play_ui_click"):
                        self.game.play_ui_click()
                    self.confirm_reset()
                elif self.reset_modal_btns["cancel"].collidepoint(mx, my):
                    if hasattr(self.game, "play_ui_click"):
                        self.game.play_ui_click()
                    self.cancel_reset()
            return
        
        if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
            self.back_to_title()
            return

        self.back_btn.handle_event(e)
        self.bgm_slider.handle_event(e)
        self.sfx_slider.handle_event(e)
        for b in self.res_buttons:
            b.handle_event(e)
        self.reset_btn.handle_event(e)

    def draw_reset_modal(self, screen):
        w, h = screen.get_size()

        # 어두운 오버레이
        overlay = pygame.Surface((w, h), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        screen.blit(overlay, (0, 0))

        panel_w, panel_h = 520, 220
        panel_rect = pygame.Rect(0, 0, panel_w, panel_h)
        panel_rect.center = (w // 2, h // 2)

        pygame.draw.rect(screen, (40, 46, 60), panel_rect, border_radius=16)
        pygame.draw.rect(screen, (100, 110, 140), panel_rect, width=2, border_radius=16)

        y = panel_rect.top + 30
        title = self.ui_font.render("게임 데이터를 초기화할까요?", True, (234, 242, 255))
        screen.blit(title, (panel_rect.left + 24, y))
        y += title.get_height() + 12

        msg = self.small_font.render("모든 데이터가 삭제되고 게임이 초기화됩니다.", True, (200, 210, 230))
        screen.blit(msg, (panel_rect.left + 24, y))

        btn_w, btn_h = 120, 40
        gap = 20
        total_w = btn_w * 2 + gap
        start_x = panel_rect.centerx - total_w // 2
        btn_y = panel_rect.bottom - 24 - btn_h

        ok_rect = pygame.Rect(start_x, btn_y, btn_w, btn_h)
        cancel_rect = pygame.Rect(start_x + btn_w + gap, btn_y, btn_w, btn_h)

        # 확인 버튼 (빨간 느낌)
        pygame.draw.rect(screen, (160, 60, 60), ok_rect, border_radius=10)
        ok_txt = self.small_font.render("예, 초기화", True, (255, 255, 255))
        screen.blit(ok_txt, ok_txt.get_rect(center=ok_rect.center))

        # 취소 버튼 (회색)
        pygame.draw.rect(screen, (90, 96, 120), cancel_rect, border_radius=10)
        cancel_txt = self.small_font.render("취소", True, (255, 255, 255))
        screen.blit(cancel_txt, cancel_txt.get_rect(center=cancel_rect.center))

        return {"ok": ok_rect, "cancel": cancel_rect}

    def draw(self, screen):
        screen.fill((10, 14, 24))
        W, H = self.game.WIDTH, self.game.HEIGHT

        # 제목
        draw_label_center(screen, "옵션", self.title_font, (W//2, int(H*0.16)))

        # 라벨 텍스트
        bgm_label = self.ui_font.render("배경 음악 볼륨", True, (234,242,255))
        sfx_label = self.ui_font.render("효과음 볼륨", True, (234,242,255))
        res_label = self.ui_font.render("화면 모드", True, (234,242,255))

        screen.blit(bgm_label, (self.bgm_slider.rect.left,
                                self.bgm_slider.rect.top - 32))
        screen.blit(sfx_label, (self.sfx_slider.rect.left,
                                self.sfx_slider.rect.top - 32))

        res_y = self.sfx_slider.rect.top + 80
        screen.blit(res_label, (self.bgm_slider.rect.left, res_y - 36))

        # 슬라이더/버튼 그리기
        self.bgm_slider.draw(screen)
        self.sfx_slider.draw(screen)
        current_idx = getattr(self.game, "display_mode_index", 0)
        for i, b in enumerate(self.res_buttons):
            # 선택된 표시 모드는 살짝 밝게
            if i == current_idx:
                b.bg = (80, 96, 130)
            else:
                b.bg = (40, 46, 60)
            b.draw(screen)


        self.back_btn.draw(screen)
        self.reset_btn.draw(screen)
        if self.reset_modal_active:
            self.reset_modal_btns = self.draw_reset_modal(screen)   

class CreditsScene(Scene):
    def __init__(self, game):
        super().__init__(game)
        self.title_font = self.game.load_font(40)
        self.ui_font = self.game.load_font(22)
        self.small_font = self.game.load_font(18)

        # 뒤로가기 버튼
        self.back_btn = Button(
            rect=(20, 20, 100, 40),
            text="뒤로가기",
            font=self.small_font,
            on_click=self.back_to_title,   # ← 이 메서드를 밑에 정의
        )

        # 임시 크레딧 텍스트
        self.lines = [
            "",
            "",
            "THANKS FOR PLAYING!",
            "",
            "기획: 김태영",
            "구현: 김태영",
            "버그 수정: 김태영",
            "곧 군대 가는 사람: 김태영",
            "",
            "2025 OSS Term Project"
        ]
        # 크레딧 들어왔을 때는 BGM 안 건드리려면 이 부분은 빼도 됨
        # if hasattr(self.game, "play_bgm"):
        #     self.game.play_bgm("main")

    def back_to_title(self):
        # 타이틀로 돌아가기
        from core.scenes import TitleScene  # 같은 파일이면 맨 위 import 안 해도 됨
        self.game.change_scene(TitleScene(self.game))

    def handle_event(self, e):
        if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
            self.back_to_title()   # 언더바 없는 걸로 통일
            return
        self.back_btn.handle_event(e)

    def draw(self, screen):
        screen.fill((12, 16, 26))
        W, H = self.game.WIDTH, self.game.HEIGHT

        draw_label_center(screen, "크레딧", self.title_font, (W//2, int(H*0.18)))

        # 여러 줄 텍스트 중앙 정렬
        total_h = 0
        rendered = []
        for s in self.lines:
            img = self.ui_font.render(s, True, (234, 242, 255))
            rendered.append(img)
            total_h += img.get_height() + 4

        y = int(H*0.35) - total_h // 2
        for img in rendered:
            rect = img.get_rect(center=(W//2, y))
            screen.blit(img, rect)
            y += img.get_height() + 4

        self.back_btn.draw(screen)
    

# 2) 레벨 선택 (1~37) – 정면에서 본 정육각형 37칸
class LevelSelectScene(Scene):
    def __init__(self, game, total=37):
        super().__init__(game)
        self.total = total
        self.title_font = self.game.load_font(36)
        self.ui_font = self.game.load_font(20)

        # 진행도: 1 ~ max_unlocked_stage-1 = 클리어, max_unlocked_stage = 현재까지 열린 최고 단계
        self.max_unlocked = getattr(self.game, "max_unlocked_stage", 1)

        # 배경 (타이틀과 같은 우주 배경 재사용)
        W, H = self.game.WIDTH, self.game.HEIGHT
        self.bg = TitleBackground((W, H), show_hex=False)

        # 37칸 hex-grid 기반 스테이지 타일 정보
        self.stage_tiles = []   # 각 타일: {"idx", "poly", "center", "cleared", "locked", "ring"}
        self.last_size = None
        self.glow_time = 0.0

        # 뒤로가기 버튼
        btn_w, btn_h = 100, 40
        pad = 20
        self.back_btn = Button(
            rect=(pad, pad, btn_w, btn_h),
            text="뒤로가기",
            font=self.ui_font,
            on_click=self.go_title
        )

        # 최초 레이아웃
        self.build_layout(W, H)


    # --- 헥사 타일 내부 폴리곤 (안쪽 보호막/판) ---
    def _inner_poly(self, center, poly, scale=0.80):
        cx, cy = center
        inner = []
        for (x, y) in poly:
            ix = cx + (x - cx) * scale
            iy = cy + (y - cy) * scale
            inner.append((ix, iy))
        return inner

    # --- 포인트가 볼록 다각형(육각형) 안에 있는지 ---
    def _point_in_poly(self, x, y, poly):
        inside = False
        n = len(poly)
        for i in range(n):
            x1, y1 = poly[i]
            x2, y2 = poly[(i + 1) % n]
            if ((y1 > y) != (y2 > y)):
                t = (y - y1) / (y2 - y1 + 1e-9)
                x_cross = x1 + t * (x2 - x1)
                if x < x_cross:
                    inside = not inside
        return inside

    # --- 37칸 정육각형 그리드 레이아웃 구성 ---
    def build_layout(self, W, H):
        self.stage_tiles.clear()
        self.last_size = (W, H)

        cx = W // 2
        cy = H // 2 + 20  # 화면 중앙보다 아주 약간 아래

        # 화면 크기에 따라 타일 크기 (조금 크게)
        base_size = min(W, H) * 0.055
        tile_size = max(24, min(44, int(base_size)))  # 너무 작거나 너무 크지 않게

        # 링 간격 보정 계수 (0이면 딱 붙는 정육각형, 값이 클수록 링 사이가 넓어짐)
        ring_gap_scale = 0.10

        # radius = 3 인 정육각형 그리드 생성 (총 37칸)
        grid = HexGrid(3)
        cells = list(grid.cells)

        # 셀을 "ring(0~3) → 각도" 순으로 정렬해서
        # 1(센터) → 2~7 → 8~19 → 20~37 순으로 스테이지 번호를 부여한다.
        def sort_key(pos):
            q, r = pos
            ring = cube_len(q, r)  # 0(중앙), 1, 2, 3
            if ring == 0:
                angle = -math.pi / 2  # 중앙은 그냥 고정
            else:
                x, y = axial_to_pixel(q, r, 1.0)  # 방향만 필요하므로 size=1.0
                angle = math.atan2(y, x)
            return (ring, angle)

        cells.sort(key=sort_key)

        for idx, (q, r) in enumerate(cells, start=1):
            ring = cube_len(q, r)

            # axial → pixel (정면에서 본 평면 육각)
            px, py = axial_to_pixel(q, r, tile_size)

            # 링 번호에 따라 조금씩 바깥으로 더 밀어내서 링 간격을 띄운다
            # ring 0 → factor=1.0, ring 1 → 1+ring_gap_scale, ring 2 → 1+2*..., ...
            factor = 1.0 + ring_gap_scale * ring
            px *= factor
            py *= factor

            x = cx + px
            y = cy + py

            poly = hex_corners((x, y), tile_size - 2)

            # 상태 플래그
            is_unlocked = (idx <= self.max_unlocked)
            is_cleared = (idx < self.max_unlocked)
            locked = not is_unlocked
            stars = self.get_stage_stars(idx)  # ← 추가

            self.stage_tiles.append({
                "idx": idx,
                "center": (x, y),
                "poly": poly,
                "ring": ring,
                "cleared": is_cleared,
                "locked": locked,
                "stars": stars,
            })

        # 뒤로가기 버튼은 화면 좌상단 고정
        back_w, back_h = 100, 40
        pad = 20
        self.back_btn.rect.update(pad, pad, back_w, back_h)

    def get_stage_stars(self, idx: int) -> int:
        """저장된 최고 별 개수를 0~3 범위로 돌려준다."""
        m = getattr(self.game, "stage_best_stars", {})
        if not isinstance(m, dict):
            return 0

        if idx in m:
            v = m[idx]
        elif str(idx) in m:
            v = m[str(idx)]
        else:
            return 0

        try:
            return max(0, min(3, int(v)))
        except (TypeError, ValueError):
            return 0

    # --- 스테이지 시작 ---
    def start_level(self, idx: int):
        rel = stage_index_to_relpath(idx)  # "stages/basic/003.json" 같은 문자열
        path = os.path.join(self.game.BASE_DIR, rel)

        if not os.path.exists(path):
            print(f"[INFO] 스테이지 파일이 없습니다: {path}")
            return

        self.game.change_scene(GameplayScene(self.game, path))

    def go_title(self):
        self.game.change_scene(TitleScene(self.game))

    # --- 입력 처리 ---
    def handle_event(self, e):
        # 뒤로가기 버튼부터
        self.back_btn.handle_event(e)

        if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            mx, my = e.pos
            for tile in self.stage_tiles:
                if tile["locked"]:
                    continue
                if self._point_in_poly(mx, my, tile["poly"]):
                    self.start_level(tile["idx"])
                    break

    def update(self, dt):
        # 우주 배경 애니메이션 업데이트
        if hasattr(self, "bg"):
            self.bg.update(dt)

        self.glow_time += dt


    def draw(self, screen):
        size = screen.get_size()
        if size != self.last_size:
            self.build_layout(*size)

        W, H = size
        # 우주 배경 그리기
        if hasattr(self, "bg"):
            self.bg.draw(screen)
        else:
            screen.fill((12, 16, 26))

        # 진행도 기준
        max_u = self.max_unlocked
        current_diff = stage_difficulty_index(max_u)

        # 스테이지 육각 타일들
        for tile in self.stage_tiles:
            poly   = tile["poly"]
            cx, cy = tile["center"]
            idx    = tile["idx"]

            diff = stage_difficulty_index(idx)

            is_unlocked = (idx <= max_u)
            is_cleared  = (idx < max_u)      # 이미 클리어한 스테이지
            is_current  = (idx == max_u)     # 지금 막 도전 중인 스테이지

            # ---- 색상 팔레트 (파랑-회색 계열, 인게임과는 다른 디자인) ----
            if is_cleared:
                # 클리어: 푸른 보호막 느낌
                outer = (40, 70, 115)
                inner = (90, 155, 210)
                border = (190, 225, 255)
                text_color = (238, 246, 255)

            elif is_current:
                # 현재 도전 중인 스테이지
                outer = (60, 85, 135)
                inner = (100, 145, 195)
                border = (210, 235, 255)
                text_color = (240, 245, 255)

            elif (not is_unlocked) and diff == current_diff:
                # 현재 난이도 구간 안의 잠긴 칸 (예: basic 3 도전 중이면 basic 4~6)
                outer = (62, 68, 80)
                inner = (76, 82, 96)
                border = (110, 120, 142)
                text_color = (180, 188, 205)

            elif (not is_unlocked) and diff > current_diff:
                # 다음 난이도들 (아직 먼 구간): 더 어두운 회색
                outer = (28, 30, 38)
                inner = (20, 22, 30)
                border = (60, 66, 84)
                text_color = (120, 124, 140)

            else:
                # 그 외 (열려 있지만 아직 클리어 안 한 이전 난이도 등)
                outer = (72, 78, 92)
                inner = (88, 96, 112)
                border = (130, 142, 168)
                text_color = (225, 232, 245)

            # ---- 부드러운 halo 반지름 계산 (기존 poly로부터 추정) ----
            r_est = max(((vx - cx) ** 2 + (vy - cy) ** 2) ** 0.5 for (vx, vy) in poly)
            halo_poly = hex_corners((cx, cy), r_est + 4)

            halo_surf = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
            pygame.draw.polygon(halo_surf, (*outer, 40), halo_poly)
            screen.blit(halo_surf, (0, 0))

            # ---- 메인 육각형(outer + inner + border) ----
            pygame.draw.polygon(screen, outer, poly)

            inner_poly = self._inner_poly((cx, cy), poly, scale=0.80)
            pygame.draw.polygon(screen, inner, inner_poly)

            pygame.draw.polygon(screen, border, poly, width=2)

            # ---- 위쪽 하이라이트 ----
            hi_surf = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
            top_two = sorted(poly, key=lambda p: p[1])[:2]
            pygame.draw.line(
                hi_surf,
                (255, 255, 255, 35),
                top_two[0],
                top_two[1],
                width=2,
            )
            screen.blit(hi_surf, (0, 0))

            # ---- 스테이지 번호 ----
            label = f"{idx:02d}"
            txt = self.ui_font.render(label, True, text_color)
            screen.blit(txt, txt.get_rect(center=(cx, cy)))

            # 별 3개 스테이지에만 펄스 하이라이트
            if tile.get("stars", 0) >= 3:
                draw_stage_star_glow(screen, (cx, cy), poly, self.glow_time)

        # 뒤로가기 버튼
        self.back_btn.draw(screen)


# 3) 게임 플레이 래퍼: 기존 보드/렌더 사용
class GameplayScene(Scene):
    def __init__(self, game, stage_path):
        super().__init__(game)
        self.stage_path = stage_path
        self.font = self.game.load_font(20)

        W, H = self.game.WIDTH, self.game.HEIGHT
        self.bg = GameHexBackground((W, H))

        self.board, self.stage, self.hex_size = self.reload_board(stage_path)
        self.stage_label = self.stage_label_from(self.stage, stage_path)
        self.stage_index = path_to_stage_index(stage_path)

        # --- 튜토리얼 관련 상태 ---
        idx = path_to_stage_index(stage_path)
        self.is_tutorial_stage = (idx == 1)
        self.tutorial_active = False
        self.tutorial_pages = []
        self.tutorial_index = 0
        self.tutorial_btn_rects = {}

        if self.is_tutorial_stage and getattr(self.game, "max_unlocked_stage", 1) <= 1:
            self.load_tutorial_images()
            if self.tutorial_pages:
                self.tutorial_active = True

        # 클리어 모달
        self.modal_active = False
        self.modal_btn_rects = {}

        # 일시정지 모달 + 버튼
        self.pause_active = False
        self.pause_btn_rects = {}
        btn_w, btn_h = 100, 36
        pad = 16
        self.menu_button = Button(
            rect=(pad, pad, btn_w, btn_h),
            text="메뉴",
            font=self.game.load_font(18),
            on_click=self.open_pause_modal
        )
        self.apply_stage_bgm()

        self.reveal_anims = []
        self.reveal_anim_duration = 0.15  # 초 단위
        self.reveal_anim_wave_delay = 0.04    # flood fill 시 인접 칸 사이 딜레이(초)

        # JSON에서 시작 상태가 REVEALED인 칸에도 리빌 애니메이션 적용
        for q, r in self.stage.get("start_revealed", []):
            t = self.board.tiles.get((q, r))
            if t is not None and t.state == C_REVEALED and not t.is_mine:
                self.reveal_anims.append(
                    TileRevealAnim(q, r, duration=self.reveal_anim_duration)
                )

        self.hover_anim = None          # TileHoverAnim 인스턴스
        self.hover_tile = None          # (q, r) 또는 None
        
    # ----- 유틸 -----
    def load_stage(self, path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
        
    def apply_stage_bgm(self):
        """현재 stage_path에 맞는 BGM을 선택해서 재생."""
        idx = path_to_stage_index(self.stage_path)
        key = "main"

        if idx is None:
            key = "main"
        elif 2 <= idx <= 7:
            key = "basic"            # basic 스테이지 6개
        elif 8 <= idx <= 13:
            key = "intermediate_1"   # intermediate 1~6
        elif 14 <= idx <= 19:
            key = "intermediate_2"   # intermediate 7~12
        elif 20 <= idx <= 25:
            key = "advance_1"        # advance 1~6
        elif 26 <= idx <= 31:
            key = "advance_2"        # advance 7~12
        elif 32 <= idx <= 37:
            key = "advance_3"        # advance 13~18
        else:
            key = "main"             # 혹시 범위 밖이면 메인으로

        if hasattr(self.game, "play_bgm"):
            self.game.play_bgm(key)

        # --- 실수(오류 클릭) 애니메이션 ---
        self.mistake_anims = []
        # 한 번 흔들리는 전체 시간(초)
        self.mistake_anim_duration = 0.25
        # 흔들림 세기(픽셀) – 기본값은 타일 크기에 비례
        self.mistake_anim_amplitude = self.hex_size * 0.14
        
    def reload_board(self, path):
        st = self.load_stage(path)
        grid = HexGrid.from_stage(st)
        board = Board(grid, st)

        # 🔹 스테이지별 타일 크기 결정
        hex_size = st.get("hex_size") or st.get("tile_size") or HEX_SIZE
        hex_size = int(hex_size)

        return board, st, hex_size
    
    def open_pause_modal(self):
        # 클리어된 상태에서는 굳이 열 필요 없음
        if self.board.is_game_over and self.board.is_win:
            return
        self.pause_active = True

    def stage_label_from(self, st, path):
        if isinstance(st, dict) and "name" in st:
            return st["name"]
        m = re.search(r"(\d+)\.json$", path)
        return f"Stage {m.group(1)}" if m else path

    def next_stage_path(self, path):
        cur = path_to_stage_index(path)
        if cur is None:
            return path  # 숫자 못 뽑으면 그대로

        if cur >= TOTAL_STAGES:
            # 마지막 스테이지면 그대로 유지 (또는 나중에 엔딩씬으로 보내도 됨)
            return path

        nxt = cur + 1
        rel = stage_index_to_relpath(nxt)
        return os.path.join(self.game.BASE_DIR, rel)
    
    def on_stage_cleared(self):
        idx = path_to_stage_index(self.stage_path)
        if idx is not None and hasattr(self.game, "unlock_stage"):
            # 실수 횟수 → 별 개수 환산
            star_count = render_mod.calc_star_count(self.board.mistakes)
            # 잠금 해제 + 최고 별 기록 갱신
            self.game.unlock_stage(idx, TOTAL_STAGES, star_count=star_count)

    def load_tutorial_images(self):
        """assets/images/tutorial/tuto_01~04.png 로부터 튜토리얼 이미지 로드."""
        base = os.path.join(self.game.ASSET_DIR, "images", "tutorial")
        pages = []
        for i in range(1, 5):
            fname = f"tuto_{i:02d}.png"
            fpath = os.path.join(base, fname)
            if os.path.exists(fpath):
                img = pygame.image.load(fpath).convert_alpha()
                pages.append(img)
        self.tutorial_pages = pages
        self.tutorial_index = 0
        self.tutorial_btn_rects = {}

    def draw_tutorial_modal(self, screen):
        """튜토리얼 페이지를 화면 중앙에 띄우고, 버튼 rect들을 반환."""
        w, h = screen.get_size()
        btn_rects = {}

        # 어두운 오버레이
        overlay = pygame.Surface((w, h), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))

        if not self.tutorial_pages:
            return btn_rects

        panel_w = int(w * 0.75)
        panel_h = int(h * 0.75)
        panel_rect = pygame.Rect(0, 0, panel_w, panel_h)
        panel_rect.center = (w // 2, h // 2)

        pygame.draw.rect(screen, (20, 26, 46), panel_rect, border_radius=18)
        pygame.draw.rect(screen, (110, 130, 190), panel_rect, width=2, border_radius=18)

        # 현재 페이지 이미지
        img = self.tutorial_pages[self.tutorial_index]
        iw, ih = img.get_size()

        # 위쪽: 건너뛰기 텍스트용 여백 + 약간의 공간
        top_margin = 72  # 기존 32보다 훨씬 아래에서 시작

        # 아래쪽: 페이지 번호 + 버튼 영역 여백
        bottom_reserved = 120

        max_iw = panel_w - 60
        max_ih = panel_h - (top_margin + bottom_reserved)
        scale = min(max_iw / iw, max_ih / ih, 1.0)
        if scale < 1.0:
            img_disp = pygame.transform.smoothscale(img, (int(iw * scale), int(ih * scale)))
        else:
            img_disp = img
        img_rect = img_disp.get_rect(midtop=(panel_rect.centerx, panel_rect.top + 32))
        screen.blit(img_disp, img_rect)

        # 페이지 표시
        page_text = f"{self.tutorial_index + 1} / {len(self.tutorial_pages)}"
        label = self.font.render(page_text, True, (220, 230, 245))
        label_rect = label.get_rect(midtop=(panel_rect.centerx, img_rect.bottom + 8))
        screen.blit(label, label_rect)

        # 버튼들 (이전 / 다음 or 시작하기 / 건너뛰기)
        btn_w, btn_h = 120, 40
        gap = 24
        y = panel_rect.bottom - 30 - btn_h
        center_x = panel_rect.centerx

        # 이전 버튼
        if self.tutorial_index > 0:
            prev_rect = pygame.Rect(center_x - btn_w - gap // 2, y, btn_w, btn_h)
            pygame.draw.rect(screen, (40, 50, 96), prev_rect, border_radius=14)
            pygame.draw.rect(screen, (120, 140, 210), prev_rect, width=2, border_radius=14)
            txt = self.font.render("이전", True, (234, 242, 255))
            screen.blit(txt, txt.get_rect(center=prev_rect.center))
            btn_rects["prev"] = prev_rect

        # 다음 / 시작하기 버튼
        next_label = "다음" if self.tutorial_index < len(self.tutorial_pages) - 1 else "시작하기"
        next_rect = pygame.Rect(center_x + (0 if self.tutorial_index == 0 else gap // 2),
                                y, btn_w, btn_h)
        pygame.draw.rect(screen, (70, 92, 160), next_rect, border_radius=14)
        pygame.draw.rect(screen, (150, 170, 230), next_rect, width=2, border_radius=14)
        txt = self.font.render(next_label, True, (240, 245, 255))
        screen.blit(txt, txt.get_rect(center=next_rect.center))
        btn_rects["next"] = next_rect

        # 우측 상단 건너뛰기 (선택)
        skip_text = self.font.render("건너뛰기", True, (200, 210, 230))
        skip_rect = skip_text.get_rect()
        pad = 18
        skip_rect.topright = (panel_rect.right - pad, panel_rect.top + pad)
        screen.blit(skip_text, skip_rect)
        btn_rects["skip"] = skip_rect

        return btn_rects


    # ----- 이벤트 -----
    def handle_event(self, e):
        # 0) 튜토리얼 모달이 켜져 있으면, 다른 입력은 모두 막고 여기서만 처리
        if self.tutorial_active:
            # 마우스 클릭으로 버튼 처리
            if (
                e.type == pygame.MOUSEBUTTONDOWN
                and e.button == 1
                and self.tutorial_btn_rects
            ):
                mx, my = e.pos
                if "skip" in self.tutorial_btn_rects and self.tutorial_btn_rects["skip"].collidepoint(mx, my):
                    self.tutorial_active = False
                    return
                if "prev" in self.tutorial_btn_rects and self.tutorial_btn_rects["prev"].collidepoint(mx, my):
                    if self.tutorial_index > 0:
                        self.tutorial_index -= 1
                    return
                if "next" in self.tutorial_btn_rects and self.tutorial_btn_rects["next"].collidepoint(mx, my):
                    if self.tutorial_index < len(self.tutorial_pages) - 1:
                        self.tutorial_index += 1
                    else:
                        self.tutorial_active = False
                    return

            # 키보드로 페이지 넘기기 / 종료
            if e.type == pygame.KEYDOWN:
                if e.key in (pygame.K_SPACE, pygame.K_RETURN):
                    if self.tutorial_index < len(self.tutorial_pages) - 1:
                        self.tutorial_index += 1
                    else:
                        self.tutorial_active = False
                    return
                elif e.key == pygame.K_ESCAPE:
                    self.tutorial_active = False
                    return

            # 튜토리얼 중에는 다른 입력 무시
            return

        # ESC
        if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
            if self.modal_active:
                return
            self.pause_active = not self.pause_active
            return
        
        if not self.modal_active and not self.pause_active:
            self.menu_button.handle_event(e)

        # ----- 마우스 클릭 처리 -----
        if e.type == pygame.MOUSEBUTTONDOWN:
            w, h = self.game.WIDTH, self.game.HEIGHT
            cx, cy = w // 2, h // 2

            # 1) 클리어 모달 버튼
            if self.modal_active and e.button == 1 and self.modal_btn_rects:
                mx, my = e.pos
                if self.modal_btn_rects["retry"].collidepoint(mx, my):
                    # 현재 스테이지 재시도
                    self.board, self.stage, self.hex_size = self.reload_board(self.stage_path)
                    self.stage_label = self.stage_label_from(self.stage, self.stage_path)

                    self.reveal_anims.clear()
                    self.mistake_anims.clear()
                    self.hover_anim = None
                    self.hover_tile = None

                    self.modal_active = False
                    self.modal_btn_rects = {}
                elif self.modal_btn_rects["menu"].collidepoint(mx, my):
                    # 레벨 선택 화면으로
                    self.game.change_scene(LevelSelectScene(self.game))
                elif "next" in self.modal_btn_rects and self.modal_btn_rects["next"].collidepoint(mx, my):
                    # 다음 스테이지로 진행
                    nxt = self.next_stage_path(self.stage_path)
                    if os.path.exists(nxt):
                        self.stage_path = nxt
                        self.board, self.stage, self.hex_size = self.reload_board(self.stage_path)
                        self.stage_label = self.stage_label_from(self.stage, self.stage_path)
                        self.stage_index = path_to_stage_index(self.stage_path)
                        self.modal_active = False
                        self.modal_btn_rects = {}
                return  # 모달 중엔 아래 입력 무시

            # 2) 일시정지 모달 버튼
            if self.pause_active and e.button == 1 and self.pause_btn_rects:
                mx, my = e.pos
                if self.pause_btn_rects["resume"].collidepoint(mx, my):
                    if hasattr(self.game, "play_ui_click"):
                        self.game.play_ui_click()
                    self.pause_active = False
                    self.pause_btn_rects = {}
                elif self.pause_btn_rects["level"].collidepoint(mx, my):
                    if getattr(self.game, "max_unlocked_stage", 1) <= 1:
                        self.game.change_scene(TitleScene(self.game))
                    else:
                        self.game.change_scene(LevelSelectScene(self.game))
                elif self.pause_btn_rects["restart"].collidepoint(mx, my):
                    if hasattr(self.game, "play_ui_click"):
                        self.game.play_ui_click()
                    self.board, self.stage, self.hex_size = self.reload_board(self.stage_path)
                    self.stage_label = self.stage_label_from(self.stage, self.stage_path)
                    self.pause_active = False
                    self.pause_btn_rects = {}
                return  # 모달 중에는 보드 입력 막음

            # 3) 테두리 숫자 클릭 처리
            if not self.modal_active and not self.pause_active:
                idx = render_mod.edge_hint_hit_test(
                    self.board, (cx, cy), self.hex_size, e.pos
                )
                if idx is not None:
                    ent = self.board.edge_hints[idx]
                    if e.button == 1:
                        ent["helper_on"] = not ent.get("helper_on", False)
                    elif e.button == 3:
                        ent["dimmed"] = not ent.get("dimmed", False)
                        ent["helper_on"] = False
                    return  # 숫자를 눌렀으면 보드에는 클릭 전달 안 함

            # 4) 보드 타일 클릭 처리
            if not self.modal_active and not self.pause_active:
                mx, my = pygame.mouse.get_pos()
                lx, ly = mx - cx, my - cy
                q, r = pixel_to_axial(lx, ly, self.hex_size)
                if (q, r) in self.board.tiles:
                    # 사운드 판별을 위해 이전 상태 저장
                    old_mistakes = self.board.mistakes
                    old_revealed = getattr(self.board, "revealed_count", 0)
                    old_flags    = getattr(self.board, "flag_count", 0)

                    # 애니메이션 판정을 위해 클릭 전 상태 저장
                    t_before = self.board.tiles.get((q, r))
                    prev_state = t_before.state if t_before is not None else None
                    prev_is_mine = t_before.is_mine if t_before is not None else False

                    if e.button == 1:
                        self.board.reveal(q, r)
                    elif e.button == 3:
                        self.board.toggle_flag(q, r)

                    # 실수 증가 여부 체크
                    if self.board.mistakes > old_mistakes:
                        if hasattr(self.game, "play_tile_click"):
                            self.game.play_tile_click(ok=False)

                        # 🔹 실수한 타일에 흔들림 애니메이션 추가
                        if hasattr(self, "mistake_anims"):
                            self.mistake_anims.append(
                                TileShakeAnim(
                                    q, r,
                                    duration=self.mistake_anim_duration,
                                    amplitude=self.mistake_anim_amplitude,
                                )
                            )

                    else:
                        new_revealed = getattr(self.board, "revealed_count", 0)
                        new_flags    = getattr(self.board, "flag_count", 0)
                        if (new_revealed > old_revealed) or (new_flags != old_flags):
                            if hasattr(self.game, "play_tile_click"):
                                self.game.play_tile_click(ok=True)

                    # 리빌 애니메이션 생성
                    t_after = self.board.tiles.get((q, r))
                    if (
                        e.button == 1
                        and t_after is not None
                        and not prev_is_mine
                        and prev_state != C_REVEALED
                        and t_after.state == C_REVEALED
                        and self.board.mistakes == old_mistakes
                    ):
                        self.reveal_anims.append(
                            TileRevealAnim(q, r, duration=self.reveal_anim_duration)
                        )

        # ----- 마우스 호버 처리 -----
        if e.type == pygame.MOUSEMOTION:
            # 튜토리얼 / 모달 / 일시정지 중에는 호버 꺼두기
            if self.tutorial_active or self.modal_active or self.pause_active:
                self.hover_anim = None
                self.hover_tile = None
                return

            w, h = self.game.WIDTH, self.game.HEIGHT
            cx, cy = w // 2, h // 2
            mx, my = e.pos
            lx, ly = mx - cx, my - cy

            q, r = pixel_to_axial(lx, ly, self.hex_size)
            t = self.board.tiles.get((q, r))

            # 보드 밖이거나, BLOCKED / REVEALED 타일이면 호버 없음
            if t is None or t.state in (C_BLOCKED, C_REVEALED):
                if self.hover_tile is not None:
                    self.hover_tile = None
                    self.hover_anim = None
                return

            # 여기서부터는 "reveal되지 않은 타일" (C_COVERED, C_FLAGGED 등)
            # → 타일 밖으로 나갔다가 다시 들어올 때마다 새로 애니/사운드
            if self.hover_tile != (q, r):
                self.hover_tile = (q, r)
                self.hover_anim = TileHoverAnim(q, r)

                if hasattr(self.game, "play_tile_hover"):
                    self.game.play_tile_hover()


    # ----- 프레임 -----
    def update(self, dt):
        if hasattr(self, "bg"):
            self.bg.update(dt)

        # 클리어 모달 처리
        if self.board.is_game_over and self.board.is_win:
            # 아직 클리어 모달이 안 켜졌다면, 이번이 첫 클리어 프레임
            if not self.modal_active:
                self.on_stage_cleared()
            self.modal_active = True

        # 타일 리빌 애니메이션 업데이트
        if self.reveal_anims:
            alive = []
            for anim in self.reveal_anims:
                anim.update(dt)
                if not anim.finished:
                    alive.append(anim)
            self.reveal_anims = alive

        if self.mistake_anims:
            alive = []
            for anim in self.mistake_anims:
                anim.update(dt)
                if not anim.finished:
                    alive.append(anim)
            self.mistake_anims = alive

        if self.hover_anim is not None:
            self.hover_anim.update(dt)


    def draw(self, screen):
        # 배경 그리기
        size = screen.get_size()
        if hasattr(self, "bg"):
            if self.bg.size != size:
                self.bg.resize(size)
            self.bg.draw(screen)
        else:
            screen.fill((0, 0, 0))

        # 현재 화면 크기 기준 중앙 좌표
        w, h = screen.get_size()
        center = (w // 2, h // 2)

        render_mod.draw_board(screen, self.board, center, self.hex_size, self.font)
        render_mod.draw_edge_hints(screen, self.board, center, self.hex_size, self.font)
        render_mod.draw_topright_info(screen, self.board, self.font)

        if self.hover_anim is not None and self.hover_tile is not None:
            draw_hover_anim(screen, self.hover_anim, center, self.hex_size)

        draw_reveal_anims(screen, self.reveal_anims, center, self.hex_size)
        draw_shake_anims(screen, self.mistake_anims, center, self.hex_size)

        self.menu_button.draw(screen)

        if self.tutorial_active:
            self.tutorial_btn_rects = self.draw_tutorial_modal(screen)
            return
    
        if self.pause_active:
            # 🔹 튜토리얼(1번 스테이지 + 아직 2번이 안 열린 상태)인 경우
            is_tutorial = (
                getattr(self.game, "max_unlocked_stage", 1) <= 1
            )
            self.pause_btn_rects = render_mod.draw_pause_modal(
                screen,
                self.stage_label,
                self.board.mistakes,
                self.font,
                is_tutorial=is_tutorial,
            )

        if self.modal_active:
            # 튜토리얼 / basic / intermediate / advance 마지막 스테이지에서는 다음 스테이지 버튼 숨김
            show_next = self.stage_index not in MAJOR_STEP_LAST_INDICES
            self.modal_btn_rects = render_mod.draw_success_modal(
                screen,
                self.stage_label,
                self.board.mistakes,
                self.font,
                show_next=show_next,
            )