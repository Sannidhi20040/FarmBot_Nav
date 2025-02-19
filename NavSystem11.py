import pygame
import sys
import math
import RPi.GPIO as GPIO
import os

# --------------------------
# GPIO Setup and Motor Functions
# --------------------------
GPIO.setmode(GPIO.BOARD)
# Setup GPIO output pins (adjust these pins as per your wiring)
GPIO.setup(7, GPIO.OUT)
GPIO.setup(11, GPIO.OUT)
GPIO.setup(13, GPIO.OUT)
GPIO.setup(15, GPIO.OUT)

def motor_forward():
    """Motor command for moving forward (to the right)."""
    GPIO.output(7, True)
    GPIO.output(11, False)
    GPIO.output(13, True)
    GPIO.output(15, False)

def motor_backward():
    """Motor command for moving backward (to the left)."""
    GPIO.output(7, False)
    GPIO.output(11, True)
    GPIO.output(13, False)
    GPIO.output(15, True)

def motor_down():
    """Motor command for moving down (vertical alignment)."""
    # Adjust these outputs as needed for your hardware.
    GPIO.output(7, False)
    GPIO.output(11, True)
    GPIO.output(13, True)
    GPIO.output(15, False)

def motor_stop():
    """Stop all motor outputs."""
    GPIO.output(7, False)
    GPIO.output(11, False)
    GPIO.output(13, False)
    GPIO.output(15, False)

# --------------------------
# Pygame Initialization & Simulation Setup
# --------------------------
pygame.init()

# Screen settings for simulation
screen_width, screen_height = 800, 400
screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption("Farmbot Navigation Simulation (Integrated)")

# Colors
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
YELLOW = (255, 255, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)

# Bot (farmbot) simulation settings
bot_size = 15
bot_pos = [50, 125]  # Starting position on screen
direction = "FORWARD"  # Autonomous states: "FORWARD", "ALIGN_DOWN", "MOVE_TO_RIGHT", "BACKWARD", "CHECK_PLANT"
current_row_group = 0  # 0 for rows 1 & 2; 1 for rows 3 & 4

# Plant settings (positions for visual simulation)
plant_spacing = 100                # Horizontal distance between plants
row_positions = [100, 150, 200, 250]  # Y positions for rows
plants_per_row = 6
plants = [
    [(100 + i * plant_spacing, row) for i in range(plants_per_row)]
    for row in row_positions
]
checked_plants = set()

# RFID settings (simulation waypoints)
rfid_positions = [
    (650, 125),  # RFID marker at end of row 1 (for turning)
    (50, 225),   # RFID marker at left end after turn (for rows 3 & 4)
    (650, 225)   # Rightmost RFID for rows 3 & 4 (not used in this example)
]

# Simulation parameters
speed = 2
check_distance = 20      # Distance threshold for plant/RFID detection
check_timer = 0          # Timer for plant checking (in frames)
check_duration = 30      # Frames to "check" a plant

# Manual override flag; if True, manual control (via arrow keys) is active.
manual_override = False

clock = pygame.time.Clock()

# --------------------------
# Main Loop: Integrated Autonomous + Manual Override
# --------------------------
try:
    while True:
        screen.fill(WHITE)

        # Process events (manual override toggling and quit events)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            # Toggle manual override mode when pressing 'm'
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_m:
                    manual_override = not manual_override
                # Manual override: Quit if 'q' is pressed.
                if manual_override and event.key == pygame.K_q:
                    pygame.quit()
                    sys.exit()

        # --------------------------
        # Manual Override Mode
        # --------------------------
        if manual_override:
            keys = pygame.key.get_pressed()
            # Direct motor commands (and optionally update bot_pos for simulation view)
            if keys[pygame.K_RIGHT]:
                motor_forward()
                bot_pos[0] += speed
            elif keys[pygame.K_LEFT]:
                motor_backward()
                bot_pos[0] -= speed
            elif keys[pygame.K_UP]:
                # For manual vertical control, use motor_down as an example
                motor_down()
                bot_pos[1] -= speed  # Move up
            elif keys[pygame.K_DOWN]:
                motor_down()
                bot_pos[1] += speed  # Move down
            else:
                motor_stop()
        # --------------------------
        # Autonomous Navigation Mode
        # --------------------------
        else:
            # Autonomous state machine for navigation
            if direction == "FORWARD" and current_row_group == 0:
                motor_forward()
                bot_pos[0] += speed

                # Check if near a plant to inspect
                for plant_row in plants[current_row_group * 2 : current_row_group * 2 + 2]:
                    for plant in plant_row:
                        if abs(bot_pos[0] - plant[0]) < check_distance and plant not in checked_plants:
                            motor_stop()
                            direction = "CHECK_PLANT"
                            current_plant = plant
                            check_timer = 0
                            break

                # When reaching RFID at the end of row 1, start turning maneuver
                if abs(bot_pos[0] - rfid_positions[0][0]) < check_distance:
                    motor_stop()
                    direction = "ALIGN_DOWN"

            elif direction == "ALIGN_DOWN":
                # Turn maneuver: first, move down until y ~225.
                if bot_pos[1] < 225:
                    motor_down()
                    bot_pos[1] += speed
                # Then, adjust horizontally by moving left (simulate point-turn)
                elif bot_pos[0] > 100:
                    motor_backward()
                    bot_pos[0] -= speed
                else:
                    motor_stop()
                    direction = "MOVE_TO_RIGHT"

            elif direction == "MOVE_TO_RIGHT":
                # Move right in rows 3 & 4
                motor_forward()
                if bot_pos[0] < rfid_positions[2][0]:
                    bot_pos[0] += speed
                else:
                    motor_stop()
                    direction = "BACKWARD"
                    current_row_group = 1

            elif direction == "BACKWARD" and current_row_group == 1:
                motor_backward()
                bot_pos[0] -= speed

                # Check for nearby plant (scanning right-to-left)
                for plant_row in plants[current_row_group * 2 : current_row_group * 2 + 2]:
                    for plant in plant_row[::-1]:
                        if abs(bot_pos[0] - plant[0]) < check_distance and plant not in checked_plants:
                            motor_stop()
                            direction = "CHECK_PLANT"
                            current_plant = plant
                            check_timer = 0
                            break

                # End simulation when reaching left RFID marker
                if abs(bot_pos[0] - rfid_positions[1][0]) < check_distance:
                    motor_stop()
                    print("Simulation complete. All rows checked.")
                    sys.exit()

            elif direction == "CHECK_PLANT":
                motor_stop()
                check_timer += 1
                # Optionally draw a line to indicate checking
                pygame.draw.line(screen, BLUE, bot_pos, current_plant, 2)
                if check_timer >= check_duration:
                    checked_plants.add(current_plant)
                    if current_row_group == 0:
                        direction = "FORWARD"
                    else:
                        direction = "BACKWARD"
                    check_timer = 0

        # --------------------------
        # Drawing: Plants, RFID markers, and Bot
        # --------------------------
        for row in plants:
            for pos in row:
                color = YELLOW if pos in checked_plants else GREEN
                pygame.draw.circle(screen, color, pos, 10)

        for rfid in rfid_positions:
            pygame.draw.rect(screen, RED, (*rfid, 20, 20))

        pygame.draw.rect(screen, BLUE, (*bot_pos, bot_size, bot_size))

        # Display manual override status
        font = pygame.font.SysFont(None, 24)
        mode_text = "Manual Mode" if manual_override else "Autonomous Mode"
        text_surface = font.render(mode_text, True, (0, 0, 0))
        screen.blit(text_surface, (10, 10))

        pygame.display.flip()
        clock.tick(60)

except KeyboardInterrupt:
    print("Interrupted! Exiting simulation...")
finally:
    motor_stop()
    GPIO.cleanup()
    pygame.quit()
    sys.exit()
