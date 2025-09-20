import sys
import random
import pygame
import math
import os


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

# Perspective scaling controls
SCALE_FAR = 0.35  # size at horizon
SCALE_NEAR = 1.35  # size near bottom
SCALE_GAMMA = 1.15  # >1 exaggerates shrinking near horizon

# Optional vector chicken data (loaded at runtime if available)
CHICKEN_VECTOR = None
# Optional PNG chicken sprite
CHICKEN_IMG = None
# Simple cache for scaled PNGs by integer size
_IMG_SCALE_CACHE = {}


def load_chicken_vector(path: str):
	if not os.path.isfile(path):
		return None
	try:
		import json
		with open(path, "r", encoding="utf-8") as f:
			data = json.load(f)
		if not isinstance(data, dict) or "shapes" not in data:
			return None
		units = float(data.get("units", 100))
		shapes = data.get("shapes", [])
		return {"units": units, "shapes": shapes}
	except Exception:
		return None


def draw_chicken_vector(surface, x, y, size, vector_data, accent_color=None, bob=0):
	units = vector_data.get("units", 100.0) or 100.0
	scale = size / units
	offx, offy = x, y - bob
	for shp in vector_data.get("shapes", []):
		typ = shp.get("type")
		role = shp.get("role")
		fill = tuple(shp.get("fill", [])) if shp.get("fill") else None
		stroke = tuple(shp.get("stroke", [])) if shp.get("stroke") else None
		if role == "accent" and accent_color is not None:
			if shp.get("fill") is not None:
				fill = accent_color
			if shp.get("stroke") is not None:
				stroke = accent_color
		width = int(shp.get("width", 1))
		if typ == "polygon":
			pts = [(int(offx + px * scale), int(offy + py * scale)) for px, py in shp.get("points", [])]
			if fill:
				pygame.draw.polygon(surface, fill, pts)
			if stroke:
				pygame.draw.polygon(surface, stroke, pts, width=max(1, width))
		elif typ == "polyline":
			pts = [(int(offx + px * scale), int(offy + py * scale)) for px, py in shp.get("points", [])]
			if stroke and len(pts) >= 2:
				pygame.draw.lines(surface, stroke, False, pts, width=max(1, width))
		elif typ == "circle":
			cx = int(offx + shp.get("cx", 0) * scale)
			cy = int(offy + shp.get("cy", 0) * scale)
			r = int(shp.get("r", 0) * scale)
			if fill:
				pygame.draw.circle(surface, fill, (cx, cy), r)
			if stroke and r > 0:
				pygame.draw.circle(surface, stroke, (cx, cy), r, width=max(1, width))
		elif typ == "ellipse":
			cx = offx + shp.get("cx", 0) * scale
			cy = offy + shp.get("cy", 0) * scale
			rx = shp.get("rx", 0) * scale
			ry = shp.get("ry", 0) * scale
			rect = pygame.Rect(int(cx - rx), int(cy - ry), int(rx * 2), int(ry * 2))
			if fill:
				pygame.draw.ellipse(surface, fill, rect)
			if stroke and rect.width > 0 and rect.height > 0:
				pygame.draw.ellipse(surface, stroke, rect, width=max(1, width))
		elif typ == "rect":
			rx = int(offx + shp.get("x", 0) * scale)
			ry = int(offy + shp.get("y", 0) * scale)
			rw = int(shp.get("w", 0) * scale)
			rh = int(shp.get("h", 0) * scale)
			radius = int(shp.get("radius", 0) * scale)
			if fill:
				pygame.draw.rect(surface, fill, (rx, ry, rw, rh), border_radius=radius)
			if stroke and rw > 0 and rh > 0:
				pygame.draw.rect(surface, stroke, (rx, ry, rw, rh), width=max(1, width), border_radius=radius)


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
	# flat ground removed; road drawn separately with perspective


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


def draw_horizon_fog(surface, horizon_y):
	# Soft vertical gradient starting at horizon fading downward
	fog_h = int(HEIGHT * 0.35)
	fog = pygame.Surface((WIDTH, fog_h), pygame.SRCALPHA)
	for i in range(fog_h):
		# Strongest near horizon (top of fog), fade out downward
		t = i / max(1, fog_h)
		alpha = int(90 * (1 - t))
		pygame.draw.rect(fog, (255, 255, 255, alpha), (0, i, WIDTH, 1))
	surface.blit(fog, (0, horizon_y))


def draw_road(surface, horizon_y, center_tilt_x, scroll):
	# Road as trapezoid converging towards horizon
	bottom_width = int(WIDTH * 0.8)
	top_width = int(WIDTH * 0.2)
	bottom_y = HEIGHT
	color_road = (40, 40, 48)
	# tilt the road slightly left by shifting center towards tilt param near horizon
	center_bottom = WIDTH // 2
	center_top = int(WIDTH * 0.5 + center_tilt_x)
	pts = [
		(center_top - top_width // 2, horizon_y),
		(center_top + top_width // 2, horizon_y),
		(center_bottom + bottom_width // 2, bottom_y),
		(center_bottom - bottom_width // 2, bottom_y),
	]
	pygame.draw.polygon(surface, color_road, pts)
	# dashed center line with perspective spacing and scroll
	line_color = (230, 230, 230)
	segments = 16
	for i in range(segments):
		v = (i / segments + scroll) % 1.0
		y0 = int(horizon_y + (HEIGHT - horizon_y) * v)
		y1 = int(horizon_y + (HEIGHT - horizon_y) * min(1.0, v + 0.05))
		scale = 1 - v
		cx = int(center_top * (1 - v) + center_bottom * v)
		w = max(2, int(6 * scale))
		pygame.draw.line(surface, line_color, (cx, y0), (cx, y1), width=w)


def draw_side_scenery(surface, horizon_y, road_tilt, scroll):
	# Grass bands + repeating tree rows that loop in a semi-random pattern
	bottom_width = int(WIDTH * 0.8)
	top_width = int(WIDTH * 0.2)
	center_bottom = WIDTH // 2
	center_top = int(WIDTH * 0.5 + road_tilt)
	segments = 24

	# Grass areas
	left_top = (center_top - top_width // 2, horizon_y)
	left_bottom = (center_bottom - bottom_width // 2, HEIGHT)
	right_top = (center_top + top_width // 2, horizon_y)
	right_bottom = (center_bottom + bottom_width // 2, HEIGHT)
	grass_left = (88, 155, 95)
	grass_right = (76, 135, 85)
	pygame.draw.polygon(surface, grass_left, [(0, horizon_y), left_top, left_bottom, (0, HEIGHT)])
	pygame.draw.polygon(surface, grass_right, [right_top, (WIDTH, horizon_y), (WIDTH, HEIGHT), right_bottom])

	# Simple tree drawing
	def draw_tree(x, y, sc):
		trunk_h = max(10, int(28 * sc))
		trunk_w = max(3, int(6 * sc))
		pygame.draw.rect(surface, (110, 80, 50), (x - trunk_w // 2, y - trunk_h, trunk_w, trunk_h))
		leaf_r = max(8, int(16 * sc))
		leaf_color = (50, 120, 60)
		pygame.draw.circle(surface, leaf_color, (x, y - trunk_h - int(leaf_r * 0.2)), leaf_r)
		pygame.draw.circle(surface, leaf_color, (x - leaf_r, y - trunk_h), int(leaf_r * 0.8))
		pygame.draw.circle(surface, leaf_color, (x + leaf_r, y - trunk_h), int(leaf_r * 0.8))

	# Deterministic pseudo-random helper stable per row/slot
	def prand(n: int, salt: int = 0) -> float:
		return (math.sin(n * 127.1 + salt * 311.7) * 43758.5453) % 1.0
	# Lateral fractions across the full grass widths (0..1)
	fracs = [0.12, 0.28, 0.45, 0.62, 0.78, 0.92]

	for i in range(segments):
		v = (i / segments + scroll) % 1.0
		y = int(horizon_y + (HEIGHT - horizon_y) * v)
		if y < horizon_y or y > HEIGHT:
			continue
		half_top = top_width * 0.5
		half_bottom = bottom_width * 0.5
		halfw = int(half_top * (1 - v) + half_bottom * v)
		cx = int(center_top * (1 - v) + center_bottom * v)
		left_edge = cx - halfw
		right_edge = cx + halfw
		margin = max(6, int(halfw * 0.10))
		sc = SCALE_FAR + (SCALE_NEAR - SCALE_FAR) * (v ** SCALE_GAMMA)

		# Row index for stable selection; do not depend on scroll for presence
		row_idx = i % 64
		# Build bitmasks for which lateral slots to use (ensure at least 2 per side)
		maskL = int(prand(row_idx, 101) * (1 << len(fracs)))
		maskR = int(prand(row_idx, 202) * (1 << len(fracs)))
		if maskL == 0:
			maskL = 0b001010  # pick a couple defaults
		if maskR == 0:
			maskR = 0b010100
		# Clamp grass widths
		left_pad = 16
		right_pad = 16
		left_min = left_pad
		left_max = max(left_min, left_edge - margin)
		right_min = min(WIDTH - right_pad, right_edge + margin)
		right_max = WIDTH - right_pad
		# Place trees across the grass using fractions and small fixed jitter per slot
		for k, f in enumerate(fracs):
			jL = int((prand(row_idx * 17 + k, 303) - 0.5) * 12)
			jR = int((prand(row_idx * 19 + k, 404) - 0.5) * 12)
			if (maskL >> k) & 1:
				gx = int(left_min + f * (left_max - left_min)) + jL
				draw_tree(gx, y, sc)
			if (maskR >> k) & 1:
				gx = int(right_min + f * (right_max - right_min)) + jR
				draw_tree(gx, y, sc)


def draw_player(surface, x, y, size, accent_color=None, anim_phase: float = 0.0, moving: bool = False):
	# Vertical bob only; prefer PNG sprite if present, else vector, else fallback drawing.
	bob = int(size * 0.04 * math.sin(anim_phase * math.tau)) if moving else 0
	if CHICKEN_IMG is not None and size > 0:
		# Draw shadow
		shadow_rect = pygame.Rect(x + int(size * 0.1), (y - bob) + int(size * 0.85), int(size * 0.8), int(size * 0.18))
		pygame.draw.ellipse(surface, (0, 0, 0, 60), shadow_rect)
		# Use cached scaled image
		img_key = int(size)
		img = _IMG_SCALE_CACHE.get(img_key)
		if img is None:
			try:
				img = pygame.transform.smoothscale(CHICKEN_IMG, (int(size), int(size)))
			except Exception:
				img = pygame.transform.scale(CHICKEN_IMG, (int(size), int(size)))
			_IMG_SCALE_CACHE[img_key] = img
			if len(_IMG_SCALE_CACHE) > 128:
				_IMG_SCALE_CACHE.clear()
		surface.blit(img, (x, y - bob))
		return
	if CHICKEN_VECTOR:
		shadow_rect = pygame.Rect(x + int(size * 0.1), (y - bob) + int(size * 0.85), int(size * 0.8), int(size * 0.18))
		pygame.draw.ellipse(surface, (0, 0, 0, 60), shadow_rect)
		draw_chicken_vector(surface, x, y, size, CHICKEN_VECTOR, accent_color=accent_color, bob=bob)
		return
	yb = y - bob
	shadow_rect = pygame.Rect(x + int(size * 0.1), yb + int(size * 0.85), int(size * 0.8), int(size * 0.18))
	pygame.draw.ellipse(surface, (0, 0, 0, 60), shadow_rect)
	body_rect = pygame.Rect(x + int(size * 0.08), yb + int(size * 0.28), int(size * 0.84), int(size * 0.62))
	pygame.draw.ellipse(surface, WHITE, body_rect)
	pygame.draw.ellipse(surface, (180, 180, 180), body_rect, width=2)
	head_center = (x + int(size * 0.35), yb + int(size * 0.25))
	head_radius = max(6, int(size * 0.18))
	pygame.draw.circle(surface, WHITE, head_center, head_radius)
	pygame.draw.circle(surface, (180, 180, 180), head_center, head_radius, width=2)
	eye_center = (head_center[0] + int(size * 0.04), head_center[1] - int(size * 0.04))
	pygame.draw.circle(surface, BLACK, eye_center, max(2, int(size * 0.03)))
	beak_len = int(size * 0.18)
	beak_height = int(size * 0.10)
	beak_tip = (head_center[0] + head_radius + beak_len, head_center[1])
	beak_top = (head_center[0] + head_radius, head_center[1] - beak_height)
	beak_bottom = (head_center[0] + head_radius, head_center[1] + beak_height)
	pygame.draw.polygon(surface, ORANGE, [beak_top, beak_tip, beak_bottom])
	comb_base_x = head_center[0] - int(head_radius * 0.6)
	comb_y = head_center[1] - head_radius - int(size * 0.02)
	comb_r = max(3, int(size * 0.05))
	pygame.draw.circle(surface, RED, (comb_base_x, comb_y), comb_r)
	pygame.draw.circle(surface, RED, (comb_base_x + comb_r, comb_y - int(comb_r * 0.6)), comb_r)
	pygame.draw.circle(surface, RED, (comb_base_x + comb_r * 2, comb_y), comb_r)
	leg_y = yb + int(size * 0.82)
	leg_x1 = x + int(size * 0.42)
	leg_x2 = x + int(size * 0.62)
	pygame.draw.line(surface, YELLOW, (leg_x1, leg_y - int(size * 0.10)), (leg_x1, leg_y), width=4)
	pygame.draw.line(surface, YELLOW, (leg_x2, leg_y - int(size * 0.10)), (leg_x2, leg_y), width=4)
	foot_w = int(size * 0.10)
	pygame.draw.line(surface, YELLOW, (leg_x1 - foot_w, leg_y), (leg_x1 + foot_w, leg_y), width=4)
	pygame.draw.line(surface, YELLOW, (leg_x2 - foot_w, leg_y), (leg_x2 + foot_w, leg_y), width=4)
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

	# Optional vector sprite loading
	global CHICKEN_VECTOR, CHICKEN_IMG
	vec_path = os.path.join(os.path.dirname(__file__), "chicken_vector.json")
	CHICKEN_VECTOR = load_chicken_vector(vec_path)
	# Optional PNG sprite loading
	png_path = os.path.join(os.path.dirname(__file__), "chicken.png")
	if os.path.isfile(png_path):
		try:
			CHICKEN_IMG = pygame.image.load(png_path).convert_alpha()
		except Exception:
			CHICKEN_IMG = None

	# World setup: two chickens in world space (y increases downward)
	player_size = max(28, int(min(WIDTH, HEIGHT) * 0.06))
	# Horizon and camera
	horizon_y = int(HEIGHT * 0.35)
	road_tilt = -int(WIDTH * 0.08)  # negative = tilt towards left
	# World positions (x around road center in world space)
	world_center_x = 0.0
	player1_world_x = -player_size * 0.8
	player2_world_x = player_size * 0.8
	start_world_y = 0.0
	player1_world_y = start_world_y
	player2_world_y = start_world_y
	# Camera follows leader, keeping them lower on screen to see road ahead
	camera_y = 0.0
	camera_y_prev = camera_y
	camera_anchor_screen_y = int(HEIGHT * 0.62)
	move_step = max(8, int(HEIGHT * 0.02))
	# Reduced movement speed for calmer pacing
	MOVE_SPEED = max(60, int(move_step * 5))
	# Reduced penalty distance when moving on red (pixels)
	RED_PENALTY = max(int(move_step * 1.2), int(HEIGHT * 0.03))
	# Slightly slower penalty cadence when holding on red (milliseconds)
	PENALTY_PERIOD_MS = 360

	# Animation accumulators driven by camera movement
	road_scroll = 0.0
	cloud_off_x = 0.0
	cloud_off_y = 0.0
	scenery_scroll = 0.0
	# Remember starting world Y to clamp backward penalties
	start_y = start_world_y
	# Track W key edge for red penalty (apply once per press)
	w_was_down = False
	# Track UP key for player 2
	up_was_down = False
	# No periodic penalty timers; red causes smooth reverse

	# No finish line; trailing-off-screen decides winner

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
	# current speed multipliers for HUD bars
	current_p1_mult = 0.0
	current_p2_mult = 0.0

	def reset_game():
		nonlocal player1_world_y, player2_world_y, camera_y, game_over, win, winner_label, elapsed_ms
		nonlocal state_index, light_state, light_timer_ms, light_interval_ms, prev_light_state
		nonlocal w_was_down, up_was_down
		nonlocal current_p1_mult, current_p2_mult
		nonlocal camera_y_prev, road_scroll, cloud_off_x, cloud_off_y
		player1_world_y = start_y
		player2_world_y = start_y
		camera_y = 0.0
		camera_y_prev = camera_y
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
		current_p1_mult = 0.0
		current_p2_mult = 0.0
		road_scroll = 0.0
		scenery_scroll = 0.0
		cloud_off_x = 0.0
		cloud_off_y = 0.0

	while running:
		dt = clock.tick(FPS)

		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				running = False
			elif event.type == pygame.KEYDOWN:
				if event.key == pygame.K_ESCAPE:
					running = False
				elif event.key == pygame.K_x:
					reset_game()

		# Per-frame key handling with per-key speed tiers (two players)
		if not game_over:
			keys = pygame.key.get_pressed()
			# Player 1 - keys QWERTY map to increasing speeds (reduced)
			p1_keys = [pygame.K_q, pygame.K_w, pygame.K_e, pygame.K_r, pygame.K_t, pygame.K_y]
			p1_multipliers = [0.3, 0.6, 0.85, 1.1, 1.35, 1.6]
			p1_level = -1
			for idx, k in enumerate(p1_keys):
				if keys[k]:
					p1_level = max(p1_level, idx)
			p1_mult = p1_multipliers[p1_level] if p1_level >= 0 else 0.0
			current_p1_mult = p1_mult
			if p1_mult > 0.0:
				if light_state in ("green", "yellow"):
					player1_world_y -= (MOVE_SPEED * p1_mult) * (dt / 1000.0)
				elif light_state == "red":
					# Smooth reverse movement during red
					player1_world_y = min(player1_world_y + (MOVE_SPEED * p1_mult) * (dt / 1000.0), start_y)
			else:
				pass

			# Player 2 - keys ASDFGH map to increasing speeds (reduced)
			p2_keys = [pygame.K_a, pygame.K_s, pygame.K_d, pygame.K_f, pygame.K_g, pygame.K_h]
			p2_multipliers = [0.3, 0.6, 0.85, 1.1, 1.35, 1.6]
			p2_level = -1
			for idx, k in enumerate(p2_keys):
				if keys[k]:
					p2_level = max(p2_level, idx)
			p2_mult = p2_multipliers[p2_level] if p2_level >= 0 else 0.0
			current_p2_mult = p2_mult
			if p2_mult > 0.0:
				if light_state in ("green", "yellow"):
					player2_world_y -= (MOVE_SPEED * p2_mult) * (dt / 1000.0)
				elif light_state == "red":
					# Smooth reverse movement during red
					player2_world_y = min(player2_world_y + (MOVE_SPEED * p2_mult) * (dt / 1000.0), start_y)
			else:
				pass

			w_was_down = any(keys[k] for k in p1_keys)
			up_was_down = any(keys[k] for k in p2_keys)

			# Camera follows the leader (smaller world_y is further ahead)
			leader_world_y = min(player1_world_y, player2_world_y)
			camera_y = leader_world_y - (camera_anchor_screen_y - horizon_y)
			# Drive animation offsets by camera movement delta
			cam_dy = camera_y - camera_y_prev
			# Road dashed center scrolls forward with negative cam movement and backward with positive
			road_scroll = (road_scroll + (-cam_dy) * 0.004) % 1.0
			scenery_scroll = (scenery_scroll + (-cam_dy) * 0.003) % 1.0
			# Clouds parallax drifts slightly with camera; reverse on backward movement
			cloud_off_x += (-cam_dy) * 0.01
			cloud_off_y += (-cam_dy) * 0.02
			camera_y_prev = camera_y

			# Win condition: trailing off-screen bottom
			sy1 = horizon_y + (player1_world_y - camera_y)
			sy2 = horizon_y + (player2_world_y - camera_y)
			off_margin = 40
			if sy1 > HEIGHT + off_margin:
				game_over = True
				win = True
				winner_label = "Player 2"
			elif sy2 > HEIGHT + off_margin:
				game_over = True
				win = True
				winner_label = "Player 1"

		# No top finish line; win handled by trailing-off-screen above

		# Update timers and traffic light state only while game active
		if not game_over:
			elapsed_ms += dt
			light_timer_ms += dt
			if light_timer_ms >= light_interval_ms:
				state_index = (state_index + 1) % len(state_sequence)
				light_state = state_sequence[state_index]
				light_timer_ms = 0
				light_interval_ms = next_interval_for(light_state)
				# No immediate jump on red; smooth reverse covers it
			prev_light_state = light_state

		# Drawing
		# Background and sky
		draw_background(screen)
		# Clouds with faint parallax driven by camera delta accumulators
		cloud_dx = int(cloud_off_x)
		cloud_dy = int(cloud_off_y)
		draw_cloud(screen, int(WIDTH * 0.15) + cloud_dx, int(HEIGHT * 0.16) + int(cloud_dy * 0.6), 1.2)
		draw_cloud(screen, int(WIDTH * 0.65) - int(cloud_dx * 0.5), int(HEIGHT * 0.12) + int(cloud_dy * 0.4), 1.4)
		draw_cloud(screen, int(WIDTH * 0.42) + int(cloud_dx * 0.3), int(HEIGHT * 0.20) + int(cloud_dy * 0.8), 1.0)
		# Side scenery under sky (before road), driven by scenery_scroll
		draw_side_scenery(screen, horizon_y, road_tilt, scenery_scroll)
		# Road with perspective and tilt; dashed center uses accumulated scroll
		draw_road(screen, horizon_y, road_tilt, road_scroll)
		# Horizon fog overlay (after road/background, before players)
		draw_horizon_fog(screen, horizon_y)
		# Traffic light
		draw_traffic_light(screen, WIDTH // 2 - 30, int(HEIGHT * 0.02), light_state)
		# Convert world to screen and draw players with perspective scale
		def world_to_screen(wx, wy):
			# Depth from horizon in screen space
			sy = horizon_y + (wy - camera_y)
			# Center shift for tilt: more shift near horizon
			v = 0.0 if HEIGHT == horizon_y else max(0.0, min(1.0, (sy - horizon_y) / (HEIGHT - horizon_y)))
			cx = int((WIDTH * 0.5 + road_tilt * (1 - v)))
			# scale from small at horizon to large at bottom
			scale = SCALE_FAR + (SCALE_NEAR - SCALE_FAR) * (v ** SCALE_GAMMA)
			sx = int(cx + wx * v)
			return sx, int(sy), scale, v
		# Compute screen positions and scales
		p1_sx, p1_sy, p1_scale, p1_v = world_to_screen(player1_world_x, player1_world_y)
		p2_sx, p2_sy, p2_scale, p2_v = world_to_screen(player2_world_x, player2_world_y)
		# Slight angled travel: bias P1 left, P2 right nearer the camera
		p1_sx += int(-WIDTH * 0.02 * p1_v)
		p2_sx += int(WIDTH * 0.02 * p2_v)
		# Draw labels BEHIND chickens so they never block
		screen.blit(font_small.render("P1", True, P1_ACCENT), (p1_sx - 10, p1_sy - int(player_size * p1_scale)))
		screen.blit(font_small.render("P2", True, P2_ACCENT), (p2_sx - 10, p2_sy - int(player_size * p2_scale)))
		# Movement animation based on speed
		p1_moving = (current_p1_mult > 0 and light_state in ("green", "yellow"))
		p2_moving = (current_p2_mult > 0 and light_state in ("green", "yellow"))
		# Depth-sorted drawing: draw farther (smaller v) first
		players = [
			(p1_v, p1_sx, p1_sy, p1_scale, P1_ACCENT, (elapsed_ms / 1000.0) * (2.0 + 2.0 * current_p1_mult), p1_moving),
			(p2_v, p2_sx, p2_sy, p2_scale, P2_ACCENT, (elapsed_ms / 1000.0) * (2.0 + 2.0 * current_p2_mult), p2_moving),
		]
		players.sort(key=lambda t: t[0])
		for v, sx, sy, sc, accent, phase, moving in players:
			draw_player(
				screen,
				sx - int(player_size * sc * 0.5),
				sy - int(player_size * sc * 0.8),
				int(player_size * sc),
				accent_color=accent,
				anim_phase=phase,
				moving=moving,
			)

		# HUD
		if light_state == "green":
			state_text = "GREEN - P1: QWERTY  |  P2: ASDFGH"
			state_color = GREEN
		elif light_state == "red":
			state_text = "RED - Do NOT move"
			state_color = RED
		else:
			state_text = "YELLOW - You may move"
			state_color = YELLOW
		screen.blit(font_small.render(state_text, True, state_color), (10, HEIGHT - 34))
		# Controls hint
		controls_text = "X: Restart   ESC: Quit"
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
				screen.blit(font_small.render("Press X to restart", True, BLACK), (10, 40))

		# Speed bars under timer
		bar_w = int(WIDTH * 0.25)
		bar_h = 10
		bar_x = 10
		p1_bar_y = 40
		p2_bar_y = 60
		max_mult = 1.6
		# Background bars
		pygame.draw.rect(screen, (220, 220, 220), (bar_x, p1_bar_y, bar_w, bar_h), border_radius=4)
		pygame.draw.rect(screen, (220, 220, 220), (bar_x, p2_bar_y, bar_w, bar_h), border_radius=4)
		# Filled portions
		p1_fill = int(bar_w * min(1.0, (current_p1_mult if 'current_p1_mult' in locals() else 0.0) / max_mult))
		p2_fill = int(bar_w * min(1.0, (current_p2_mult if 'current_p2_mult' in locals() else 0.0) / max_mult))
		pygame.draw.rect(screen, P1_ACCENT, (bar_x, p1_bar_y, p1_fill, bar_h), border_radius=4)
		pygame.draw.rect(screen, P2_ACCENT, (bar_x, p2_bar_y, p2_fill, bar_h), border_radius=4)
		# Labels
		screen.blit(font_small.render(f"P1 Speed", True, P1_ACCENT), (bar_x + bar_w + 10, p1_bar_y - 6))
		screen.blit(font_small.render(f"P2 Speed", True, P2_ACCENT), (bar_x + bar_w + 10, p2_bar_y - 6))

		pygame.display.flip()

		# No auto-exit; wait for R or ESC

	pygame.quit()
	sys.exit(0)


if __name__ == "__main__":
	main()

