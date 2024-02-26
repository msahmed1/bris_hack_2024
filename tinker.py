import tkinter as tk
from tkinter import Button
import threading
from new_main import menu as basic_dinosaur
import pygame
from PIL import ImageTk, Image, ImageFilter, ImageEnhance
import os
import webbrowser
import pygame


def play_dead_music():
    pygame.mixer.music.load(os.path.join("assets/Audio", "gamemenu.mp3"))
    pygame.mixer.music.play(-1)  # -1 makes the music loop indefinitely

play_dead_music()

IMAGE_SIZE = 200
SCREEN_HEIGHT = 600
SCREEN_WIDTH = 1100
GRID = False

def load_and_resize_image(image_path, width, height):
    if width:    
        original_image = Image.open(image_path)
        resized_image = original_image.resize((width, height))
        return ImageTk.PhotoImage(resized_image)
    else:
        original_image = Image.open(image_path)
        enhancer = ImageEnhance.Brightness(original_image)
        enhanced_image = enhancer.enhance(0.5)
        return ImageTk.PhotoImage(enhanced_image)

def run_pygame1():
    pygame.init()
    pygame.mixer.init()
    TITLE = 'RUN FOR FUN - JUMPING AND SQUATS'
    pygame.display.set_caption(TITLE)
    SCREEN = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    basic_dinosaur(death_count=0, SCREEN=SCREEN, BIRDS=True, TITLE=TITLE)

def on_button_click1():
    pygame_thread = threading.Thread(target=run_pygame1)
    pygame_thread.start()

def run_pygame2():
    pygame.init()
    pygame.mixer.init()
    TITLE = 'RUN FOR FUN - JUMPING'
    pygame.display.set_caption(TITLE)
    SCREEN = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    basic_dinosaur(death_count=0, SCREEN=SCREEN, BIRDS=False, TITLE=TITLE)

def on_button_click2():
    pygame_thread = threading.Thread(target=run_pygame2)
    pygame_thread.start()

def run_pygame4():
    webbrowser.open("http://127.0.0.1:8053/")

def on_button_click4():
    pygame_thread = threading.Thread(target=run_pygame4)
    pygame_thread.start()

# Create the main Tkinter window
root = tk.Tk()
root.title("Game Selection Menu")
root.geometry(f"{SCREEN_WIDTH}x{SCREEN_HEIGHT}")


x_position, y_position = 100, 50
root.geometry(f"+{x_position}+{y_position}")

canvas = tk.Canvas(root, width=SCREEN_WIDTH, height=SCREEN_HEIGHT, highlightthickness=0)
canvas.pack()

background_image=load_and_resize_image("assets/image/background.jpg", None, None)
# background_label = tk.Label(root, image=background_image)
# background_label.place(x=0, y=0, relwidth=1, relheight=1)
# img = tk.PhotoImage(file="images/background.png")
canvas.create_image(0,0,anchor=tk.NW,image=background_image)

canvas.create_text(550, 50, text="Welcome To Community", font="calibri 40 bold", fill="white")



img1 = load_and_resize_image("assets/image/funforrun.jpg", IMAGE_SIZE, IMAGE_SIZE)
panel1 = tk.Canvas(root, width=IMAGE_SIZE, height=IMAGE_SIZE, highlightthickness=0)
panel1.create_image(0,0,anchor=tk.NW,image=img1)
panel1.place(x=100, y=200)

# Create a button
button = Button(root, text="Jumping and Squats", command=on_button_click1, height=1, width=20,
                                background="#353839",
                                foreground="white",
                                activeforeground="white",
                                activebackground="#0E1111",
)
button.place(x=125, y=400)


img2 = load_and_resize_image("assets/image/jumping.jpg", IMAGE_SIZE, IMAGE_SIZE)
panel2 = tk.Canvas(root, width=IMAGE_SIZE, height=IMAGE_SIZE, highlightthickness=0)
panel2.create_image(0,0,anchor=tk.NW,image=img2)
panel2.place(x=450, y=200)

# Create a button
button2 = Button(root, text="Jumping", command=on_button_click2, height=1, width=20,
                                background="#353839",
                                foreground="white",
                                activeforeground="white",
                                activebackground="#0E1111",
)
button2.place(x=475, y=400)

img3 = load_and_resize_image("assets/image/squats.jpg", IMAGE_SIZE, IMAGE_SIZE)
panel3 = tk.Canvas(root, width=IMAGE_SIZE, height=IMAGE_SIZE, highlightthickness=0)
panel3.create_image(0,0,anchor=tk.NW,image=img3)
panel3.place(x=800, y=200)

# Create a button
button3 = Button(root, text="Squats", command=on_button_click2, height=1, width=20,
                                background="#353839",
                                foreground="white",
                                activeforeground="white",
                                activebackground="#0E1111",
)
button3.place(x=825, y=400)

button4 = Button(root, text="Leader Board", command=on_button_click4, height=1, width=20,
                                background="#353839",
                                foreground="white",
                                activeforeground="white",
                                activebackground="#0E1111",
)
button4.place(x=900, y=45)

# Start the Tkinter event loop
root.mainloop()
