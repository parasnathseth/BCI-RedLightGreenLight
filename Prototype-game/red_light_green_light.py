import sys
import random
import pygame


WIDTH, HEIGHT = 640, 480
FPS = 60


WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (220, 30, 30)
GREEN = (30, 200, 60)
DK_RED = (120, 0, 0)
DK_GREEN = (0, 80, 0)
YELLOW = (255, 215, 0)
DK_YELLOW = (120, 100, 0)
BLUE = (40, 120, 255)


def draw_traffic_light(surface, x, y, state):
	# Pole
	pygame.draw.rect(surface, (60, 60, 60), (x + 24, y + 160, 12, 120), border_radius=6)
	# Housing
	pygame.draw.rect(surface, (30, 30, 30), (x, y, 60, 160), border_radius=12)
	pygame.draw.rect(surface, (80, 80, 80), (x, y, 60, 160), width=2, border_radius=12)
	cx = x + 30
	# Lights
	colors = {
		"red": RED if state == "red" else DK_RED,
		"yellow": YELLOW if state == "yellow" else DK_YELLOW,
		"green": GREEN if state == "green" else DK_GREEN,
	}
	positions = {"red": y + 35, "yellow": y + 80, "green": y + 125}
	# Draw circles
	pygame.draw.circle(surface, colors["red"], (cx, positions["red"]), 22)
	pygame.draw.circle(surface, colors["yellow"], (cx, positions["yellow"]), 22)
	pygame.draw.circle(surface, colors["green"], (cx, positions["green"]), 22)

	# Glow for active light
	active = state
	if active in ("red", "yellow", "green"):
		glow_color = {
			"red": (255, 80, 80, 70),
			"yellow": (255, 240, 100, 70),
			"green": (120, 255, 140, 70),
		}[active]
		glow = pygame.Surface((140, 140), pygame.SRCALPHA)
		pygame.draw.circle(glow, glow_color, (70, 70), 60)
		gy = positions[active] - 70
		surface.blit(glow, (cx - 70, gy), special_flags=pygame.BLEND_ADD)


def draw_background(surface):
	# Sky gradient blocks
	top = (180, 210, 255)
	mid = (120, 170, 240)
	bot = (90, 140, 220)
	h1 = int(HEIGHT * 0.35)
	h2 = int(HEIGHT * 0.5)
	pygame.draw.rect(surface, top, (0, 0, WIDTH, h1))
	pygame.draw.rect(surface, mid, (0, h1, WIDTH, h2 - h1))
	# Ground/Road
	road_y = h2
	pygame.draw.rect(surface, (40, 40, 48), (0, road_y, WIDTH, HEIGHT - road_y))
	# Lane markings
	stripe_w = 80
	stripe_h = 8
	gap = 40
	y = road_y + (HEIGHT - road_y) // 2
	for x in range(0, WIDTH, stripe_w + gap):
		pygame.draw.rect(surface, (230, 230, 230), (x, y, stripe_w, stripe_h), border_radius=4)


def draw_finish_line(surface, y):
	# Checkered band
	band_h = 24
	cell = 16
	for i in range(0, WIDTH, cell):
		for j in range(0, band_h, cell):
			col = (0, 0, 0) if ((i // cell + j // cell) % 2 == 0) else (255, 255, 255)
			pygame.draw.rect(surface, col, (i, y - band_h // 2 + j, cell, cell))


def draw_player(surface, x, y, size):
	# Shadow
	shadow = pygame.Rect(x + 6, y + size - 10, size - 12, 12)
	pygame.draw.ellipse(surface, (0, 0, 0, 60), shadow)
	# Body
	pygame.draw.rect(surface, BLUE, (x, y, size, size), border_radius=10)
	# Outline
	pygame.draw.rect(surface, (20, 60, 140), (x, y, size, size), width=3, border_radius=10)


def show_center_text(screen, text, color, font):
	msg = font.render(text, True, color)
	rect = msg.get_rect(center=(WIDTH // 2, HEIGHT // 2))
	screen.blit(msg, rect)


def main():
	pygame.init()
	# Fullscreen setup
	screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
	info = pygame.display.Info()
	global WIDTH, HEIGHT
	WIDTH, HEIGHT = info.current_w, info.current_h
	pygame.display.set_caption("Red Light Green Light (Fullscreen)")
	clock = pygame.time.Clock()

	font_big = pygame.font.SysFont(None, 56)
	font_small = pygame.font.SysFont(None, 28)

	# Player setup (simple rectangle)
	player_size = max(28, int(min(WIDTH, HEIGHT) * 0.03))
	player_x = WIDTH // 2 - player_size // 2
	player_y = HEIGHT - player_size - int(HEIGHT * 0.06)
	move_step = max(8, int(HEIGHT * 0.02))

	# Finish line near the top
	finish_y = max(60, int(HEIGHT * 0.12))

	# Traffic light state machine with yellow buffer
	state_sequence = ["green", "yellow", "red", "yellow"]
	state_index = 0
	light_state = state_sequence[state_index]
	light_timer_ms = 0
	YELLOW_MS = 800
	def next_interval_for(state: str) -> int:
		return YELLOW_MS if state == "yellow" else random.randint(1500, 3000)

	light_interval_ms = next_interval_for(light_state)

	running = True
	game_over = False
	win = False

	while running:
		dt = clock.tick(FPS)

		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				running = False
			elif event.type == pygame.KEYDOWN and not game_over:
				if event.key == pygame.K_ESCAPE:
					running = False
				elif event.key == pygame.K_w:
					if light_state in ("green", "yellow"):
						player_y = max(finish_y, player_y - move_step)
					elif light_state == "red":
						game_over = True
						win = False

		# Win check: reached or crossed finish line
		if not game_over and player_y <= finish_y:
			game_over = True
			win = True

		# Update traffic light timer/state only while game active
		if not game_over:
			light_timer_ms += dt
			if light_timer_ms >= light_interval_ms:
				state_index = (state_index + 1) % len(state_sequence)
				light_state = state_sequence[state_index]
				light_timer_ms = 0
				light_interval_ms = next_interval_for(light_state)

		# Drawing
		# Background and scene
		draw_background(screen)

		# Finish line and label
		draw_finish_line(screen, finish_y)
		screen.blit(font_small.render("Finish", True, BLACK), (WIDTH - 120, finish_y - 40))

		# Traffic light
		draw_traffic_light(screen, WIDTH // 2 - 30, int(HEIGHT * 0.02), light_state)

		# Player
		draw_player(screen, player_x, player_y, player_size)

		# HUD
		if light_state == "green":
			state_text = "GREEN - Press W to move"
			state_color = GREEN
		elif light_state == "red":
			state_text = "RED - Do NOT press W"
			state_color = RED
		else:
			state_text = "YELLOW - You may move"
			state_color = YELLOW
		screen.blit(font_small.render(state_text, True, state_color), (10, HEIGHT - 34))

		if game_over:
			if win:
				show_center_text(screen, "You Win!", GREEN, font_big)
			else:
				show_center_text(screen, "You moved on RED!", RED, font_big)
				screen.blit(font_small.render("Press ESC to quit", True, BLACK), (10, 10))

		pygame.display.flip()

		# If game over on red press, pause briefly then exit loop
		if game_over and not win:
			pygame.time.delay(1600)
			running = False

		# If win, pause briefly then exit loop
		if game_over and win:
			pygame.time.delay(1600)
			running = False

	pygame.quit()
	sys.exit(0)


if __name__ == "__main__":
	main()

