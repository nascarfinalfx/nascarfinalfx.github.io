#hola, este es la version 1.0 de NASCAR
import pygame
import random
import sys

pygame.init()

# Pantalla
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Carrera Nascar Simple")

clock = pygame.time.Clock()

# Colores
WHITE = (255, 255, 255)
GRAY = (100, 100, 100)
RED = (200, 0, 0)
BLUE = (0, 120, 255)
BLACK = (0, 0, 0)
YELLOW = (255, 255, 0)

# Jugador
player_w, player_h = 60, 100
player_x = WIDTH // 2 - player_w // 2
player_y = HEIGHT - player_h - 20
player_speed = 7
boost_speed = 12

# Obstáculos
obstacles = []
obstacle_w, obstacle_h = 60, 100
obstacle_speed = 10
SPAWN = pygame.USEREVENT + 1
pygame.time.set_timer(SPAWN, 1000)

# Puntaje
score = 0
font = pygame.font.SysFont("Arial", 30)

# -------------------------------
def draw_road():
    pygame.draw.rect(screen, GRAY, (200, 0, 400, HEIGHT))
    for y in range(0, HEIGHT, 60):
        pygame.draw.rect(screen, WHITE, (WIDTH // 2 - 5, y, 10, 40))

# -------------------------------
running = True
while running:
    clock.tick(60)
    screen.fill(BLACK)
    draw_road()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        if event.type == SPAWN:
            lane = random.choice([220, 320, 420, 520])
            obstacles.append(pygame.Rect(lane, -obstacle_h, obstacle_w, obstacle_h))

    keys = pygame.key.get_pressed()
    speed = boost_speed if (keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]) else player_speed
    if keys[pygame.K_LEFT] and player_x > 210:
        player_x -= speed
    if keys[pygame.K_RIGHT] and player_x < WIDTH - player_w - 210:
        player_x += speed

    # Dibujar jugador
    pygame.draw.rect(screen, BLUE, (player_x, player_y, player_w, player_h))

    # Obstáculos
    for obs in obstacles[:]:
        obs.y += obstacle_speed
        pygame.draw.rect(screen, RED, obs)

        if obs.colliderect(pygame.Rect(player_x, player_y, player_w, player_h)):
            text = font.render("¡COLISIÓN! GAME OVER", True, RED)
            screen.blit(text, (WIDTH // 2 - text.get_width() // 2, HEIGHT // 2))
            pygame.display.flip()
            pygame.time.wait(2000)
            pygame.quit()
            sys.exit()

        if obs.y > HEIGHT:
            obstacles.remove(obs)
            score += 2 if speed == boost_speed else 1

    # Mostrar puntaje
    text = font.render(f"Puntos: {score}", True, YELLOW)
    screen.blit(text, (WIDTH // 2 - text.get_width() // 2, 20))

    pygame.display.flip()
