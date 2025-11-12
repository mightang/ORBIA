DIRECTIONS = [
    (1, 0), (1, -1), (0, -1),
    (-1, 0), (-1, 1), (0, 1)
]

def cube_len(q, r):
    s = -q - r
    return max(abs(q), abs(r), abs(s))

class HexGrid:
    def __init__(self, radius:int):
        self.radius = radius
        self.cells = self.make_cells(radius)

    @classmethod
    def from_stage(cls, st:dict):
        if "cells" in st:
            g = cls.__new__(cls)
            g.radius = None
            g.cells = set(map(tuple, st["cells"]))
        else:
            shape=st.get("shape", "hex")
            if shape == "hex":
                g = cls(st["radius"])
            elif shape == "ring":  # 도넛형: inner~outer의 셀만 채택
                outer = st["outer"]
                inner = st.get("inner", max(0, outer - 1))
                base = cls(outer)
                g = cls.__new__(cls)
                g.radius = outer
                g.cells = {c for c in base.cells if inner <= cube_len(*c) <= outer}
            elif shape == "parallelogram":
                q0, q1 = st["q"]
                r0, r1 = st["r"]
                s0, s1 = st["s"]
                cells = set()
                for q in range(q0, q1 + 1):
                    for r in range(r0, r1 + 1):
                        s = -q - r
                        if s0 <= s <= s1:
                            cells.add((q, r))
                g = cls.__new__(cls)
                g.radius = None
                g.cells = cells
            else:
                raise ValueError(f"Unknown shape: {shape}")
            
        include = set(map(tuple, st.get("include", [])))
        exclude = set(map(tuple, st.get("exclude", [])))
        g.cells |= include
        g.cells -= exclude

        return g
    
    def make_cells(self, R):
        s = set()
        for q in range(-R, R + 1):
            for r in range(-R, R + 1):
                if -R <= q + r <= R:
                    s.add((q, r))
        return s

    def neighbors(self, q, r):
        for dq, dr in DIRECTIONS:
            nb = (q + dq, r + dr)
            if nb in self.cells:
                yield nb