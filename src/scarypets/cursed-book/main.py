import pygame
import pygame_gui
import random
import math
import threading
import sys
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
from mock_controller import launch_controller

pygame.init()

WIDTH, HEIGHT = 240, 320
window_surface = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption('Graveyard Buddy')

def load_sprite_sheet(path, frame_count):
  sheet = pygame.image.load(path).convert_alpha()
  sheet_width, sheet_height = sheet.get_size()
  frame_width = sheet_width // frame_count
  frames = []
  for i in range(frame_count):
    frame = sheet.subsurface((i * frame_width, 0, frame_width, sheet_height)).copy()
    frames.append(frame)
  return frames

SPRITE_FRAME_COUNT = 2
SPRITE_ANIM_FRAME_DURATION = 0.5
SPRITE_SCALE = 1.5
STILL_SPEED_THRESHOLD = 3.0
STILL_CHANCE = 0.2
SCARE_ANIM_FRAME_DURATION = 0.3
SCARE_LOOPS = 3
SCARE_CHANCE = 0.05
scare_check_timer = 0.0
scare_loops_remaining = 0

EMOTE_FRAME_DURATION = 0.5
EMOTE_LOOPS = 2
EMOTE_CHANCE = 0.03
emote_check_timer = 0.0
emote_loops_remaining = 0
emoting = False
current_emote = None

sprite_path = os.path.join(BASE_DIR, "..", "..", "..", "assets", "cursed-book", "sprite-idle1.png")
move_left_path = os.path.join(BASE_DIR, "..", "..", "..", "assets", "cursed-book", "move-left.png")
move_right_path = os.path.join(BASE_DIR, "..", "..", "..", "assets", "cursed-book", "move-right.png")
scare_path = os.path.join(BASE_DIR, "..", "..", "..", "assets", "cursed-book", "scare.png")

def scale_frames(frames, scale):
  scaled = []
  for frame in frames:
    w, h = frame.get_size()
    scaled.append(pygame.transform.smoothscale(frame, (int(w * scale), int(h * scale))))
  return scaled


sprite_frames = scale_frames(load_sprite_sheet(sprite_path, SPRITE_FRAME_COUNT), SPRITE_SCALE)
move_left_frames = scale_frames(load_sprite_sheet(move_left_path, SPRITE_FRAME_COUNT), SPRITE_SCALE)
move_right_frames = scale_frames(load_sprite_sheet(move_right_path, SPRITE_FRAME_COUNT), SPRITE_SCALE)
scare_frames = scale_frames(load_sprite_sheet(scare_path, SPRITE_FRAME_COUNT), SPRITE_SCALE)

ANIM_FRAMES = {
    'idle': sprite_frames,
    'left': move_left_frames,
    'right': move_right_frames,
    'scare': scare_frames,
}

EMOTES = [
  "pumpkin",
  "shy",
  "heart",
  "candle",
]

for emote_name in EMOTES:
  emote_path = os.path.join(BASE_DIR, "..", "..", "..", "assets", "cursed-book", f"{emote_name}.png")
  ANIM_FRAMES[emote_name] = scale_frames(load_sprite_sheet(emote_path, SPRITE_FRAME_COUNT), SPRITE_SCALE)

background_path = os.path.join(BASE_DIR, "..", "..", "..", "assets", "cursed-book", "temp-background.png")
background = pygame.image.load(background_path).convert()
background = pygame.transform.smoothscale(background, (WIDTH, HEIGHT))

ui_manager = pygame_gui.UIManager((WIDTH, HEIGHT))

clock = pygame.time.Clock()
is_running = True

BG_COLOR = (2, 7, 7)


def pick_target_speed():
  if random.random() < STILL_CHANCE:
    return 0.0
  return random.uniform(5, 40)


def generate_sprites(count, width, height):
  sprites = []
  for _ in range(count):
    radius = random.randint(int(8 * SPRITE_SCALE), int(14 * SPRITE_SCALE))
    x = random.randint(radius, width - radius)
    y = random.randint(radius, height - radius)
    sprites.append({
        'x': x, 'y': y,
        'radius': radius,
        'angle': random.uniform(0, math.tau),
        'speed': random.uniform(5, 20),
        'target_angle': random.uniform(0, math.tau),
        'target_speed': pick_target_speed(),
        'turn_timer': random.uniform(1, 3),
        'anim_state': 'idle',
        'anim_frame': 0,
        'anim_timer': 0.0,
    })
  return sprites


def draw_sprite(surface, sprite, anim_frames):
  frames = anim_frames[sprite['anim_state']]
  frame = frames[sprite['anim_frame']]
  rect = frame.get_rect(center=(sprite['x'], sprite['y']))
  surface.blit(frame, rect)


def update_anim_state(sprite):
  if sprite['speed'] < STILL_SPEED_THRESHOLD:
    new_state = 'idle'
  else:
    hx = math.cos(sprite['angle'])
    vy = math.sin(sprite['angle'])
    if abs(hx) > abs(vy):
      new_state = 'right' if hx > 0 else 'left'
    else:
      new_state = 'idle'

  if new_state != sprite['anim_state']:
    sprite['anim_state'] = new_state
    sprite['anim_frame'] = 0
    sprite['anim_timer'] = 0.0


def move_sprites(sprites, time_delta, width, height):
  for sprite in sprites:
    sprite['turn_timer'] -= time_delta
    if sprite['turn_timer'] <= 0:
      sprite['target_angle'] = sprite['angle'] + random.uniform(-math.pi / 2, math.pi / 2)
      sprite['target_speed'] = pick_target_speed()
      sprite['turn_timer'] = random.uniform(1, 4)

    angle_diff = (sprite['target_angle'] - sprite['angle'] + math.pi) % math.tau - math.pi
    sprite['angle'] += angle_diff * min(1, time_delta * 1.5)

    sprite['speed'] += (sprite['target_speed'] - sprite['speed']) * min(1, time_delta * 1.0)

    dx = math.cos(sprite['angle']) * sprite['speed'] * time_delta
    dy = math.sin(sprite['angle']) * sprite['speed'] * time_delta
    sprite['x'] += dx
    sprite['y'] += dy

    update_anim_state(sprite)

    sprite['anim_timer'] += time_delta
    if sprite['anim_timer'] >= SPRITE_ANIM_FRAME_DURATION:
      sprite['anim_timer'] = 0
      sprite['anim_frame'] = (sprite['anim_frame'] + 1) % SPRITE_FRAME_COUNT

    margin = sprite['radius']
    if sprite['x'] < margin:
      sprite['x'] = margin
      sprite['target_angle'] = 0.0
    elif sprite['x'] > width - margin:
      sprite['x'] = width - margin
      sprite['target_angle'] = math.pi
    if sprite['y'] < margin:
      sprite['y'] = margin
      sprite['target_angle'] = math.pi / 2
    elif sprite['y'] > height - margin:
      sprite['y'] = height - margin
      sprite['target_angle'] = -math.pi / 2


def advance_scare_animation(sprites, time_delta):
  global scaring, scare_loops_remaining
  loop_completed = False
  for sprite in sprites:
    sprite['anim_timer'] += time_delta
    if sprite['anim_timer'] >= SCARE_ANIM_FRAME_DURATION:
      sprite['anim_timer'] = 0
      sprite['anim_frame'] = (sprite['anim_frame'] + 1) % SPRITE_FRAME_COUNT
      if sprite['anim_frame'] == 0:
        loop_completed = True

  if loop_completed:
    scare_loops_remaining -= 1
    if scare_loops_remaining <= 0:
      scaring = False
      for sprite in sprites:
        sprite['anim_state'] = 'idle'
        sprite['anim_frame'] = 0
        sprite['anim_timer'] = 0.0


def advance_emote_animation(sprites, time_delta):
  global emoting, emote_loops_remaining
  loop_completed = False
  for sprite in sprites:
    sprite['anim_timer'] += time_delta
    if sprite['anim_timer'] >= EMOTE_FRAME_DURATION:
      sprite['anim_timer'] = 0
      sprite['anim_frame'] = (sprite['anim_frame'] + 1) % SPRITE_FRAME_COUNT
      if sprite['anim_frame'] == 0:
        loop_completed = True

  if loop_completed:
    emote_loops_remaining -= 1
    if emote_loops_remaining <= 0:
      emoting = False
      for sprite in sprites:
        sprite['anim_state'] = 'idle'
        sprite['anim_frame'] = 0
        sprite['anim_timer'] = 0.0


def button1_pressed():
  pygame.event.post(pygame.event.Event(pygame.QUIT))


def trigger_scare():
  global scaring, scare_loops_remaining
  if scaring or emoting:
    return
  scaring = True
  scare_loops_remaining = SCARE_LOOPS
  for sprite in sprites:
    sprite['anim_state'] = 'scare'
    sprite['anim_frame'] = 0
    sprite['anim_timer'] = 0.0


def button2_pressed():
  print("Boo!")
  trigger_scare()


def button3_pressed():
  sprites.extend(generate_sprites(1, WIDTH, HEIGHT))
  if len(sprites) > 15:
    sprites.pop(0)
  print("Added 1 Sprite")


def button4_pressed():
  if len(sprites) >= 1:
    sprites.pop(0)
  print("Removed 1 Sprite")


def trigger_emote(name=None):
  global emoting, current_emote, emote_loops_remaining
  if scaring or emoting:
    return
  current_emote = name or random.choice(EMOTES)
  emoting = True
  emote_loops_remaining = EMOTE_LOOPS
  for sprite in sprites:
    sprite['anim_state'] = current_emote
    sprite['anim_frame'] = 0
    sprite['anim_timer'] = 0.0


def button5_pressed():
  print("Hitting an Emote!")
  trigger_emote()


controller_thread = threading.Thread(
    target=launch_controller,
    args=(button1_pressed, button2_pressed, button3_pressed, button4_pressed, button5_pressed),
    daemon=True,
)
controller_thread.start()


sprites = generate_sprites(1, WIDTH, HEIGHT)
scaring = False
elapsed_time = 0

while is_running:
  time_delta = clock.tick(60) / 1000
  elapsed_time += time_delta

  for event in pygame.event.get():
    if event.type == pygame.QUIT:
      is_running = False
    ui_manager.process_events(event)

  ui_manager.update(time_delta)

  if scaring:
    advance_scare_animation(sprites, time_delta)
  elif emoting:
    advance_emote_animation(sprites, time_delta)
  else:
    scare_check_timer += time_delta
    if scare_check_timer >= 1.0:
      scare_check_timer = 0.0
      if random.random() < SCARE_CHANCE:
        trigger_scare()

    if not scaring:
      emote_check_timer += time_delta
      if emote_check_timer >= 1.0:
        emote_check_timer = 0.0
        if random.random() < EMOTE_CHANCE:
          trigger_emote()

    if not scaring and not emoting:
      move_sprites(sprites, time_delta, WIDTH, HEIGHT)

  # window_surface.fill(BG_COLOR)
  window_surface.blit(background, (0, 0))

  for sprite in sprites:
    draw_sprite(window_surface, sprite, ANIM_FRAMES)

  ui_manager.draw_ui(window_surface)

  pygame.display.update()

pygame.quit()