try:
    import pyi_splash
    pyi_splash.close()
except:
    pass

import pygame
import numpy as np
import os
import sys

CELLSIZE = None
BGCELLSIZE = 94
CELLPAD = 5
COLORS = {
    0:(88, 88, 88),
    2:(255, 128, 0),
    4:(128, 255, 255),
    8:(128, 0, 255),
    16:(128, 128, 0),
    32:(0, 255, 0),
    64:(255, 128, 255),
    128:(255, 255, 0),
    256:(255, 128, 100),
    512:(64, 128, 128),
    1024:(190, 120, 120),
    2048:(0, 0, 0)
}
WIDTH = 500
HEIGHT = 600

def path(relative_path):
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")

    return os.path.normpath(os.path.join(base_path, relative_path))

def play_sound(name):
    sound = pygame.mixer.Sound(path("assets/"+name+".wav"))
    sound.play()
    
class Bg:
    def __init__(self):
        self.group = pygame.sprite.Group()
        self.transparent = pygame.Surface((WIDTH, HEIGHT)).convert_alpha()
        self.transparent.fill((0, 0, 0, 200))
    
        self.add()

    def add(self):
        self.lastline = BgLine()
        self.group.add(self.lastline)

    def update(self, screen):
        screen.fill((0, 0, 0))
            
        self.group.draw(screen)
        self.group.update()
        screen.blit(self.transparent, (0, 0))
        
        if self.lastline.run_100_pixel:
            self.add()
    
class BgLine(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()

        self.image = pygame.Surface((WIDTH, BGCELLSIZE+CELLPAD))
        self.rect = self.image.get_rect(x=0, y=HEIGHT)
        self.run_100_pixel = False

        for i in range(5):
            n = np.random.choice(tuple(COLORS.keys()))
            t = Text(BGCELLSIZE, BGCELLSIZE, "", COLORS[n])
            self.image.blit(t, ((BGCELLSIZE+CELLPAD)*i+CELLPAD, 0))

    def update(self):
        self.rect.y -= 2
        if self.rect.bottom < 0:
            self.kill()
        elif (not self.run_100_pixel) and (HEIGHT - self.rect.y >= 100):
            self.run_100_pixel = True

class Text(pygame.Surface):
    def __init__(self, width, height, text, bg, font=60):
        super().__init__((width, height))
        self.fill(bg)

        font = pygame.font.SysFont("Ariel", font)
        render = font.render(text, True, (255, 255, 255))
        self.blit(render, render.get_rect(center=self.get_rect().center))
        
class Board(pygame.Surface):
    def __init__(self, screen, width, height, endnum):
        super().__init__((width*(CELLSIZE+CELLPAD)+CELLPAD,
                          height*(CELLSIZE+CELLPAD)+CELLPAD))
        self.gamestate = None
        self.score = 0
        self.pos = (0, HEIGHT - WIDTH)
        self.screen = screen
        self.width = width
        self.height = height
        self.endnum = endnum
        self.board = np.zeros([width, height], dtype=int)
        self.add_tile()
        self.add_tile()
        self.lastboard = self.board.copy()
        
    def add_tile(self):
        board = self.board.flatten()
        poslist = np.where(board == 0)[0]
        if len(poslist) > 0:
            pos = np.random.choice(poslist)
            self.board[pos // self.height, pos % self.height] = np.random.choice([2, 4])

    def can_move(self):
        board = self.board.flatten()
        
        if len(np.where(board == 0)[0]) > 0:
            return True

        for r in range(len(board) - self.width):
            if board[r] == board[r+self.width]:
                return True

        for r in range(0, len(board)-1, self.width):
            for c in range(0, self.width-1, 1):
                if board[r+(c)] == board[r+(c+1)]:
                    return True

        return False
    
    def record(self):
        if 0 in self.board.flatten():
            self.add_tile()

        if not self.can_move():
            self.gamestate = "lose"
            return

        if self.endnum in self.board.flatten():
            self.gamestate="win"
            return

    def shift(self, ln):
        lnlist = []
        for tile in ln:
            if tile > 0:
                lnlist.append(tile)

        for empty in range(len(ln)-len(lnlist)):
            lnlist.append(0)

        return lnlist

    def find_min_except_0(self, value):
        return (9999 if value == 0 else value)

    def get_set(self, ln):
        res = []
        for tile in ln:
            if tile not in res:
                res.append(tile)

        return res
    
    def move_up(self, isrecord=True):
        play_sound("move")
        if isrecord:
            self.lastboard = self.board.copy()
        
        for i in range(self.height):
            ln = self.shift(self.board[..., i])
            ln_cpy = ln.copy()

            x = 0
            while x < len(ln)-1:
                if ln[x] == ln[x+1]:
                    ln_cpy[x] = 0
                    ln_cpy[x+1] *= 2
                    self.score += ln_cpy[x+1] * 2
                    x += 1
                x += 1

            self.board[..., i] = self.shift(ln_cpy)

        if isrecord:
            self.record()

    def move_down(self):
        self.lastboard = self.board.copy()
        self.board = np.flip(self.board, False)
        self.move_up(False)
        self.board = np.flip(self.board, False)
        self.record()

    def move_left(self, isrecord=True):
        play_sound("move")
        if isrecord:
            self.lastboard = self.board.copy()
                
        for i in range(self.width):
            ln = self.shift(self.board[i])
            ln_cpy = ln.copy()

            x = 0
            while x < len(ln)-1:
                if ln[x] == ln[x+1]:
                    ln_cpy[x] = 0
                    ln_cpy[x+1] *= 2
                    self.score += ln_cpy[x+1] * 2
                    x += 1
                x += 1

            self.board[i] = self.shift(ln_cpy)
            
        if isrecord:
            self.record()

    def move_right(self):
        self.lastboard = self.board.copy()
        self.board = np.flip(self.board, True)
        self.move_left(False)
        self.board = np.flip(self.board, True)
        self.record()
            
    def undo(self):
        lastboard = self.lastboard.copy()
        board = self.board.copy()

        self.board = lastboard
        self.lastboard = board
            
    def update(self):
        self.screen.blit(self, self.pos)
        
        self.fill((65, 65, 65))
        for row, x in enumerate(self.board):
            for column, y in enumerate(x):
                t = Text(CELLSIZE, CELLSIZE, (str(y) if y > 0 else ""), COLORS[y],
                         font=CELLSIZE // 2)
                self.blit(t, (column * (CELLSIZE+CELLPAD)+CELLPAD,
                              row * (CELLSIZE+CELLPAD)+CELLPAD))

        return self.gamestate

def main():
    global CELLSIZE
    
    pygame.init()
    pygame.mixer.pre_init()
    pygame.mixer.music.load(path("assets/bgm.ogg"))
    pygame.mixer.music.play(-1)

    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    screen_rect = screen.get_rect()
    pygame.display.set_caption("2048")
    pygame.display.set_icon(pygame.image.load(path("assets/icon.ico")))
    clock = pygame.time.Clock()

    bg = Bg()
    boardsize = 4
    tip2 = pygame.font.SysFont("Ariel", 36).render("Mode: 4x4", True, (255, 255, 255))

    while True:
        
        font = pygame.font.SysFont("Ariel", 72)
        title = font.render("2048 Game", True, (176, 176, 176))
        title_rect = title.get_rect(centerx=screen_rect.centerx, y=100)

        font = pygame.font.SysFont("Ariel", 36)
        tip = font.render("Play !", True, (255, 255, 255))
        tip_rect = tip.get_rect(centerx=screen_rect.centerx, y=320)

        buttonframe_rect = (tip_rect.x-15, tip_rect.y-15,
                            tip_rect.width+30, tip_rect.height+30)

        tip_rect2 = tip2.get_rect(centerx=screen_rect.centerx, y=380)
        
        buttonframe_rect2 = (tip_rect2.x-15, tip_rect2.y-15,
                             tip_rect2.width+30, tip_rect2.height+30)
        
        running = True
        while running:
            bg.update(screen)
            screen.blit(title, title_rect)
            screen.blit(tip, tip_rect)
            screen.blit(tip2, tip_rect2)

            pos = pygame.mouse.get_pos()
            pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)
            
            if tip_rect.collidepoint(pos):
                pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND)
                pygame.draw.rect(screen, (255, 0, 0), buttonframe_rect, width=2)

            if tip_rect2.collidepoint(pos):
                pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND)
                pygame.draw.rect(screen, (255, 0, 0), buttonframe_rect2, width=2)
                
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    raise SystemExit

                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if tip_rect.collidepoint(pos):
                        play_sound("click")
                        pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)
                        running = False
                    if tip_rect2.collidepoint(pos):
                        play_sound("click")
                        if boardsize == 4:
                            boardsize = 5
                            tip2 = font.render("Mode: 5x5", True, (255, 255, 255))
                        else:
                            boardsize = 4
                            tip2 = font.render("Mode: 4x4", True, (255, 255, 255))

            clock.tick(60)
            pygame.display.update()
            
        CELLSIZE = (WIDTH if WIDTH < HEIGHT else HEIGHT) // boardsize - CELLPAD - 1
        board = Board(screen, boardsize, boardsize, 2048)

        font = pygame.font.SysFont("Ariel", 50)
        
        running = True
        while running:
            screen.fill((0, 0, 0))

            score = font.render(f"Score:{board.score}", True, (176, 176, 176))
            score_rect = score.get_rect(x=50, centery=(HEIGHT-WIDTH)/2)
            screen.blit(score, score_rect)

            if gamestate := board.update():
                running = False
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    gamestate = "lose"
                    running = False
                    
                if event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_UP, pygame.K_w):
                        board.move_up()
                    elif event.key in (pygame.K_DOWN, pygame.K_s):
                        board.move_down()
                    elif event.key in (pygame.K_LEFT, pygame.K_a):
                        board.move_left()
                    elif event.key in (pygame.K_RIGHT, pygame.K_d):
                        board.move_right()
                    elif event.key == pygame.K_z:
                        board.undo()

            clock.tick(60)
            pygame.display.update()

        play_sound(gamestate)
        
        font = pygame.font.SysFont("Ariel", 72)
        title = font.render("You Win !" if gamestate == "win" else "You Lose !", True, (176, 176, 176))
        title_rect = title.get_rect(centerx=screen_rect.centerx, y=100)

        font = pygame.font.SysFont("Ariel", 36)
        scoretip = font.render(f"Score: {board.score}", True, (255, 255, 255))
        scoretip_rect = scoretip.get_rect(centerx=screen_rect.centerx, y=200)
        
        tip = font.render("Return", True, (255, 255, 255))
        tip_rect = tip.get_rect(centerx=screen_rect.centerx, y=350)
        
        buttonframe_rect = (tip_rect.x-15, tip_rect.y-15,
                            tip_rect.width+30, tip_rect.height+30)
    
        running = True
        while running:
            bg.update(screen)
            screen.blit(title, title_rect)
            screen.blit(scoretip, scoretip_rect)
            screen.blit(tip, tip_rect)

            pos = pygame.mouse.get_pos()

            if tip_rect.collidepoint(pos):
                pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND)
                pygame.draw.rect(screen, (255, 0, 0), buttonframe_rect, width=2)
            else:
                pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)
                
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if tip_rect.collidepoint(pos):
                        play_sound("click")
                        pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)
                        running = False

            clock.tick(60)
            pygame.display.update()
            
if __name__ == "__main__":
    main()
