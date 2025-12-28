# client.py — оновлений: додає меню, завантаження текстур і магазин скінів
from pygame import *
import pygame as pg
import socket
import json
from threading import Thread
import os

# ---ПУГАМЕ НАЛАШТУВАННЯ ---
WIDTH, HEIGHT = 800, 600
ASSET_DIR = os.path.join(os.path.dirname(__file__), "assets")

init()
screen = display.set_mode((WIDTH, HEIGHT))
clock = time.Clock()
display.set_caption("Пінг-Понг")
# ---СЕРВЕР ---
def connect_to_server():
    while True:
        try:
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.connect(('localhost', 8080))
            buffer = ""
            game_state = {}
            my_id = int(client.recv(24).decode())
            return my_id, game_state, buffer, client
        except Exception:
            pass


def receive():
    global buffer, game_state, game_over
    while not game_over:
        try:
            data = client.recv(1024).decode()
            buffer += data
            while "\n" in buffer:
                packet, buffer = buffer.split("\n", 1)
                if packet.strip():
                    game_state = json.loads(packet)
        except Exception:
            game_state["winner"] = -1
            break

# --- ШРИФТИ ---
font_win = font.Font(None, 72)
font_main = font.Font(None, 36)

# --- Helpers: ensure simple assets exist (creates placeholder images) ---
def ensure_assets():
    if not os.path.isdir(ASSET_DIR):
        os.makedirs(ASSET_DIR, exist_ok=True)

    def save_surface(path, size, fill, circle=None, text=None):
        surf = pg.Surface(size, pg.SRCALPHA)
        surf.fill(fill)
        if circle:
            pg.draw.circle(surf, circle[0], circle[1], circle[2])
        if text:
            f = pg.font.Font(None, 24)
            txt = f.render(text, True, (255,255,255))
            surf.blit(txt, txt.get_rect(center=(size[0]//2, size[1]//2)))
        pg.image.save(surf, path)

    bg_path = os.path.join(ASSET_DIR, "background.png")
    if not os.path.exists(bg_path):
        save_surface(bg_path, (WIDTH, HEIGHT), (40, 40, 60), None, "PING PONG")

    # ball skins
    balls = [("ball_red.png", (200,50,50)), ("ball_blue.png", (50,120,200))]
    for name, color in balls:
        p = os.path.join(ASSET_DIR, name)
        if not os.path.exists(p):
            save_surface(p, (20,20), (0,0,0,0), circle=(color, (10,10), 9))

    # paddle skins
    paddles = [("paddle_red.png", (200,50,50)), ("paddle_blue.png", (50,120,200))]
    for name, color in paddles:
        p = os.path.join(ASSET_DIR, name)
        if not os.path.exists(p):
            save_surface(p, (20,100), color)

    # buttons
    buttons = ["btn_play.png", "btn_settings.png", "btn_shop.png", "btn_exit.png"]
    for b in buttons:
        p = os.path.join(ASSET_DIR, b)
        if not os.path.exists(p):
            save_surface(p, (200,60), (80,80,100), None, b.split('_')[1].split('.')[0].upper())


ensure_assets()

# --- Load textures and settings ---
def load_image(name, size=None):
    path = os.path.join(ASSET_DIR, name)
    try:
        img = pg.image.load(path).convert_alpha()
        if size:
            img = pg.transform.smoothscale(img, size)
        return img
    except Exception:
        return None

settings_path = os.path.join(os.path.dirname(__file__), "settings.json")
default_settings = {"player_name": "Player", "ball_skin": "ball_red.png", "paddle_skin": "paddle_red.png"}
if os.path.exists(settings_path):
    try:
        with open(settings_path, 'r', encoding='utf-8') as f:
            settings = json.load(f)
    except Exception:
        settings = default_settings.copy()
else:
    settings = default_settings.copy()

bg_img = load_image("background.png", (WIDTH, HEIGHT))
ball_img = load_image(settings.get('ball_skin', default_settings['ball_skin']), (20,20))
paddle_img = load_image(settings.get('paddle_skin', default_settings['paddle_skin']), (20,100))
btn_play = load_image('btn_play.png', (200,60))
btn_settings = load_image('btn_settings.png', (200,60))
btn_shop = load_image('btn_shop.png', (200,60))
btn_exit = load_image('btn_exit.png', (200,60))

# --- ЗВУКИ (тимчасово пусті) ---
sound_events = {
    'wall_hit': None,
    'platform_hit': None
}

# --- ГРА helpers ---
game_over = False
winner = None
you_winner = None
client = None
buffer = ""
game_state = {}

def save_settings():
    try:
        with open(settings_path, 'w', encoding='utf-8') as f:
            json.dump(settings, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

def draw_button(surf, img, rect):
    if img:
        surf.blit(img, rect)
    else:
        draw.rect(surf, (100,100,140), rect)

def shop_screen():
    # Simple shop: choose between red and blue skins
    running = True
    choices = {
        'balls': ['ball_red.png', 'ball_blue.png'],
        'paddles': ['paddle_red.png', 'paddle_blue.png']
    }
    while running:
        for e in event.get():
            if e.type == QUIT:
                exit()
            if e.type == KEYDOWN and e.key == K_ESCAPE:
                running = False
            if e.type == MOUSEBUTTONDOWN and e.button == 1:
                mx,my = e.pos
                # ball choices on left
                for i, name in enumerate(choices['balls']):
                    r = Rect(100, 150 + i*120, 60, 60)
                    if r.collidepoint(mx,my):
                        settings['ball_skin'] = name
                        save_settings()
                        global ball_img
                        ball_img = load_image(name, (20,20))
                # paddle choices on right
                for i, name in enumerate(choices['paddles']):
                    r = Rect(500, 150 + i*120, 20, 100)
                    if r.collidepoint(mx,my):
                        settings['paddle_skin'] = name
                        save_settings()
                        global paddle_img
                        paddle_img = load_image(name, (20,100))

        screen.fill((30,30,40))
        title = font_main.render('Shop — вибір скінів (Esc назад)', True, (255,255,255))
        screen.blit(title, (60, 40))

        # draw options
        for i, name in enumerate(choices['balls']):
            img = load_image(name, (60,60))
            if img:
                screen.blit(img, (100,150 + i*120))
            lbl = font_main.render(name.replace('.png',''), True, (200,200,200))
            screen.blit(lbl, (180, 160 + i*120))

        for i, name in enumerate(choices['paddles']):
            img = load_image(name, (20,100))
            if img:
                screen.blit(img, (500,150 + i*120))
            lbl = font_main.render(name.replace('.png',''), True, (200,200,200))
            screen.blit(lbl, (540, 180 + i*120))

        display.update()
        clock.tick(30)

def settings_screen():
    running = True
    input_active = False
    name_text = settings.get('player_name', 'Player')
    input_rect = Rect(300, 200, 200, 40)
    while running:
        for e in event.get():
            if e.type == QUIT:
                exit()
            if e.type == KEYDOWN:
                if e.key == K_ESCAPE:
                    running = False
                elif input_active:
                    if e.key == K_BACKSPACE:
                        name_text = name_text[:-1]
                    elif e.key == K_RETURN:
                        settings['player_name'] = name_text or 'Player'
                        save_settings()
                        running = False
                    else:
                        name_text += e.unicode
            if e.type == MOUSEBUTTONDOWN:
                if input_rect.collidepoint(e.pos):
                    input_active = True
                else:
                    input_active = False

        screen.fill((20,20,30))
        title = font_main.render('Settings (Enter to save, Esc to cancel)', True, (255,255,255))
        screen.blit(title, (40,40))

        txt_surf = font_main.render('Player name:', True, (200,200,200))
        screen.blit(txt_surf, (200, 170))
        draw.rect(screen, (255,255,255), input_rect, 2 if input_active else 1)
        name_surf = font_main.render(name_text, True, (255,255,255))
        screen.blit(name_surf, (input_rect.x + 6, input_rect.y + 6))

        display.update()
        clock.tick(30)

def main_menu():
    # Simple main menu loop
    while True:
        for e in event.get():
            if e.type == QUIT:
                exit()
            if e.type == MOUSEBUTTONDOWN and e.button == 1:
                mx,my = e.pos
                # Play
                r_play = Rect(WIDTH//2-100, 200, 200, 60)
                r_shop = Rect(WIDTH//2-100, 280, 200, 60)
                r_set = Rect(WIDTH//2-100, 360, 200, 60)
                r_exit = Rect(WIDTH//2-100, 440, 200, 60)
                if r_play.collidepoint(mx,my):
                    return 'play'
                if r_shop.collidepoint(mx,my):
                    shop_screen()
                if r_set.collidepoint(mx,my):
                    settings_screen()
                if r_exit.collidepoint(mx,my):
                    exit()

        if bg_img:
            screen.blit(bg_img, (0,0))
        else:
            screen.fill((20,20,40))

        title = font_win.render('PING PONG', True, (255,215,0))
        screen.blit(title, (WIDTH//2 - title.get_width()//2, 60))

        # buttons
        r_play = Rect(WIDTH//2-100, 200, 200, 60)
        r_shop = Rect(WIDTH//2-100, 280, 200, 60)
        r_set = Rect(WIDTH//2-100, 360, 200, 60)
        r_exit = Rect(WIDTH//2-100, 440, 200, 60)

        draw_button(screen, btn_play, r_play)
        draw_button(screen, btn_shop, r_shop)
        draw_button(screen, btn_settings, r_set)
        draw_button(screen, btn_exit, r_exit)

        display.update()
        clock.tick(30)


# --- Основна гра (міграція існуючого циклу) ---
def play_game():
    global game_over, you_winner, ball_img, paddle_img, client, buffer, game_state
    game_over = False
    you_winner = None
    my_id, game_state, buffer, client = connect_to_server()
    Thread(target=receive, daemon=True).start()

    while True:
        for e in event.get():
            if e.type == QUIT:
                exit()

        if "countdown" in game_state and game_state["countdown"] > 0:
            screen.fill((0, 0, 0))
            countdown_text = font.Font(None, 72).render(str(game_state["countdown"]), True, (255, 255, 255))
            screen.blit(countdown_text, (WIDTH // 2 - 20, HEIGHT // 2 - 30))
            display.update()
            continue

        if "winner" in game_state and game_state["winner"] is not None:
            screen.fill((20, 20, 20))

            if you_winner is None:
                if game_state["winner"] == my_id:
                    you_winner = True
                else:
                    you_winner = False

            if you_winner:
                text = "Ти переміг!"
            else:
                text = "Пощастить наступним разом!"

            win_text = font_win.render(text, True, (255, 215, 0))
            text_rect = win_text.get_rect(center=(WIDTH // 2, HEIGHT // 2))
            screen.blit(win_text, text_rect)

            text = font_win.render('K - рестарт (Esc для меню)', True, (255, 215, 0))
            text_rect = text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 120))
            screen.blit(text, text_rect)

            display.update()
            keys = key.get_pressed()
            if keys[K_k]:
                return
            if keys[K_ESCAPE]:
                return
            continue

        if game_state:
            if bg_img:
                screen.blit(bg_img, (0,0))
            else:
                screen.fill((30,30,30))

            # paddles
            p0y = game_state['paddles']['0']
            p1y = game_state['paddles']['1']
            if paddle_img:
                screen.blit(paddle_img, (20, p0y))
                screen.blit(paddle_img, (WIDTH - 40, p1y))
            else:
                draw.rect(screen, (0, 255, 0), (20, p0y, 20, 100))
                draw.rect(screen, (255, 0, 255), (WIDTH - 40, p1y, 20, 100))

            # ball
            bx = game_state['ball']['x']
            by = game_state['ball']['y']
            if ball_img:
                screen.blit(ball_img, (bx-10, by-10))
            else:
                draw.circle(screen, (255,255,255), (bx, by), 10)

            score_text = font_main.render(f"{game_state['scores'][0]} : {game_state['scores'][1]}", True, (255, 255, 255))
            screen.blit(score_text, (WIDTH // 2 -25, 20))

        else:
            wating_text = font_main.render(f"Очікування гравців...", True, (255, 255, 255))
            screen.blit(wating_text, (WIDTH // 2 - 25, 20))

        display.update()
        clock.tick(60)

        keys = key.get_pressed()
        try:
            if keys[K_w]:
                client.send(b"UP")
            elif keys[K_s]:
                client.send(b"DOWN")
        except Exception:
            pass


if __name__ == '__main__':
    # Show menu first
    while True:
        action = main_menu()
        if action == 'play':
            play_game()
        else:
            break
