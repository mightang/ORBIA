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

def lighten(color, amount):
    r = min(255, color[0] + amount)
    g = min(255, color[1] + amount)
    b = min(255, color[2] + amount)
    return (r, g, b)

def darken(color, amount):
    r = max(0, color[0] - amount)
    g = max(0, color[1] - amount)
    b = max(0, color[2] - amount)
    return (r, g, b)

# --- 실수 횟수에 따른 별 개수 계산 ---
def calc_star_count(mistakes: int) -> int:
    """
    실수가 1번 이하, 3번 이하, 5번 이하일 때마다 별 1개씩 추가:
      0~1회  → ★★★
      2~3회 → ★★☆
      4~5회 → ★☆☆
      6회↑  → ☆☆☆
    """
    try:
        m = int(mistakes)
    except (TypeError, ValueError):
        return 0

    stars = 0
    if m <= 5:
        stars += 1
    if m <= 3:
        stars += 1
    if m <= 1:
        stars += 1
    return stars

def draw_board(surface, board, center, size, font):
    cx, cy = center
    for (q, r), t in board.tiles.items():
        x, y = axial_to_pixel(q, r, size)
        x += cx
        y += cy

        outer_corners = hex_corners((x, y), size - 1)
        inner_corners = hex_corners((x, y), size - 5)

        # -------- BLOCKED ----------
        if t.state == C_BLOCKED:
            pygame.draw.polygon(surface, darken(COL_BG, 6), outer_corners)
            pygame.draw.polygon(surface, COL_GRID, outer_corners, width=1)
            continue

        # -------- TILE COLOR LOGIC ----------
        # ★1) 깃발 = 붉은 보호막
        if t.state == C_FLAGGED:
            base_color  = darken(COL_MINE, 25)   # 어두운 붉은 바깥
            inner_color = COL_MINE               # 메인 보호막
            edge_color  = lighten(COL_MINE, 35)

        # ★2) 덮인 타일(회색 금속)
        elif t.state == C_COVERED:
            base_color  = COL_COVERED
            inner_color = lighten(COL_COVERED, 10)
            edge_color  = darken(COL_COVERED, 18)

        # ★3) 안전 타일(REVEALED & not mine) — 더 단조롭게
        elif t.state == C_REVEALED:
            # 톤다운된 푸른-회색
            safe_base  = (70, 100, 125)
            safe_inner = (90, 130, 160)
            base_color  = safe_base
            inner_color = safe_inner
            edge_color  = lighten(safe_inner, 25)

        else:
            # 예비
            base_color  = COL_COVERED
            inner_color = lighten(COL_COVERED, 10)
            edge_color  = darken(COL_COVERED, 18)

        # -------- LAYER DRAW ----------
        pygame.draw.polygon(surface, base_color, outer_corners)
        pygame.draw.polygon(surface, inner_color, inner_corners)
        pygame.draw.polygon(surface, edge_color, outer_corners, width=2)

        # -------- TOP HIGHLIGHT (살짝만) ----------
        highlight_color = (255, 255, 255, 40)
        highlight_surf = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        top_pts = sorted(outer_corners, key=lambda p: p[1])[:2]
        pygame.draw.line(
            highlight_surf, highlight_color,
            top_pts[0], top_pts[1], width=max(1, size//5)
        )
        surface.blit(highlight_surf, (0, 0))

        # -------- 숫자 ----------
        if t.state == C_REVEALED and not t.is_mine:
            hint = board.number_hint.get((q, r))
            label = None
            if hint == "unknown":
                label = "?"
            elif t.number > 0:
                if hint == "tight":
                    label = f"{{{t.number}}}"
                elif hint == "loose":
                    label = f"-{t.number}-"
                else:
                    label = str(t.number)

            if label:
                txt = font.render(label, True, COL_TEXT)
                surface.blit(txt, txt.get_rect(center=(x, y)))

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

def draw_success_modal(surface, stage_label: str, mistakes: int, font, *, pad=20, show_next: bool = True):
    w, h = surface.get_size()

    # 1) 어두운 오버레이 (튜토리얼 모달과 비슷한 톤)
    overlay = pygame.Surface((w, h), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))
    surface.blit(overlay, (0, 0))

    # 2) 중앙 패널
    panel_w = int(min(560, w * 0.72))
    panel_h = 310

    panel_rect = pygame.Rect(0, 0, panel_w, panel_h)
    panel_rect.center = (w // 2, h // 2)

    panel_bg   = (20, 26, 46)    # 튜토리얼 모달 패널 색과 비슷
    panel_edge = (110, 130, 190) # 파란 보더

    pygame.draw.rect(surface, panel_bg, panel_rect, border_radius=18)
    pygame.draw.rect(surface, panel_edge, panel_rect, width=2, border_radius=18)

    # 3) 텍스트 영역
    title_color = (234, 242, 255)
    text_color  = (200, 210, 230)

    y = panel_rect.top + 26

    # 상단 타이틀
    title_font = font
    title = title_font.render("스테이지 클리어", True, title_color)
    surface.blit(title, title.get_rect(midtop=(panel_rect.centerx, y)))
    y += title.get_height() + 10

    # Stage 라벨
    label_txt = font.render(f"Stage: {stage_label}", True, title_color)
    surface.blit(label_txt, label_txt.get_rect(midtop=(panel_rect.centerx, y)))
    y += label_txt.get_height() + 6

    # 설명 + 실수 정보
    msg = font.render("성공! 클리어를 축하합니다.", True, text_color)
    surface.blit(msg, msg.get_rect(midtop=(panel_rect.centerx, y)))
    y += msg.get_height() + 4

    mist = font.render(f"실수 횟수: {mistakes}", True, text_color)
    surface.blit(mist, mist.get_rect(midtop=(panel_rect.centerx, y)))

    star_count = calc_star_count(mistakes)

    y += mist.get_height() + 10

    # 텍스트로 한 번 명시
    star_text = font.render(f"이번 판 별: {star_count} / 3", True, text_color)
    surface.blit(star_text, star_text.get_rect(midtop=(panel_rect.centerx, y)))
    y += star_text.get_height() + 6

    # ★아이콘 3개 그리기 (획득한 별은 밝게, 나머지는 어둡게)
    full_color = (255, 215, 120)   # 황금색 느낌
    empty_color = (90, 96, 120)    # 어두운 회색/남색 계열
    star_gap = 10

    # 먼저 각 별 이미지를 만든다
    star_imgs = []
    for i in range(3):
        color = full_color if i < star_count else empty_color
        img = font.render("★", True, color)
        star_imgs.append(img)

    total_w = sum(img.get_width() for img in star_imgs) + star_gap * (len(star_imgs) - 1)
    sx = panel_rect.centerx - total_w // 2
    star_y = y

    x = sx
    for img in star_imgs:
        rect = img.get_rect(midtop=(x + img.get_width() // 2, star_y))
        surface.blit(img, rect)
        x += img.get_width() + star_gap

    # 4) 버튼들 (튜토리얼 모달 스타일의 둥근 버튼)
    btn_w, btn_h = 140, 44
    gap = 18

    if show_next:
        total_w = btn_w * 3 + gap * 2
    else:
        total_w = btn_w * 2 + gap

    btn_y = panel_rect.bottom - 32 - btn_h
    start_x = panel_rect.centerx - total_w // 2

    def button(x, y, label, bg_color, border_color, text_color=(234, 242, 255)):
        r = pygame.Rect(x, y, btn_w, btn_h)
        pygame.draw.rect(surface, bg_color, r, border_radius=14)
        pygame.draw.rect(surface, border_color, r, width=2, border_radius=14)
        t = font.render(label, True, text_color)
        surface.blit(t, t.get_rect(center=r.center))
        return r

    rects = {}

    # 색 계열 (튜토리얼 모달 버튼 느낌)
    btn_dark_bg   = (40, 50, 96)
    btn_dark_edge = (120, 140, 210)
    btn_main_bg   = (70, 92, 160)
    btn_main_edge = (150, 170, 230)

    # 왼쪽: 재시도 (파란 톤)
    rects["retry"] = button(
        start_x, btn_y,
        "재시도",
        bg_color=btn_main_bg,
        border_color=btn_main_edge,
    )

    # 가운데: 레벨 선택
    mid_x = start_x + btn_w + gap
    rects["menu"] = button(
        mid_x, btn_y,
        "레벨 선택",
        bg_color=btn_dark_bg,
        border_color=btn_dark_edge,
    )

    # 오른쪽: 다음 스테이지 (옵션)
    if show_next:
        next_x = start_x + (btn_w + gap) * 2
        rects["next"] = button(
            next_x, btn_y,
            "다음 스테이지",
            bg_color=btn_main_bg,
            border_color=btn_main_edge,
        )

    return rects

def draw_pause_modal(surface, stage_label: str, mistakes: int, font, *, pad=20, is_tutorial=False):
    w, h = surface.get_size()

    # 1) 어두운 오버레이
    overlay = pygame.Surface((w, h), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))
    surface.blit(overlay, (0, 0))

    # 2) 중앙 패널 (튜토리얼 모달과 동일한 계열)
    panel_w = int(min(560, w * 0.72))
    panel_h = 260
    panel_rect = pygame.Rect(0, 0, panel_w, panel_h)
    panel_rect.center = (w // 2, h // 2)

    panel_bg   = (20, 26, 46)
    panel_edge = (110, 130, 190)

    pygame.draw.rect(surface, panel_bg, panel_rect, border_radius=18)
    pygame.draw.rect(surface, panel_edge, panel_rect, width=2, border_radius=18)

    # 3) 텍스트
    title_color = (234, 242, 255)
    text_color  = (200, 210, 230)

    y = panel_rect.top + 26

    title = font.render("일시정지", True, title_color)
    surface.blit(title, title.get_rect(midtop=(panel_rect.centerx, y)))
    y += title.get_height() + 10

    stage_txt = font.render(f"Stage: {stage_label}", True, title_color)
    surface.blit(stage_txt, stage_txt.get_rect(midtop=(panel_rect.centerx, y)))
    y += stage_txt.get_height() + 6

    mist = font.render(f"현재 실수 횟수: {mistakes}", True, text_color)
    surface.blit(mist, mist.get_rect(midtop=(panel_rect.centerx, y)))
    y += mist.get_height() + 6

    hint = font.render("ESC 또는 '계속하기'를 눌러 게임을 재개할 수 있습니다.", True, text_color)
    surface.blit(hint, hint.get_rect(midtop=(panel_rect.centerx, y)))

    # 4) 버튼 3개 (튜토리얼 모달 스타일)
    btn_w, btn_h = 140, 44
    gap = 18
    total_w = btn_w * 3 + gap * 2
    btn_y = panel_rect.bottom - 32 - btn_h
    start_x = panel_rect.centerx - total_w // 2

    def button(x, y, label, bg_color, border_color, text_color=(234, 242, 255)):
        r = pygame.Rect(x, y, btn_w, btn_h)
        pygame.draw.rect(surface, bg_color, r, border_radius=14)
        pygame.draw.rect(surface, border_color, r, width=2, border_radius=14)
        t = font.render(label, True, text_color)
        surface.blit(t, t.get_rect(center=r.center))
        return r

    rects = {}

    # 색 계열
    btn_resume_bg   = (70, 120, 90)   # 계속하기: 초록 느낌
    btn_resume_edge = (140, 200, 160)
    btn_mid_bg      = (40, 50, 96)    # 레벨 선택 / 타이틀: 남색
    btn_mid_edge    = (120, 140, 210)
    btn_reset_bg    = (150, 70, 70)   # 초기화: 붉은색
    btn_reset_edge  = (200, 120, 120)

    # 왼쪽: 계속하기
    rects["resume"] = button(
        start_x, btn_y,
        "계속하기",
        bg_color=btn_resume_bg,
        border_color=btn_resume_edge,
    )

    # 가운데: 레벨 선택 / 타이틀 화면으로
    mid_label = "타이틀 화면으로" if is_tutorial else "레벨 선택"
    mid_x = start_x + btn_w + gap
    rects["level"] = button(
        mid_x, btn_y,
        mid_label,
        bg_color=btn_mid_bg,
        border_color=btn_mid_edge,
    )

    # 오른쪽: 초기화
    right_x = start_x + (btn_w + gap) * 2
    rects["restart"] = button(
        right_x, btn_y,
        "초기화",
        bg_color=btn_reset_bg,
        border_color=btn_reset_edge,
    )

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