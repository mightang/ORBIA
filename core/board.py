from .grid import DIRECTIONS
from collections import deque

C_COVERED  = 0
C_REVEALED = 1
C_FLAGGED  = 2
C_BLOCKED  = 3

class Tile:
    __slots__ = ("is_mine","number","state")
    def __init__(self):
        self.is_mine = False
        self.number  = 0
        self.state   = C_COVERED

class Board:
    def __init__(self, grid, stage_data):
        self.grid = grid
        self.stage = stage_data
        self.tiles = {pos: Tile() for pos in grid.cells}

        # 게임 상태
        self.is_game_over = False
        self.is_win = False
        self.mistakes = 0
        self.locked_flags = set()

        # 차단/지뢰 배치
        for q, r in stage_data.get("blocked", []):
            if (q, r) in self.tiles:
                self.tiles[(q, r)].state = C_BLOCKED
        for q, r in stage_data.get("mines", []):
            if (q, r) in self.tiles and self.tiles[(q, r)].state != C_BLOCKED:
                self.tiles[(q, r)].is_mine = True

        # 숫자 계산
        self.recompute_numbers()

        # 시작 상태 반영(reveal/flag)
        for q, r in stage_data.get("start_revealed", []):
            if (q, r) in self.tiles:
                t = self.tiles[(q, r)]
                if t.state != C_BLOCKED and not t.is_mine:
                    t.state = C_REVEALED

        for q, r in stage_data.get("start_flagged", []):
            if (q, r) in self.tiles:
                t = self.tiles[(q, r)]
                if t.state != C_BLOCKED:
                    t.state = C_FLAGGED
                    if t.is_mine:
                        self.locked_flags.add((q, r))   # ← 시작부터 잠금

        # 셀 숫자 힌트 맵
        self.number_hint = {}
        def apply(lst, tag):
            for q, r in stage_data.get(lst, []):
                if (q, r) in self.tiles:
                    t = self.tiles[(q, r)]
                    if (t.state != C_BLOCKED) and (not t.is_mine):
                        self.number_hint[(q, r)] = tag
        apply("hint_tight", "tight")
        apply("hint_loose", "loose")
        apply("hint_unknown", "unknown")

        self.build_edge_hints(stage_data)
        self.recompute_counters()
        self.check_win_and_update()
        self.last_flood_open = []

    def line_cells(self, q, r, dir_idx):
        """pos=(q,r)에서 dir 방향으로 필드 안쪽 끝까지 좌표를 나열."""
        dq, dr = DIRECTIONS[dir_idx]
        path = []
        cq, cr = q, r
        if (cq, cr) not in self.tiles:  # 테두리 바깥서 시작하면 먼저 한 칸 안쪽으로
            cq += dq; cr += dr
        while (cq, cr) in self.tiles:
            path.append((cq, cr))
            cq += dq; cr += dr
        return path
    
    def build_edge_hints(self, st):
        self.edge_hints = []
        def add_entries(key, style):
            for ent in st.get(key, []):
                pos = tuple(ent["pos"]); d = int(ent["dir"])
                path = self.line_cells(pos[0], pos[1], d)
                path_play = [(q,r) for (q,r) in path if self.tiles[(q,r)].state != C_BLOCKED]
                idx_list = [i for i,(q,r) in enumerate(path_play) if self.tiles[(q,r)].is_mine]
                self.edge_hints.append({
                    "pos": pos,
                    "dir": d,
                    "count": len(idx_list),
                    "style": style,
                    # ▼ 새로 전달할 선택 필드들
                    "label_pos": tuple(ent["label_pos"]) if "label_pos" in ent else None,
                    "label_dir": int(ent["label_dir"]) if "label_dir" in ent else None,
                    "label_dist": float(ent["label_dist"]) if "label_dist" in ent else None,
                    "label_angle": float(ent["label_angle"]) if "label_angle" in ent else None,
                })
        add_entries("edge_hint_normal", "normal")
        add_entries("edge_hint_tight",  "tight")
        add_entries("edge_hint_loose",  "loose")


    def neighbors(self, q, r):
        for nq, nr in self.grid.neighbors(q, r):
            yield (nq, nr)

    def recompute_numbers(self):
        for (q, r), t in self.tiles.items():
            if t.state == C_BLOCKED:
                t.number = 0
                continue
            if t.is_mine:
                t.number = -1
                continue
            cnt = 0
            for (nq, nr) in self.neighbors(q, r):
                if self.tiles[(nq, nr)].is_mine:
                    cnt += 1
            t.number = cnt

    def recompute_counters(self):
        self.total_cells = sum(1 for t in self.tiles.values() if t.state != C_BLOCKED)
        self.total_mines = sum(1 for t in self.tiles.values() if t.is_mine and t.state != C_BLOCKED)
        self.flag_count  = sum(1 for t in self.tiles.values() if t.state == C_FLAGGED)
        self.revealed_count = sum(1 for t in self.tiles.values() if t.state == C_REVEALED and not t.is_mine)
        self.mines_left = max(0, self.total_mines - self.flag_count)

    def toggle_flag(self, q, r):
        if self.is_game_over:
            return
        t = self.tiles.get((q, r))
        if not t or t.state in (C_REVEALED, C_BLOCKED):
            return
        
        pos = (q, r)

        if t.state == C_FLAGGED:
            # 잠금(=지뢰 깃발)인 경우 해제 불가
            if pos in self.locked_flags:
                return
            # 잠금이 아니면(안전칸에 있었던 시작 깃발 등) 해제 허용
            t.state = C_COVERED
            self.recompute_counters()
            self.check_win_and_update()
            return

        # 여기 오면 C_COVERED
        if t.is_mine:
            # 지뢰면 깃발 + 잠금
            t.state = C_FLAGGED
            self.locked_flags.add(pos)
        else:
            # 안전칸이면 깃발 금지: 실수 +1만, 상태는 그대로
            self.mistakes += 1

        self.recompute_counters()
        self.check_win_and_update()

    def reveal(self, q, r):
        if self.is_game_over:
            return

        # 연쇄 공개 로그 초기화(이번 클릭 기준으로 다시 채움)
        self.last_flood_open = []

        t = self.tiles.get((q, r))
        if not t:
            return
        if t.state == C_BLOCKED:
            return
        if t.state == C_REVEALED:
            return
        if t.state == C_FLAGGED:
            return

        # 지뢰 규칙: 열지 않고 실수만 +1
        if t.is_mine:
            self.mistakes += 1
            self.check_win_and_update()
            return

        # 안전칸 공개 (클릭한 칸)
        t.state = C_REVEALED
        self.revealed_count += 1

        opened_chain = []
        # 숫자 0이면 연쇄 공개
        if t.number == 0:
            opened_chain = self.flood_fill_open((q, r))

        # 이번 클릭으로 flood-fill로 추가로 열린 칸들 기록
        self.last_flood_open = opened_chain

        # 승리 조건 갱신
        self.check_win_and_update()

    def flood_fill_open(self, start_pos):
        if start_pos not in self.tiles:
            return []
        start = self.tiles[start_pos]
        if start.is_mine or start.state == C_BLOCKED:
            return []
        # 시작점이 0이 아니면 연쇄 공개 불필요
        if start.number != 0:
            return []

        q = deque([start_pos])
        seen = {start_pos}
        opened = []  # ← 이번 flood-fill로 새로 열린 칸들을 순서대로 기록

        while q:
            cq, cr = q.popleft()
            for nb in self.grid.neighbors(cq, cr):
                t = self.tiles.get(nb)
                if not t:
                    continue
                # 연쇄 공개 중에도 다음 규칙을 지킴
                if t.state == C_BLOCKED:
                    continue
                if t.state == C_FLAGGED:
                    continue
                if t.is_mine:
                    continue

                # 새로 여는 경우에만 카운트 + 리스트에 기록
                if t.state != C_REVEALED:
                    t.state = C_REVEALED
                    # 안전칸만 카운팅
                    self.revealed_count += 1
                    opened.append(nb)

                # 0이면 큐에 추가(더 확장)
                if t.number == 0 and nb not in seen:
                    seen.add(nb)
                    q.append(nb)

        return opened

    def all_safe_revealed(self) -> bool:
        for t in self.tiles.values():
            if t.state == C_BLOCKED:
                continue
            if (not t.is_mine) and t.state != C_REVEALED:
                return False
        return True

    def all_mines_flagged(self) -> bool:
        for t in self.tiles.values():
            if t.state == C_BLOCKED:
                continue
            if t.is_mine and t.state != C_FLAGGED:
                return False
        return True

    def check_win_and_update(self):
        if self.all_safe_revealed() and self.all_mines_flagged():
            self.is_game_over = True
            self.is_win = True
