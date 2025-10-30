"""
PY_NASCAR_EMAYLEO_pixel.py
Versión: Pixel-art ultra realista (dibujado por código)
Mejoras visuales: carreteras con curvas mejoradas, árboles y faroles con menor densidad
y estilo "pixel" simulado usando rectángulos. Se preserva toda la lógica del juego.

Para ejecutar: python PY_NASCAR_EMAYLEO_pixel.py
"""

import pygame
import random
import sys
import math

pygame.init()
WIDTH, HEIGHT = 900, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("NASCAR Pixel FX - Circuito")
clock = pygame.time.Clock()

# -----------------------------
# COLORES Y CONSTANTES PIXEL
# -----------------------------
WHITE = (255, 255, 255)
GRAY = (80, 80, 80)
DARK_GRAY = (42, 42, 42)
RED = (200, 0, 0)
YELLOW = (255, 235, 120)
GREEN = (20, 160, 60)
BLUE = (20, 110, 240)
BLACK = (0, 0, 0)
BROWN = (100, 56, 20)
LIGHT_GRAY = (200, 200, 200)
ORANGE = (255, 165, 0)
LIGHT_BLUE = (130, 200, 255)
GOLD = (230, 190, 0)

# Pixel scale: higher = "bigger pixels"
PIXEL = 3

ROAD_WIDTH = 520
ROAD_CENTER_X = WIDTH // 2
LANE_OFFSETS = [40, 160, 280, 400]

# Dimensiones jugador/obstáculo (en pixeles reales)
CAR_W, CAR_H = 60, 100

# Fuentes
title_font = pygame.font.SysFont("Arial", 48, bold=True)
menu_font = pygame.font.SysFont("Arial", 26)
hud_font = pygame.font.SysFont("Arial", 18)
small_font = pygame.font.SysFont("Arial", 16)

# Efectos de sonido (opcionales)
def load_sound(name):
    try:
        s = pygame.mixer.Sound(name)
        s.set_volume(0.5)
        return s
    except Exception:
        return None

turbo_sound = load_sound("turbo.wav")
cheer_sound = load_sound("cheer.wav")
pop_sound = load_sound("pop.wav")

# -----------------------------
# VARIABLES GLOBALES (iniciales)
# -----------------------------
player_x = WIDTH // 2 - CAR_W // 2
player_y = HEIGHT - CAR_H - 20
player_speed = 7
boost_speed = 13
is_boosting = False

obstacles = []
trees = []
lamps = []

SPAWN_OBSTACLE_EVENT = pygame.USEREVENT + 1

# meta / bandera
finish_line_y = -10000
finish_visible = False
finish_traveled = False

celebrating = False
celebration_start = 0

player_progress = 0.0
rival_progress = 0.0
score = 0

level_name = "MEDIO"
level_params = {}

praise_messages = ["¡Genial!", "¡Excelente!", "¡Todo un experto!", "¡Increíble!", "¡Sigue así!"]
praise_timer = 0
praise_text = ""

track_distance = 0.0
lap_count = 0
laps_total = 3
lap_distance = 2000.0

curve_amplitude = 160
curve_wavelength = 800.0

# Spawning visual density controls (reducción de amontonamiento)
TREE_MIN_SPACING = 120  # píxeles mínimos entre árboles
LAMP_MIN_SPACING = 220  # píxeles mínimos entre faroles
INITIAL_TREE_COUNT = 6
INITIAL_LAMP_COUNT = 5

# -----------------------------
# UTILIDADES PIXEL ART
# -----------------------------

def pixel_rect(surf, x, y, w, h, color):
    """Dibuja un rectángulo con 'bloques' de tamaño PIXEL: aspecto pixelado."""
    for ix in range(0, w, PIXEL):
        for iy in range(0, h, PIXEL):
            pygame.draw.rect(surf, color, (x + ix, y + iy, PIXEL, PIXEL))


def place_non_overlapping(x_range, existing, min_spacing, attempts=30):
    """Devuelve una x válida que no esté demasiado cerca de 'existing'.
    Si no encuentra en 'attempts', devuelve una posición cualquiera dentro de x_range."""
    for _ in range(attempts):
        x = random.randint(x_range[0], x_range[1])
        ok = True
        for e in existing:
            if abs(x - e.centerx) < min_spacing:
                ok = False
                break
        if ok:
            return x
    return random.randint(x_range[0], x_range[1])

# -----------------------------
# DIBUJO PIXEL-ART DE ELEMENTOS
# -----------------------------

def draw_road_pixel(vis_alpha, dist):
    """Carretera pixelada con contornos de asfalto, borde y líneas de carril.
    Añadimos una ligera textura de bandas para dar sensación de profundidad."""
    road_left_x = get_road_center_x(dist) - ROAD_WIDTH // 2
    # capa asfalto base
    pygame.draw.rect(screen, DARK_GRAY, (road_left_x, 0, ROAD_WIDTH, HEIGHT))

    # textura: bandas horizontales delgadas (pixel style)
    band_h = 6
    for y in range(0, HEIGHT, band_h * 6):
        for x_off in range(0, ROAD_WIDTH, 8 * PIXEL):
            shade = max(20, 60 - (x_off // 12))
            color = (shade, shade, shade)
            pygame.draw.rect(screen, color, (road_left_x + x_off, y, 8 * PIXEL, band_h))

    # borde de la carretera (grava)
    gravel_w = 18
    pygame.draw.rect(screen, (100, 92, 82), (road_left_x - gravel_w, 0, gravel_w, HEIGHT))
    pygame.draw.rect(screen, (100, 92, 82), (road_left_x + ROAD_WIDTH, 0, gravel_w, HEIGHT))

    # líneas de centro (pixel-dashed)
    center_x = get_road_center_x(dist)
    dash_h = 28
    gap = 18
    x = center_x - 6
    for y in range(0, HEIGHT, dash_h + gap):
        # dibujamos bloques pequeños (pixelized)
        for dx in range(0, 12, PIXEL*3):
            pixel_rect(screen, x + dx, y, PIXEL*3, dash_h, WHITE)

    # overlay por visibilidad (oscuridad que aumenta con dificultad)
    overlay = pygame.Surface((WIDTH, HEIGHT))
    overlay.fill((0, 0, 0))
    overlay.set_alpha(int(vis_alpha))
    screen.blit(overlay, (0, 0))


def draw_tree_pixel(rect):
    """Árbol pixel-art: tronco sencillo y copa con varios tonos para dar volumen."""
    # tronco
    trunk_x = rect.x + 6
    trunk_y = rect.y + 28
    pixel_rect(screen, trunk_x, trunk_y, 12, 28, (90, 60, 30))
    # sombra del tronco
    pixel_rect(screen, trunk_x + 8, trunk_y + 6, 4, 18, (70, 45, 20))

    # copa: montículos de píxeles con tonos verdes
    cx = rect.x + 12
    cy = rect.y + 16
    # capa inferior
    pixel_rect(screen, cx - 18, cy + 10, 36, 18, (20, 120, 40))
    # capa media
    pixel_rect(screen, cx - 22, cy - 2, 44, 20, (10, 150, 55))
    # luces (hojas con brillo)
    pixel_rect(screen, cx - 8, cy + 2, 8, 6, (160, 220, 140))

    # borde de sombra bajo la copa
    pygame.draw.rect(screen, (0, 0, 0, 40), (rect.x, rect.y + rect.h - 6, rect.w, 4))


def draw_lamp_pixel(lamp):
    """Poste con luminaria pixelada y cono de luz sutil pixelado."""
    # poste
    pole_x = lamp.x
    pole_y = lamp.y
    pixel_rect(screen, pole_x, pole_y, 6, 80, (140, 140, 150))
    # cabeza de la lámpara
    head_w, head_h = 14, 10
    pixel_rect(screen, pole_x - 4, pole_y - head_h, head_w, head_h, (220, 210, 160))
    # bombilla brillante
    pixel_rect(screen, pole_x + 3, pole_y - 6, 4, 4, YELLOW)

    # cono de luz: hacemos un parche con píxeles semitransparentes
    cone = pygame.Surface((200, 260), pygame.SRCALPHA)
    for i in range(0, 200, PIXEL * 2):
        alpha = max(6, 90 - i // 2)
        pygame.draw.polygon(cone, (255, 245, 200, alpha), [(100, 0), (0 + i//4, 200), (200 - i//4, 200)])
    # colocamos el cono un poco por delante de la carretera para crear reflejo
    screen.blit(cone, (lamp.centerx - 100, lamp.y))


def draw_lamp_reflection_pixel(lamp):
    refl_surface = pygame.Surface((160, 60), pygame.SRCALPHA)
    for i in range(0, 160, PIXEL*3):
        a = max(10, 120 - i)
        pixel_rect(refl_surface, i, 0, PIXEL*3, 40, (255, 255, 210, a))
    rx = lamp.centerx - 80
    ry = lamp.y + 30
    screen.blit(refl_surface, (rx, ry))


def draw_car_pixel(x, y, color, wheels_offset=0, scale=1.0):
    """Carro pixel-art: cuerpo con sombreado, parabrisas y luces.
    'scale' permite dibujar rivales más pequeños o grandes con el mismo estilo."""
    w = int(CAR_W * scale)
    h = int(CAR_H * scale)
    # cuerpo principal (rect en pixel blocks)
    body = pygame.Surface((w, h), pygame.SRCALPHA)
    # sombra base
    pixel_rect(body, 0, int(h*0.1), w, int(h*0.8), color)
    # parabrisas
    gw = max(6, int(w*0.6))
    gh = max(6, int(h*0.25))
    pixel_rect(body, int(w*0.18), int(h*0.12), gw, gh, (180, 230, 255))
    # detalles frontales: luces
    pixel_rect(body, 6, int(h - 18), 6, 6, YELLOW if not is_boosting else LIGHT_BLUE)
    pixel_rect(body, w - 12, int(h - 18), 6, 6, YELLOW if not is_boosting else LIGHT_BLUE)
    # ruedas (simples) con brillo
    pygame.draw.circle(body, BLACK, (int(w*0.2), int(h*0.18)), int(8*scale))
    pygame.draw.circle(body, BLACK, (int(w*0.8), int(h*0.18)), int(8*scale))
    pygame.draw.circle(body, BLACK, (int(w*0.2), int(h*0.78)), int(8*scale))
    pygame.draw.circle(body, BLACK, (int(w*0.8), int(h*0.78)), int(8*scale))

    # brillo en el lateral
    pixel_rect(body, int(w*0.6), int(h*0.3), int(w*0.12), int(h*0.18), (255, 255, 255, 40))

    screen.blit(body, (x, y))


def draw_obstacle_pixel(obs):
    # reutilizamos draw_car_pixel con color rojo y un toque de daño visual
    draw_car_pixel(obs.x, obs.y, RED, scale=1.0)
    # grieta/panel
    pixel_rect(screen, obs.x + 8, obs.y + 28, 12, 8, (120, 20, 20))

# -----------------------------
# FUNCIONES EXISTENTES/CONSERVADAS
# -----------------------------

def center_text(surface, text, y, font, color=WHITE):
    img = font.render(text, True, color)
    rect = img.get_rect(center=(WIDTH // 2, y))
    surface.blit(img, rect)


def get_road_center_x(dist):
    return WIDTH // 2 + int(math.sin(dist / curve_wavelength) * curve_amplitude)


def compute_lane_positions(dist):
    center_x = get_road_center_x(dist)
    left_x = center_x - ROAD_WIDTH // 2
    return [left_x + off for off in LANE_OFFSETS], left_x, center_x

# Reemplazo de funciones de dibujo anteriores por nuevas versiones pixel

def spawn_obstacle_using_current_lanes():
    lanes, _, _ = compute_lane_positions(track_distance)
    lane_x = random.choice(lanes)
    rect = pygame.Rect(lane_x, -CAR_H, CAR_W, CAR_H)
    obstacles.append(rect)

# -----------------------------
# MENÚ / SELECCIÓN NIVEL
# -----------------------------

def selection_screen():
    global level_params, level_name, laps_total, lap_distance
    while True:
        screen.fill(BLACK)
        center_text(screen, "Objetivo: NO CHOQUES!!", HEIGHT // 2 - 70, small_font, WHITE)
        center_text(screen, "NASCAR - Selección de nivel", HEIGHT // 2 - 120, title_font, YELLOW)
        center_text(screen, "Elige un nivel: 1 - FÁCIL | 2 - MEDIO | 3 - EXTREMO", HEIGHT // 2 - 35, menu_font, WHITE)
        center_text(screen, "Controles: ← → mover | Shift TURBO | Espacio reiniciar | 0 salir", HEIGHT // 2 + 50, hud_font, LIGHT_GRAY)
        center_text(screen, "Presiona 1/2/3 para seleccionar", HEIGHT // 2 + 70, small_font, ORANGE)
        pygame.display.flip()
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_1:
                    level_name = "FÁCIL"
                    level_params = {
                        "spawn_ms": 1400,
                        "obstacle_speed": 8,
                        "rival_base": 0.25,
                        "visibility": 30,
                        "score_base": 12,
                        "rival_multiplier": 0.8,
                        "curve_amp": 100,
                        "lap_distance": 1600,
                        "laps_total": 3
                    }
                    pygame.time.set_timer(SPAWN_OBSTACLE_EVENT, level_params["spawn_ms"])
                    laps_total = level_params["laps_total"]
                    lap_distance = level_params["lap_distance"]
                    return
                if e.key == pygame.K_2:
                    level_name = "MEDIO"
                    level_params = {
                        "spawn_ms": 1000,
                        "obstacle_speed": 10,
                        "rival_base": 0.4,
                        "visibility": 60,
                        "score_base": 15,
                        "rival_multiplier": 1.0,
                        "curve_amp": 160,
                        "lap_distance": 2000,
                        "laps_total": 3
                    }
                    pygame.time.set_timer(SPAWN_OBSTACLE_EVENT, level_params["spawn_ms"])
                    laps_total = level_params["laps_total"]
                    lap_distance = level_params["lap_distance"]
                    return
                if e.key == pygame.K_3:
                    level_name = "EXTREMO"
                    level_params = {
                        "spawn_ms": 800,
                        "obstacle_speed": 13,
                        "rival_base": 0.6,
                        "visibility": 110,
                        "score_base": 18,
                        "rival_multiplier": 1.25,
                        "curve_amp": 220,
                        "lap_distance": 2400,
                        "laps_total": 4
                    }
                    pygame.time.set_timer(SPAWN_OBSTACLE_EVENT, level_params["spawn_ms"])
                    laps_total = level_params["laps_total"]
                    lap_distance = level_params["lap_distance"]
                    return
                if e.key == pygame.K_0:
                    pygame.quit()
                    sys.exit()

# -----------------------------
# PANTALLA GAME OVER / CELEBRACION
# -----------------------------

def show_game_over():
    global finish_visible, finish_traveled, celebrating
    while True:
        screen.fill(BLACK)
        center_text(screen, "FIN DE LA CARRERA", HEIGHT // 2 - 120, title_font, RED)
        center_text(screen, f"Nivel: {level_name}", HEIGHT // 2 - 40, menu_font, WHITE)
        center_text(screen, f"Puntaje: {score}", HEIGHT // 2 - 10, hud_font, WHITE)
        center_text(screen, f"Tu progreso: {int(player_progress)}  |  Rival: {int(rival_progress)}", HEIGHT // 2 + 20, small_font, LIGHT_GRAY)
        center_text(screen, f"Vueltas completadas: {lap_count}/{laps_total}", HEIGHT // 2 + 50, small_font, ORANGE)
        if player_progress > rival_progress:
            center_text(screen, "¡Ganaste la carrera!", HEIGHT // 2 + 90, menu_font, GREEN)
        else:
            center_text(screen, "¡Perdiste la carrera!", HEIGHT // 2 + 90, menu_font, ORANGE)
        center_text(screen, "Presiona ESPACIO para volver a jugar  |  Presiona 0 para salir", HEIGHT // 2 + 140, small_font, WHITE)
        pygame.display.flip()
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit(); sys.exit()
        keys = pygame.key.get_pressed()
        if keys[pygame.K_SPACE]:
            reset_game()
            return
        if keys[pygame.K_0]:
            pygame.quit(); sys.exit()


def celebration_animation():
    global celebrating, celebration_start
    celebrating = True
    celebration_start = pygame.time.get_ticks()
    if cheer_sound:
        cheer_sound.play()

    anim_duration = 3500
    start = pygame.time.get_ticks()
    while pygame.time.get_ticks() - start < anim_duration:
        dt = clock.tick(60)
        screen.fill(BLACK)
        center_text(screen, "¡CAMPEÓN!", 70, title_font, GOLD)
        # trofeo pixel
        trophy_x = WIDTH // 2 - 40
        trophy_y = 140
        pixel_rect(screen, trophy_x + 10, trophy_y + 70, 60, 20, GOLD)
        pixel_rect(screen, trophy_x + 25, trophy_y + 20, 30, 50, GOLD)
        pygame.draw.circle(screen, GOLD, (trophy_x + 40, trophy_y + 20), 14)
        # conductor con copa (pixel)
        driver_x, driver_y = WIDTH // 2 - 140, 280
        pixel_rect(screen, driver_x, driver_y, 50, 80, BLUE)
        pygame.draw.circle(screen, (255, 220, 170), (driver_x + 25, driver_y - 10), 18)
        # confeti
        for i in range(20):
            px = WIDTH // 2 - 100 + random.randint(0, 200)
            py = 350 + random.randint(0, 140)
            if random.random() < 0.5:
                pixel_rect(screen, px, py, 4, 4, (255, 255, 200))
            else:
                pixel_rect(screen, px, py, 3, 3, (random.randint(0,255), random.randint(0,255), random.randint(0,255)))
        center_text(screen, "¡FELICITACIONES!", HEIGHT - 80, small_font, WHITE)
        pygame.display.flip()
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit(); sys.exit()
    celebrating = False

# -----------------------------
# RESET / INICIO PARTIDA
# -----------------------------

def reset_game():
    global player_x, player_y, obstacles, trees, lamps
    global player_progress, rival_progress, score, is_boosting
    global finish_line_y, finish_visible, finish_traveled, celebrating
    global track_distance, lap_count
    player_x = WIDTH // 2 - CAR_W // 2
    obstacles = []
    trees = []
    lamps = []
    player_progress = 0.0
    rival_progress = 0.0
    score = 0
    is_boosting = False
    finish_line_y = -10000
    finish_visible = False
    finish_traveled = False
    celebrating = False
    track_distance = 0.0
    lap_count = 0

# -----------------------------
# BUCLE PRINCIPAL
# -----------------------------

def main_loop():
    global player_x, is_boosting, player_progress, rival_progress, score
    global finish_line_y, finish_visible, finish_traveled, praise_timer, praise_text
    global track_distance, lap_count, curve_amplitude, curve_wavelength

    obstacle_speed = level_params["obstacle_speed"]
    rival_rate = level_params["rival_base"]
    visibility_max = level_params["visibility"]
    base_score = level_params["score_base"]
    rival_multiplier = level_params["rival_multiplier"]

    curve_amplitude = level_params.get("curve_amp", curve_amplitude)

    # plantar árboles / lámparas iniciales con espaciamiento
    road_left_preview = get_road_center_x(track_distance) - ROAD_WIDTH // 2
    left_range = (30, road_left_preview - 60)
    right_range = (road_left_preview + ROAD_WIDTH + 20, WIDTH - 60)

    for i in range(INITIAL_TREE_COUNT):
        side = random.choice(["L", "R"])
        r = left_range if side == "L" else right_range
        x = place_non_overlapping(r, trees, TREE_MIN_SPACING)
        trees.append(pygame.Rect(x, random.randint(-600, HEIGHT), 24, 64))

    for i in range(INITIAL_LAMP_COUNT):
        side = random.choice(["L", "R"])
        r = left_range if side == "L" else right_range
        x = place_non_overlapping(r, lamps, LAMP_MIN_SPACING)
        lamps.append(pygame.Rect(x, random.randint(-800, HEIGHT), 10, 100))

    finish_threshold = int(lap_distance * 0.9 / 20)
    running = True
    last_time = pygame.time.get_ticks()
    wheel_offset = 0

    # menor probabilidad de spawn para evitar amontonamiento
    tree_spawn_chance = 0.035
    lamp_spawn_chance = 0.015

    while running:
        dt = clock.tick(60)
        now = pygame.time.get_ticks()

        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if e.type == SPAWN_OBSTACLE_EVENT:
                spawn_obstacle_using_current_lanes()
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_0:
                    pygame.quit(); sys.exit()

        keys = pygame.key.get_pressed()
        if keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]:
            current_speed = boost_speed
            if not is_boosting and turbo_sound:
                turbo_sound.play()
            is_boosting = True
        else:
            current_speed = player_speed
            is_boosting = False

        lanes_now, road_left_x, road_center_x = compute_lane_positions(track_distance)
        if keys[pygame.K_LEFT] and player_x > road_left_x + 6:
            player_x -= current_speed
        if keys[pygame.K_RIGHT] and player_x < road_left_x + ROAD_WIDTH - CAR_W - 6:
            player_x += current_speed

        for obs in obstacles[:]:
            obs.y += obstacle_speed
            if obs.colliderect(pygame.Rect(player_x, player_y, CAR_W, CAR_H)):
                show_game_over()
                return
            if obs.y > HEIGHT + 50:
                obstacles.remove(obs)
                gain = base_score + (base_score // 2 if is_boosting else 0)
                score += gain
                player_progress += 1
                inc = 40 + (25 if is_boosting else 0)
                track_distance += inc
                praise_text = random.choice(praise_messages)
                praise_timer = now

        rival_progress += rival_rate * (1.2 if is_boosting else 1.0) * 0.1

        if int(player_progress) and int(player_progress) % 10 == 0:
            obstacle_speed = min(obstacle_speed + 0.004 * dt, level_params["obstacle_speed"] + 6)

        if track_distance >= lap_distance:
            lap_count += 1
            track_distance -= lap_distance
            score += level_params.get("score_base", 15) * 3
            if lap_count >= laps_total:
                finish_visible = True
                finish_traveled = True
                celebration_animation()
                show_game_over()
                return

        if (player_progress >= int(lap_distance / 25)) and not finish_visible and lap_count >= (laps_total - 1):
            finish_line_y = -200
            finish_visible = True

        # generar árboles y lámparas con menor densidad y evitando solapamientos
        road_left_x = get_road_center_x(track_distance) - ROAD_WIDTH // 2
        if random.random() < tree_spawn_chance:
            side = random.choice(["L", "R"])
            r = (30, road_left_x - 40) if side == "L" else (road_left_x + ROAD_WIDTH + 20, WIDTH - 60)
            x = place_non_overlapping(r, trees, TREE_MIN_SPACING)
            trees.append(pygame.Rect(x, -60, 24, 64))
        for t in trees[:]:
            t.y += obstacle_speed / 2
            if t.y > HEIGHT + 80:
                trees.remove(t)

        if random.random() < lamp_spawn_chance:
            side = random.choice(["L", "R"])
            r = (30, road_left_x - 40) if side == "L" else (road_left_x + ROAD_WIDTH + 20, WIDTH - 60)
            x = place_non_overlapping(r, lamps, LAMP_MIN_SPACING)
            lamps.append(pygame.Rect(x, -120, 10, 100))
        for l in lamps[:]:
            l.y += obstacle_speed / 2
            if l.y > HEIGHT + 140:
                lamps.remove(l)

        wheel_offset = (wheel_offset + 1) % 6

        # RENDER
        screen.fill(BLACK)
        current_vis = min(level_params["visibility"], level_params["visibility"] + int(player_progress * 0.2))
        draw_road_pixel(current_vis, track_distance)

        # dibujar reflejos y faroles
        for lamp in lamps:
            draw_lamp_pixel(lamp)
            draw_lamp_reflection_pixel(lamp)

        # dibujar árboles
        for t in trees:
            draw_tree_pixel(t)

        # dibujar meta si visible
        if finish_visible and not finish_traveled:
            finish_line_y += 2
            left_x = get_road_center_x(track_distance) - ROAD_WIDTH // 2 + 40
            right_x = get_road_center_x(track_distance) + ROAD_WIDTH // 2 - 40
            pygame.draw.rect(screen, LIGHT_GRAY, (left_x, finish_line_y, 8, 120))
            pygame.draw.rect(screen, LIGHT_GRAY, (right_x, finish_line_y, 8, 120))
            sq = 12
            for i in range(0, 10):
                for j in range(0, 5):
                    color = WHITE if (i + j) % 2 == 0 else BLACK
                    px = left_x + 8 + i * sq
                    py = finish_line_y + j * sq + 10
                    pygame.draw.rect(screen, color, (px, py, sq, sq))
            center_text(screen, "-- META --", finish_line_y - 20, small_font, ORANGE)
            if finish_line_y > player_y - 200:
                finish_traveled = True
                celebration_animation()
                show_game_over()
                return

        # dibujar obstáculos
        for obs in obstacles:
            draw_obstacle_pixel(obs)

        # dibujar rival con escala y pixel style
        rival_rel = (rival_progress - player_progress) * 6
        rival_screen_y = player_y - 200 + int(rival_rel)
        rival_x = get_road_center_x(track_distance) + ROAD_WIDTH // 2 - 120
        if -200 < rival_screen_y < HEIGHT:
            draw_car_pixel(rival_x, rival_screen_y, ORANGE, scale=0.9)

        # efecto turbo y carro jugador
        if is_boosting:
            for i in range(3):
                flame_color = random.choice([(255, 200, 40), (255, 120, 10), (255, 60, 0)])
                flame = pygame.Rect(player_x + 12, player_y + CAR_H + i * 6, 36, 10)
                pygame.draw.ellipse(screen, flame_color, flame)
            glow = pygame.Surface((CAR_W + 30, CAR_H + 30), pygame.SRCALPHA)
            pygame.draw.ellipse(glow, (100, 170, 255, 60), glow.get_rect())
            screen.blit(glow, (player_x - 15, player_y - 10))

        draw_car_pixel(player_x, player_y, BLUE, wheels_offset=wheel_offset, scale=1.0)

        hud_text = f"Puntos: {score}   |   Nivel: {level_name}   |   Vueltas: {lap_count}/{laps_total}   |   Distancia vuelta: {int(track_distance)}/{int(lap_distance)}"
        center_text(screen, hud_text, 22, hud_font, WHITE)
        if praise_timer and now - praise_timer < 1000:
            center_text(screen, praise_text, 50, small_font, LIGHT_BLUE)

        pygame.display.flip()

# -----------------------------
# FLUJO DE EJECUCIÓN
# -----------------------------
if __name__ == "__main__":
    reset_game()
    selection_screen()
    pygame.time.set_timer(SPAWN_OBSTACLE_EVENT, level_params["spawn_ms"])

    while True:
        main_loop()
        show_game_over()
        reset_game()
        selection_screen()
        pygame.time.set_timer(SPAWN_OBSTACLE_EVENT, level_params["spawn_ms"])
