# import, set up 'correct' paths for silicon macs 
import os
home_dir = os.path.expanduser("~")

if home_dir == "/Users/nat":
    mediapipe_dylibs_path = "/Users/nat/Documents/coding/bris_hack_2024/venv/lib/python3.9/site-packages/mediapipe/.dylibs"
    os.environ["DYLD_LIBRARY_PATH"] = mediapipe_dylibs_path + ":" + os.environ.get("DYLD_LIBRARY_PATH", "")

import time
import mediapipe as mp
import numpy as np
import asyncio
import sys 
import json
import pygame
import random

from person_headheight import Person

mp_pose = mp.solutions.pose

# set constants
SETUP_TIME = 0

FPS = 60

SCREEN_HEIGHT, SCREEN_WIDTH = 540, 960

PIPE_WIDTH = 80
PIPE_HEIGHT = 500
PIPE_GAP = 120  # Gap between the top and bottom pipes
PIPE_INTERVAL = 1500  # Milliseconds between new pipes
PIPE_SPEED_START = 6
PIPE_EDGE_MARGIN = 50

BIRD_WIDTH = 30
BIRD_HEIGHT = 30
BIRD_MARGIN_LEFT = 50

LIGHT_BLUE = (173, 216, 230)  # RGB for light blue

# setup pygame
pygame.init()
font = pygame.font.SysFont("Arial", 30)  
font_smaller = pygame.font.SysFont("Arial", 24)  
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

# set global vars
bird_image = pygame.image.load("assets/bird.png")
bird_image = pygame.transform.scale(bird_image, (BIRD_WIDTH, BIRD_HEIGHT))
bird_y = 0

background_image = pygame.image.load("assets/flappy_bg.png")
pipes = [] # pipes stored in format - (x coord, height, is_scored)
last_pipe_time = 0
score = 0
top_score = 0
clock = None
start_time = None
person = None
pipe_speed_up_coro = None
pipe_speed = PIPE_SPEED_START
top_score_name = ""

async def speed_up():
    try:
        await asyncio.sleep(10)
        while True:
            PIPE_SPEED += max(2, 0.15 * PIPE_SPEED)
            await asyncio.sleep(5)
    except asyncio.CancelledError:
        pass


def on_collision():
    global pipe_speed
    pipe_speed = PIPE_SPEED_START
    pipe_speed_up_coro.cancel()

    player_name = do_gameover()  # Get player name and show game over screen
    print(f"got name: {player_name}")

    if player_name is not None:
        update_scores(player_name, score)
        return True  # Indicate that player wants to restart
    else:
        return False  # Indicate game end


def update_scores(name, current_score):
    scores_data = read_scores()

    # Check if the player already has a score and if the current score is higher
    existing_scores = [score for score in scores_data["scores"] if name in score]
    if existing_scores:
        best_score = max(score[name] for score in existing_scores)
        if current_score <= best_score:
            print(f"No update needed. Current score {current_score} is not higher than best score {best_score} for {name}")
            return

    # Update scores if this is a new best or the first score for this player
    scores_data["scores"].append({name: current_score})
    with open('scores.json', 'w') as file:
        json.dump(scores_data, file, indent=4)
        print(f"Updated score {current_score} for {name}")


def draw_score():
    """
    Draw the score 
    """

    global score

    # text
    score_surface = font.render(f'Score: {score}', True, (0, 0, 0))
    score_width, score_height = score_surface.get_size()
    
    score_position = (screen.get_width() - score_width - 10, 10)

    # add background
    background_rect = pygame.Rect(score_position[0] - 5, score_position[1] - 5, score_width + 10, score_height + 10)
    pygame.draw.rect(screen, LIGHT_BLUE, background_rect)

    # draw
    screen.blit(score_surface, score_position)

def draw():
    """
    Draw all elements.
    """

    print("drawing screen…")
    screen.fill((255, 255, 255))  # clear screen
    
    draw_bird()
    draw_pipes()
    draw_score()
    draw_top_score()
    
    pygame.display.update()
    print("drawn screen")


def draw_bird():
    screen.blit(bird_image, (BIRD_MARGIN_LEFT, bird_y))


def update_bird(person : Person):
    """
    Gets head position, then sets player height
    """

    print("updating bird…")
    global bird_y
    
    # landmarks, _ = person.get_landmarks()
    result = person.get_landmarks()
    if result is None:
        print(f"no significant landmarks, kept height at {bird_y}")
        return
    landmarks = result[0]

    player_pos = person.get_player_height(landmarks.landmark)

    bird_y = int(SCREEN_HEIGHT * player_pos)
    bird_y = max(0, bird_y)
    print(f"updated bird to {bird_y}")


def check_collisions_scores():
    """
    Checks if the bird has collided with a pipe, or if any pipes need to be scored
    """
    global score
    global pipes

    pipe_upto = min(len(pipes), 3)
    for i in range(pipe_upto):
        pipe = pipes[i]
        
        # check collisions
        c = (BIRD_MARGIN_LEFT + BIRD_WIDTH, bird_y) # (x, y)

        if c[0] > pipe[0] and c[0] < pipe[0] + PIPE_WIDTH:
            if c[1] < pipe[1] or c[1] + BIRD_HEIGHT > pipe[1] + PIPE_GAP:
                return True
            
        # check if any pipes need to be scored
        if BIRD_MARGIN_LEFT > pipe[0] + PIPE_WIDTH and not pipe[2]:
            score += 1
            pipe_new = (pipe[0], pipe[1], True)
            pipes[i] = pipe_new
            

def generate_pipes():
    """
    Create new pipes, if it's the right time to.
    """

    print("generating pipes…")
    global last_pipe_time

    current_time = pygame.time.get_ticks()
    if current_time - last_pipe_time > PIPE_INTERVAL:
        last_pipe_time = current_time
        pipe_gap_y = random.randint(PIPE_EDGE_MARGIN, SCREEN_HEIGHT - PIPE_EDGE_MARGIN - PIPE_GAP)
        pipes.append((SCREEN_WIDTH, pipe_gap_y, False))

        print("generated a pipe")
    else:
        print("not generated pipes")


def update_pipes():
    """
    Move pipes left, and delete off screen pipes.
    """

    # move pipes left
    print("moving pipes left…")
    for i in range(len(pipes)):
        pipe_x_new = pipes[i][0] - pipe_speed
        pipes[i] = (pipe_x_new, pipes[i][1], pipes[i][2])

    # remove pipes that have moved off-screen
    print("removing off screen pipes…")
    pipes[:] = [pipe for pipe in pipes if pipe[0] > -PIPE_WIDTH]
    print("updated pipes")


def draw_top_score():
    t_now = time.time()
    if t_now < start_time + 4 and t_now % 1 < 0.6:
        msg = f"Top Score: {top_score} by {top_score_name}"
        text_surface = font.render(msg, True, (0, 0, 0))  # Black color

        text_width, text_height = text_surface.get_size()

        x = (screen.get_width() - text_width) // 2
        y = (screen.get_height() - text_height) // 2

        screen.blit(text_surface, (x, y))


def read_scores():
    try:
        with open('scores.json', 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        return {"scores": []}


def get_top_score():
    scores_data = read_scores()
    top_score = 0
    top_name = None

    for entry in scores_data["scores"]:
        for name, score in entry.items():
            if score > top_score:
                top_score = score
                top_name = name

    return top_name, top_score 


def do_gameover():
    box_width, box_height = 300, 200
    box_x, box_y = (screen.get_width() - box_width) // 2, (screen.get_height() - box_height) // 2
    input_box = pygame.Rect(box_x + 50, box_y + 140, 200, 36)
    color_inactive = pygame.Color('lightskyblue3')
    color_active = pygame.Color('dodgerblue2')
    color = color_inactive
    active = False
    name = ""
    _, top_score = get_top_score()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None
            if event.type == pygame.MOUSEBUTTONDOWN:
                if input_box.collidepoint(event.pos):
                    active = not active
                else:
                    active = False
                color = color_active if active else color_inactive
            if event.type == pygame.KEYDOWN:
                if active:
                    if event.key == pygame.K_RETURN:
                        return name
                    elif event.key == pygame.K_BACKSPACE:
                        name = name[:-1]
                    else:
                        name += event.unicode

        draw_bird()
        draw_pipes()
        draw_score()
    
        # draw the box
        pygame.draw.rect(screen, (173, 216, 230), (box_x, box_y, box_width, box_height))
        pygame.draw.rect(screen, (0, 0, 0), (box_x, box_y, box_width, box_height), 2)

        # game Over text
        game_over_surface = font.render("Game Over", True, (0, 0, 0))
        screen.blit(game_over_surface, (box_x + 70, box_y + 30))

        # display user score
        score_surface = font.render(f"Your Score: {score}", True, (0, 0, 0))
        screen.blit(score_surface, (box_x + 50, box_y + 70))

        # display top score
        top_score_surface = font.render(f"Top Score: {top_score} by {top_score_name}", True, (0, 0, 0))
        screen.blit(top_score_surface, (box_x + 50, box_y + 100))

        # name input
        txt_surface = font.render(name, True, color)
        screen.blit(txt_surface, (input_box.x + 5, input_box.y + 5))
        pygame.draw.rect(screen, color, input_box, 2)

        pygame.display.flip()
        print("rendered game over")

        # check if person has crouched
        res = person.get_landmarks()
        if res is None:
            print(f"no significant landmarks, kept height at {bird_y}")
            return
        landmarks = res[0]

        player_pos = person.get_player_height(landmarks.landmark)

        if player_pos > 0.5:
            return name
        

def draw_pipes():
    screen.blit(background_image, (0, 0))
    for x, height, _ in pipes:
        # draw top pipe
        pygame.draw.rect(screen, (0, 0, 0), (x, 0, PIPE_WIDTH, height))

        # draw bottom pipe
        pygame.draw.rect(screen, (0, 0, 0), (x, height + PIPE_GAP, PIPE_WIDTH, SCREEN_HEIGHT - PIPE_GAP - height))


async def game_loop():
    """
    Run the main game loop, return True if user wants to end the game.
    """

    global score, pipes, bird_y, last_pipe_time, pipe_speed_up_coro, start_time

    score = 0
    pipes = []
    bird_y = 0
    last_pipe_time = pygame.time.get_ticks()
    start_time = time.time()
    pipe_speed_up_coro = asyncio.create_task(speed_up())

    while True:
        # pygame event loop
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        # update bird
        update_bird(person)

        # handle pipes
        generate_pipes()
        update_pipes()

        # check if there are any collisions
        is_collision = check_collisions_scores()
        if is_collision:
            play_again = on_collision()
            print(f"player wants to continue: {play_again}")
            return play_again
        
        else:
            draw()
            clock.tick(FPS)
            
            await asyncio.sleep(0)

async def main():
    global person, clock, top_score, top_score_name
    person = Person(SETUP_TIME)
    
    clock = pygame.time.Clock() 

    top_score_name, top_score = get_top_score()

    # wait until the extremeties have initialised
    while True:
        await asyncio.sleep(0.5)
        if person.nose is None or person.thigh is None:
            print("waiting for setup…")
            continue
        else:
            print("received setup")
            break

    while True:
        game_over = await game_loop()
        if not game_over:
            break

if __name__ == "__main__":
    asyncio.run(main())