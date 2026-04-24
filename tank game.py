import pygame
import math
import time

pygame.init()

screen = pygame.display.set_mode((1000, 600))
pygame.display.set_caption("Tank Game")

running = True

tank_x = 500
tank2_x = 0
tank_y = 300
tank2_y = 0
size = 15
collison_size = 8
speed = 2
angle = -90
angle2 = 0
steering = 1
steering2 = 1
map = [
"####################",
"#.M................#",
"#..##...####...##..#",
"#.##...##..##...##.#",
"#.#..............#.#",
"#.#####......#####.#",
"#.....#......#.....#",
"#..#............#..#",
"#..######..######..#",
"#.......#..#.......#",
"#................S.#",
"####################"
]
tile_size = 50
walls = []

bullets = []
tank_bullets = 0
tank2_bullets = 0

bullet_speed = 3

last_shot_time = 0
last_shot_time2 = 0
shoot_cooldown = 100

spawn_protect = False
spawn_protect2 = False

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

while running:
    screen.fill((255, 255, 255))
    collision = False
    collision2 = False
    if pygame.time.get_ticks() - last_shot_time > shoot_cooldown/2:
        spawn_protect = False
    if pygame.time.get_ticks() - last_shot_time2 > shoot_cooldown/2:
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

    dx = 0
    dy = 0
    dx2 = 0
    dy2 = 0

    if keys[pygame.K_UP]:
        dx = speed * math.cos(math.radians(angle))
        dy = speed * math.sin(math.radians(angle))
        steering = 1
    elif keys[pygame.K_DOWN]: 
        dx = -speed * math.cos(math.radians(angle))
        dy = -speed * math.sin(math.radians(angle))
        steering = -1
    else:
        steering = 1

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

    if keys[pygame.K_LEFT]:
            angle -= 5*steering

    if keys[pygame.K_RIGHT]:
            angle += 5*steering

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
            break

    for wall in walls:
        closest_x2 = max(wall.left, min(next_x2, wall.right))
        closest_y2 = max(wall.top, min(next_y2, wall.bottom))
    
        dx_u2 = next_x2 - closest_x2
        dy_u2 = next_y2 - closest_y2

        if (dx_u2 * dx_u2 + dy_u2 * dy_u2) < (collison_size * collison_size):
            collision2 = True
            break

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

    for bullet in bullets:

        prev_x = bullet['bullet_x']
        prev_y = bullet['bullet_y']

        bullet['bullet_x'] += bullet_speed * math.cos(math.radians(bullet['bullet_angle']))
        bullet['bullet_y'] += bullet_speed * math.sin(math.radians(bullet['bullet_angle']))
        pygame.draw.circle(screen, (255, 0, 0), (int(bullet['bullet_x']), int(bullet['bullet_y'])), 5)
        
        rounding_error = 0.01

        if not spawn_protect:
            if bullet['bullet_x'] < tank_x + collison_size and bullet['bullet_x'] > tank_x - collison_size and bullet['bullet_y'] < tank_y + collison_size and bullet['bullet_y'] > tank_y - collison_size:
                print("Player 2 wins!")
                running = False
        
        if not spawn_protect2:
            if bullet['bullet_x'] < tank2_x + collison_size and bullet['bullet_x'] > tank2_x - collison_size and bullet['bullet_y'] < tank2_y + collison_size and bullet['bullet_y'] > tank2_y - collison_size:
                print("Player 1 wins!")
                running = False

        for wall in walls:
            if wall.collidepoint(bullet['bullet_x'], bullet['bullet_y']) or wall.collidepoint(prev_x, prev_y):
                if prev_x <= (wall.left + rounding_error) or prev_x >= (wall.right - rounding_error):
                    bullet['bullet_angle'] = 180 - bullet['bullet_angle']
                
                if prev_y <= (wall.top + rounding_error) or prev_y >= (wall.bottom - rounding_error):
                    bullet['bullet_angle'] = -bullet['bullet_angle']
                bullet['bullet_x'] += bullet_speed * math.cos(math.radians(bullet['bullet_angle']))
                bullet['bullet_y'] += bullet_speed * math.sin(math.radians(bullet['bullet_angle']))
                break
            
                

    print(len(bullets))

    pygame.draw.polygon(screen, (0, 128, 0), [(tank_x + math.cos(math.radians(angle)) * size, tank_y + math.sin(math.radians(angle)) * size), 
                                              (tank_x + math.cos(math.radians(angle) + 2.5) * size, tank_y + math.sin(math.radians(angle) + 2.5) * size), 
                                              (tank_x + math.cos(math.radians(angle) - 2.5) * size, tank_y + math.sin(math.radians(angle) - 2.5) * size)])
    pygame.draw.polygon(screen, (0, 0, 128), [(tank2_x + math.cos(math.radians(angle2)) * size, tank2_y + math.sin(math.radians(angle2)) * size), 
                                              (tank2_x + math.cos(math.radians(angle2) + 2.5) * size, tank2_y + math.sin(math.radians(angle2) + 2.5) * size), 
                                              (tank2_x + math.cos(math.radians(angle2) - 2.5) * size, tank2_y + math.sin(math.radians(angle2) - 2.5) * size)])
    for wall in walls:
        pygame.draw.rect(screen, (0, 0, 0), wall)
    pygame.time.Clock().tick(60)
    pygame.display.flip() 