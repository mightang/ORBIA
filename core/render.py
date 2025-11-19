import pygame
import math
from .hexmath import axial_to_pixel, hex_corners
from .board import C_BLOCKED, C_COVERED, C_FLAGGED, C_REVEALED
from settings import (
    COL_BG, COL_GRID, COL_COVERED, COL_BLOCKED, COL_REVEAL, COL_MINE, COL_TEXT, COL_FLAG_TILE,
    COL_BTN_BG, COL_BTN_BORDER, COL_BTN_TEXT, COL_BTN_RETRY, COL_BTN_MENU, COL_BTN_NEXT,
    EDGE_HINT_OFFSET, EDGE_HINT_ROTATE
)

# ---- 공통 방향 벡터 (엣지 힌트용) ----
DIRS = [(1,0),(1,-1),(0,-1),(-1,0),(-1,1),(0,1)]

def dir_pixel(size, d):
    dq, dr = DIRS[int(d) % 6]
    x0, y0 = axial_to_pixel(0, 0, size)
    x1, y1 = axial_to_pixel(dq, dr, size)
    return (x1 - x0, y1 - y0)

def first_inbounds_from(board, pos, d):
    dq, dr = DIRS[int(d) % 6]
    q, r = pos
    if (q, r) not in board.tiles:
        q += dq; r += dr
    while (q, r) not in board.tiles:
        q += dq; r += dr
    return (q, r)

def edge_label_center(board, ent, center, size):
    cx, cy = center
    d = int(ent["dir"])

    # --- 기준 타일: JSON label_pos 우선, 없으면 첫 내부 셀 ---
    anchor_qr = ent.get("label_pos")
    if not (
        isinstance(anchor_qr, (list, tuple))
        and len(anchor_qr) == 2
        and all(isinstance(v, (int, float)) for v in anchor_qr)
    ):
        anchor_qr = first_inbounds_from(board, tuple(ent["pos"]), d)
    else:
        anchor_qr = (int(anchor_qr[0]), int(anchor_qr[1]))

    ax, ay = axial_to_pixel(anchor_qr[0], anchor_qr[1], size)
    ax += cx; ay += cy

    # --- 바깥 방향: JSON label_dir 우선, 없으면 반대 방향 ---
    offset_dir = ent.get("label_dir")
    if not isinstance(offset_dir, (int, float)):
        offset_dir = (d + 3) % 6
    offset_dir = int(offset_dir) % 6

    off_dx, off_dy = dir_pixel(size, offset_dir)
    off_norm = (off_dx * off_dx + off_dy * off_dy) ** 0.5 or 1.0

    # --- 거리: JSON label_dist 우선, 없으면 EDGE_HINT_OFFSET ---
    dist_raw = ent.get("label_dist", None)
    dist = dist_raw if isinstance(dist_raw, (int, float)) else EDGE_HINT_OFFSET
    offset = max(12, int(size * float(dist)))

    px = ax + (off_dx / off_norm) * offset
    py = ay + (off_dy / off_norm) * offset
    return px, py


def draw_board(surface, board, center, size, font):
    cx, cy = center
    for (q, r), t in board.tiles.items():
        x, y = axial_to_pixel(q, r, size)
        x += cx
        y += cy
        corners = hex_corners((x, y), size - 1)

        if t.state == C_BLOCKED:
            continue
        
        if t.state == C_FLAGGED:
            fill = COL_FLAG_TILE
        elif t.state == C_COVERED:
            fill = COL_COVERED
        elif t.state == C_REVEALED:
            fill = COL_REVEAL
        else:
            fill = COL_COVERED
        
        pygame.draw.polygon(surface, fill, corners)
        pygame.draw.polygon(surface, COL_GRID, corners, width=1)

        if t.state == C_REVEALED and (not t.is_mine):
            hint = getattr(board, "number_hint", {}).get((q, r))
            label = None
            if hint == "unknown":
                label = "?"
            else:
                if t.number > 0:
                    if hint == "tight":
                        label = f"{{{t.number}}}"   # {숫자}
                    elif hint == "loose":
                        label = f"-{t.number}-"    # -숫자-
                    else:
                        label = str(t.number)      # 기본 숫자
                # t.number == 0 이면 label=None (표시 안 함)

            if label is not None:
                txt = font.render(label, True, COL_TEXT)
                rect = txt.get_rect(center=(x, y))
                surface.blit(txt, rect)


def draw_edge_hints(surface, board, center, size, font):
    if not hasattr(board, "edge_hints"):
        return

    cx, cy = center

    for ent in board.edge_hints:
        d = int(ent["dir"])
        cnt = int(ent["count"])
        style = ent["style"]

        # 라벨 문자열
        label = f"{{{cnt}}}" if style == "tight" else (f"-{cnt}-" if style == "loose" else str(cnt))
        img = font.render(label, True, COL_TEXT)

        # --- 라벨 위치 계산 (공통 함수 사용) ---
        px, py = edge_label_center(board, ent, center, size)

        # --- 회전 각도 ---
        custom_angle = ent.get("label_angle", None)
        if isinstance(custom_angle, (int, float)):
            angle_deg = float(custom_angle)
        else:
            # 회전 기준 벡터는 dir(보드 안쪽) — 숫자가 '지뢰가 있는 열'을 바라봄
            rot_dx, rot_dy = dir_pixel(size, d)
            angle_deg = math.degrees(math.atan2(-rot_dy, rot_dx))
            if angle_deg > 90:
                angle_deg -= 180
            elif angle_deg < -90:
                angle_deg += 180

        rot = pygame.transform.rotate(img, angle_deg)

        # --- 흐리기(dimming) 처리 ---
        if ent.get("dimmed"):
            rot.set_alpha(80)   # 반투명
        else:
            rot.set_alpha(255)

        surface.blit(rot, rot.get_rect(center=(px, py)))

        # --- 보조선(helper line) 표시 ---
        if ent.get("helper_on"):
            # board.line_cells 사용해서 해당 줄의 셀들 얻기
            path = board.line_cells(ent["pos"][0], ent["pos"][1], d)
            # 차단된 셀은 제외
            path_play = [
                (q, r) for (q, r) in path
                if board.tiles[(q, r)].state != C_BLOCKED
            ]
            if len(path_play) >= 2:
                overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
                pts = []
                for (q, r) in path_play:
                    x, y = axial_to_pixel(q, r, size)
                    x += cx; y += cy
                    pts.append((x, y))
                # 반투명 흰색 보조선
                pygame.draw.lines(overlay, (255, 255, 255, 120), False, pts, 3)
                surface.blit(overlay, (0, 0))


def draw_topright_info(surface, board, font, pad=12):
    w, _ = surface.get_size()
    s = f"남은 지뢰 {board.mines_left}   실수 {board.mistakes}"
    img = font.render(s, True, COL_TEXT)
    rect = img.get_rect(topright=(w - pad, pad))
    surface.blit(img, rect)


def draw_success_modal(surface, stage_label: str, mistakes: int, font, *, pad=20):
    w, h = surface.get_size()

    # 1) 어둡게 덮는 오버레이(반투명)
    overlay = pygame.Surface((w, h), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 150))
    surface.blit(overlay, (0, 0))

    # 2) 패널(중앙)
    panel_w, panel_h = 520, 300
    panel_rect = pygame.Rect(0, 0, panel_w, panel_h)
    panel_rect.center = (w // 2, h // 2)

    # 패널 배경/테두리
    pygame.draw.rect(surface, COL_REVEAL, panel_rect, border_radius=16)
    pygame.draw.rect(surface, COL_GRID, panel_rect, width=2, border_radius=16)

    # 3) 텍스트들
    y = panel_rect.top + pad
    title = font.render(f"Stage: {stage_label}", True, COL_TEXT)
    surface.blit(title, (panel_rect.left + pad, y))
    y += title.get_height() + 8

    msg = font.render("성공! 클리어를 축하합니다.", True, COL_TEXT)
    surface.blit(msg, (panel_rect.left + pad, y))
    y += msg.get_height() + 6

    mist = font.render(f"실수 횟수: {mistakes}", True, COL_TEXT)
    surface.blit(mist, (panel_rect.left + pad, y))

    # 4) 버튼들 (가로 3개)
    btn_w, btn_h = 130, 44
    gap = 20
    total_w = btn_w * 3 + gap * 2
    start_x = panel_rect.centerx - total_w // 2
    btn_y = panel_rect.bottom - pad - btn_h

    def button(x, y, label, bg=COL_BTN_BG, border=COL_BTN_BORDER, text=COL_BTN_TEXT):
        r = pygame.Rect(x, y, btn_w, btn_h)
        pygame.draw.rect(surface, bg, r, border_radius=10)
        pygame.draw.rect(surface, border, r, width=2, border_radius=10)
        t = font.render(label, True, COL_TEXT)
        surface.blit(t, t.get_rect(center=r.center))
        return r

    rects = {}
    rects["retry"] = button(start_x, btn_y, "재시도", bg=COL_BTN_RETRY)
    rects["menu"]  = button(start_x + btn_w + gap, btn_y, "메뉴", bg=COL_BTN_MENU)
    rects["next"]  = button(start_x + (btn_w + gap) * 2, btn_y, "다음 스테이지", bg=COL_BTN_NEXT)

    return rects


# 게임 일시정지 창
def draw_pause_modal(surface, stage_label: str, mistakes: int, font, *, pad=20):
    w, h = surface.get_size()

    # 1) 반투명 오버레이
    overlay = pygame.Surface((w, h), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 150))
    surface.blit(overlay, (0, 0))

    # 2) 패널
    panel_w, panel_h = 520, 260
    panel_rect = pygame.Rect(0, 0, panel_w, panel_h)
    panel_rect.center = (w // 2, h // 2)

    pygame.draw.rect(surface, COL_REVEAL, panel_rect, border_radius=16)
    pygame.draw.rect(surface, COL_GRID, panel_rect, width=2, border_radius=16)

    # 3) 텍스트
    y = panel_rect.top + pad
    title = font.render("일시정지", True, COL_TEXT)
    surface.blit(title, (panel_rect.left + pad, y))
    y += title.get_height() + 6

    stage_txt = font.render(f"Stage: {stage_label}", True, COL_TEXT)
    surface.blit(stage_txt, (panel_rect.left + pad, y))
    y += stage_txt.get_height() + 6

    mist = font.render(f"현재 실수 횟수: {mistakes}", True, COL_TEXT)
    surface.blit(mist, (panel_rect.left + pad, y))

    # 4) 버튼 3개
    btn_w, btn_h = 140, 44
    gap = 20
    total_w = btn_w * 3 + gap * 2
    start_x = panel_rect.centerx - total_w // 2
    btn_y = panel_rect.bottom - pad - btn_h

    def button(x, y, label, bg=COL_BTN_BG, border=COL_BTN_BORDER, text=COL_BTN_TEXT):
        r = pygame.Rect(x, y, btn_w, btn_h)
        pygame.draw.rect(surface, bg, r, border_radius=10)
        pygame.draw.rect(surface, border, r, width=2, border_radius=10)
        t = font.render(label, True, COL_TEXT)
        surface.blit(t, t.get_rect(center=r.center))
        return r

    rects = {}
    # 계속하기(초록) / 레벨 선택(회색) / 초기화(파랑) 느낌으로 배색
    rects["resume"]   = button(start_x, btn_y, "계속하기",    bg=COL_BTN_NEXT)
    rects["level"]    = button(start_x + btn_w + gap, btn_y, "레벨 선택", bg=COL_BTN_MENU)
    rects["restart"]  = button(start_x + (btn_w + gap)*2, btn_y, "초기화", bg=COL_BTN_RETRY)

    return rects


# ---- 새로 추가: 테두리 숫자 히트 테스트 ----
def edge_hint_hit_test(board, center, size, font, mouse_pos, radius=20):
    if not hasattr(board, "edge_hints"):
        return None

    mx, my = mouse_pos
    for idx, ent in enumerate(board.edge_hints):
        px, py = edge_label_center(board, ent, center, size)
        dx = mx - px
        dy = my - py
        if dx*dx + dy*dy <= radius*radius:
            return idx
    return None