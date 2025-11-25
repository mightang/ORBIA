import os
import pygame, sys, json, re
from core.grid import HexGrid
from core.board import Board
from core.render import (
    draw_board, draw_edge_hints, draw_topright_info, draw_success_modal,
    edge_hint_hit_test,
)
from core.hexmath import pixel_to_axial
from settings import WIDTH, HEIGHT, BOARD_CENTER, COL_BG
from settings import HEX_SIZE as DEFAULT_HEX

def load_font():
    # 1순위: 동봉 폰트
    if os.path.exists("assets/fonts/PretendardVariable.ttf"):
        return pygame.font.Font("assets/fonts/PretendardVariable.ttf", 22)

    candidates = [
        "malgungothic",          # Windows: 맑은 고딕
        "noto sans cjk kr",      # Noto CJK
        "noto sans kr",
        "applegothic",           # macOS
        "nanumgothic", "nanum gothic"
    ]
    for name in candidates:
        try:
            f = pygame.font.SysFont(name, 22)
            _ = f.render("한글 테스트", True, (255, 255, 255))
            return f
        except Exception:
            continue

    # 3순위: 최후의 폴백(한글 미보장)
    return pygame.font.SysFont(None, 22)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
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
    else:
        subdir = "advance"

    return os.path.join("stages", subdir, f"{num:03d}.json")

def path_to_stage_index(path: str):
    m = re.search(r"(\d+)\.json$", path)
    return int(m.group(1)) if m else None


def load_stage(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def stage_label_from(st, path):
    if isinstance(st, dict) and "name" in st:
        return st["name"]
    m = re.search(r"(\d+)\.json$", path)
    return f"Stage {m.group(1)}" if m else path

def next_stage_path(path):
    cur = path_to_stage_index(path)
    if cur is None or cur >= TOTAL_STAGES:
        return path
    nxt = cur + 1
    return os.path.join(BASE_DIR, stage_index_to_relpath(nxt))

def reload_board(stage_path):
    st = load_stage(stage_path)
    grid = HexGrid.from_stage(st)
    board = Board(grid, st)

    # 스테이지별 타일 크기
    hex_size = st.get("hex_size") or st.get("tile_size") or DEFAULT_HEX
    hex_size = int(hex_size)

    return board, st, hex_size

def main(stage_path=None):
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    clock = pygame.time.Clock()
    font = load_font()

    if stage_path is None:
        # 디폴트: 001 튜토리얼
        stage_path = os.path.join(BASE_DIR, stage_index_to_relpath(1))

    board, st, hex_size= reload_board(stage_path)
    modal_active = False
    modal_btn_rects = {}
    stage_label = stage_label_from(st, stage_path)

    running = True
    while running:
        # 성공 시 모달 띄우기(한 번만)
        if board.is_game_over and board.is_win:
            modal_active = True

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.MOUSEBUTTONDOWN:
                # 모달이 떠 있을 땐 버튼만 처리
                if modal_active:
                    if event.button == 1 and modal_btn_rects:
                        mx, my = event.pos
                        if modal_btn_rects["retry"].collidepoint(mx, my):
                            board, st, hex_size = reload_board(stage_path)
                            stage_label = stage_label_from(st, stage_path)
                            modal_active = False
                            modal_btn_rects = {}
                        elif modal_btn_rects["menu"].collidepoint(mx, my):
                            # 메뉴: 아직 미구현 → 임시로 종료(원하면 메뉴 씬으로 교체)
                            running = False
                        elif modal_btn_rects["next"].collidepoint(mx, my):
                            # 다음 스테이지 시도 로드
                            nxt = next_stage_path(stage_path)
                            try:
                                board, st, hex_size = reload_board(nxt)
                                stage_path = nxt
                                stage_label = stage_label_from(st, stage_path)
                                modal_active = False
                                modal_btn_rects = {}
                            except FileNotFoundError:
                                # 없으면 그대로 유지(모달 유지)
                                pass
                    continue  # 모달 중에는 아래 보드 입력 막음

                # (새로 추가) 테두리 숫자 클릭 처리
                idx = edge_hint_hit_test(board, BOARD_CENTER, hex_size, font, event.pos)
                if idx is not None:
                    ent = board.edge_hints[idx]
                    if event.button == 1:
                        # 좌클릭: 보조선 토글
                        ent["helper_on"] = not ent.get("helper_on", False)
                    elif event.button == 3:
                        # 우클릭: 숫자 흐리게 토글 + 보조선 끄기
                        ent["dimmed"] = not ent.get("dimmed", False)
                        ent["helper_on"] = False
                    continue  # 숫자 클릭 시 보드 입력 막음

                # 평소 입력
                mx, my = pygame.mouse.get_pos()
                lx, ly = mx - BOARD_CENTER[0], my - BOARD_CENTER[1]
                q, r = pixel_to_axial(lx, ly, hex_size)
                if (q, r) in board.tiles:
                    if event.button == 1:
                        board.reveal(q, r)
                    elif event.button == 3:
                        board.toggle_flag(q, r)

        screen.fill(COL_BG)
        draw_board(screen, board, BOARD_CENTER, hex_size, font)
        draw_edge_hints(screen, board, BOARD_CENTER, hex_size, font)
        draw_topright_info(screen, board, font)

        # 모달 그리기
        if modal_active:
            modal_btn_rects = draw_success_modal(screen, stage_label, board.mistakes, font)

        pygame.display.flip()
        clock.tick(60)

if __name__ == "__main__":
    stage = sys.argv[1] if len(sys.argv) > 1 else None
    main(stage)