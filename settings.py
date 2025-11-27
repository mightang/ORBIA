WIDTH, HEIGHT = 960, 720
FPS = 60

HEX_SIZE = 28
BOARD_CENTER = (WIDTH//2, HEIGHT//2)

FONT_PATH = "assets/fonts/PretendardVariable.ttf"
FONT_SIZE = 24

COL_BG = (18, 20, 24)
COL_GRID = (55, 60, 70)
# ▶ 아무것도 안 열린 타일: 바위/철 느낌의 회색 계열
COL_COVERED = (82, 86, 96)     # 어두운 금속 회색

COL_BLOCKED = COL_BG

# ▶ 지뢰가 아닌 칸이 열린 경우: 하늘색 타일
COL_REVEAL = (88, 160, 205)    # 기본 하늘색 계열 (안쪽은 draw_board에서 더 밝게)

# ▶ 지뢰 칸이 드러난 경우: 붉은 보호막 계열
COL_MINE = (200, 60, 80)       # 보호막 느낌의 붉은 계열

# ▶ 깃발이 꽂힌 타일 (지금처럼 파란 보호색 유지)
COL_FLAG_TILE = (72, 128, 240)

COL_TEXT = (255, 255, 255)

COL_BTN_BG      = (60, 70, 90)
COL_BTN_BORDER  = (55, 60, 70)
COL_BTN_TEXT    = (255, 255, 255)
COL_BTN_RETRY   = (72, 128, 240)
COL_BTN_MENU    = (120, 120, 130)
COL_BTN_NEXT    = (90, 180, 110)

EDGE_HINT_OFFSET = 1.25
EDGE_HINT_ROTATE = True 

RESOLUTIONS = [
    (960, 720),
    (1280, 720),
    (1600, 900),
]
DEFAULT_RES_INDEX = 0