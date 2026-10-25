import pygame
import math
import time
import random
import numpy as np
import os
from collections import deque

render = True

def flatten_buffer(buf):
    flat_buf = []
    for item in buf:
        flat_buf.extend(item)
    return flat_buf

if render:
    pygame.init()

    screen = pygame.display.set_mode((1000, 600))
    pygame.display.set_caption("Tank Game")

def can_see(x1, y1, x2, y2):
    p1 = (int(x1), int(y1))
    p2 = (int(x2), int(y2))

    for wall in walls:
        if wall.clipline(p1, p2):
            return 0 

    return 1 


def reset_game():
    global tank_x, tank_y, angle, tank2_x, tank2_y, angle2, bullets, tank_bullets, tank2_bullets, last_shot_time, last_shot_time2, spawn_protect, spawn_protect2
    global frame_count, action1, action2
    global map, tile_size, walls
    global size, collison_size, speed, steering, steering2
    global bullets, bullet_speed,shoot_cooldown, random_spawn
    frame_count = 0
    action1 = 0
    action2 = 0

    tank_x = 500
    tank2_x = 0
    tank_y = 300
    tank2_y = 0
    size = 15
    collison_size = 8
    speed = 2
    angle = random.uniform(0,360)
    angle2 = random.uniform(0,360)
    steering = 1
    steering2 = 1
    map = [
    "####################",
    "#..................#",
    "#..........M.......#",
    "#..................#",
    "#......##..##......#",
    "#...#.......#......#",
    "#......#.......#...#",
    "#......##..##......#",
    "#..................#",
    "#..................#",
    "#..................#",
    "####################"
    ]
    tile_size = 50
    walls = []
    valid_tiles = []
    valid_tiles2 = []
    valid_tiles3 = []
    min_dist = 200
    max_dist = 600

    for row_index, row in enumerate(map):
        for col_index, tile in enumerate(row):
            if tile == "#":
                wall_rect = pygame.Rect(col_index * tile_size, row_index * tile_size, tile_size, tile_size)
                walls.append(wall_rect)
            elif tile == "S":
                tank_x = col_index * tile_size + tile_size / 2
                tank_y = row_index * tile_size + tile_size / 2
            elif tile == "M":
                tank2_x = col_index * tile_size + tile_size / 2
                tank2_y = row_index * tile_size + tile_size / 2
            elif tile == ".":
                x = col_index * tile_size + tile_size / 2
                y = row_index * tile_size + tile_size / 2
                valid_tiles.append((x, y))
            elif tile == "C":
                x = col_index * tile_size + tile_size / 2
                y = row_index * tile_size + tile_size / 2
                valid_tiles2.append((x, y))
            elif tile == "N":
                x = col_index * tile_size + tile_size / 2
                y = row_index * tile_size + tile_size / 2
                valid_tiles3.append((x, y))

    random_spawn = False
    set_random_spawn = False

    if random.random() > 0:
        random_spawn = True
        while True:
            tank_x, tank_y = random.choice(valid_tiles)
            tank2_x, tank2_y = random.choice(valid_tiles)

            dist = math.sqrt((tank_x - tank2_x)**2 + (tank_y - tank2_y)**2)

            if min_dist < dist < max_dist:
                if can_see(tank_x, tank_y, tank2_x, tank2_y) == 0:
                    break

    if set_random_spawn == True:
        tank_x, tank_y = random.choice(valid_tiles2)
        tank2_x, tank2_y = random.choice(valid_tiles3)

    bullets = []
    tank_bullets = 0
    tank2_bullets = 0

    bullet_speed = 3

    last_shot_time = 0
    last_shot_time2 = 0
    shoot_cooldown = 6

    spawn_protect = False
    spawn_protect2 = False

def get_lidar_data(x, y, tank_angle, num_rays=32, max_dist=300):
    distances = []
    for i in range(num_rays):
        ray_angle = math.radians(tank_angle + (i * (360 / num_rays)))

        dx = math.cos(ray_angle)
        dy = math.sin(ray_angle)
        
        min_dist = max_dist
        
        x2, y2 = x + dx * max_dist, y + dy * max_dist
        
        for wall in walls:
            if abs(wall.centerx - x) > max_dist + wall.width and abs(wall.centery - y) > max_dist + wall.height:
                continue

            clip = wall.clipline(x, y, x2, y2)
            
            if clip:
                p1 = clip[0]
                d = math.sqrt((p1[0] - x)**2 + (p1[1] - y)**2)
                if d < min_dist:
                    min_dist = d
                    
        distances.append(min_dist / max_dist)
        
    return distances

def get_target_angle_from_lidar(default_target_angle, angle, ld):
    if can_see(tank_x, tank_y, tank2_x, tank2_y) == 1:
        target_angle = default_target_angle
    else:
        best_ray = 0
        min_angle_diff = 360
        for i in range(len(ld)):
            diff = abs(((angle + (i * (360 / len(ld)))) % 360) - default_target_angle)
            if diff < min_angle_diff:
                min_angle_diff = diff
                best_ray = i
        if ld[best_ray] > 0.5:
            target_angle = (angle + (best_ray * (360 / len(ld)))) % 360
        else:
            left_ray = (best_ray - 1) % len(ld)
            right_ray = (best_ray + 1) % len(ld)

            if ld[left_ray] > ld[right_ray]:
                target_angle = (angle + (left_ray * (360 / len(ld)))) % 360
            else:
                target_angle = (angle + (right_ray * (360 / len(ld)))) % 360
    return target_angle

def get_state1():
    state1 = []
    global ld1
    global ld2
    ld2 = get_lidar_data(tank2_x, tank2_y, angle2)
    ld1 = get_lidar_data(tank_x, tank_y, angle)
    state1.append(math.sin(math.radians(angle)))
    state1.append(math.cos(math.radians(angle)))
    state1.append(math.sin(math.radians(angle2)))
    state1.append(math.cos(math.radians(angle2)))
    dxa = tank2_x - tank_x
    dya = tank2_y - tank_y
    default_target_angle = (math.degrees(math.atan2(dya, dxa)) + 360) % 360
    target_angle = get_target_angle_from_lidar(default_target_angle, angle, ld1)
    angle_diff = abs((angle - target_angle + 180) % 360 - 180)
    state1.append(math.sin(math.radians(angle_diff)))
    state1.append(math.cos(math.radians(angle_diff)))
    state1.extend(ld1)
    state1.extend(ld2)
    state1.append(can_see(tank_x, tank_y, tank2_x, tank2_y))
    adx = (tank2_x - tank_x) / 1000
    ady = (tank2_y - tank_y) / 600
    state1.append(adx)
    state1.append(ady)
    dist = math.sqrt((tank2_x - tank_x)**2 + (tank2_y - tank_y)**2)
    state1.append(dist / 1000)
    for i in range(10):
        if i < len(bullets):
            state1.append(math.sin(math.radians(bullets[i]['bullet_angle'])))
            state1.append(math.cos(math.radians(bullets[i]['bullet_angle'])))
            rel_bx = (bullets[i]['bullet_x'] - tank_x) / 1000
            rel_by = (bullets[i]['bullet_y'] - tank_y) / 600
            
            state1.append(rel_bx)
            state1.append(rel_by)
        else:
            state1.extend([0,0,0,0])
    return state1

def get_state2():
    state2 = []
    state2.append(math.sin(math.radians(angle2)))
    state2.append(math.cos(math.radians(angle2)))
    state2.append(math.sin(math.radians(angle)))
    state2.append(math.cos(math.radians(angle)))
    dxb = tank_x - tank2_x
    dyb = tank_y - tank2_y
    default_target_angle2 = (math.degrees(math.atan2(dyb, dxb)) + 360) % 360
    target_angle2 = get_target_angle_from_lidar(default_target_angle2, angle2, ld2)
    angle_diff2 = abs((angle2 - target_angle2 + 180) % 360 - 180)
    state2.append(math.sin(math.radians(angle_diff2)))
    state2.append(math.cos(math.radians(angle_diff2)))
    state2.extend(ld2)
    state2.extend(ld1)
    state2.append(can_see(tank2_x, tank2_y, tank_x, tank_y))
    adx = (tank_x - tank2_x) / 1000
    ady = (tank_y - tank2_y) / 600
    state2.append(adx)
    state2.append(ady)
    dist = math.sqrt((tank2_x - tank_x)**2 + (tank2_y - tank_y)**2)
    state2.append(dist / 1000)
    for i in range(10):
        if i < len(bullets):
            state2.append(math.sin(math.radians(bullets[i]['bullet_angle'])))
            state2.append(math.cos(math.radians(bullets[i]['bullet_angle'])))
            rel_bx = (bullets[i]['bullet_x'] - tank2_x) / 1000
            rel_by = (bullets[i]['bullet_y'] - tank2_y) / 600
            
            state2.append(rel_bx)
            state2.append(rel_by)
        else:
            state2.extend([0,0,0,0])
    return state2 

input_size = 456
h1_size = 256
h2_size = 256
output_size = 5

try:
    w1 = np.load("w1.npy")
    w2 = np.load("w2.npy")
    w3 = np.load("w3.npy")

    b1 = np.load("b1.npy")
    b2 = np.load("b2.npy")
    b3 = np.load("b3.npy")

    epsilon = np.load("epsilon.npy")

    print("Loaded trained weights")

except:
    print("Starting with random weights")

    w1 = np.random.randn(input_size, h1_size)*math.sqrt(2/input_size)
    w2 = np.random.randn(h1_size, h2_size)*math.sqrt(2/h1_size)
    w3 = np.random.randn(h2_size, output_size)*math.sqrt(2/h2_size)

    b1 = np.zeros(h1_size)
    b2 = np.zeros(h2_size)
    b3 = np.zeros(output_size)

    epsilon = 1

try:
    w1a = np.load("w1a.npy")
    w2a = np.load("w2a.npy")
    w3a = np.load("w3a.npy")

    b1a = np.load("b1a.npy")
    b2a = np.load("b2a.npy")
    b3a = np.load("b3a.npy")
    epsilon2 = np.load("epsilon2.npy")

except:
    w1a = np.random.randn(input_size, h1_size)*math.sqrt(2/input_size)
    w2a = np.random.randn(h1_size, h2_size)*math.sqrt(2/h1_size)
    w3a = np.random.randn(h2_size, output_size)*math.sqrt(2/h2_size)

    b1a = np.zeros(h1_size)
    b2a = np.zeros(h2_size)
    b3a = np.zeros(output_size)
    epsilon2 = 1

def relu(x):
    return np.maximum(0, x)

def forward(state):

    x = np.array(state)
    
    h1 = relu(x @ w1 + b1)
    h2 = relu(h1 @ w2 + b2)
    output = h2 @ w3 + b3
    return output

def forward2(state):

    x = np.array(state)
    
    h1 = relu(x @ w1a + b1a)
    h2 = relu(h1 @ w2a + b2a)
    output = h2 @ w3a + b3a
    return output

target_w1 = w1.copy()
target_w2 = w2.copy()
target_w3 = w3.copy()

target_b1 = b1.copy()
target_b2 = b2.copy()
target_b3 = b3.copy()

def target_forward(state):
    x = np.array(state)
    h1 = relu(x @ target_w1 + target_b1)
    h2 = relu(h1 @ target_w2 + target_b2)
    output = h2 @ target_w3 + target_b3
    return output

target_w1a = w1a.copy()
target_w2a = w2a.copy()
target_w3a = w3a.copy()

target_b1a = b1a.copy()
target_b2a = b2a.copy()
target_b3a = b3a.copy()

def target_forward2(state):
    x = np.array(state)
    h1 = relu(x @ target_w1a + target_b1a)
    h2 = relu(h1 @ target_w2a + target_b2a)
    output = h2 @ target_w3a + target_b3a
    return output

replay_buffer = deque(maxlen=50000)
replay_buffer2 = deque(maxlen=50000)

Stalemates = 0
Wins_1 = 0
Wins_2 = 0
Suicides_1 = 0
Suicides_2 = 0

try:
    for episode in range(100000):
        reset_game()
        states = []
        actions = []
        rewards = []
        next_states = []
        episode_running = True
        winner = 0
        reward1 = 0
        reward2 = 0
        epsilon = max(0.05, epsilon * 0.9998)
        epsilon2 = max(0.05, epsilon2 * 0.9998)

        raw1 = get_state1()
        raw2 = get_state2()

        buf1 = deque([raw1, raw1, raw1, raw1], maxlen=4)
        buf2 = deque([raw2, raw2, raw2, raw2], maxlen=4)

        while episode_running:
            reward1 = -0.05
            reward2 = -0.05
            frame_count += 1
            collision = False
            collision2 = False
            if frame_count - last_shot_time > shoot_cooldown/2:
                spawn_protect = False
            if frame_count - last_shot_time2 > shoot_cooldown/2:
                spawn_protect2 = False

            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RSHIFT and pygame.time.get_ticks() - last_shot_time > shoot_cooldown:
                        bullet = {'bullet_x': tank_x + math.cos(math.radians(angle)) * 8,
                                    'bullet_y': tank_y + math.sin(math.radians(angle)) * 8,
                                    'bullet_angle': angle,
                                    'bullet_owner': 1}
                        if tank_bullets >= 5:
                            for i, b in enumerate(bullets):
                                if b['bullet_owner'] == 1:
                                    bullets.pop(i)
                                    tank_bullets -= 1
                                    break
                        bullets.append(bullet)
                        tank_bullets += 1
                        last_shot_time = pygame.time.get_ticks()
                        spawn_protect = True
                    if event.key == pygame.K_q and pygame.time.get_ticks() - last_shot_time2 > shoot_cooldown:
                        bullet = {'bullet_x': tank2_x + math.cos(math.radians(angle2)) * 8,
                                    'bullet_y': tank2_y + math.sin(math.radians(angle2)) * 8,
                                    'bullet_angle': angle2,
                                    'bullet_owner': 2}
                        if tank2_bullets >= 5:
                            for i, b in enumerate(bullets):
                                if b['bullet_owner'] == 2:
                                    bullets.pop(i)
                                    tank2_bullets -= 1
                                    break
                        bullets.append(bullet)
                        tank2_bullets += 1
                        last_shot_time2 = pygame.time.get_ticks()
                        spawn_protect2 = True
            
                if event.type == pygame.QUIT:
                    running = False
                
            keys = pygame.key.get_pressed()

            stacked_state1 = flatten_buffer(buf1)
            stacked_state2 = flatten_buffer(buf2)
            
            q_values1 = forward(stacked_state1)
            q_values2 = forward2(stacked_state2)

            if random.random() < epsilon:
                action1 = random.randint(0,4)
            else:
                action1 = np.argmax(q_values1)

            if random.random() < epsilon2:
                action2 = random.randint(0,4)
            else:
                action2 = np.argmax(q_values2)

            if render:
                screen.fill((255, 255, 255))

                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        pygame.quit()
                        exit()

            dx = 0
            dy = 0
            dx2 = 0
            dy2 = 0

            dxa = tank2_x - tank_x
            dya = tank2_y - tank_y
            default_target_angle = (math.degrees(math.atan2(dya, dxa)) + 360) % 360
            target_angle = get_target_angle_from_lidar(default_target_angle, angle, ld1)
            angle_diff = abs((angle - target_angle + 180) % 360 - 180)
            
            dxb = tank_x - tank2_x
            dyb = tank_y - tank2_y
            default_target_angle2 = (math.degrees(math.atan2(dyb, dxb)) + 360) % 360
            target_angle2 = get_target_angle_from_lidar(default_target_angle2, angle2, ld2)
            angle_diff2 = abs((angle2 - target_angle2 + 180) % 360 - 180)

            if action1 == 0:
                dx = speed * math.cos(math.radians(angle))
                dy = speed * math.sin(math.radians(angle))
                steering = 1
            elif action1 == 1: 
                dx = -speed * math.cos(math.radians(angle))
                dy = -speed * math.sin(math.radians(angle))
                steering = -1
            else:
                steering = 1

            if action1 == 2:
                    angle -= 5*steering

            if action1 == 3:
                    angle += 5*steering
            
            if keys[pygame.K_w]:
                dx2 = speed * math.cos(math.radians(angle2))
                dy2 = speed * math.sin(math.radians(angle2))
                steering2 = 1
            elif keys[pygame.K_s]: 
                dx2 = -speed * math.cos(math.radians(angle2))
                dy2 = -speed * math.sin(math.radians(angle2))
                steering2 = -1
            else:
                steering2 = 1
            
            if keys[pygame.K_a]:
                angle2 -= 5*steering2
            
            if keys[pygame.K_d]:
                angle2 += 5*steering2

            next_x = tank_x + dx
            next_y = tank_y + dy

            next_x2 = tank2_x + dx2
            next_y2 = tank2_y + dy2

            for wall in walls:
                closest_x = max(wall.left, min(next_x, wall.right))
                closest_y = max(wall.top, min(next_y, wall.bottom))
            
                dx_u = next_x - closest_x
                dy_u = next_y - closest_y

                if (dx_u * dx_u + dy_u * dy_u) < (collison_size * collison_size):
                    collision = True
                    next_x -= dx * 2
                    next_y -= dy * 2
                    reward1 -= 2
                    break

            for wall in walls:
                closest_x2 = max(wall.left, min(next_x2, wall.right))
                closest_y2 = max(wall.top, min(next_y2, wall.bottom))
            
                dx_u2 = next_x2 - closest_x2
                dy_u2 = next_y2 - closest_y2

                if (dx_u2 * dx_u2 + dy_u2 * dy_u2) < (collison_size * collison_size):
                    collision2 = True
                    next_x2 -= dx2 * 2
                    next_y2 -= dy2 * 2
                    reward2 -= 2
                    break
            
            prev_dist = math.sqrt((tank2_x - tank_x)**2 + (tank2_y - tank_y)**2)
            prev_dist2 = math.sqrt((tank_x - tank2_x)**2 + (tank_y - tank2_y)**2)

            if not collision:
                tank_x = next_x
            else:
                dx = 0

            if not collision:
                tank_y = next_y
            else:
                dy = 0

            if not collision2:
                tank2_x = next_x2
            else:
                dx2 = 0
            
            if not collision2:
                tank2_y = next_y2
            else:
                dy2 = 0

            dist = math.sqrt((tank2_x - tank_x)**2 + (tank2_y - tank_y)**2)
            dist_change = prev_dist - dist
            if not collision:
                reward1 += dist_change * 0.1

            dist2 = math.sqrt((tank_x - tank2_x)**2 + (tank_y - tank2_y)**2)
            dist_change2 = prev_dist2 - dist2

            if not collision2:
                reward2 += dist_change2 * 0.1

            if not collision and can_see(tank_x, tank_y, tank2_x, tank2_y) == 1:
                reward1 += dist_change * 0.1

            if not collision2 and can_see(tank2_x, tank2_y, tank_x, tank_y) == 1:
                reward2 += dist_change2 * 0.1

            if can_see(tank_x, tank_y, tank2_x, tank2_y) == 1:
                reward1 += 0.05
            
            if can_see(tank2_x, tank2_y, tank_x, tank_y) == 1:
                reward2 += 0.05

            dxa = tank2_x - tank_x
            dya = tank2_y - tank_y
            default_target_angle = (math.degrees(math.atan2(dya, dxa)) + 360) % 360
            target_angle = get_target_angle_from_lidar(default_target_angle, angle, ld1)
            angle_diffa = abs((angle - target_angle + 180) % 360 - 180)
            
            dxb = tank_x - tank2_x
            dyb = tank_y - tank2_y
            default_target_angle2 = (math.degrees(math.atan2(dyb, dxb)) + 360) % 360
            target_angle2 = get_target_angle_from_lidar(default_target_angle2, angle2, ld2)
            angle_diff2a = abs((angle2 - target_angle2 + 180) % 360 - 180)

            reward1 += math.cos(math.radians(angle_diffa)) * 0.1

            reward2 += math.cos(math.radians(angle_diff2a)) * 0.1

            movement1 = abs(dx) + abs(dy)
            
            if movement1 < 0.5:
                reward1 -= 0.1

            movement2 = abs(dx2) + abs(dy2)
            
            if movement2 < 0.5:
                reward2 -= 0.1

            mdl1 = min(ld1)
            mdl2 = min(ld2)

            if mdl1 < 0.1:
                reward1 -= 0.1

            if mdl2 < 0.1:
                reward2 -= 0.1

            if action1 == 4 and frame_count - last_shot_time > shoot_cooldown:
                reward1 -= 1
                if can_see(tank_x, tank_y, tank2_x, tank2_y) == 1:
                    reward1 += math.cos(math.radians(angle_diffa)) * 0.2
                else:
                    reward1 -= 1
                bullet = {'bullet_x': tank_x + math.cos(math.radians(angle)) * 8,
                            'bullet_y': tank_y + math.sin(math.radians(angle)) * 8,
                            'bullet_angle': angle,
                            'bullet_owner': 1}
                if tank_bullets >= 5:
                    for i, b in enumerate(bullets):
                        if b['bullet_owner'] == 1:
                            bullets.pop(i)
                            reward1 -= 1
                            tank_bullets -= 1
                            break
                bullets.append(bullet)
                tank_bullets += 1
                last_shot_time = frame_count
                spawn_protect = True

            for bullet in bullets:

                prev_x = bullet['bullet_x']
                prev_y = bullet['bullet_y']

                bullet['bullet_x'] += bullet_speed * math.cos(math.radians(bullet['bullet_angle']))
                bullet['bullet_y'] += bullet_speed * math.sin(math.radians(bullet['bullet_angle']))
                if render:
                    pygame.draw.circle(screen, (255, 0, 0), (int(bullet['bullet_x']), int(bullet['bullet_y'])), 5)
                
                rounding_error = 0.01

                if not spawn_protect:
                    if bullet['bullet_x'] < tank_x + collison_size and bullet['bullet_x'] > tank_x - collison_size and bullet['bullet_y'] < tank_y + collison_size and bullet['bullet_y'] > tank_y - collison_size:
                        if bullet['bullet_owner'] == 1:
                            reward1 -= 60
                            Suicides_1 += 1
                        elif bullet['bullet_owner'] == 2:
                            reward1 -= 40
                            reward2 += 160
                            Wins_2 += 1
                        episode_running = False

                if not spawn_protect2:
                    if bullet['bullet_x'] < tank2_x + collison_size and bullet['bullet_x'] > tank2_x - collison_size and bullet['bullet_y'] < tank2_y + collison_size and bullet['bullet_y'] > tank2_y - collison_size:
                        if bullet['bullet_owner'] == 2:
                            reward2 -= 60
                            Suicides_2 += 1
                        elif bullet['bullet_owner'] == 1:
                            reward1 += 160
                            reward2 -= 40
                            Wins_1 += 1
                        episode_running = False
                        
                for wall in walls:
                    if wall.collidepoint(bullet['bullet_x'], bullet['bullet_y']) or wall.collidepoint(prev_x, prev_y):
                        if prev_x <= (wall.left + rounding_error) or prev_x >= (wall.right - rounding_error):
                            bullet['bullet_angle'] = 180 - bullet['bullet_angle']
                        
                        if prev_y <= (wall.top + rounding_error) or prev_y >= (wall.bottom - rounding_error):
                            bullet['bullet_angle'] = -bullet['bullet_angle']
                        bullet['bullet_x'] += bullet_speed * math.cos(math.radians(bullet['bullet_angle']))
                        bullet['bullet_y'] += bullet_speed * math.sin(math.radians(bullet['bullet_angle']))
                        break
            
            if render:
                pygame.draw.polygon(screen, (0, 128, 0), [(tank_x + math.cos(math.radians(angle)) * size, tank_y + math.sin(math.radians(angle)) * size), 
                                                        (tank_x + math.cos(math.radians(angle) + 2.5) * size, tank_y + math.sin(math.radians(angle) + 2.5) * size), 
                                                        (tank_x + math.cos(math.radians(angle) - 2.5) * size, tank_y + math.sin(math.radians(angle) - 2.5) * size)])
                pygame.draw.polygon(screen, (0, 0, 128), [(tank2_x + math.cos(math.radians(angle2)) * size, tank2_y + math.sin(math.radians(angle2)) * size), 
                                                        (tank2_x + math.cos(math.radians(angle2) + 2.5) * size, tank2_y + math.sin(math.radians(angle2) + 2.5) * size), 
                                                        (tank2_x + math.cos(math.radians(angle2) - 2.5) * size, tank2_y + math.sin(math.radians(angle2) - 2.5) * size)])
                for wall in walls:
                    pygame.draw.rect(screen, (0, 0, 0), wall)
                pygame.time.Clock().tick(120)
                pygame.display.flip()
            
            if frame_count > 600:
                episode_running = False
                reward1 -= 0
                reward2 -= 0
                Stalemates += 1
            
            next_raw1 = get_state1()
            next_raw2 = get_state2()

            buf1.append(next_raw1)
            buf2.append(next_raw2)

            stacked_next_state1 = flatten_buffer(buf1)
            stacked_next_state2 = flatten_buffer(buf2)

            replay_buffer.append((stacked_state1, action1, reward1, stacked_next_state1, not episode_running))
            replay_buffer.append((stacked_state2, action2, reward2, stacked_next_state2, not episode_running))

        if len(replay_buffer) > 1000:
                
            for _ in range(max(10, frame_count//10)):    
                
                batch = random.sample(replay_buffer, 64)

                dw1 = np.zeros_like(w1)
                dw2 = np.zeros_like(w2)
                dw3 = np.zeros_like(w3)

                db1 = np.zeros_like(b1)
                db2 = np.zeros_like(b2)
                db3 = np.zeros_like(b3)

                for state, action, reward, next_state, done in batch:

                    q_values = forward(state)
                    next_q_values = target_forward(next_state)
 
                    if done:
                        target = reward
                    else:
                        target = reward + 0.99 * np.max(next_q_values)

                    target = np.clip(target, -250, 250)
                    error = target - q_values[action]
                    error = np.clip(error, -250, 250)

                    x = np.array(state)
                    h1 = relu(x @ w1 + b1)
                    h2 = relu(h1 @ w2 + b2)

                    error3 = np.zeros(output_size)
                    error3[action] = error

                    error2 = error3 @ w3.T * (h2 > 0)
                    error1 = error2 @ w2.T * (h1 > 0)

                    dw3 += np.outer(h2, error3)
                    db3 += error3
                    dw2 += np.outer(h1, error2)
                    db2 += error2
                    dw1 += np.outer(x, error1)
                    db1 += error1

                w3 += dw3 * 0.0002 / len(batch)
                b3 += db3 * 0.0002 / len(batch)
                w2 += dw2 * 0.0002 / len(batch) 
                b2 += db2 * 0.0002 / len(batch)
                w1 += dw1 * 0.0002 / len(batch)
                b1 += db1 * 0.0002 / len(batch)
                
                if np.isnan(w1).any() or np.isnan(w2).any() or np.isnan(w3).any():
                    print("NaN detected in weights, stopping training")
                    pygame.quit()
                    exit()

        '''if len(replay_buffer2) > 1000:
            
            for _ in range(max(10, frame_count//10)):

                batch = random.sample(replay_buffer2, 64)

                dw1 = np.zeros_like(w1a)
                dw2 = np.zeros_like(w2a)
                dw3 = np.zeros_like(w3a)

                db1 = np.zeros_like(b1a)
                db2 = np.zeros_like(b2a)
                db3 = np.zeros_like(b3a)

                for state, action, reward, next_state, done in batch:

                    q_values = forward2(state)
                    next_q_values = target_forward2(next_state)

                    if done:
                        target = reward
                    else:
                        target = reward + 0.99 * np.max(next_q_values)

                    target = np.clip(target, -250, 250)
                    error = target - q_values[action]
                    error = np.clip(error, -250, 250)

                    x = np.array(state)
                    h1 = relu(x @ w1a + b1a)
                    h2 = relu(h1 @ w2a + b2a)

                    error3 = np.zeros(output_size)
                    error3[action] = error

                    error2 = error3 @ w3a.T * (h2 > 0)
                    error1 = error2 @ w2a.T * (h1 > 0)

                    dw3 += np.outer(h2, error3)
                    db3 += error3
                    dw2 += np.outer(h1, error2)
                    db2 += error2
                    dw1 += np.outer(x, error1)
                    db1 += error1

                w3a += dw3 * 0.0002 / len(batch)
                b3a += db3 * 0.0002 / len(batch)
                w2a += dw2 * 0.0002 / len(batch) 
                b2a += db2 * 0.0002 / len(batch)
                w1a += dw1 * 0.0002 / len(batch)
                b1a += db1 * 0.0002 / len(batch)
                
                if np.isnan(w1a).any() or np.isnan(w2a).any() or np.isnan(w3a).any():
                    print("NaN detected in weights, stopping training")
                    pygame.quit()
                    exit()'''

        if episode % 200 == 0:
            target_w1 = w1.copy()
            target_w2 = w2.copy()
            target_w3 = w3.copy()

            target_b1 = b1.copy()
            target_b2 = b2.copy()
            target_b3 = b3.copy()

            target_w1a = w1a.copy()
            target_w2a = w2a.copy()
            target_w3a = w3a.copy()

            target_b1a = b1a.copy()
            target_b2a = b2a.copy()
            target_b3a = b3a.copy()

            print("Target updated")

        if episode % 100 == 0:
            print(f"""
            Tank 1 wins: {Wins_1}
            Tank 2 wins: {Wins_2}
            Tank 1 suicides: {Suicides_1}
            Tank 2 suicides: {Suicides_2}
            Stalemates: {Stalemates}
            """)
            Wins_1 = 0
            Wins_2 = 0
            Suicides_1 = 0
            Suicides_2 = 0
            Stalemates = 0

            w1a = w1.copy()
            w2a = w2.copy()
            w3a = w3.copy()
            
            b1a = b1.copy()
            b2a = b2.copy()
            b3a = b3.copy()

            np.save("w1.npy", w1)
            np.save("w2.npy", w2)
            np.save("w3.npy", w3)

            np.save("b1.npy", b1)
            np.save("b2.npy", b2)
            np.save("b3.npy", b3)  

            np.save("w1a.npy", w1a)
            np.save("w2a.npy", w2a)
            np.save("w3a.npy", w3a)

            np.save("b1a.npy", b1a)
            np.save("b2a.npy", b2a)
            np.save("b3a.npy", b3a)   

            np.save("epsilon.npy", epsilon)
            np.save("epsilon2.npy", epsilon2)

        print(f"Episode: {episode}, Epsilon: {epsilon:.3f}, Epsilon 2: {epsilon2:.3f}, Max_Q1: {np.max(q_values1):.3f}, Max_Q2: {np.max(q_values2):.3f}")

        if os.path.exists("stop.txt"):
            print("Stopped through file")
            break

except KeyboardInterrupt:
    print("Stopped Manually")