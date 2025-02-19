import pygame
import RPi.GPIO as GPIO
import sys
import time

# --------------------------
# GPIO Setup and Motor Functions
# --------------------------
GPIO.setmode(GPIO.BOARD)
# Setup GPIO output pins (adjust these pins as per your wiring)
GPIO.setup(7, GPIO.OUT)   # Left Motor Forward / Backward control
GPIO.setup(11, GPIO.OUT)  # Left Motor Backward / Forward control
GPIO.setup(13, GPIO.OUT)  # Right Motor Forward / Backward control
GPIO.setup(15, GPIO.OUT)  # Right Motor Backward / Forward control

def move_forward():
    # Moves bot forward (to the right)
    GPIO.output(7, False)
    GPIO.output(11, True)
    GPIO.output(13, True)
    GPIO.output(15, False)
    print("Moving Forward")

def move_backward():
    # Moves bot backward (to the left)
    GPIO.output(7, True)
    GPIO.output(11, False)
    GPIO.output(13, False)
    GPIO.output(15, True)
    print("Moving Backward")

def point_turn_left():
    """Performs a point turn (spin in place) to the left (counterclockwise)."""
    GPIO.output(7, True)
    GPIO.output(11, False)
    GPIO.output(13, True)
    GPIO.output(15, False)
    time.sleep(1)  # Adjust this delay for the desired turn angle
    print("Turning left")
    stop()

def point_turn_right():
    """Performs a point turn (spin in place) to the right (clockwise)."""
    GPIO.output(7, False)
    GPIO.output(11, True)
    GPIO.output(13, False)
    GPIO.output(15, True)
    time.sleep(1)  # Adjust this delay for the desired turn angle
    print("Turning Right")
    stop()

def stop():
    GPIO.output(7, False)
    GPIO.output(11, False)
    GPIO.output(13, False)
    GPIO.output(15, False)
    print("Halt")

# --------------------------
# Pygame Initialization & Simulation Setup
# --------------------------
pygame.init()
screen_width, screen_height = 800, 400
screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption("Farmbot Navigation Simulation")

# Colors
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
YELLOW = (255, 255, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)

# Bot settings
bot_size = 15
bot_pos = [50, 125]  # Start position
direction = "FORWARD"  # Initial state: "FORWARD", "CHECK_PLANT", "POINT_TURN_1", "MOVE_DOWN", "POINT_TURN_2", "FORWARD_TO_ROW_3"
current_row_group = 0  # 0 for rows 1 & 2; will be set to 1 after turn

# Plant settings
plant_spacing = 100  # Distance between plants
row_positions = [100, 150, 200, 250]  # Y positions for rows
plants_per_row = 6
plants = [[(100 + i * plant_spacing, row) for i in range(plants_per_row)] for row in row_positions]
checked_plants = set()

# RFID settings
rfid_positions = [
    (650, 125),  # RFID marker at end of row 1 (first RFID)
    (50, 225),   # RFID marker used after turning (midpoint RFID)
    (650, 225)   # RFID marker at end of rows 3 & 4 (final RFID)
]

# Simulation settings
speed = 2
check_distance = 20  # Distance threshold for plant or RFID detection
check_timer = 0      # Timer for plant checking (in frames)
check_duration = 30  # Frames to "check" a plant
turning = False

# --------------------------
# Main Simulation Loop
# --------------------------
running = True
try:
    while running:
        screen.fill(WHITE)
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
        # Navigation State Machine
        # --------------------------
        # 1. Moving forward in first row group (rows 1 & 2)
        if direction == "FORWARD" and not turning:
            move_forward()
            bot_pos[0] += speed

            # Check for plant in current row group (rows 1 & 2)
            for plant_row in plants[current_row_group * 2 : current_row_group * 2 + 2]:
                for plant in plant_row:
                    if abs(bot_pos[0] - plant[0]) < check_distance and plant not in checked_plants:
                        stop()
                        direction = "CHECK_PLANT"
                        current_plant = plant
                        check_timer = 0
                        break

            # Check if RFID at end of row 1 is detected
            if current_row_group == 0 and abs(bot_pos[0] - rfid_positions[0][0]) < check_distance:
                stop()
                turning = True
                direction = "POINT_TURN_1"

        # 2. First Point Turn (at end of row 1)
        elif direction == "POINT_TURN_1":
            point_turn_left()
            direction = "MOVE_DOWN"

        # 3. Moving Down (to align with the next row)
        elif direction == "MOVE_DOWN":
            # Move down until reaching y = 225
            if bot_pos[1] < 225:
                # Using move_backward() here to simulate vertical adjustment
                move_backward()
                bot_pos[1] += speed
            else:
                stop()
                direction = "POINT_TURN_2"

        # 4. Second Point Turn (to align with path for rows 3 & 4)
        elif direction == "POINT_TURN_2":
            point_turn_right()
            # Set row group to 1 so that we are in rows 3 & 4 now
            current_row_group = 1
            direction = "FORWARD_TO_ROW_3"

        # 5. Moving forward along rows 3 & 4
        elif direction == "FORWARD_TO_ROW_3":
            move_forward()
            bot_pos[0] += speed

            # Check for plants in row group 1 (rows 3 & 4)
            for plant_row in plants[current_row_group * 2 : current_row_group * 2 + 2]:
                for plant in plant_row:
                    if abs(bot_pos[0] - plant[0]) < check_distance and plant not in checked_plants:
                        stop()
                        direction = "CHECK_PLANT"
                        current_plant = plant
                        check_timer = 0
                        break

            # If the bot has reached (or passed) the final RFID marker (x >= 650), finish
            if bot_pos[0] >= rfid_positions[2][0]:
                stop()
                print("✅ Task Complete: All rows checked. Stopping bot.")
                running = False

        # 6. Plant Checking State (common for both row groups)
        elif direction == "CHECK_PLANT":
            stop()
            check_timer += 1
            pygame.draw.line(screen, BLUE, bot_pos, current_plant, 2)
            if check_timer >= check_duration:
                checked_plants.add(current_plant)
                # Resume movement: if we are in row group 1, resume FORWARD_TO_ROW_3; else FORWARD
                if current_row_group == 1:
                    direction = "FORWARD_TO_ROW_3"
                else:
                    direction = "FORWARD"
                check_timer = 0

        # --------------------------
        # Draw the Bot
        # --------------------------
        pygame.draw.rect(screen, BLUE, (*bot_pos, bot_size, bot_size))

        pygame.display.flip()
        pygame.time.delay(30)

except KeyboardInterrupt:
    print("🚨 Interrupted! Cleaning up...")
finally:
    GPIO.cleanup()
    pygame.quit()
    sys.exit()
