import socket
import json
import threading
import sys
import pygame
import random

# ==================== LÓGICA DO TETRIS ====================
BOARD_WIDTH = 10
BOARD_HEIGHT = 20

SHAPES = [
    [[1, 1, 1, 1]], # I
    [[1, 1], [1, 1]], # O
    [[0, 1, 0], [1, 1, 1]], # T
    [[0, 1, 1], [1, 1, 0]], # S
    [[1, 1, 0], [0, 1, 1]], # Z
    [[1, 0, 0], [1, 1, 1]], # J
    [[0, 0, 1], [1, 1, 1]]  # L
]

class TetrisGame:
    def __init__(self):
        self.board = [[0 for _ in range(BOARD_WIDTH)] for _ in range(BOARD_HEIGHT)]
        self.current_piece = None
        self.current_x = 0
        self.current_y = 0
        self.current_shape_idx = 0
        self.game_over = False
        self.score = 0
        self.spawn_piece()

    def spawn_piece(self):
        self.current_shape_idx = random.randint(0, len(SHAPES) - 1)
        self.current_piece = [row[:] for row in SHAPES[self.current_shape_idx]]
        self.current_x = BOARD_WIDTH // 2 - len(self.current_piece[0]) // 2
        self.current_y = 0
        if self.check_collision(self.current_piece, self.current_x, self.current_y):
            self.game_over = True

    def check_collision(self, shape, offset_x, offset_y):
        for r_idx, row in enumerate(shape):
            for c_idx, cell in enumerate(row):
                if cell:
                    board_x = c_idx + offset_x
                    board_y = r_idx + offset_y
                    if board_x < 0 or board_x >= BOARD_WIDTH or board_y >= BOARD_HEIGHT:
                        return True
                    if board_y >= 0 and self.board[board_y][board_x] != 0:
                        return True
        return False

    def rotate_piece(self):
        if self.game_over: return
        rotated = [list(row) for row in zip(*self.current_piece[::-1])]
        if not self.check_collision(rotated, self.current_x, self.current_y):
            self.current_piece = rotated
        elif not self.check_collision(rotated, self.current_x - 1, self.current_y):
            self.current_x -= 1
            self.current_piece = rotated
        elif not self.check_collision(rotated, self.current_x + 1, self.current_y):
            self.current_x += 1
            self.current_piece = rotated

    def move(self, dx, dy):
        if self.game_over: return 0
        new_x = self.current_x + dx
        new_y = self.current_y + dy
        if not self.check_collision(self.current_piece, new_x, new_y):
            self.current_x = new_x
            self.current_y = new_y
            return 0
        if dy > 0:
            return self.lock_piece()
        return 0

    def hard_drop(self):
        if self.game_over: return 0
        while not self.check_collision(self.current_piece, self.current_x, self.current_y + 1):
            self.current_y += 1
        return self.lock_piece()

    def lock_piece(self):
        for r_idx, row in enumerate(self.current_piece):
            for c_idx, cell in enumerate(row):
                if cell:
                    board_y = self.current_y + r_idx
                    board_x = self.current_x + c_idx
                    if 0 <= board_y < BOARD_HEIGHT and 0 <= board_x < BOARD_WIDTH:
                        self.board[board_y][board_x] = self.current_shape_idx + 1
        
        lines_cleared = self.clear_lines()
        
        garbage_sent = 0
        if lines_cleared == 2:
            garbage_sent = 1
        elif lines_cleared == 3:
            garbage_sent = 2
        elif lines_cleared >= 4:
            garbage_sent = 4

        self.spawn_piece()
        return garbage_sent

    def clear_lines(self):
        full_lines = [r for r, row in enumerate(self.board) if all(c != 0 for c in row)]
        for r in full_lines:
            del self.board[r]
            self.board.insert(0, [0 for _ in range(BOARD_WIDTH)])
        
        count = len(full_lines)
        if count > 0:
            self.score += (count ** 2) * 100
        return count

    def add_garbage_lines(self, num_lines):
        for _ in range(num_lines):
            self.board.pop(0)
            garbage_row = [8 for _ in range(BOARD_WIDTH)]
            hole_idx = random.randint(0, BOARD_WIDTH - 1)
            garbage_row[hole_idx] = 0
            self.board.append(garbage_row)
            
            if self.check_collision(self.current_piece, self.current_x, self.current_y):
                self.current_y -= 1
                if self.check_collision(self.current_piece, self.current_x, self.current_y):
                    self.game_over = True

    def update_gravity(self):
        return self.move(0, 1)

    def get_render_board(self):
        temp_board = [row[:] for row in self.board]
        if self.current_piece:
            for r_idx, row in enumerate(self.current_piece):
                for c_idx, cell in enumerate(row):
                    if cell:
                        bx = self.current_x + c_idx
                        by = self.current_y + r_idx
                        if 0 <= by < BOARD_HEIGHT and 0 <= bx < BOARD_WIDTH:
                            temp_board[by][bx] = self.current_shape_idx + 1
        return temp_board

# ==================== REDE TCP E PYGAME ====================
SERVER_HOST = '127.0.0.1'
SERVER_PORT = 50005

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
try:
    client_socket.connect((SERVER_HOST, SERVER_PORT))
except Exception as e:
    print(f"Não foi possível conectar ao servidor: {e}")
    sys.exit()

WIDTH, HEIGHT = 650, 520
GRID_SIZE = 22

pygame.init()
pygame.key.set_repeat(200, 50)

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Tetris Multiplayer TCP")
clock = pygame.time.Clock()

player_id = None
game_started = False
game_seed = None
opponent_board = [[0 for _ in range(BOARD_WIDTH)] for _ in range(BOARD_HEIGHT)]

tetris = TetrisGame()

COLORS = [
    (0, 0, 0),        # 0: Vazio
    (0, 255, 255),    # 1: I - Ciano
    (255, 255, 0),    # 2: O - Amarelo
    (128, 0, 128),    # 3: T - Roxo
    (0, 255, 0),      # 4: S - Verde
    (255, 0, 0),      # 5: Z - Vermelho
    (0, 0, 255),      # 6: J - Azul
    (255, 127, 0),    # 7: L - Laranja
    (100, 100, 100)   # 8: Linha de Lixo (Cinza)
]

font = pygame.font.SysFont(None, 24)

# Thread para escutar o stream contínuo de dados do servidor TCP
def receive_server_messages():
    global game_started, opponent_board, game_seed, player_id
    buffer = ""
    while True:
        try:
            data = client_socket.recv(4096)
            if not data:
                break
            buffer += data.decode('utf-8')
            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)
                if not line.strip():
                    continue
                message = json.loads(line)
                
                msg_type = message.get("type")
                if msg_type == "WELCOME":
                    player_id = message.get("player_id")
                elif msg_type == "START":
                    game_seed = message.get("seed")
                    random.seed(game_seed)
                    game_started = True
                    tetris.spawn_piece()
                elif msg_type == "BOARD_UPDATE":
                    if message.get("player_id") != player_id:
                        opponent_board = message.get("board")
                elif msg_type == "GARBAGE":
                    if message.get("target_id") == player_id:
                        tetris.add_garbage_lines(message.get("lines"))
        except Exception:
            break

threading.Thread(target=receive_server_messages, daemon=True).start()

FALL_EVENT = pygame.USEREVENT + 1
pygame.time.set_timer(FALL_EVENT, 500)

def send_to_server(data_dict):
    try:
        message_str = json.dumps(data_dict) + "\n"
        client_socket.sendall(message_str.encode('utf-8'))
    except:
        pass

running = True
while running:
    screen.fill((25, 25, 25))
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            
        elif event.type == FALL_EVENT and game_started and not tetris.game_over:
            garbage_sent = tetris.update_gravity()
            if garbage_sent > 0:
                opp_id = 2 if player_id == 1 else 1
                send_to_server({"type": "GARBAGE", "target_id": opp_id, "lines": garbage_sent})
            
        elif event.type == pygame.KEYDOWN and game_started and not tetris.game_over:
            garbage_sent = 0
            if event.key == pygame.K_LEFT:
                tetris.move(-1, 0)
            elif event.key == pygame.K_RIGHT:
                tetris.move(1, 0)
            elif event.key == pygame.K_DOWN:
                garbage_sent = tetris.move(0, 1)
            elif event.key == pygame.K_UP:
                tetris.rotate_piece()
            elif event.key == pygame.K_SPACE:
                garbage_sent = tetris.hard_drop()
            
            if garbage_sent > 0:
                opp_id = 2 if player_id == 1 else 1
                send_to_server({"type": "GARBAGE", "target_id": opp_id, "lines": garbage_sent})

    if game_started:
        send_to_server({
            "type": "BOARD_UPDATE",
            "player_id": player_id,
            "board": tetris.board
        })

    if not game_started:
        status_txt = "Conectado ao servidor. Aguardando o 2º jogador..." if player_id is None else f"Conectado como Jogador {player_id}. Aguardando o 2º jogador..."
        txt = font.render(status_txt, True, (255, 255, 255))
        screen.blit(txt, (WIDTH // 2 - txt.get_width() // 2, HEIGHT // 2))
    else:
        screen.blit(font.render(f"Seu Jogo (P{player_id}) - Score: {tetris.score}", True, (255, 255, 255)), (40, 20))
        screen.blit(font.render("Oponente", True, (255, 255, 255)), (360, 20))

        render_me = tetris.get_render_board()
        for r in range(BOARD_HEIGHT):
            for c in range(BOARD_WIDTH):
                val = render_me[r][c]
                color = COLORS[val]
                pygame.draw.rect(screen, color, (40 + c*GRID_SIZE, 50 + r*GRID_SIZE, GRID_SIZE-1, GRID_SIZE-1))
                pygame.draw.rect(screen, (40, 40, 40), (40 + c*GRID_SIZE, 50 + r*GRID_SIZE, GRID_SIZE-1, GRID_SIZE-1), 1)

        for r in range(BOARD_HEIGHT):
            for c in range(BOARD_WIDTH):
                val = opponent_board[r][c]
                color = COLORS[val]
                pygame.draw.rect(screen, color, (360 + c*GRID_SIZE, 50 + r*GRID_SIZE, GRID_SIZE-1, GRID_SIZE-1))
                pygame.draw.rect(screen, (40, 40, 40), (360 + c*GRID_SIZE, 50 + r*GRID_SIZE, GRID_SIZE-1, GRID_SIZE-1), 1)

        if tetris.game_over:
            go_txt = font.render("GAME OVER", True, (255, 0, 0))
            screen.blit(go_txt, (100, HEIGHT // 2))

    pygame.display.flip()
    clock.tick(30)

pygame.quit()
sys.exit()