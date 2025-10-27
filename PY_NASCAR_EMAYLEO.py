"""
PY_NASCAR_EMAYLEO_circuito.py
Versión con curvas y circuito por vueltas, manteniendo HUD centrado, turbo visual + sonido,
reflejos de luz, bandera/meta, animación de celebración, selección de nivel.
"""

import pygame
import random
import sys
import math

pygame.init()
WIDTH, HEIGHT = 900, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("NASCAR Final FX - Circuito")
clock = pygame.time.Clock()

# -----------------------------
# COLORES Y CONSTANTES
# -----------------------------
WHITE = (255, 255, 255)
GRAY = (80, 80, 80)
DARK_GRAY = (50, 50, 50)
RED = (200, 0, 0)
YELLOW = (255, 255, 0)
GREEN = (0, 200, 0)
BLUE = (0, 120, 255)
BLACK = (0, 0, 0)
BROWN = (120, 60, 20)
LIGHT_GRAY = (200, 200, 200)
ORANGE = (255, 165, 0)
LIGHT_BLUE = (120, 200, 255)
GOLD = (230, 190, 0)

ROAD_WIDTH = 520
# ROAD center will be dynamic to simulate curves:
ROAD_CENTER_X = WIDTH // 2
# lanes offsets relative to road left
LANE_OFFSETS = [40, 160, 280, 400]

# Dimensiones jugador/obstáculo
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
finish_line_y = -10000  # posición alta hasta que deba aparecer
finish_visible = False
finish_traveled = False  # si el jugador cruzó la meta

# celebracion
celebrating = False
celebration_start = 0

# progresos y puntaje
player_progress = 0.0
rival_progress = 0.0
score = 0

# nivel (se define en selección)
level_name = "MEDIO"
level_params = {}

# temporizadores
praise_messages = ["¡Genial!", "¡Excelente!", "¡Todo un experto!", "¡Increíble!", "¡Sigue así!"]
praise_timer = 0
praise_text = ""

# circuito: distancia, vueltas
track_distance = 0.0           # distancia recorrida en la vuelta actual (puntos arbitraros)
lap_count = 0
laps_total = 3
lap_distance = 2000.0         # distancia necesaria para completar una vuelta (ajustable)

# parámetros de curva
curve_amplitude = 160        # cuánto se desplaza el centro de la pista horizontalmente
curve_wavelength = 800.0     # longitud de onda de la curva (en distancia de pista)

# -----------------------------
# FUNCS DIBUJO / UTILIDADES
# -----------------------------
def center_text(surface, text, y, font, color=WHITE):
    img = font.render(text, True, color)
    rect = img.get_rect(center=(WIDTH // 2, y))
    surface.blit(img, rect)

def get_road_center_x(dist):
    """Devuelve el centro de la carretera según la distancia recorrida (curvas)."""
    # usamos seno para curvas suaves; se puede cambiar por lista de segmentos para más control.
    return WIDTH // 2 + int(math.sin(dist / curve_wavelength) * curve_amplitude)

def compute_lane_positions(dist):
    """Calcula las posiciones X de los 4 carriles según curvatura actual."""
    center_x = get_road_center_x(dist)
    left_x = center_x - ROAD_WIDTH // 2
    return [left_x + off for off in LANE_OFFSETS], left_x, center_x

def draw_road(vis_alpha, dist):
    road_left_x = get_road_center_x(dist) - ROAD_WIDTH // 2
    pygame.draw.rect(screen, DARK_GRAY, (road_left_x, 0, ROAD_WIDTH, HEIGHT))
    # líneas centrales (perpendicular a pantalla, se mantienen centradas en center_x)
    center_x = get_road_center_x(dist)
    for y in range(0, HEIGHT, 60):
        pygame.draw.rect(screen, WHITE, (center_x - 6, y, 12, 40))
    # overlay por visibilidad (oscuridad que aumenta con dificultad)
    overlay = pygame.Surface((WIDTH, HEIGHT))
    overlay.fill((0, 0, 0))
    overlay.set_alpha(int(vis_alpha))
    screen.blit(overlay, (0, 0))

def draw_car(x, y, color, wheels_offset=0):
    # carro central: cuerpo, parabrisas, luces, ruedas
    pygame.draw.rect(screen, color, (x, y, CAR_W, CAR_H), border_radius=8)
    pygame.draw.rect(screen, LIGHT_GRAY, (x + 8, y + 10, CAR_W - 16, 28), border_radius=4)
    # luces delanteras (si boosting azules)
    if is_boosting:
        pygame.draw.circle(screen, LIGHT_BLUE, (x + 10, y + CAR_H - 12), 6)
        pygame.draw.circle(screen, LIGHT_BLUE, (x + CAR_W - 10, y + CAR_H - 12), 6)
    else:
        pygame.draw.circle(screen, YELLOW, (x + 10, y + CAR_H - 12), 5)
        pygame.draw.circle(screen, YELLOW, (x + CAR_W - 10, y + CAR_H - 12), 5)
    # ruedas
    pygame.draw.circle(screen, BLACK, (x + 14, y + 20 + wheels_offset), 10)
    pygame.draw.circle(screen, BLACK, (x + CAR_W - 14, y + 20 + wheels_offset), 10)
    pygame.draw.circle(screen, BLACK, (x + 14, y + CAR_H - 20 + wheels_offset), 10)
    pygame.draw.circle(screen, BLACK, (x + CAR_W - 14, y + CAR_H - 20 + wheels_offset), 10)

def draw_obstacle(obs):
    draw_car(obs.x, obs.y, RED)

def spawn_obstacle_using_current_lanes():
    """Crea un obstáculo usando las posiciones de carril actuales según track_distance."""
    lanes, _, _ = compute_lane_positions(track_distance)
    lane_x = random.choice(lanes)
    rect = pygame.Rect(lane_x, -CAR_H, CAR_W, CAR_H)
    obstacles.append(rect)

def draw_tree(rect):
    pygame.draw.rect(screen, BROWN, (rect.x + 6, rect.y + 30, 12, 30))
    pygame.draw.circle(screen, GREEN, (rect.x + 12, rect.y + 20), 22)

def draw_lamp(lamp):
    pygame.draw.rect(screen, LIGHT_GRAY, lamp)
    pygame.draw.circle(screen, YELLOW, (lamp.centerx, lamp.y), 6)
    # luz proyectada
    cone = pygame.Surface((160, 160), pygame.SRCALPHA)
    pygame.draw.polygon(cone, (255, 255, 200, 45), [(80, 0), (0, 160), (160, 160)])
    screen.blit(cone, (lamp.x - 40, lamp.y))

def draw_lamp_reflection(lamp):
    # elipse suave en carretera para reflejo
    refl_surface = pygame.Surface((140, 60), pygame.SRCALPHA)
    pygame.draw.ellipse(refl_surface, (255, 255, 200, 30), (0, 0, 140, 40))
    rx = lamp.centerx - 70
    ry = lamp.y + 30
    screen.blit(refl_surface, (rx, ry))

# -----------------------------
# FUNCIONES MENÚ / SELECCIÓN NIVEL
# -----------------------------
def selection_screen():
    """
    Muestra la pantalla de selección de nivel.
    El usuario presiona 1 (Fácil), 2 (Medio) o 3 (Extremo).
    """
    global level_params, level_name, laps_total, lap_distance
    while True:
        screen.fill(BLACK)
        center_text(screen, "Objetivo: NO CHOQUES!!", HEIGHT // 2 - 70, small_font, WHITE)
        center_text(screen, "NASCAR - Selección de nivel", HEIGHT // 2 - 120, title_font, YELLOW)
        center_text(screen, "Elige un nivel: 1 - FÁCIL | 2 - MEDIO | 3 - EXTREMO", HEIGHT // 2 - 35, menu_font, WHITE)
        center_text(screen, "Controles: ← → mover | Shift TURBO | Espacio reiniciar | 0 salir", HEIGHT // 2 + 50, hud_font, LIGHT_GRAY)
        center_text(screen, "Presiona 1/2/3 para seleccionar", HEIGHT // 2 + 70, small_font, ORANGE)
        center_text(screen, "El tutorial es facil: debes esquivar los obstaculos y ganarle al rival para ser campeon definitivo", HEIGHT // 2 + 19, hud_font, YELLOW)
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
                        "spawn_ms": 700,
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
    # simple screen asking to restart or quit
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
    """
    Animación corta: conductor con copa, confeti/champaña y trofeo.
    """
    global celebrating, celebration_start
    celebrating = True
    celebration_start = pygame.time.get_ticks()
    if cheer_sound:
        cheer_sound.play()

    anim_duration = 4000  # ms
    start = pygame.time.get_ticks()
    while pygame.time.get_ticks() - start < anim_duration:
        dt = clock.tick(60)
        screen.fill(BLACK)
        center_text(screen, "¡CAMPEÓN!", 70, title_font, GOLD)
        # dibujar trofeo central
        trophy_x = WIDTH // 2 - 40
        trophy_y = 140
        pygame.draw.rect(screen, GOLD, (trophy_x + 10, trophy_y + 70, 60, 20))  # base
        pygame.draw.rect(screen, GOLD, (trophy_x + 25, trophy_y + 20, 30, 50), border_radius=6)  # cuerpo
        pygame.draw.circle(screen, GOLD, (trophy_x + 40, trophy_y + 20), 14)  # copa
        # conductor con copa
        driver_x, driver_y = WIDTH // 2 - 140, 280
        pygame.draw.rect(screen, BLUE, (driver_x, driver_y, 50, 80), border_radius=6)
        pygame.draw.circle(screen, (255, 220, 170), (driver_x + 25, driver_y - 10), 18)  # cara
        # copa en mano (movimiento)
        t = (pygame.time.get_ticks() - start) / anim_duration
        cup_y = driver_y + int(-20 * math.sin(t * math.pi * 6))
        pygame.draw.rect(screen, LIGHT_GRAY, (driver_x + 50, cup_y, 12, 24))
        pygame.draw.circle(screen, YELLOW, (driver_x + 56, cup_y), 8)
        # champaña / confeti: salpicaduras aleatorias
        for i in range(15):
            px = WIDTH // 2 - 100 + random.randint(0, 200)
            py = 350 + random.randint(0, 140)
            if random.random() < 0.4:
                pygame.draw.circle(screen, (255, 255, 200), (px, py), random.randint(1, 4))
            else:
                pygame.draw.circle(screen, (random.randint(0,255), random.randint(0,255), random.randint(0,255)), (px, py), random.randint(1,3))
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

    # ajustar parámetros del nivel
    obstacle_speed = level_params["obstacle_speed"]
    rival_rate = level_params["rival_base"]
    visibility_max = level_params["visibility"]
    base_score = level_params["score_base"]
    rival_multiplier = level_params["rival_multiplier"]

    # ajustar curva según nivel
    curve_amplitude = level_params.get("curve_amp", curve_amplitude)

    # plantar algunos árboles / lámparas iniciales
    for i in range(8):
        side = random.choice(["L", "R"])
        x = random.randint(30, WIDTH // 2 - ROAD_WIDTH // 2 - 40) if side == "L" else random.randint(WIDTH // 2 + ROAD_WIDTH // 2 + 20, WIDTH - 60)
        trees.append(pygame.Rect(x, random.randint(-600, HEIGHT), 24, 64))
    for i in range(6):
        side = random.choice(["L", "R"])
        x = WIDTH // 2 - ROAD_WIDTH // 2 - 10 if side == "L" else WIDTH // 2 + ROAD_WIDTH // 2
        lamps.append(pygame.Rect(x, random.randint(-800, HEIGHT), 10, 100))

    # Meta variables
    finish_threshold = int(lap_distance * 0.9 / 20)  # threshold in player's "progress" count approx (keep old logic partially)
    running = True
    last_time = pygame.time.get_ticks()
    wheel_offset = 0

    while running:
        dt = clock.tick(60)
        now = pygame.time.get_ticks()

        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if e.type == SPAWN_OBSTACLE_EVENT:
                # spawn using lane positions based on current track_distance
                spawn_obstacle_using_current_lanes()
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_0:
                    pygame.quit(); sys.exit()

        keys = pygame.key.get_pressed()
        # turbo
        if keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]:
            current_speed = boost_speed
            if not is_boosting and turbo_sound:
                turbo_sound.play()
            is_boosting = True
        else:
            current_speed = player_speed
            is_boosting = False

        # movimiento lateral limitado al ancho de la carretera dinámica
        lanes_now, road_left_x, road_center_x = compute_lane_positions(track_distance)
        if keys[pygame.K_LEFT] and player_x > road_left_x + 6:
            player_x -= current_speed
        if keys[pygame.K_RIGHT] and player_x < road_left_x + ROAD_WIDTH - CAR_W - 6:
            player_x += current_speed

        # mover obstáculos
        for obs in obstacles[:]:
            obs.y += obstacle_speed
            # ajustar su x ligeramente para simular que siguen la curva (mantener en su carril realista)
            # no cambiamos obs.x aquí porque se spawnearon sobre la carretera; para más realismo podríamos desplazar según el centro
            if obs.colliderect(pygame.Rect(player_x, player_y, CAR_W, CAR_H)):
                # choque -> pantalla de game over
                show_game_over()
                return
            if obs.y > HEIGHT + 50:
                obstacles.remove(obs)
                # puntuación: turbo da más puntos y distancia
                gain = base_score + (base_score // 2 if is_boosting else 0)
                score += gain
                player_progress += 1
                # avanzar distancia: turbo da más distancia
                inc = 40 + (25 if is_boosting else 0)
                track_distance += inc
                praise_text = random.choice(praise_messages)
                praise_timer = now

        # rival avanza (más rápido según dificultad)
        rival_progress += rival_rate * (1.2 if is_boosting else 1.0) * 0.1

        # dificultad progresiva: eleva velocidad ligeramente (limitado)
        if int(player_progress) and int(player_progress) % 10 == 0:
            obstacle_speed = min(obstacle_speed + 0.004 * dt, level_params["obstacle_speed"] + 6)

        # gestionar vueltas: cuando track_distance supera lap_distance, completar vuelta
        if track_distance >= lap_distance:
            lap_count += 1
            track_distance -= lap_distance
            # bonificación al completar vuelta
            score += level_params.get("score_base", 15) * 3
            if lap_count >= laps_total:
                # mostrar meta y celebrar
                finish_visible = True
                finish_traveled = True
                # animación de celebración y luego pantalla final
                celebration_animation()
                show_game_over()
                return

        # mostrar meta si progresa suficiente (mantengo lógica de aparición en pantalla por player_progress también)
        if (player_progress >= int(lap_distance / 25)) and not finish_visible and lap_count >= (laps_total - 1):
            # aparecerá la puerta de meta; usamos finish_visible para iniciar la animación de descenso
            finish_line_y = -200
            finish_visible = True

        # Mover árboles y lámparas
        if random.random() < 0.06:
            side = random.choice(["L", "R"])
            x = random.randint(30, road_left_x - 40) if side == "L" else random.randint(road_left_x + ROAD_WIDTH + 20, WIDTH - 60)
            trees.append(pygame.Rect(x, -60, 24, 64))
        for t in trees[:]:
            t.y += obstacle_speed / 2
            if t.y > HEIGHT + 80:
                trees.remove(t)

        if random.random() < 0.03:
            side = random.choice(["L", "R"])
            x = road_left_x - 10 if side == "L" else road_left_x + ROAD_WIDTH
            lamps.append(pygame.Rect(x, -120, 10, 100))
        for l in lamps[:]:
            l.y += obstacle_speed / 2
            if l.y > HEIGHT + 140:
                lamps.remove(l)

        # animación de ruedas simple
        wheel_offset = (wheel_offset + 1) % 6

        # RENDER
        screen.fill(BLACK)
        # road con visibilidad según nivel y progreso (se oscurece con dificultad)
        current_vis = min(level_params["visibility"], level_params["visibility"] + int(player_progress * 0.2))
        draw_road(current_vis, track_distance)

        # dibujar reflejos de lámparas directamente sobre la carretera
        for lamp in lamps:
            pygame.draw.rect(screen, LIGHT_GRAY, lamp)
            pygame.draw.circle(screen, YELLOW, (lamp.centerx, lamp.y), 6)
            reflect = pygame.Surface((160, 80), pygame.SRCALPHA)
            alpha = max(10, 140 - lamp.y // 8) if lamp.y > -50 else 25
            pygame.draw.ellipse(reflect, (255, 255, 200, alpha), (0, 0, 160, 40))
            rx = lamp.centerx - 80
            ry = lamp.y + 20
            screen.blit(reflect, (rx, ry))

        # dibujar árboles
        for t in trees:
            draw_tree(t)

        # dibujar meta si visible (una bandera/puerta que baja desde arriba)
        if finish_visible and not finish_traveled:
            finish_line_y += 2  # baja lentamente
            # pintar una estructura de meta: dos postes y bandera a cuadros
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

        # dibujar obstáculos (no alteramos x; spawn usa lanes actuales)
        for obs in obstacles:
            # Si quieres, ajustar obs.x con pequeña curvatura visual:
            # obs.x += int((get_road_center_x(track_distance) - WIDTH//2) * 0.002)
            draw_obstacle(obs)

        # dibujar rival (posición relativa)
        rival_rel = (rival_progress - player_progress) * 6
        rival_screen_y = player_y - 200 + int(rival_rel)
        rival_x = get_road_center_x(track_distance) + ROAD_WIDTH // 2 - 120
        if -200 < rival_screen_y < HEIGHT:
            draw_car(rival_x, rival_screen_y, ORANGE)

        # dibujar jugador (con efecto turbo: llamas y luz)
        if is_boosting:
            for i in range(3):
                flame_color = random.choice([(255, 200, 40), (255, 120, 10), (255, 60, 0)])
                flame = pygame.Rect(player_x + 12, player_y + CAR_H + i * 6, 36, 10)
                pygame.draw.ellipse(screen, flame_color, flame)
            glow = pygame.Surface((CAR_W + 30, CAR_H + 30), pygame.SRCALPHA)
            pygame.draw.ellipse(glow, (100, 170, 255, 60), glow.get_rect())
            screen.blit(glow, (player_x - 15, player_y - 10))

        draw_car(player_x, player_y, BLUE, wheels_offset=wheel_offset)

        # HUD centrado arriba (texto pequeño y ordenado)
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
    selection_screen()  # selecciona level_params y setea el timer para spawn
    # asegurar timer
    pygame.time.set_timer(SPAWN_OBSTACLE_EVENT, level_params["spawn_ms"])

    # Entrar al bucle principal - se repetirá hasta que el usuario salga
    while True:
        main_loop()
        show_game_over()
        reset_game()
        selection_screen()
        pygame.time.set_timer(SPAWN_OBSTACLE_EVENT, level_params["spawn_ms"])
