import pygame
import math
import random
import array
import sys

# --- GAME CONFIGURATION ---
BLOCK_SIZE = 30
BOARD_WIDTH = 10
BOARD_HEIGHT = 20
SCREEN_WIDTH = 600
SCREEN_HEIGHT = 700
FPS = 60

# --- COLORS ---
BLACK = (20, 20, 20)
WHITE = (255, 255, 255)
GRAY = (100, 100, 100)
DARK_GRAY = (40, 40, 40)
CYAN = (0, 255, 255)
YELLOW = (255, 255, 0)

# Standard Tetris Colors
COLORS = [
    (0, 255, 255),   # I - Cyan
    (0, 0, 255),     # J - Blue
    (255, 165, 0),   # L - Orange
    (255, 255, 0),   # O - Yellow
    (0, 255, 0),     # S - Green
    (128, 0, 128),   # T - Purple
    (255, 0, 0)      # Z - Red
]

# --- SHAPE DEFINITIONS ---
# Represented as string grids to naturally define their rotation centers.
SHAPE_DATA = [
    ['....', 'XXXX', '....', '....'], # I
    ['X..', 'XXX', '...'],            # J
    ['..X', 'XXX', '...'],            # L
    ['XX', 'XX'],                     # O
    ['.XX', 'XX.', '...'],            # S
    ['.X.', 'XXX', '...'],            # T
    ['XX.', '.XX', '...']             # Z
]

# --- AUDIO GENERATION (FILES = OFF) ---
def generate_korobeiniki_theme():
    """
    Procedurally generates the full classic 'duh duh duh' Russian Tetris song.
    """
    notes = {
        'E5': 659.25, 'D5': 587.33, 'C5': 523.25, 'B4': 493.88,
        'A4': 440.00, 'A5': 880.00, 'G5': 783.99, 'F5': 698.46,
        'Gs4': 415.30, 'Gs5': 830.61
    }
    
    melody = [
        ('E5', 400), ('B4', 200), ('C5', 200), ('D5', 400), 
        ('C5', 200), ('B4', 200), ('A4', 400), ('A4', 200), 
        ('C5', 200), ('E5', 400), ('D5', 200), ('C5', 200), 
        ('B4', 600), ('C5', 200), ('D5', 400), ('E5', 400), 
        ('C5', 400), ('A4', 400), ('A4', 800),
        
        ('D5', 400), ('F5', 200), ('A5', 400), ('G5', 200),
        ('F5', 200), ('E5', 600), ('C5', 200), ('E5', 400),
        ('D5', 200), ('C5', 200), ('B4', 400), ('B4', 200),
        ('C5', 200), ('D5', 400), ('E5', 400), ('C5', 400),
        ('A4', 400), ('A4', 800),

        ('E5', 800), ('C5', 800), ('D5', 800), ('B4', 800),
        ('C5', 800), ('A4', 800), ('Gs4', 800), ('B4', 800),
        ('E5', 800), ('C5', 800), ('D5', 800), ('B4', 800),
        ('C5', 400), ('E5', 400), ('A5', 800), ('Gs5', 1200)
    ]

    sample_rate = 44100
    amplitude = 6000
    full_buffer = array.array('h')
    
    for note, duration in melody:
        freq = notes.get(note, 440.0)
        play_dur = duration * 0.85
        gap_dur = duration * 0.15
        
        samples_play = max(0, int(sample_rate * play_dur / 1000.0))
        samples_gap = max(0, int(sample_rate * gap_dur / 1000.0))
        
        for i in range(samples_play):
            t = float(i) / sample_rate
            val = int(math.copysign(amplitude, math.sin(2.0 * math.pi * freq * t)))
            
            if samples_play > 200:
                if i < 100: val = int(val * (i / 100.0))
                elif i > samples_play - 100: val = int(val * (max(0, samples_play - i) / 100.0))
                    
            full_buffer.append(val)
            
        for i in range(samples_gap):
            full_buffer.append(0)
            
    try:
        sound = pygame.mixer.Sound(buffer=full_buffer.tobytes())
        sound.set_volume(0.3)
        return sound
    except Exception as e:
        return None

def generate_thud_sound():
    """
    Generates a low-frequency crunchy thud sound for when a piece locks.
    """
    sample_rate = 44100
    duration_ms = 80
    samples = int(sample_rate * (duration_ms / 1000.0))
    full_buffer = array.array('h')
    
    amplitude = 12000
    start_freq = 150.0
    end_freq = 30.0
    
    for i in range(samples):
        t = float(i) / sample_rate
        progress = i / samples
        current_freq = start_freq - (start_freq - end_freq) * progress
        current_amp = int(amplitude * (1.0 - progress))
        
        wave = math.copysign(1.0, math.sin(2.0 * math.pi * current_freq * t))
        noise = random.uniform(-1.0, 1.0)
        
        val = int(current_amp * (wave * 0.6 + noise * 0.4))
        full_buffer.append(val)
        
    try:
        sound = pygame.mixer.Sound(buffer=full_buffer.tobytes())
        sound.set_volume(0.5)
        return sound
    except Exception:
        return None

def generate_line_clear_sound():
    """
    Generates a bright, high-pitched classic clear arpeggio.
    """
    sample_rate = 44100
    duration_ms = 200
    samples = int(sample_rate * (duration_ms / 1000.0))
    full_buffer = array.array('h')
    
    amplitude = 8000
    for i in range(samples):
        t = float(i) / sample_rate
        progress = i / samples
        
        # Fast C6 -> E6 -> G6 arpeggio
        if progress < 0.33: freq = 1046.50
        elif progress < 0.66: freq = 1318.51
        else: freq = 1567.98
            
        wave = math.copysign(1.0, math.sin(2.0 * math.pi * freq * t))
        
        # Envelope to prevent clicking
        env = 1.0
        if i < 100: env = i / 100.0
        if i > samples - 100: env = max(0.0, (samples - i) / 100.0)
            
        val = int(amplitude * wave * env)
        full_buffer.append(val)
        
    try:
        sound = pygame.mixer.Sound(buffer=full_buffer.tobytes())
        sound.set_volume(0.4)
        return sound
    except Exception:
        return None


# --- GAME LOGIC ---
class Piece:
    def __init__(self, x, y, shape_index):
        self.x = x
        self.y = y
        self.shape_index = shape_index
        self.color = COLORS[shape_index]
        self.rotation = 0
        self.shape_matrix = SHAPE_DATA[shape_index]
        self.rotations = self._generate_rotations(self.shape_matrix)

    def _generate_rotations(self, shape):
        rots = [shape]
        for _ in range(3):
            prev = rots[-1]
            size = len(prev)
            new_rot = [''.join([prev[y][x] for y in range(size-1, -1, -1)]) for x in range(size)]
            rots.append(new_rot)
        return rots

    def get_shape(self):
        return self.rotations[self.rotation % 4]


class Tetris:
    def __init__(self, thud_sound=None, clear_sound=None):
        self.board = [[None for _ in range(BOARD_WIDTH)] for _ in range(BOARD_HEIGHT)]
        self.score = 0
        self.lines = 0
        self.level = 1
        self.game_over = False
        
        self.thud_sound = thud_sound
        self.clear_sound = clear_sound
        
        # Line clear animation state
        self.animating_clear = False
        self.lines_to_clear = []
        self.clear_step = 0
        self.clear_anim_time = 0

        self.next_piece = self._get_random_piece()
        self.current_piece = self._get_random_piece()
        
    def _get_random_piece(self):
        return Piece(BOARD_WIDTH // 2 - 2, 0, random.randint(0, len(SHAPE_DATA) - 1))

    def get_gameboy_speed(self):
        gb_frames = [53, 49, 45, 41, 37, 33, 28, 22, 17, 11, 10, 9, 8, 7, 6, 6, 5, 5, 4, 4, 3]
        idx = self.level - 1
        frames = gb_frames[idx] if 0 <= idx < len(gb_frames) else 2
        return int((float(frames) / 60.0) * 1000)

    def check_collision(self, dx=0, dy=0, rotation_offset=0):
        test_rotation = (self.current_piece.rotation + rotation_offset) % 4
        shape = self.current_piece.rotations[test_rotation]
        for y, row in enumerate(shape):
            for x, cell in enumerate(row):
                if cell == 'X':
                    board_x = self.current_piece.x + x + dx
                    board_y = self.current_piece.y + y + dy
                    if board_x < 0 or board_x >= BOARD_WIDTH or board_y >= BOARD_HEIGHT:
                        return True
                    if board_y >= 0 and self.board[board_y][board_x] is not None:
                        return True
        return False

    def lock_piece(self):
        shape = self.current_piece.get_shape()
        for y, row in enumerate(shape):
            for x, cell in enumerate(row):
                if cell == 'X':
                    board_y = self.current_piece.y + y
                    if board_y >= 0:
                        self.board[board_y][self.current_piece.x + x] = self.current_piece.color
        
        # Check for full lines BEFORE spawning a new piece
        self.lines_to_clear = [i for i, row in enumerate(self.board) if all(cell is not None for cell in row)]
        
        if self.lines_to_clear:
            # Trigger the classic pause and animation
            self.animating_clear = True
            self.clear_step = 1
            self.clear_anim_time = 0
            if self.clear_sound:
                self.clear_sound.play()
        else:
            # Standard piece lock without clearing lines
            if self.thud_sound:
                self.thud_sound.play()
            self.score += 10
            self.spawn_next_piece()

    def spawn_next_piece(self):
        self.current_piece = self.next_piece
        self.next_piece = self._get_random_piece()
        if self.check_collision():
            self.game_over = True

    def execute_line_clear(self):
        """Called after the animation finishes to actually collapse the lines."""
        cleared = len(self.lines_to_clear)
        for i in self.lines_to_clear:
            del self.board[i]
            self.board.insert(0, [None for _ in range(BOARD_WIDTH)])
            
        self.lines += cleared
        self.level = (self.lines // 10) + 1
        
        scores = {1: 40, 2: 100, 3: 300, 4: 1200}
        self.score += scores.get(cleared, 0) * self.level
        self.score += 10 # 10 Points for placing the piece
        
        self.lines_to_clear = []
        self.animating_clear = False
        self.spawn_next_piece()

    def hard_drop(self):
        drop_distance = 0
        while not self.check_collision(dy=1):
            self.current_piece.y += 1
            drop_distance += 1
        self.score += drop_distance * 2
        self.lock_piece()

    def get_ghost_y(self):
        ghost_y = self.current_piece.y
        while not self.check_collision(dy=ghost_y - self.current_piece.y + 1):
            ghost_y += 1
        return ghost_y


# --- RENDERING ENGINE ---
def draw_3d_block(surface, color, x, y, size):
    pygame.draw.rect(surface, color, (x, y, size, size))
    light = (min(color[0] + 70, 255), min(color[1] + 70, 255), min(color[2] + 70, 255))
    pygame.draw.line(surface, light, (x, y), (x + size - 1, y), 3)
    pygame.draw.line(surface, light, (x, y), (x, y + size - 1), 3)
    dark = (max(color[0] - 70, 0), max(color[1] - 70, 0), max(color[2] - 70, 0))
    pygame.draw.line(surface, dark, (x, y + size - 1), (x + size - 1, y + size - 1), 3)
    pygame.draw.line(surface, dark, (x + size - 1, y), (x + size - 1, y + size - 1), 3)

def draw_menu(surface, title_font, font, options, selected_idx):
    surface.fill(BLACK)
    title_label = title_font.render("AC'S TETRIS", True, CYAN)
    title_rect = title_label.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 4))
    surface.blit(title_label, title_rect)
    
    start_y = SCREEN_HEIGHT // 2 - 50
    for i, option in enumerate(options):
        if i == selected_idx:
            color = YELLOW
            text = f"> {option} <"
        else:
            color = WHITE
            text = option
            
        opt_label = font.render(text, True, color)
        opt_rect = opt_label.get_rect(center=(SCREEN_WIDTH // 2, start_y + i * 50))
        surface.blit(opt_label, opt_rect)

    inst_label = font.render("Use UP/DOWN to navigate, SPACE to select", True, GRAY)
    inst_rect = inst_label.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 50))
    surface.blit(inst_label, inst_rect)
    pygame.display.update()

def draw_info_screen(surface, title_font, font, title, lines):
    surface.fill(BLACK)
    title_label = title_font.render(title, True, CYAN)
    title_rect = title_label.get_rect(center=(SCREEN_WIDTH // 2, 100))
    surface.blit(title_label, title_rect)
    
    start_y = 250
    for i, line in enumerate(lines):
        line_label = font.render(line, True, WHITE)
        line_rect = line_label.get_rect(center=(SCREEN_WIDTH // 2, start_y + i * 40))
        surface.blit(line_label, line_rect)
        
    back_label = font.render("Press ESC to return to Menu", True, YELLOW)
    if pygame.time.get_ticks() % 1000 < 500:
        back_rect = back_label.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 100))
        surface.blit(back_label, back_rect)
    pygame.display.update()

def draw_window(surface, game, font):
    surface.fill(BLACK)
    board_px_width = BOARD_WIDTH * BLOCK_SIZE
    board_px_height = BOARD_HEIGHT * BLOCK_SIZE
    offset_x = 50
    offset_y = 50

    pygame.draw.rect(surface, DARK_GRAY, (offset_x, offset_y, board_px_width, board_px_height))
    pygame.draw.rect(surface, WHITE, (offset_x - 2, offset_y - 2, board_px_width + 4, board_px_height + 4), 2)

    for i in range(BOARD_HEIGHT):
        pygame.draw.line(surface, BLACK, (offset_x, offset_y + i * BLOCK_SIZE), (offset_x + board_px_width, offset_y + i * BLOCK_SIZE))
    for j in range(BOARD_WIDTH):
        pygame.draw.line(surface, BLACK, (offset_x + j * BLOCK_SIZE, offset_y), (offset_x + j * BLOCK_SIZE, offset_y + board_px_height))

    for y in range(BOARD_HEIGHT):
        for x in range(BOARD_WIDTH):
            if game.board[y][x]:
                is_clearing = False
                # If animating, don't draw the blocks in the cleared columns
                if game.animating_clear and y in game.lines_to_clear:
                    # Classic Center-Out animation (Columns 4 & 5 disappear first)
                    if x >= 5 - game.clear_step and x <= 4 + game.clear_step:
                        is_clearing = True
                
                if not is_clearing:
                    draw_3d_block(surface, game.board[y][x], offset_x + x * BLOCK_SIZE, offset_y + y * BLOCK_SIZE, BLOCK_SIZE)

    # Hide the ghost piece and current piece if we are pausing for a line clear animation
    if not game.game_over and not game.animating_clear:
        ghost_y = game.get_ghost_y()
        shape = game.current_piece.get_shape()
        for y, row in enumerate(shape):
            for x, cell in enumerate(row):
                if cell == 'X':
                    px = offset_x + (game.current_piece.x + x) * BLOCK_SIZE
                    py = offset_y + (ghost_y + y) * BLOCK_SIZE
                    if py >= offset_y:
                        pygame.draw.rect(surface, GRAY, (px, py, BLOCK_SIZE, BLOCK_SIZE), 1)

        for y, row in enumerate(shape):
            for x, cell in enumerate(row):
                if cell == 'X':
                    px = offset_x + (game.current_piece.x + x) * BLOCK_SIZE
                    py = offset_y + (game.current_piece.y + y) * BLOCK_SIZE
                    if py >= offset_y:
                        draw_3d_block(surface, game.current_piece.color, px, py, BLOCK_SIZE)

    ui_x = offset_x + board_px_width + 50
    title_label = font.render("AC'S TETRIS", True, WHITE)
    surface.blit(title_label, (ui_x, 50))

    score_label = font.render(f"SCORE: {game.score}", True, WHITE)
    level_label = font.render(f"LEVEL: {game.level}", True, WHITE)
    lines_label = font.render(f"LINES: {game.lines}", True, WHITE)
    surface.blit(score_label, (ui_x, 150))
    surface.blit(level_label, (ui_x, 200))
    surface.blit(lines_label, (ui_x, 250))

    next_label = font.render("NEXT:", True, WHITE)
    surface.blit(next_label, (ui_x, 350))
    next_shape = game.next_piece.get_shape()
    for y, row in enumerate(next_shape):
        for x, cell in enumerate(row):
            if cell == 'X':
                draw_3d_block(surface, game.next_piece.color, ui_x + x * BLOCK_SIZE, 400 + y * BLOCK_SIZE, BLOCK_SIZE)

    esc_label = font.render("ESC to Menu", True, GRAY)
    surface.blit(esc_label, (ui_x, 650))

    if game.game_over:
        over_label = font.render("GAME OVER!", True, (255, 50, 50))
        restart_label = font.render("Press ESC for Menu", True, WHITE)
        surface.blit(over_label, (ui_x, 550))
        surface.blit(restart_label, (ui_x, 600))

    pygame.display.update()


# --- MAIN ENGINE ---
def main():
    pygame.init()
    pygame.mixer.init(frequency=44100, size=-16, channels=2) 
    
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("AC'S Tetris")
    clock = pygame.time.Clock()
    
    font = pygame.font.SysFont('consolas', 24, bold=True)
    title_font = pygame.font.SysFont('consolas', 60, bold=True)
    
    music = generate_korobeiniki_theme()
    thud_sound = generate_thud_sound()
    clear_sound = generate_line_clear_sound()

    pygame.key.set_repeat(200, 50) 
    
    game = Tetris(thud_sound, clear_sound)
    state = "MENU"
    fall_time = 0
    fast_drop = False

    menu_options = ["Play Game", "How to Play", "About", "Credits", "Exit"]
    selected_option = 0

    running = True
    while running:
        dt = clock.get_time()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                
            if state == "MENU":
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_UP:
                        selected_option = (selected_option - 1) % len(menu_options)
                    elif event.key == pygame.K_DOWN:
                        selected_option = (selected_option + 1) % len(menu_options)
                    elif event.key in (pygame.K_SPACE, pygame.K_RETURN):
                        selected_text = menu_options[selected_option]
                        
                        if selected_text == "Play Game":
                            state = "PLAYING"
                            game = Tetris(thud_sound, clear_sound)
                            fall_time = 0
                            fast_drop = False
                            if music:
                                music.play(loops=-1)
                        elif selected_text == "How to Play":
                            state = "HOW_TO_PLAY"
                        elif selected_text == "About":
                            state = "ABOUT"
                        elif selected_text == "Credits":
                            state = "CREDITS"
                        elif selected_text == "Exit":
                            running = False

            elif state in ("HOW_TO_PLAY", "ABOUT", "CREDITS"):
                if event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_ESCAPE, pygame.K_SPACE, pygame.K_RETURN):
                        state = "MENU"

            elif state == "PLAYING":
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        state = "MENU"
                        if music:
                            music.stop()
                            
                    # Freeze player inputs while animating a line clear
                    elif not game.game_over and not game.animating_clear:
                        if event.key == pygame.K_LEFT and not game.check_collision(dx=-1):
                            game.current_piece.x -= 1
                        elif event.key == pygame.K_RIGHT and not game.check_collision(dx=1):
                            game.current_piece.x += 1
                        elif event.key == pygame.K_DOWN:
                            fast_drop = True
                        elif event.key == pygame.K_UP:
                            if not game.check_collision(rotation_offset=1):
                                game.current_piece.rotation += 1
                            elif not game.check_collision(dx=-1, rotation_offset=1):
                                game.current_piece.x -= 1
                                game.current_piece.rotation += 1
                            elif not game.check_collision(dx=1, rotation_offset=1):
                                game.current_piece.x += 1
                                game.current_piece.rotation += 1
                        elif event.key == pygame.K_SPACE:
                            game.hard_drop()
                            fall_time = 0
                            
                if event.type == pygame.KEYUP:
                    if event.key == pygame.K_DOWN:
                        fast_drop = False

        if state == "MENU":
            draw_menu(screen, title_font, font, menu_options, selected_option)
            
        elif state == "HOW_TO_PLAY":
            lines = [
                "Left/Right Arrow: Move Piece",
                "Up Arrow: Rotate Piece",
                "Down Arrow: Soft Drop",
                "Spacebar: Hard Drop",
                "",
                "ESC: Return to Main Menu"
            ]
            draw_info_screen(screen, title_font, font, "HOW TO PLAY", lines)
            
        elif state == "ABOUT":
            lines = [
                "AC'S TETRIS",
                "A purely mathematical and procedural",
                "implementation of the classic game.",
                "Runs at exactly 60 FPS and features",
                "completely file-less generated audio!"
            ]
            draw_info_screen(screen, title_font, font, "ABOUT", lines)
            
        elif state == "CREDITS":
            lines = [
                "Created by: AC",
                "Music: Korobeiniki (Traditional)",
                "Engine: Pygame",
                "",
                "Thanks for playing!"
            ]
            draw_info_screen(screen, title_font, font, "CREDITS", lines)
        
        elif state == "PLAYING":
            was_game_over = game.game_over

            if game.animating_clear:
                # Handle the step-by-step visual line clear pause
                game.clear_anim_time += dt
                if game.clear_anim_time >= 50: # 50ms per expansion step
                    game.clear_anim_time = 0
                    game.clear_step += 1
                    # 5 steps out from the center complete the clearing animation
                    if game.clear_step >= 6:
                        game.execute_line_clear()
            else:
                # Standard drop logic
                fall_time += dt
                current_speed = 50 if fast_drop else game.get_gameboy_speed()

                if not game.game_over and fall_time >= current_speed:
                    fall_time = 0
                    if not game.check_collision(dy=1):
                        game.current_piece.y += 1
                        if fast_drop:
                            game.score += 1
                    else:
                        game.lock_piece()

            # Stop the music the exact moment Game Over happens
            if not was_game_over and game.game_over:
                if music:
                    music.stop()

            draw_window(screen, game, font)
            
        clock.tick(FPS)

    pygame.quit()
    sys.exit()

if __name__ == '__main__':
    main()
