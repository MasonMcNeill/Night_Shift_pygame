import pygame
import sys
import random
import time

# --- Settings ---
WINDOW_WIDTH = 1100
WINDOW_HEIGHT = 900

# Colors
BLACK = (0, 0, 0)
LIGHT_BLACK = (40,40,40)
WHITE = (255, 255, 255)
RED = (200, 50, 50)
BLUE = (50, 50, 200)
GREEN = (50, 200, 50)
ORANGE = (255, 137, 0)
YELLOW = (255, 230, 0)
PINK = (255, 0, 240)
GRAY = (100, 100, 100)
LIGHT_GRAY = (180, 180, 180)

colours = [RED, ORANGE, BLUE, YELLOW, GREEN, PINK]

# Initialize Pygame
pygame.init()
WINDOW = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption("PYNAF - Room Map Prototype")
FONT = pygame.font.SysFont(None, 28)

use_sprite = True # toggleable variable to swithc on/off sprites.

player_sprite = "assets/images/security_cat_32.png"
# [fox, bear, rabbit, bird, bb, mangle]
enemy_sprite_list = [
    "assets/images/evil_larry_32.png",
    "assets/images/bear_cat_32.png",
    "assets/images/rabbit_cat_32.png",
    "assets/images/phinx_cat_32.png",
    "assets/images/propellor_cat_32.png",
    "assets/images/alien_cat_32.png"
    ]
enemy_sprites = [pygame.transform.scale(pygame.image.load(i).convert_alpha(),
                                         (30,30)) for i in enemy_sprite_list]
#--- Define rooms ---
rooms = [
    pygame.Rect(250, 550, 125, 125),   # room 0// MAIN OFFICE
    pygame.Rect(100, 550, 100, 100), # room 1 // LEFT VENT
    pygame.Rect(425, 550, 100, 100), # room 2 // right vent

    pygame.Rect(250, 285, 125, 235),  # room 3 // LONG HALL CLOSE
    pygame.Rect(250, 75, 125, 210),  # room 4 // LONG HALL FAR

    pygame.Rect(25, 375, 200, 150),   # room 5
    pygame.Rect(25, 200, 200, 150),   # room 6
    pygame.Rect(50, 25, 175, 150),    # room 7

    pygame.Rect(400, 375, 100, 150), # room 8
    pygame.Rect(400, 200, 100, 150), # room 9
    pygame.Rect(400, 50, 150, 125), # room 10

    pygame.Rect(575, 50, 150, 150), # room 11
    pygame.Rect(575, 200, 150, 150), # room 12
    pygame.Rect(725, 50, 150, 150), # room 13
    pygame.Rect(725, 200, 150, 150) # room 14
]

# Map connectivity (which rooms are adjacent)
adjacent_rooms = {
    0: [1,2],
    1: [0],
    2: [0],
    3: [0, 5, 8], # this one maybe needs to go to 6 && 9 as well
    4: [3, 6, 7, 9, 10],
    5: [1, 3],
    6: [4, 3, 7],
    7: [4, 6],
    8: [2, 3],
    9: [4, 8],
    10: [4,9],
    11: [10],
    12: [11],
    13: [11],
    14: [11, 12, 13, 14] # special square for "fox"
}


# --- Game state ---
player_pos = 0              # index of player office

# --- ENEMY INFO ---
# [fox, bear, rabbit, bird, bb, mangle]
enemies_start_pos = [14, 7, 11, 13, 5, 12]      # list of room start indices for enemies
enemies_pos = [i for i in enemies_start_pos] # current pos of enemies
enemy_turns = 1 # how many turns the enemies get.

enemy_delay = 2 # how long it takes between enemy moves
enemy_turn_counter = 0

enemy_rect_pos = []
for i, pos in enumerate(enemies_pos):
    rect = rooms[pos]
    x,y = rect.center
    enemy_rect_pos.append([x,y])

enemy_level = [20,20,20,20,20,20] # [1-20], represents chance to move. low to high
fox_charge = enemy_level[0] * 2.5 # gives number [2.5-50] representing chance to charge from 4

allowed_rooms = [
    [0,4,6,7,10,11,12,13,14], # fox can only get you by charging from 4
    [0,3,4,5,6,7],
    [0,2,3,4,8,9,10,11,12],
    [0,1,2,3,4,5,6,8,9,10,11,13],
    [0,1,5],
    [0,2,3,5,8,9,10,11,12,13,14]
]

main_hall_flashable = [0,5] # index for characters that can be flashed in main hall
vent_flashable = [4,5] # index for characters that can be flashed in vents


# --- Game state variables ---
game_time = 1
winning_round = 30 # once this many enemy turns happens, player wins
player_won = False

# FLASHLIGHT
battery = 100 # represents flashlight battery, each flash costs 5? or something
battery_cost = 4 # battery depletion
battery_dead = False
flash_cost = 1 # action point cost
bb_flashlight_cost = 10 # bb steals this much battery

flash_effect = {
    "rooms": [], # which rooms to light up
    "timer": 0, # ms left in effect
    "max_time": 150 # duration in ms
}

# MUSIC BOX
music = 100 # ticks down by X every turn? once 0 player loses?
music_inc = 5 # increase by this much?
music_dec = 5 # decreases this much each enemy turn 
music_cost = 2
music_max = 100

# MASK
mask_on = False
mask_cost = 3 # action point cost

# CAMERA
used_camera = False
camera_cost = 1

camera_overlay_alpha = 60
camera_fading = None
camera_fade_duration = 3 # seconds


actions = 0 # player gets 5 actions.
player_actions = 5


# --- Buttons ---
buttons = {
    "Flash": pygame.Rect(50, WINDOW_HEIGHT-80, 100, 50),
    "Music": pygame.Rect(200, WINDOW_HEIGHT-80, 100, 50),
    "L Vent": pygame.Rect(350, WINDOW_HEIGHT-80, 100, 50),
    "R Vent": pygame.Rect(500, WINDOW_HEIGHT-80, 100, 50),
    "Mask": pygame.Rect(650, WINDOW_HEIGHT-80, 100, 50),
    "Camera": pygame.Rect(800, WINDOW_HEIGHT-80, 100, 50),
    "EndTurn": pygame.Rect(980, WINDOW_HEIGHT-130, 100, 100),
    "SpriteToggle" : pygame.Rect(925, WINDOW_HEIGHT-275, 150, 50)
}

# --- Status displays ---
status = {
    "Battery": [pygame.Rect(50, WINDOW_HEIGHT-160, 100, 50), battery],
    "Windup": [pygame.Rect(200, WINDOW_HEIGHT-160, 100, 50), music],
    "Wearing": [pygame.Rect(650, WINDOW_HEIGHT-160, 100, 50), mask_on],
    "UsedCam": [pygame.Rect(800, WINDOW_HEIGHT-160, 100, 50), used_camera],
    "Moves": [pygame.Rect(980, WINDOW_HEIGHT-190, 100, 50), actions],
    "Time": [pygame.Rect(950, 40, 100, 100), game_time]
}

# --- Upgraded visuals ---

def draw_bar(surface, x, y, w, h, percent, color_full, color_empty=(60,60,60)):
    # Draw progress bar
    pygame.draw.rect(surface, color_empty, (x,y,w,h))
    fill = int(w * max(0, min(1, percent)))
    pygame.draw.rect(surface, color_full, (x,y,fill,h))
    pygame.draw.rect(surface, WHITE, (x,y,w,h), 2)

def draw_flash_overlay():
    # Flashlight effect
    flash_surface = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
    flash_surface.fill((255,255,255,40)) # translucent white overlay
    WINDOW.blit(flash_surface, (0,0))

def draw_mask_overlay():
    # For mask effect
    mask_surf = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
    mask_surf.fill((0,0,0,100)) # dark overlay
    WINDOW.blit(mask_surf, (0,0))

def draw_camera_overlay():
    # Security camera blue tint
    global used_camera
    global camera_fading
    global camera_overlay_alpha
    global camera_fade_duration

    if not used_camera:
        return

    cam_surf = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
    if camera_fading is not None:
            elapsed = time.time() - camera_fading
            alpha = max(0, camera_overlay_alpha * (1 - elapsed / camera_fade_duration))
            cam_surf.fill((50, 100, 180, int(alpha)))
            if alpha == 0:
                used_camera = False
                camera_fading = None
    else:
        cam_surf.fill((50,100,180,camera_overlay_alpha))

    WINDOW.blit(cam_surf, (0,0))

    for i, pos in enumerate(enemies_pos):
        #rect = rooms[pos]
        if pos not in [0,1,2,3]:
            x,y = enemy_rect_pos[i]
        #enemy_color = colours[i]

        #enemy_surf = pygame.Surface((30,30), pygame.SRCALPHA)
        #pygame.draw.circle(enemy_surf, (*enemy_color, alpha), (15,15), 15)
       # WINDOW.blit(enemy_surf, (x-15, y-15))
            if use_sprite:
                enemy_img = enemy_sprites[i]
                enemy_img.set_alpha(alpha)
                WINDOW.blit(enemy_img, (x-15, y-15)) # circle center offset.
            else:
                enemy_color = colours[i]
                enemy_surf = pygame.Surface((30,30), pygame.SRCALPHA)
                pygame.draw.circle(enemy_surf, (*enemy_color, alpha), (15,15), 15)
                WINDOW.blit(enemy_surf, (x-15, y-15))

# --- Functions ---
def draw_map(enemy_rect_pos):
    # Draw hallways (lines connecting room centers)
    
    for room_index, neighbors in adjacent_rooms.items():
        for neighbor in neighbors:
            pygame.draw.line(WINDOW, LIGHT_GRAY, rooms[room_index].center, rooms[neighbor].center, 3)
    
    # Draw rooms
    for index, rect in enumerate(rooms):
        pygame.draw.rect(WINDOW, LIGHT_BLACK, rect)        # room background
        pygame.draw.rect(WINDOW, WHITE, rect, 2)    # room border
        
        # Flashlight brightening
        if flash_effect["timer"] > 0 and index in flash_effect["rooms"]:
            alpha = int(255 * (flash_effect["timer"] / flash_effect["max_time"]))
            glow = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
            glow.fill((255,255,200,alpha)) # warm flashlight color
            WINDOW.blit(glow, (rect.x, rect.y))

        for j, pos in enumerate(enemies_pos):
            if pos == index:
                if pos in [0,1,2,3]: # draw all enemies that are close within a room
                    x,y = enemy_rect_pos[j]
                    # Glow around enemies
                    if use_sprite:
                        enemy_img = enemy_sprites[j]
                        enemy_img.set_alpha(255) # ensure not transparent
                        WINDOW.blit(enemy_img, (x-15, y-15)) # circle center offset.
                    else:
                        pygame.draw.circle(WINDOW, (255,255,255,50), (x,y), 16)
                        pygame.draw.circle(WINDOW, colours[j], (x,y), 15)

        # Draw player
        if player_pos == index:
            x, y = rect.center
            pygame.draw.circle(WINDOW, (255,255,255,50), (x,y+25), 16) # add outline
            pygame.draw.circle(WINDOW, BLUE, (x, y+25), 15)
        
        # Room labels
        label = FONT.render(f"CAM {index}", True, WHITE)
        WINDOW.blit(label, (rect.x + 5, rect.y + 5))

def draw_buttons():
    mx, my = pygame.mouse.get_pos()
    
    for name, rect in buttons.items():
        hovered = rect.collidepoint(mx, my)
        if name != "SpriteToggle":
            color = (80,200,80) if hovered else (40, 160, 40)
        else:
            color = (80, 200, 80) if use_sprite else RED
        
        pygame.draw.rect(WINDOW, color, rect, border_radius=8)
        pygame.draw.rect(WINDOW, WHITE, rect, 2, border_radius=8)


        text = FONT.render(name, True, BLACK)
        WINDOW.blit(text, (rect.x + 10, rect.y + 10))


def draw_status():
    # UI background
    pygame.draw.rect(WINDOW, (25,25,25), (0, WINDOW_HEIGHT-200, WINDOW_WIDTH, 200))

    # Battery bar
    draw_bar(WINDOW, 50, WINDOW_HEIGHT-170, 200, 25, battery/100,
             (0,200,0) if battery > 30 else (200, 150, 0) if battery > 10 else (200,0,0))
    WINDOW.blit(FONT.render("Battery", True, WHITE), (50, WINDOW_HEIGHT-195))
    moves_text = FONT.render(f"{battery}/{100}", True, WHITE)
    WINDOW.blit(moves_text, (250+5, WINDOW_HEIGHT-170))

    # Music Box
    draw_bar(WINDOW, 350, WINDOW_HEIGHT-170, 200, 25,
             music / 100, (200, 200, 0))
    WINDOW.blit(FONT.render("Music Box", True, WHITE), (350, WINDOW_HEIGHT-195))
    music_text = FONT.render(f"{music}/{music_max}", True, WHITE)
    WINDOW.blit(music_text, (550+5, WINDOW_HEIGHT-170))

    # Actions 
    draw_bar(WINDOW, 650, WINDOW_HEIGHT-170, 200, 25,
             actions / 5, (0, 150, 255))
    WINDOW.blit(FONT.render("Actions", True, WHITE), (650, WINDOW_HEIGHT-195))
    actions_text = FONT.render(f"{actions}/{player_actions}", True, WHITE)
    WINDOW.blit(actions_text, (850+5, WINDOW_HEIGHT-170))

    # Round counter
    round_text = FONT.render(f"Round: {game_time}/30", True, WHITE)
    WINDOW.blit(round_text, (950, 25))

    # Phase Indicator
    phase = "PLAYER TURN" if actions > 0 else "ENEMY TURN"
    color = BLUE if actions > 0 else RED
    text = FONT.render(phase, True, color)
    WINDOW.blit(text, (950, WINDOW_HEIGHT-180))


def random_position_in_room(rect):
    x = random.randint(rect.left + 20, rect.right - 20)
    y = random.randint(rect.top + 20, rect.bottom - 20)
    return x, y

def choose_room(enemy, choices):
    # takes enemy id, and their current options.
    # [fox, bear, rabbit, bird, bb, mangle]
        global enemies_pos

        allowed = allowed_rooms[enemy]
        chance = enemy_level[enemy]
        roll = random.randint(1,20)

        set1 = set(allowed)
        set2 = set(choices)
        common_set = set1.intersection(set2)
        common_list = list(common_set)

        if roll > chance or len(common_list) == 0: # dont move if this happens
            return -1
        elif enemy == 0 and enemies_pos[0] == 4 and random.randint(1,100) > fox_charge:
            return 0 # if fox rolls chance to move, then check charge chance
        else:
            return random.choice(common_list) 
        

def move_enemies(enemy_rect_pos):
    # Need special move case for BB and fox.
    global mask_on
    global running
    global bb_flashlight_cost
    global battery

    for i, room in enumerate(enemies_pos):
        # Randomly choose adjacent room to move into
        neighbors = adjacent_rooms[room]
        new_room = choose_room(i, neighbors)
        if new_room == -1:
            new_room = room # if no move, keep room the same
        elif new_room == 0 and mask_on == True:
            if i == 5:
                running = 0
                print("died to mangle")
            else:
                new_room = enemies_start_pos[i]
        elif new_room == 0:
            if i == 4: # if bb gets in and no mask, he takes battery and leaves.
                battery -= bb_flashlight_cost
                status.update({"Battery": [pygame.Rect(50, WINDOW_HEIGHT-120, 100, 25), battery]})
                new_room = enemies_start_pos[i]
            else:
                running = 0
                print("player died to enemy")

        enemies_pos[i] = new_room

        rect = rooms[new_room]
        x, y = random_position_in_room(rect)
        enemy_rect_pos[i] = [x,y]
    

def update_one_enemy_pos(char_index, room_index):
    rect = rooms[room_index]
    x,y = random_position_in_room(rect)
    enemy_rect_pos[char_index] = [x,y]
    draw_map(enemy_rect_pos)

def update_actions(change):
    global actions
    actions += change
    status.update({"Moves": [pygame.Rect(980, WINDOW_HEIGHT-190, 100, 50), actions]})

def next_round():
    global game_time
    global winning_round
    global running
    global player_won

    game_time += 1
    status.update({"Time": [pygame.Rect(950, 40, 100, 100), game_time]})

    if (game_time == winning_round):
        running = False
        player_won = True
        print("player WINS!")

def flash_hallway():
    global battery
    global battery_cost
    global battery_dead
    global actions

    flash_effect["rooms"] = [3,4]
    flash_effect["timer"] = flash_effect["max_time"]
    
    for index, pos in enumerate(enemies_pos):
        if pos == 3 or pos == 4:
            if index in main_hall_flashable:
                enemies_pos[index] = enemies_start_pos[index] # send back to their start if flashed
                update_one_enemy_pos(index, enemies_start_pos[index])


    battery -= battery_cost
    status.update({"Battery": [pygame.Rect(50, WINDOW_HEIGHT-160, 100, 50), battery]})
    update_actions(-flash_cost)

    if battery == 0:
        battery_dead = True

def wind_music():
    global music
    global music_inc
    global actions

    if actions >= 2 and music < 100:
        music += music_inc
        status.update({"Windup": [pygame.Rect(200, WINDOW_HEIGHT-160, 100, 50), music]})
        update_actions(-music_cost)

def unwind_music():
    global music
    global music_dec
    global running
    
    music -= music_dec
    status.update({"Windup": [pygame.Rect(200, WINDOW_HEIGHT-160, 100, 50), music]})
    if music <= 0:
        running = False
        print("Player died to music")


def flash_left_vent():
    global battery
    global battery_cost
    global battery_dead
    global actions

    flash_effect["rooms"] = [1]
    flash_effect["timer"] = flash_effect["max_time"]
    
    for index, pos in enumerate(enemies_pos):
        if pos == 1:
            if index in vent_flashable:
                enemies_pos[index] = enemies_start_pos[index] # send back to their start if flashed
                update_one_enemy_pos(index, enemies_start_pos[index])

    battery -= battery_cost
    status.update({"Battery": [pygame.Rect(50, WINDOW_HEIGHT-160, 100, 50), battery]})
    update_actions(-flash_cost)

    if battery == 0:
        battery_dead = True

def flash_right_vent():
    global battery
    global battery_cost
    global battery_dead
    global actions

    flash_effect["rooms"] = [2]
    flash_effect["timer"] = flash_effect["max_time"]
    
    for index, pos in enumerate(enemies_pos):
        if pos == 2:
            if index in vent_flashable:
                enemies_pos[index] = enemies_start_pos[index] # send back to their start if flashed
                update_one_enemy_pos(index, enemies_start_pos[index])

    battery -= battery_cost
    status.update({"Battery": [pygame.Rect(50, WINDOW_HEIGHT-160, 100, 50), battery]})
    update_actions(-flash_cost)

    if battery == 0:
        battery_dead = True

def use_mask(state):
    # NEED to remove this after enemy turns
    global mask_on
    global actions

    if state == False:
        mask_on = False
    else: 
        if actions >= 3:
            mask_on = True
            update_actions(-mask_cost)
    
    status.update({"Wearing": [pygame.Rect(650, WINDOW_HEIGHT-160, 100, 50), mask_on]})


def use_camera(state):
    global actions
    global used_camera
    global camera_fading

    if state == False:
        used_camera = False
        camera_fading = None
    else:
        used_camera = True
        camera_fading = time.time()
        update_actions(-camera_cost)
    status.update({"UsedCam": [pygame.Rect(800, WINDOW_HEIGHT-160, 100, 50), used_camera]})

def toggle_sprites():
    # simply switches toggle.
    global use_sprite

    use_sprite = not use_sprite


# --- Main loop ---
clock = pygame.time.Clock()
running = True
enemy_move_timer = 0


while running:
    dt = clock.tick(30)
    enemy_move_timer += dt

    if actions <= 0:
        for event in pygame.event.get(): # necessary to prevent crash
            if event.type == pygame.QUIT:
                running = False
        if enemy_turn_counter < enemy_turns:
            if enemy_move_timer >= enemy_delay * 1000:
                move_enemies(enemy_rect_pos)
                unwind_music()
                enemy_turn_counter += 1
                enemy_move_timer = 0
        else:
            #next_round()
            update_actions(player_actions)
            use_mask(False)
            use_camera(False)
            enemy_turn_counter = 0
    
    else:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                enemy_move_timer = 0
                mx, my = pygame.mouse.get_pos()
                #print(f"clicked: ({mx},{my})") # debug
                for name, rect in buttons.items():
                    if rect.collidepoint(mx, my):
                        #print(f"Player used {name}!") # debug
                        if (name == "Flash" and battery_dead == False):
                            flash_hallway()
                        elif (name == "Music"):
                            wind_music()
                        elif (name == "L Vent"):
                            flash_left_vent()
                        elif (name == "R Vent"):
                            flash_right_vent()
                        elif (name == "Mask"):
                            use_mask(True)
                        elif (name == "Camera"):
                            use_camera(True)
                        elif (name == "EndTurn"):
                            update_actions(-actions)
                        elif (name == "SpriteToggle"):
                            toggle_sprites()
                if (actions <= 0): # end player turn, go to next round
                    next_round()

    # Draw everything
    WINDOW.fill(BLACK)
    draw_map(enemy_rect_pos)
    if mask_on:
        draw_mask_overlay()
    if used_camera:
        draw_camera_overlay()
    if flash_effect["timer"] > 0:
        flash_effect["timer"] -= dt
        if flash_effect["timer"] < 0:
            flash_effect["timer"] = 0
    draw_status()
    draw_buttons()


    pygame.display.flip()

pygame.quit()
sys.exit()
