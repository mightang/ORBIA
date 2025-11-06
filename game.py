import json, sys, pygame
from settings import WIDTH, HEIGHT, FPS, HEX_SIZE, BOARD_CENTER, FONT_NAME
from core.grid import HexGrid
from core.board import Board, C_REVEALED
from core.render import draw_board
from core.hexmath import pixel_to_axial

def load_stage(path):
    with open(path, "r", encoding = "utf-8") as f:
        return json.load(f)
    
def main(stage_path = "stages/005.json"):
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    clock = pygame.time.Clock()
    font = pygame.font.Font(FONT_NAME, 22)

    st = load_stage(stage_path)
    grid = HexGrid.from_stage(st)
    board = Board(grid, st)

    running = True
    while running:
        dt = clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = pygame.mouse.get_pos()
                lx, ly = mx - BOARD_CENTER[0], my - BOARD_CENTER[1]
                q, r = pixel_to_axial(lx, ly, HEX_SIZE)

                if (q, r) in board.tiles:
                    if event.button == 1:
                        result = board.reveal(q, r)
                        if result == "boom":
                            for(mq, mr), t in board.tiles.items():
                                if t.is_mine:
                                    t.state = C_REVEALED
                            print("mine clicked-game over")
                    elif event.button == 3:
                        board.toggle_flag(q, r)

        screen.fill((12, 14, 18))
        draw_board(screen, board, BOARD_CENTER, HEX_SIZE, font)
        pygame.display.flip()
    pygame.quit()

if __name__ == "__main__":
    stage = sys.argv[1] if len(sys.argv) > 1 else "stages/005.json"
    main(stage)