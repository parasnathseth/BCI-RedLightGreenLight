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
ORANGE = (255, 140, 0)
GRAY = (200, 200, 200)
P1_ACCENT = (90, 150, 255)
P2_ACCENT = (255, 120, 120)


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


def draw_cloud(surface, x, y, scale=1.0):
	color = (245, 250, 255)
	r = int(22 * scale)
	c = [
		(x, y),
		(x + r * 2, y - int(r * 0.4)),
		(x + r * 4, y),
		(x + r * 1, y + int(r * 0.6)),
		(x + r * 3, y + int(r * 0.5)),
	]
	for cx, cy in c:
		pygame.draw.circle(surface, color, (int(cx), int(cy)), r)


def draw_finish_line(surface, y):
	# Checkered band
	band_h = 24
	cell = 16
	for i in range(0, WIDTH, cell):
		for j in range(0, band_h, cell):
			col = (0, 0, 0) if ((i // cell + j // cell) % 2 == 0) else (255, 255, 255)
			pygame.draw.rect(surface, col, (i, y - band_h // 2 + j, cell, cell))


def draw_player(surface, x, y, size, accent_color=None):
	# Draw a simple chicken sprite
	# Shadow
	shadow_rect = pygame.Rect(x + int(size * 0.1), y + int(size * 0.85), int(size * 0.8), int(size * 0.18))
	pygame.draw.ellipse(surface, (0, 0, 0, 60), shadow_rect)
	# Body (white oval)
	body_rect = pygame.Rect(x + int(size * 0.08), y + int(size * 0.28), int(size * 0.84), int(size * 0.62))
	pygame.draw.ellipse(surface, WHITE, body_rect)
	pygame.draw.ellipse(surface, (180, 180, 180), body_rect, width=2)
	# Wing (light gray)
	wing_rect = pygame.Rect(x + int(size * 0.32), y + int(size * 0.42), int(size * 0.42), int(size * 0.34))
	pygame.draw.ellipse(surface, GRAY, wing_rect)
	# Head (white circle)
	head_center = (x + int(size * 0.35), y + int(size * 0.25))
	head_radius = max(6, int(size * 0.18))
	pygame.draw.circle(surface, WHITE, head_center, head_radius)
	pygame.draw.circle(surface, (180, 180, 180), head_center, head_radius, width=2)
	# Eye
	eye_center = (head_center[0] + int(size * 0.04), head_center[1] - int(size * 0.04))
	pygame.draw.circle(surface, BLACK, eye_center, max(2, int(size * 0.03)))
	# Beak (triangle)
	beak_len = int(size * 0.18)
	beak_height = int(size * 0.10)
	beak_tip = (head_center[0] + head_radius + beak_len, head_center[1])
	beak_top = (head_center[0] + head_radius, head_center[1] - beak_height)
	beak_bottom = (head_center[0] + head_radius, head_center[1] + beak_height)
	pygame.draw.polygon(surface, ORANGE, [beak_top, beak_tip, beak_bottom])
	# Comb (red on top of head)
	comb_base_x = head_center[0] - int(head_radius * 0.6)
	comb_y = head_center[1] - head_radius - int(size * 0.02)
	comb_r = max(3, int(size * 0.05))
	pygame.draw.circle(surface, RED, (comb_base_x, comb_y), comb_r)
	pygame.draw.circle(surface, RED, (comb_base_x + comb_r, comb_y - int(comb_r * 0.6)), comb_r)
	pygame.draw.circle(surface, RED, (comb_base_x + comb_r * 2, comb_y), comb_r)
	# Legs (yellow)
	leg_y = y + int(size * 0.82)
	leg_x1 = x + int(size * 0.42)
	leg_x2 = x + int(size * 0.62)
	pygame.draw.line(surface, YELLOW, (leg_x1, leg_y - int(size * 0.10)), (leg_x1, leg_y), width=4)
	pygame.draw.line(surface, YELLOW, (leg_x2, leg_y - int(size * 0.10)), (leg_x2, leg_y), width=4)
	# Feet
	foot_w = int(size * 0.10)
	pygame.draw.line(surface, YELLOW, (leg_x1 - foot_w, leg_y), (leg_x1 + foot_w, leg_y), width=4)
	pygame.draw.line(surface, YELLOW, (leg_x2 - foot_w, leg_y), (leg_x2 + foot_w, leg_y), width=4)
	# Scarf/accent band to distinguish players
	if accent_color is not None:
		band_rect = pygame.Rect(
			head_center[0] - head_radius,
			head_center[1] + int(head_radius * 0.35),
			head_radius * 2,
			max(3, int(size * 0.08)),
		)
		pygame.draw.rect(surface, accent_color, band_rect, border_radius=6)


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

	# Player setup (two chickens)
	player_size = max(28, int(min(WIDTH, HEIGHT) * 0.06))
	# Place players side-by-side
	player1_x = WIDTH // 2 - int(player_size * 1.4)
	player2_x = WIDTH // 2 + int(player_size * 0.4)
	player1_y = float(HEIGHT - player_size - int(HEIGHT * 0.06))
	player2_y = float(HEIGHT - player_size - int(HEIGHT * 0.06))
	move_step = max(8, int(HEIGHT * 0.02))
	# Hold-to-move speed (pixels per second) derived from prior step size
	MOVE_SPEED = max(80, int(move_step * 10))
	# Penalty distance when moving on red (pixels)
	RED_PENALTY = max(move_step * 2, int(HEIGHT * 0.05))
	# Continuous penalty cadence when holding on red (milliseconds)
	PENALTY_PERIOD_MS = 280
	# Remember starting Y to clamp backward penalties
	start_y = float(HEIGHT - player_size - int(HEIGHT * 0.06))
	# Track W key edge for red penalty (apply once per press)
	w_was_down = False
	# Track UP key for player 2
	up_was_down = False
	# Penalty timers per player for holding during red
	penalty_timer_p1_ms = 0
	penalty_timer_p2_ms = 0

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
	prev_light_state = light_state

	running = True
	game_over = False
	win = False
	winner_label = ""
	elapsed_ms = 0

	def reset_game():
		nonlocal player1_y, player2_y, game_over, win, winner_label, elapsed_ms
		nonlocal state_index, light_state, light_timer_ms, light_interval_ms, prev_light_state
		nonlocal w_was_down, up_was_down, penalty_timer_p1_ms, penalty_timer_p2_ms
		player1_y = start_y
		player2_y = start_y
		game_over = False
		win = False
		winner_label = ""
		elapsed_ms = 0
		state_index = 0
		light_state = state_sequence[state_index]
		light_timer_ms = 0
		light_interval_ms = next_interval_for(light_state)
		prev_light_state = light_state
		w_was_down = False
		up_was_down = False
		penalty_timer_p1_ms = 0
		penalty_timer_p2_ms = 0

	while running:
		dt = clock.tick(FPS)

		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				running = False
			elif event.type == pygame.KEYDOWN:
				if event.key == pygame.K_ESCAPE:
					running = False
				elif event.key == pygame.K_r:
					reset_game()

		# Per-frame key handling for hold-to-move (two players)
		if not game_over:
			keys = pygame.key.get_pressed()
			# Player 1 - W
			w_down = keys[pygame.K_w]
			if w_down:
				if light_state in ("green", "yellow"):
					player1_y = max(finish_y, player1_y - MOVE_SPEED * (dt / 1000.0))
					penalty_timer_p1_ms = 0
				elif light_state == "red":
					penalty_timer_p1_ms += dt
					if penalty_timer_p1_ms >= PENALTY_PERIOD_MS:
						player1_y = min(player1_y + RED_PENALTY, start_y)
						penalty_timer_p1_ms = 0
			else:
				penalty_timer_p1_ms = 0
			# Player 2 - Up Arrow
			up_down = keys[pygame.K_UP]
			if up_down:
				if light_state in ("green", "yellow"):
					player2_y = max(finish_y, player2_y - MOVE_SPEED * (dt / 1000.0))
					penalty_timer_p2_ms = 0
				elif light_state == "red":
					penalty_timer_p2_ms += dt
					if penalty_timer_p2_ms >= PENALTY_PERIOD_MS:
						player2_y = min(player2_y + RED_PENALTY, start_y)
						penalty_timer_p2_ms = 0
			else:
				penalty_timer_p2_ms = 0
			w_was_down = w_down
			up_was_down = up_down

		# Win check: reached or crossed finish line (either player)
		if not game_over:
			if player1_y <= finish_y:
				game_over = True
				win = True
				winner_label = "Player 1"
			elif player2_y <= finish_y:
				game_over = True
				win = True
				winner_label = "Player 2"

		# Update timers and traffic light state only while game active
		if not game_over:
			elapsed_ms += dt
			light_timer_ms += dt
			if light_timer_ms >= light_interval_ms:
				state_index = (state_index + 1) % len(state_sequence)
				light_state = state_sequence[state_index]
				light_timer_ms = 0
				light_interval_ms = next_interval_for(light_state)
				# Immediate punishment when switching into red while holding
				if prev_light_state != "red" and light_state == "red":
					keys_now = pygame.key.get_pressed()
					if keys_now[pygame.K_w]:
						player1_y = min(player1_y + RED_PENALTY, start_y)
						penalty_timer_p1_ms = 0
					if keys_now[pygame.K_UP]:
						player2_y = min(player2_y + RED_PENALTY, start_y)
						penalty_timer_p2_ms = 0
			prev_light_state = light_state

		# Drawing
		# Background and scene
		draw_background(screen)
		# Visual improvements: clouds
		draw_cloud(screen, int(WIDTH * 0.15), int(HEIGHT * 0.16), 1.2)
		draw_cloud(screen, int(WIDTH * 0.65), int(HEIGHT * 0.12), 1.4)
		draw_cloud(screen, int(WIDTH * 0.42), int(HEIGHT * 0.20), 1.0)

		# Finish line and label
		draw_finish_line(screen, finish_y)
		screen.blit(font_small.render("Finish", True, BLACK), (WIDTH - 120, finish_y - 40))

		# Traffic light
		draw_traffic_light(screen, WIDTH // 2 - 30, int(HEIGHT * 0.02), light_state)

		# Players
		draw_player(screen, player1_x, int(player1_y), player_size, accent_color=P1_ACCENT)
		draw_player(screen, player2_x, int(player2_y), player_size, accent_color=P2_ACCENT)
		# Player labels
		screen.blit(font_small.render("P1", True, P1_ACCENT), (player1_x + player_size // 2 - 8, int(player1_y) - 24))
		screen.blit(font_small.render("P2", True, P2_ACCENT), (player2_x + player_size // 2 - 8, int(player2_y) - 24))

		# HUD
		if light_state == "green":
			state_text = "GREEN - P1: W  |  P2: Up Arrow"
			state_color = GREEN
		elif light_state == "red":
			state_text = "RED - Do NOT move"
			state_color = RED
		else:
			state_text = "YELLOW - You may move"
			state_color = YELLOW
		screen.blit(font_small.render(state_text, True, state_color), (10, HEIGHT - 34))
		# Controls hint
		controls_text = "R: Restart   ESC: Quit"
		screen.blit(font_small.render(controls_text, True, BLACK), (WIDTH - 280, HEIGHT - 34))

		# Timer display (MM:SS.t)
		mins = int(elapsed_ms // 60000)
		secs = int((elapsed_ms // 1000) % 60)
		tenths = int((elapsed_ms % 1000) // 100)
		time_text = f"Time: {mins:02}:{secs:02}.{tenths}"
		screen.blit(font_small.render(time_text, True, BLACK), (10, 10))

		if game_over:
			if win:
				show_center_text(screen, f"{winner_label} Wins!", GREEN, font_big)
				screen.blit(font_small.render("Press R to restart", True, BLACK), (10, 40))

		pygame.display.flip()

		# No auto-exit; wait for R or ESC

	pygame.quit()
	sys.exit(0)


if __name__ == "__main__":
	main()

