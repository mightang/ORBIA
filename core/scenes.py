# core/scenes.py
import os, json, re
import pygame
from core.ui import Button, draw_label_center, Slider
from core import render as render_mod
from core.board import Board
from core.grid import HexGrid
from core.hexmath import pixel_to_axial
from settings import BOARD_CENTER, HEX_SIZE, WIDTH, HEIGHT

TOTAL_STAGES = 37

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

        btn_w, btn_h = 240, 56
        center_x = (W - btn_w) // 2
        base_y = int(H * 0.45)
        gap = 12

        self.start_btn = Button(
            rect=(center_x, base_y, btn_w, btn_h),
            text="시작하기",
            font=self.ui_font,
            on_click=self.go_level_select
        )
        self.option_btn = Button(
            rect=(center_x, base_y + (btn_h + gap), btn_w, btn_h),
            text="옵션",
            font=self.ui_font,
            on_click=self.go_options
        )
        self.credit_btn = Button(
            rect=(center_x, base_y + 2 * (btn_h + gap), btn_w, btn_h),
            text="크레딧",
            font=self.ui_font,
            on_click=self.go_credits
        )
        self.quit_btn = Button(
            rect=(center_x, base_y + 3 * (btn_h + gap), btn_w, btn_h),
            text="게임 종료",
            font=self.ui_font,
            on_click=self.quit_game
        )
        if hasattr(self.game, "play_bgm"):
            self.game.play_bgm("main")

    def go_level_select(self):
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

    def draw(self, screen):
        screen.fill((14,18,32))
        draw_label_center(
            screen, "GAME TITLE",
            self.title_font,
            (self.game.WIDTH//2, int(self.game.HEIGHT*0.28))
        )
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
        btn_w, btn_h = 150, 40
        gap = 20
        count = len(self.game.resolutions)
        total_w = count * btn_w + (count-1) * gap
        start_x = (W - total_w) // 2

        for i, (rw, rh) in enumerate(self.game.resolutions):
            x = start_x + i * (btn_w + gap)
            label = f"{rw}x{rh}"
            def make_cb(idx=i):
                def cb():
                    self.select_resolution(idx)
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
        if hasattr(self.game, "play_bgm"):
            self.game.play_bgm("main")

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
        # 해상도 변경 후, 옵션 씬을 새로 만들어 레이아웃 재계산
        self.game.set_resolution(idx)
        self.game.change_scene(OptionsScene(self.game))

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

    def update(self, dt):
        pass

    def draw(self, screen):
        screen.fill((10, 14, 24))
        W, H = self.game.WIDTH, self.game.HEIGHT

        # 제목
        draw_label_center(screen, "옵션", self.title_font, (W//2, int(H*0.16)))

        # 라벨 텍스트
        bgm_label = self.ui_font.render("배경 음악 볼륨", True, (234,242,255))
        sfx_label = self.ui_font.render("효과음 볼륨", True, (234,242,255))
        res_label = self.ui_font.render("화면 크기 (해상도)", True, (234,242,255))

        screen.blit(bgm_label, (self.bgm_slider.rect.left,
                                self.bgm_slider.rect.top - 32))
        screen.blit(sfx_label, (self.sfx_slider.rect.left,
                                self.sfx_slider.rect.top - 32))

        res_y = self.sfx_slider.rect.top + 80
        screen.blit(res_label, (self.bgm_slider.rect.left, res_y - 36))

        # 슬라이더/버튼 그리기
        self.bgm_slider.draw(screen)
        self.sfx_slider.draw(screen)
        for i, b in enumerate(self.res_buttons):
            # 선택된 해상도는 살짝 밝게
            if i == self.game.res_index:
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
            on_click=self._back_to_title
        )

        # 임시 크레딧 텍스트
        self.lines = [
            "HEXFIELD (임시 타이틀)",
            "",
            "기획 / 구현 : 김태영",
            "도움 : ChatGPT",
            "",
            "감사합니다!"
        ]
        if hasattr(self.game, "play_bgm"):
            self.game.play_bgm("main")

    def _back_to_title(self):
        self.game.change_scene(TitleScene(self.game))

    def handle_event(self, e):
        if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
            self._back_to_title()
            return
        self.back_btn.handle_event(e)

    def update(self, dt):
        pass

    def draw(self, screen):
        screen.fill((12, 16, 26))
        W, H = self.game.WIDTH, self.game.HEIGHT

        draw_label_center(screen, "크레딧", self.title_font, (W//2, int(H*0.18)))

        # 여러 줄 텍스트 중앙 정렬
        total_h = 0
        rendered = []
        for s in self.lines:
            img = self.ui_font.render(s, True, (234,242,255))
            rendered.append(img)
            total_h += img.get_height() + 4

        y = int(H*0.35) - total_h//2
        for img in rendered:
            rect = img.get_rect(center=(W//2, y))
            screen.blit(img, rect)
            y += img.get_height() + 4

        self.back_btn.draw(screen)
        


# 2) 레벨 선택 (1~37)
class LevelSelectScene(Scene):
    def __init__(self, game, total=37):
        super().__init__(game)
        self.total = total
        self.title_font = self.game.load_font(36)
        self.ui_font = self.game.load_font(20)
        self.max_unlocked = getattr(self.game, "max_unlocked_stage", 1)
        self.buttons = self.build_buttons()

        # 뒤로가기 버튼
        btn_w, btn_h = 100, 40
        pad = 20
        self.back_btn = Button(
            rect=(pad, pad, btn_w, btn_h),
            text="뒤로가기",
            font=self.ui_font,
            on_click=self.go_title
        )
        if hasattr(self.game, "play_bgm"):
            self.game.play_bgm("main")

    def build_buttons(self):
        W, H = self.game.WIDTH, self.game.HEIGHT
        cols = 10
        gap = 12
        btn_w, btn_h = 64, 40
        grid_w = cols*btn_w + (cols-1)*gap
        start_x = (W - grid_w)//2
        start_y = int(H*0.25)

        btns = []
        for i in range(1, self.total+1):
            row = (i-1)//cols
            col = (i-1)%cols
            x = start_x + col*(btn_w+gap)
            y = start_y + row*(btn_h+gap)
            label = f"{i:02d}"

            locked = (i > self.max_unlocked)

            def make_cb(idx=i):
                def _cb():
                    self.start_level(idx)
                return _cb
            on_click = None if locked else make_cb()

            b = Button((x, y, btn_w, btn_h), label, self.ui_font, on_click)
            b.locked = locked
            btns.append(b)
        return btns

    def start_level(self, idx):
        # 번호 → 폴더 포함 상대 경로로 변환
        rel = stage_index_to_relpath(idx)  # "stages/basic/003.json" 같은 문자열
        path = os.path.join(self.game.BASE_DIR, rel)

        if not os.path.exists(path):
            print(f"[INFO] 스테이지 파일이 없습니다: {path}")
            return

        self.game.change_scene(GameplayScene(self.game, path))

    def go_title(self):
        self.game.change_scene(TitleScene(self.game))

    def handle_event(self, e):
        self.back_btn.handle_event(e)     # ← 추가
        for b in self.buttons:
            b.handle_event(e)

    def draw(self, screen):
        screen.fill((18,22,36))
        draw_label_center(screen, "레벨 선택", self.title_font,
                          (self.game.WIDTH//2, int(self.game.HEIGHT*0.14)))
        for b in self.buttons:
            if getattr(b, "locked", False):
                # 잠긴 스테이지: 어둡게 + 텍스트 흐리게
                b.bg = (30, 30, 40)
                b.fg = (120, 120, 140)
            else:
                b.bg = (40, 46, 60)
                b.fg = (234, 242, 255)
            b.draw(screen)
        self.back_btn.draw(screen)

# 3) 게임 플레이 래퍼: 기존 보드/렌더 사용
class GameplayScene(Scene):
    def __init__(self, game, stage_path):
        super().__init__(game)
        self.stage_path = stage_path
        self.font = self.game.load_font(20)

        self.board, self.stage, self.hex_size = self.reload_board(stage_path)
        self.stage_label = self.stage_label_from(self.stage, stage_path)

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
            self.game.unlock_stage(idx, TOTAL_STAGES)


    # ----- 이벤트 -----
    def handle_event(self, e):
        if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
            if self.modal_active:
                return
            self.pause_active = not self.pause_active
            return
        
        if not self.modal_active and not self.pause_active:
            self.menu_button.handle_event(e)

        if e.type == pygame.MOUSEBUTTONDOWN:
            # 클리어 모달 활성화 시 버튼만 처리
            if self.modal_active and e.button == 1 and self.modal_btn_rects:
                mx, my = e.pos
                if self.modal_btn_rects["retry"].collidepoint(mx, my):
                    if hasattr(self.game, "play_ui_click"):
                        self.game.play_ui_click()
                    self.board, self.stage, self.hex_size = self.reload_board(self.stage_path)
                    self.stage_label = self.stage_label_from(self.stage, self.stage_path)
                    self.modal_active = False
                    self.modal_btn_rects = {}
                elif self.modal_btn_rects["menu"].collidepoint(mx, my):
                    if hasattr(self.game, "play_ui_click"):
                        self.game.play_ui_click()
                    self.game.change_scene(LevelSelectScene(self.game))
                elif self.modal_btn_rects["next"].collidepoint(mx, my):
                    if hasattr(self.game, "play_ui_click"):
                        self.game.play_ui_click()
                    nxt = self.next_stage_path(self.stage_path)
                    if os.path.exists(nxt):
                        self.stage_path = nxt
                        self.board, self.stage, self.hex_size = self.reload_board(self.stage_path)
                        self.stage_label = self.stage_label_from(self.stage, self.stage_path)
                        self.apply_stage_bgm() 
                        self.modal_active = False
                        self.modal_btn_rects = {}
                return  # 모달 중엔 아래 입력 무시
            
            # 2) 일시정지 모달이 활성화된 경우: 일시정지 모달 버튼만 처리
            if self.pause_active and e.button == 1 and self.pause_btn_rects:
                mx, my = e.pos
                if self.pause_btn_rects["resume"].collidepoint(mx, my):
                    if hasattr(self.game, "play_ui_click"):
                        self.game.play_ui_click()
                    self.pause_active = False
                    self.pause_btn_rects = {}
                elif self.pause_btn_rects["level"].collidepoint(mx, my):
                    if hasattr(self.game, "play_ui_click"):
                        self.game.play_ui_click()
                    self.game.change_scene(LevelSelectScene(self.game))
                elif self.pause_btn_rects["restart"].collidepoint(mx, my):
                    if hasattr(self.game, "play_ui_click"):
                        self.game.play_ui_click()
                    self.board, self.stage, self.hex_size = self.reload_board(self.stage_path)
                    self.stage_label = self.stage_label_from(self.stage, self.stage_path)
                    self.pause_active = False
                    self.pause_btn_rects = {}
                return  # 모달 중에는 보드 입력 막음
            
            # 3) (새로 추가) 테두리 숫자 클릭 처리
            if not self.modal_active and not self.pause_active:
                idx = render_mod.edge_hint_hit_test(
                    self.board, BOARD_CENTER, self.hex_size, self.font, e.pos
                )
                if idx is not None:
                    ent = self.board.edge_hints[idx]
                    if e.button == 1:
                        # 좌클릭: 보조선 토글
                        ent["helper_on"] = not ent.get("helper_on", False)
                    elif e.button == 3:
                        # 우클릭: 숫자 흐리게 토글 + 보조선 끄기
                        ent["dimmed"] = not ent.get("dimmed", False)
                        ent["helper_on"] = False
                    return  # 숫자를 눌렀으면 보드에는 클릭 전달 안 함

            # 4) 평소 입력: 픽셀→육각 좌표 변환 후 Board API 호출
            mx, my = pygame.mouse.get_pos()
            lx, ly = mx - BOARD_CENTER[0], my - BOARD_CENTER[1]
            q, r = pixel_to_axial(lx, ly, self.hex_size)
            if (q, r) in self.board.tiles:
                # 사운드 판별을 위해 이전 상태 저장
                old_mistakes = self.board.mistakes
                old_revealed = getattr(self.board, "revealed_count", 0)
                old_flags    = getattr(self.board, "flag_count", 0)

                if e.button == 1:
                    self.board.reveal(q, r)
                elif e.button == 3:
                    self.board.toggle_flag(q, r)

                # 실수 증가 여부 체크
                if self.board.mistakes > old_mistakes:
                    # 잘못 클릭 (실수 증가)
                    if hasattr(self.game, "play_tile_click"):
                        self.game.play_tile_click(ok=False)
                else:
                    # 실수는 아니지만, 실제로 뭔가 상태가 바뀐 경우에만 "옳은 클릭"으로 취급
                    new_revealed = getattr(self.board, "revealed_count", 0)
                    new_flags    = getattr(self.board, "flag_count", 0)
                    if (new_revealed > old_revealed) or (new_flags != old_flags):
                        if hasattr(self.game, "play_tile_click"):
                            self.game.play_tile_click(ok=True)

    # ----- 프레임 -----
    def update(self, dt):
        if self.board.is_game_over and self.board.is_win:
            # 아직 클리어 모달이 안 켜졌다면, 이번이 첫 클리어 프레임
            if not self.modal_active:
                self.on_stage_cleared()
            self.modal_active = True

    def draw(self, screen):
        screen.fill((16,20,32))
        render_mod.draw_board(screen, self.board, BOARD_CENTER, self.hex_size, self.font)
        render_mod.draw_edge_hints(screen, self.board, BOARD_CENTER, self.hex_size, self.font)
        render_mod.draw_topright_info(screen, self.board, self.font)

        self.menu_button.draw(screen)

        if self.pause_active:
            self.pause_btn_rects = render_mod.draw_pause_modal(
                screen, self.stage_label, self.board.mistakes, self.font
            )

        if self.modal_active:
            self.modal_btn_rects = render_mod.draw_success_modal(
                screen, self.stage_label, self.board.mistakes, self.font
            )