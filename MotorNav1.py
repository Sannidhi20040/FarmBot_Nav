import pygame
import sys
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
    """
    Motor command for moving "forward" (to the right).
    (Mapping similar to pressing K_RIGHT.)
    """
    GPIO.output(7, True)
    GPIO.output(11, False)
    GPIO.output(13, True)
    GPIO.output(15, False)

def motor_backward():
    """
    Motor command for moving "backward" (to the left).
    (Mapping similar to pressing K_LEFT.)
    """
    GPIO.output(7, False)
    GPIO.output(11, True)
    GPIO.output(13, False)
    GPIO.output(15, True)

def motor_down():
    """
    Motor command for moving "down" (or aligning vertically).
    (Mapping similar to a K_UP or K_DOWN variant, adjust as needed.)
    """
    # For this example we use a configuration different from forward/backward.
    # You might need to fine-tune these outputs for your hardware.
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
pygame.display.set_caption("Row Navigation Simulation with RFID")

# Colors
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
YELLOW = (255, 255, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)

# Bot settings (simulation representation)
bot_size = 15
bot_pos = [50, 125]   # Start position on screen
direction = "FORWARD" # Initial state ("FORWARD", "ALIGN_DOWN", "MOVE_TO_RIGHT", "BACKWARD", "CHECK_PLANT")
current_row_group = 0 # 0 for rows 1 & 2, 1 for rows 3 & 4

# Plant settings
plant_spacing = 100          # Horizontal distance between plants
row_positions = [100, 150, 200, 250]  # Y positions for rows
plants_per_row = 6
plants = [
    [(100 + i * plant_spacing, row) for i in range(plants_per_row)]
    for row in row_positions
]
checked_plants = set()

# RFID settings (simulation waypoints)
rfid_positions = [
    (650, 125),  # RFID marker at end of row 1 (start turning)
    (50, 225),   # RFID marker at left end after U-turn (for rows 3 & 4)
    (650, 225)   # Rightmost RFID for rows 3 & 4 (not used in this example)
]

# Simulation settings
speed = 2
check_distance = 20      # Proximity threshold for plant or RFID detection
check_timer = 0          # Timer for plant checking (in frames)
check_duration = 30      # How long (in frames) to "check" a plant

# --------------------------
# Main Simulation Loop with Integrated Motor Control
# --------------------------
running = True
try:
    while running:
        screen.fill(WHITE)

        # Process events (only handling quit event for this simulation)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # Draw plants
        for row in plants:
            for pos in row:
                color = YELLOW if pos in checked_plants else GREEN
                pygame.draw.circle(screen, color, pos, 10)

        # Draw RFID markers
        for rfid in rfid_positions:
            pygame.draw.rect(screen, RED, (*rfid, 20, 20))

        # --------------------------
        # Autonomous Navigation State Machine
        # --------------------------
        if direction == "FORWARD" and current_row_group == 0:
            # Move right along rows 1 & 2
            motor_forward()  # Activate motor command for moving right
            bot_pos[0] += speed

            # Check if near a plant to check
            for plant_row in plants[current_row_group * 2 : current_row_group * 2 + 2]:
                for plant in plant_row:
                    if abs(bot_pos[0] - plant[0]) < check_distance and plant not in checked_plants:
                        motor_stop()
                        direction = "CHECK_PLANT"
                        current_plant = plant
                        check_timer = 0
                        break

            # When reaching RFID at the end of row group, begin turning maneuver
            if abs(bot_pos[0] - rfid_positions[0][0]) < check_distance:
                motor_stop()
                direction = "ALIGN_DOWN"

        elif direction == "ALIGN_DOWN":
            # This state handles the U-turn maneuver.
            # First, move down (vertical alignment) until reaching y ~225.
            if bot_pos[1] < 225:
                motor_down()  # Use motor_down command to move vertically (adjust as needed)
                bot_pos[1] += speed
            # Then, move right (or adjust horizontally) to position the bot for the next row.
            elif bot_pos[0] < 100:
                motor_forward()
                bot_pos[0] += speed
            else:
                motor_stop()
                direction = "MOVE_TO_RIGHT"

        elif direction == "MOVE_TO_RIGHT":
            # In rows 3 & 4, move right until reaching the rightmost RFID marker.
            motor_forward()
            if bot_pos[0] < rfid_positions[2][0]:
                bot_pos[0] += speed
            else:
                motor_stop()
                direction = "BACKWARD"
                current_row_group = 1

        elif direction == "BACKWARD" and current_row_group == 1:
            # Move left along rows 3 & 4.
            motor_backward()
            bot_pos[0] -= speed

            # Check if near a plant (scanning from right to left)
            for plant_row in plants[current_row_group * 2 : current_row_group * 2 + 2]:
                for plant in plant_row[::-1]:
                    if abs(bot_pos[0] - plant[0]) < check_distance and plant not in checked_plants:
                        motor_stop()
                        direction = "CHECK_PLANT"
                        current_plant = plant
                        check_timer = 0
                        break

            # When reaching the left RFID marker, end simulation.
            if abs(bot_pos[0] - rfid_positions[1][0]) < check_distance:
                motor_stop()
                print("Simulation complete. All rows checked.")
                running = False

        elif direction == "CHECK_PLANT":
            # In the CHECK_PLANT state, stop movement and simulate plant inspection.
            motor_stop()
            check_timer += 1
            # Optionally, draw a line between bot and plant to show the checking process.
            pygame.draw.line(screen, BLUE, bot_pos, current_plant, 2)
            if check_timer >= check_duration:
                checked_plants.add(current_plant)
                # Resume movement based on row group.
                if current_row_group == 0:
                    direction = "FORWARD"
                else:
                    direction = "BACKWARD"
                check_timer = 0

        # --------------------------
        # Draw the bot (simulation representation)
        pygame.draw.rect(screen, BLUE, (*bot_pos, bot_size, bot_size))

        # Update the display and delay for frame rate control
        pygame.display.flip()
        pygame.time.delay(30)

except KeyboardInterrupt:
    print("Interrupted! Exiting simulation...")
finally:
    motor_stop()
    GPIO.cleanup()
    pygame.quit()
    sys.exit()
