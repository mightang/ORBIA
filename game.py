import os
import pygame, sys, json, re
from core.grid import HexGrid
from core.board import Board
from core.render import draw_board, draw_topright_info, draw_success_modal
from core.hexmath import pixel_to_axial
from settings import HEX_SIZE, BOARD_CENTER, COL_BG

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

def load_stage(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def stage_label_from(st, path):
    if isinstance(st, dict) and "name" in st:
        return st["name"]
    m = re.search(r"(\d+)\.json$", path)
    return f"Stage {m.group(1)}" if m else path

def next_stage_path(path):
    m = re.search(r"(.*?)(\d+)(\.json)$", path)
    if not m:
        return path
    prefix, num, suffix = m.groups()
    nxt = str(int(num) + 1).zfill(len(num))
    return f"{prefix}{nxt}{suffix}"

def reload_board(stage_path):
    st = load_stage(stage_path)
    grid = HexGrid.from_stage(st)
    return Board(grid, st), st

def main(stage_path="stages/001.json"):
    pygame.init()
    screen = pygame.display.set_mode((960, 720))
    clock = pygame.time.Clock()
    font = load_font()

    board, st = reload_board(stage_path)
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

            # elif event.type == pygame.KEYDOWN:
            #     if event.key == pygame.K_r:
            #         # 재시도: 동일 스테이지 재시작
            #         board, st = reload_board(stage_path)
            #         stage_label = stage_label_from(st, stage_path)
            #         modal_active = False
            #         modal_btn_rects = {}

            elif event.type == pygame.MOUSEBUTTONDOWN:
                # 모달이 떠 있을 땐 버튼만 처리
                if modal_active:
                    if event.button == 1 and modal_btn_rects:
                        mx, my = event.pos
                        if modal_btn_rects["retry"].collidepoint(mx, my):
                            board, st = reload_board(stage_path)
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
                                board, st = reload_board(nxt)
                                stage_path = nxt
                                stage_label = stage_label_from(st, stage_path)
                                modal_active = False
                                modal_btn_rects = {}
                            except FileNotFoundError:
                                # 없으면 그대로 유지(모달 유지)
                                pass
                    continue  # 모달 중에는 아래 보드 입력 막음

                # 평소 입력
                if event.type == pygame.MOUSEBUTTONDOWN:
                    mx, my = pygame.mouse.get_pos()
                    lx, ly = mx - BOARD_CENTER[0], my - BOARD_CENTER[1]
                    q, r = pixel_to_axial(lx, ly, HEX_SIZE)
                    if (q, r) in board.tiles:
                        if event.button == 1:
                            board.reveal(q, r)
                        elif event.button == 3:
                            board.toggle_flag(q, r)

        screen.fill(COL_BG)
        draw_board(screen, board, BOARD_CENTER, HEX_SIZE, font)
        draw_topright_info(screen, board, font)

        # 모달 그리기
        if modal_active:
            modal_btn_rects = draw_success_modal(screen, stage_label, board.mistakes, font)

        pygame.display.flip()
        clock.tick(60)

if __name__ == "__main__":
    stage = sys.argv[1] if len(sys.argv) > 1 else "stages/001.json"
    main(stage)