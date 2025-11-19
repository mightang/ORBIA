# core/scenes.py
import os, json, re
import pygame
from core.ui import Button, draw_label_center
from core import render as render_mod
from core.board import Board
from core.grid import HexGrid
from core.hexmath import pixel_to_axial
from settings import BOARD_CENTER, HEX_SIZE, WIDTH, HEIGHT

TOTAL_STAGES = 37

def stage_index_to_relpath(idx: int) -> str:
    """
    1~37 스테이지 번호를 받아서
    stages/tutorial/001.json 같은 상대 경로를 돌려준다.
    """
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
        self.start_btn = Button(
            rect=( (W-btn_w)//2, int(H*0.55), btn_w, btn_h ),
            text="시작하기",
            font=self.ui_font,
            on_click=self._go_level_select
        )

    def _go_level_select(self):
        self.game.change_scene(LevelSelectScene(self.game))

    def handle_event(self, e):
        self.start_btn.handle_event(e)

    def draw(self, screen):
        screen.fill((14,18,32))
        draw_label_center(screen, "GAME TITLE", self.title_font, (self.game.WIDTH//2, int(self.game.HEIGHT*0.35)))
        self.start_btn.draw(screen)

# 2) 레벨 선택 (1~37)
class LevelSelectScene(Scene):
    def __init__(self, game, total=37):
        super().__init__(game)
        self.total = total
        self.title_font = self.game.load_font(36)
        self.ui_font = self.game.load_font(20)
        self.buttons = self._build_buttons()

        # 뒤로가기 버튼
        btn_w, btn_h = 100, 40
        pad = 20
        self.back_btn = Button(
            rect=(pad, pad, btn_w, btn_h),
            text="뒤로가기",
            font=self.ui_font,
            on_click=self.go_title
        )

    def _build_buttons(self):
        W, H = self.game.WIDTH, self.game.HEIGHT
        cols = 10                # 1~37을 보기 좋게 그리드 배치
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
            def make_cb(idx=i):
                def _cb():
                    self._start_level(idx)
                return _cb
            btns.append(Button((x, y, btn_w, btn_h), label, self.ui_font, make_cb()))
        return btns

    def _start_level(self, idx):
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
        draw_label_center(screen, "레벨 선택", self.title_font, (self.game.WIDTH//2, int(self.game.HEIGHT*0.14)))
        for b in self.buttons:
            b.draw(screen)
        self.back_btn.draw(screen)

# 3) 게임 플레이 래퍼: 기존 보드/렌더 사용
class GameplayScene(Scene):
    def __init__(self, game, stage_path):
        super().__init__(game)
        self.stage_path = stage_path
        self.font = self.game.load_font(20)

        self.board, self.stage, self.hex_size = self._reload_board(stage_path)
        self.stage_label = self._stage_label_from(self.stage, stage_path)

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
            on_click=self._open_pause_modal
        )

        
    # ----- 유틸 -----
    def _load_stage(self, path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
        
    def _reload_board(self, path):
        st = self._load_stage(path)
        grid = HexGrid.from_stage(st)
        board = Board(grid, st)

        # 🔹 스테이지별 타일 크기 결정
        hex_size = st.get("hex_size") or st.get("tile_size") or HEX_SIZE
        hex_size = int(hex_size)

        return board, st, hex_size
    
    def _open_pause_modal(self):
        # 클리어된 상태에서는 굳이 열 필요 없음
        if self.board.is_game_over and self.board.is_win:
            return
        self.pause_active = True

    def _stage_label_from(self, st, path):
        if isinstance(st, dict) and "name" in st:
            return st["name"]
        m = re.search(r"(\d+)\.json$", path)
        return f"Stage {m.group(1)}" if m else path

    def _next_stage_path(self, path):
        cur = path_to_stage_index(path)
        if cur is None:
            return path  # 숫자 못 뽑으면 그대로

        if cur >= TOTAL_STAGES:
            # 마지막 스테이지면 그대로 유지 (또는 나중에 엔딩씬으로 보내도 됨)
            return path

        nxt = cur + 1
        rel = stage_index_to_relpath(nxt)
        return os.path.join(self.game.BASE_DIR, rel)

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
                    self.board, self.stage, self.hex_size = self._reload_board(self.stage_path)
                    self.stage_label = self._stage_label_from(self.stage, self.stage_path)
                    self.modal_active = False
                    self.modal_btn_rects = {}
                elif self.modal_btn_rects["menu"].collidepoint(mx, my):
                    self.game.change_scene(LevelSelectScene(self.game))
                elif self.modal_btn_rects["next"].collidepoint(mx, my):
                    nxt = self._next_stage_path(self.stage_path)
                    if os.path.exists(nxt):
                        self.stage_path = nxt
                        self.board, self.stage, self.hex_size = self._reload_board(self.stage_path)
                        self.stage_label = self._stage_label_from(self.stage, self.stage_path)
                        self.modal_active = False
                        self.modal_btn_rects = {}
                return  # 모달 중엔 아래 입력 무시
            
            # 2) 일시정지 모달이 활성화된 경우: 일시정지 모달 버튼만 처리
            if self.pause_active and e.button == 1 and self.pause_btn_rects:
                mx, my = e.pos
                if self.pause_btn_rects["resume"].collidepoint(mx, my):
                    # 계속하기
                    self.pause_active = False
                    self.pause_btn_rects = {}
                elif self.pause_btn_rects["level"].collidepoint(mx, my):
                    # 레벨 선택으로
                    self.game.change_scene(LevelSelectScene(self.game))
                elif self.pause_btn_rects["restart"].collidepoint(mx, my):
                    # 현재 스테이지 처음부터
                    self.board, self.stage, self.hex_size = self._reload_board(self.stage_path)
                    self.stage_label = self._stage_label_from(self.stage, self.stage_path)
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
                if e.button == 1:
                    self.board.reveal(q, r)
                elif e.button == 3:
                    self.board.toggle_flag(q, r)

    # ----- 프레임 -----
    def update(self, dt):
        if self.board.is_game_over and self.board.is_win:
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