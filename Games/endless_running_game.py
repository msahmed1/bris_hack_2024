# Import Library
import os
import sys
import pygame
import random
import time

# Add the root directory For MQTClient
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from mqtt_client import MQTTClient

# MQTT setup
mqtt_client =  MQTTClient()

#Environment Variable
os.environ['SDL_VIDEO_WINDOW_POS'] = '112,83'

#Initialize
pygame.init()
pygame.mixer.init()

#CONFIG
TITLE = 'RUN FOR FUN'
SCREEN_HEIGHT = 600
SCREEN_WIDTH = 1100
SCREEN_COLOR = (240, 236, 227)
GAME_SPEED = 10
BORDER = False

#Defining Collision Difference
dict_ = {10:30, 15:30, 20:40, 25:40, 30:50, 35:50, 40:60}
def get_collision_distance_diff(speed):
    for i, j in dict_.items():
        if int(i) >= int(speed):
            return j
#Setting Title
pygame.display.set_caption(TITLE)

# Adding image for running
RUNNING = [pygame.image.load(os.path.join("../Assets/Dino", "DinoRun1.png")),
           pygame.image.load(os.path.join("../Assets/Dino", "DinoRun2.png"))]

JUMPING = pygame.image.load(os.path.join("../Assets/Dino", "DinoJump.png"))
DUCKING = [pygame.image.load(os.path.join("../Assets/Dino", "DinoDuck1.png")),
           pygame.image.load(os.path.join("../Assets/Dino", "DinoDuck2.png"))]

SMALL_CACTUS = [pygame.image.load(os.path.join("../Assets/Cactus", "SmallCactus1.png")),
                pygame.image.load(os.path.join("../Assets/Cactus", "SmallCactus2.png")),
                pygame.image.load(os.path.join("../Assets/Cactus", "SmallCactus3.png"))]
LARGE_CACTUS = [pygame.image.load(os.path.join("../Assets/Cactus", "LargeCactus1.png")),
                pygame.image.load(os.path.join("../Assets/Cactus", "LargeCactus2.png")),
                pygame.image.load(os.path.join("../Assets/Cactus", "LargeCactus3.png"))]

BIRD = [pygame.image.load(os.path.join("../Assets/Bird", "Bird1.png")),
        pygame.image.load(os.path.join("../Assets/Bird", "Bird2.png"))]

CLOUD = pygame.image.load(os.path.join("../Assets/Other", "Cloud.png"))

BG = pygame.image.load(os.path.join("../Assets/Other", "Track.png"))

# Setting Music Backgroud
def play_menu_music():
    pygame.mixer.music.load(os.path.join("../Assets/Audio", "music.ogg"))
    pygame.mixer.music.play(-1)  # -1 makes the music loop indefinitely

def play_game_music():
    pygame.mixer.music.load(os.path.join("../Assets/Audio", "menu.mp3"))
    pygame.mixer.music.play(-1)  # -1 makes the music loop indefinitely

def play_dead_music():
    pygame.mixer.music.load(os.path.join("../Assets/Audio", "dead.mp3"))
    pygame.mixer.music.play(1)  # -1 makes the music loop indefinitely

def play_dragon_music():
    bird_sound = pygame.mixer.Sound(os.path.join("../Assets/Audio", "dragon.mp3"))
    bird_sound.play()

def play_jump_music():
    jump_sound = pygame.mixer.Sound(os.path.join("../Assets/Audio", "jump.mp3"))
    jump_sound.play()

def play_slide_music():
    jump_sound = pygame.mixer.Sound(os.path.join("../Assets/Audio", "slide.mp3"))
    jump_sound.play()

# Dino Class
class Dinosaur:
    #Global Variable
    X_POS = 80
    Y_POS = 310
    Y_POS_DUCK = 340
    JUMP_VEL = 12

    def __init__(self)->None:
        #Initialize Image
        self.duck_img = DUCKING
        self.run_img = RUNNING
        self.jump_img = JUMPING

        #Initialize Deno current State
        self.dino_duck = False
        self.dino_run = True
        self.dino_jump = False

        #Remaining Initialisation
        self.step_index = 0
        self.jump_vel = self.JUMP_VEL
        self.image = self.run_img[0]
        self.dino_rect = self.image.get_rect()
        self.dino_rect.x = self.X_POS
        self.dino_rect.y = self.Y_POS
        self.jump_sound = False
        self.duck_sound = False

    # Updating State of Dino
    def update(self, keyInputs, speed):
        #Getting user activity from the camera
        userInput = mqtt_client.get_latest_message("userInput")
        if userInput == None:
            userInput = "standing"
            
        # checking for a particular frame what is action of Dino
        if self.dino_duck:
            self.duck(speed)
        if self.dino_run:
            self.run(speed)
        if self.dino_jump:
            self.jump()

        if self.step_index >= 10:
            self.step_index = 0

        # condition of action of the Dino, on a given frame
        if (userInput == "up" or keyInputs[pygame.K_UP]) and not self.dino_jump:
            self.dino_duck = False
            self.dino_run = False
            self.dino_jump = True
        elif (userInput == "down" or keyInputs[pygame.K_DOWN]) and not self.dino_jump:
            self.dino_duck = True
            self.dino_run = False
            self.dino_jump = False
        elif not (self.dino_jump or keyInputs[pygame.K_DOWN]) and userInput == "standing":
            self.dino_duck = False
            self.dino_run = True
            self.dino_jump = False
    
    # fuction handle dino's duck
    def duck(self, speed):
        self.image = self.duck_img[self.step_index // 5]
        self.dino_rect = self.image.get_rect()
        self.dino_rect.x = self.X_POS
        self.dino_rect.y = self.Y_POS_DUCK
        self.dino_rect.width -= get_collision_distance_diff(speed)
        self.step_index += 1
        self.duck_sound = True

    # fuction handle dino's running
    def run(self, speed):
        self.image = self.run_img[self.step_index // 5]
        self.dino_rect = self.image.get_rect()
        self.dino_rect.x = self.X_POS
        self.dino_rect.y = self.Y_POS
        self.dino_rect.width -= get_collision_distance_diff(speed)
        self.dino_rect.height -= get_collision_distance_diff(speed)
        self.step_index += 1

    # fuction handle dino's jump
    def jump(self):
        self.image = self.jump_img
        if self.dino_jump:
            self.dino_rect.y -= self.jump_vel * 4
            self.jump_vel -= 0.8
        if self.jump_vel < - self.JUMP_VEL:
            self.dino_jump = False
            self.jump_vel = self.JUMP_VEL
        self.jump_sound = True

    # to draw all the update action on SCREEN
    def draw(self, SCREEN):
        if BORDER:
            pygame.draw.rect(SCREEN, (125, 255, 0), self.dino_rect, 2)
        if self.jump_sound:
            play_jump_music()
            self.jump_sound = False
        if self.duck_sound:
            play_slide_music()
            self.duck_sound = False
        SCREEN.blit(self.image, (self.dino_rect.x, self.dino_rect.y))

# Class Handling Cloud appearance
class Cloud:
    def __init__(self):
        self.x = SCREEN_WIDTH + random.randint(800, 1000)
        self.y = random.randint(50, 100)
        self.image = CLOUD
        self.width = self.image.get_width()

    def update(self):
        self.x -= game_speed
        if self.x < -self.width:
            self.x = SCREEN_WIDTH + random.randint(2500, 3000)
            self.y = random.randint(50, 100)

    def draw(self, SCREEN):
        SCREEN.blit(self.image, (self.x, self.y))

# Class Handling Obstacle appearance
class Obstacle:
    def __init__(self, image, type):
        self.image = image
        self.type = type
        self.rect = self.image[self.type].get_rect()
        self.rect.x = SCREEN_WIDTH

    def update(self):
        self.rect.x -= game_speed
        if self.rect.x < -self.rect.width:
            obstacles.pop()

    def draw(self, SCREEN):
        if BORDER:
            pygame.draw.rect(SCREEN, (125, 255, 100), self.rect, 2)
        SCREEN.blit(self.image[self.type], self.rect)

# Different Types of Trees 
class SmallCactus(Obstacle):
    def __init__(self, image):
        self.type = random.randint(0, 2)
        super().__init__(image, self.type)
        self.rect.y = 325


class LargeCactus(Obstacle):
    def __init__(self, image):
        self.type = random.randint(0, 2)
        super().__init__(image, self.type)
        self.rect.y = 300

# Adding Birds
class Bird(Obstacle):
    def __init__(self, image):
        self.type = 0
        super().__init__(image, self.type)
        self.rect.y = 250
        self.index = 0

    def draw(self, SCREEN):
        if self.index >= 9:
            self.index = 0
        play_dragon_music()
        if BORDER:
            pygame.draw.rect(SCREEN, (125, 255, 100), self.rect, 2)
        SCREEN.blit(self.image[self.index//5], self.rect)
        self.index += 1


#Main Function
def main(SCREEN, BIRDS, TITLE):
    global game_speed, x_pos_bg, y_pos_bg, points, obstacles
    
    #Adding Music
    play_game_music()

    #Initializing useful variables
    run = True
    clock = pygame.time.Clock()
    player = Dinosaur()
    cloud = Cloud()
    game_speed = GAME_SPEED
    x_pos_bg = 0
    y_pos_bg = 380
    points = 0
    font = pygame.font.Font('freesansbold.ttf', 20)
    obstacles = []
    death_count = 0

    # Adding score 
    def score():
        global points, game_speed
        points += 1
        if points % 100 == 0:
            game_speed += 1

        text = font.render("Points: " + str(points), True, (0, 0, 0))
        textRect = text.get_rect()
        textRect.center = (1000, 40)
        SCREEN.blit(text, textRect)

    # Adding background
    def background():
        global x_pos_bg, y_pos_bg
        image_width = BG.get_width()
        SCREEN.blit(BG, (x_pos_bg, y_pos_bg))
        SCREEN.blit(BG, (image_width + x_pos_bg, y_pos_bg))
        if x_pos_bg <= -image_width:
            SCREEN.blit(BG, (image_width + x_pos_bg, y_pos_bg))
            x_pos_bg = 0
        x_pos_bg -= game_speed

    #Looping the Screen
    while run:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False

        SCREEN.fill(SCREEN_COLOR)

        keyInputs = pygame.key.get_pressed()
        player.draw(SCREEN)
        player.update(keyInputs, game_speed)

        if len(obstacles) == 0:
            if random.randint(0, 2) == 0:
                obstacles.append(SmallCactus(SMALL_CACTUS))
            elif random.randint(0, 2) == 1:
                obstacles.append(LargeCactus(LARGE_CACTUS))
            elif random.randint(0, 2) == 2:
                if BIRDS:
                    obstacles.append(Bird(BIRD))

        for obstacle in obstacles:
            obstacle.draw(SCREEN)
            obstacle.update()
            if player.dino_rect.colliderect(obstacle.rect):
                play_dead_music()
                pygame.time.delay(2000)
                death_count += 1
                menu(death_count, SCREEN, BIRDS=BIRDS, TITLE=TITLE)

        background()
        cloud.draw(SCREEN)
        cloud.update()

        score()

        clock.tick(30)
        pygame.display.update()

#Adding Result Screen for the page
def menu(death_count, SCREEN, BIRDS, TITLE):
    global points
    #Adding Music
    play_menu_music()

    run = True
    while run:
        SCREEN.fill(SCREEN_COLOR)
        font = pygame.font.Font('freesansbold.ttf', 30)
        #Adding Title
        text = font.render(TITLE, True, (0, 0, 0))
        textRect = text.get_rect()
        textRect.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2-200)
        SCREEN.blit(text, textRect)
        if death_count == 0: #Inital start
            text = font.render("Press SpaceBar to Start", True, (0, 0, 0))
        elif death_count > 0: #After every Game
            text = font.render("Press SpaceBar to Restart", True, (0, 0, 0))
            score = font.render("Your Score: " + str(points), True, (0, 0, 0))
            scoreRect = score.get_rect()
            scoreRect.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 50)
            SCREEN.blit(score, scoreRect)
        textRect = text.get_rect()
        textRect.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
        SCREEN.blit(text, textRect)
        SCREEN.blit(RUNNING[0], (SCREEN_WIDTH // 2 - 20, SCREEN_HEIGHT // 2 - 140))
        pygame.display.update()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    main(SCREEN, BIRDS=BIRDS, TITLE=TITLE)
    pygame.quit()

IMAGE_SIZE = 200
SCREEN = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
TITLE = 'RUN FOR FUN - JUMPING AND SQUATS'
pygame.display.set_caption(TITLE)

#Running App
menu(death_count=0, SCREEN=SCREEN, BIRDS=True, TITLE=TITLE)
