import pygame
import RPi.GPIO as GPIO
import sys
import time

# --------------------------
# GPIO Setup and Motor Functions
# --------------------------
GPIO.setmode(GPIO.BOARD)
# Setup GPIO output pins (adjust these pins as per your wiring)
GPIO.setup(7, GPIO.OUT)    # Left Motor (controls forward/backward)
GPIO.setup(11, GPIO.OUT)   # Left Motor (controls backward/forward)
GPIO.setup(13, GPIO.OUT)   # Right Motor (controls forward/backward)
GPIO.setup(15, GPIO.OUT)   # Right Motor (controls backward/forward)

def move_forward():
    # Moves bot forward (to the right)
    GPIO.output(7, False)
    GPIO.output(11, True)
    GPIO.output(13, True)
    GPIO.output(15, False)
    print("Moving forward")

def move_backward():
    # Moves bot backward (to the left)
    GPIO.output(7, True)
    GPIO.output(11, False)
    GPIO.output(13, False)
    GPIO.output(15, True)
    print("Moving Backward")

def point_turn_left():
    """Perform a point turn to the left (counterclockwise)."""
    GPIO.output(7, True)
    GPIO.output(11, False)
    GPIO.output(13, True)
    GPIO.output(15, False)
    print("Turning left")
    time.sleep(1)  # Adjust duration for desired turn angle
    stop()

def point_turn_right():
    """Perform a point turn to the right (clockwise)."""
    GPIO.output(7, False)
    GPIO.output(11, True)
    GPIO.output(13, False)
    GPIO.output(15, True)
    print("Turning left")
    time.sleep(1)  # Adjust duration for desired turn angle
    stop()

def point_turn_180():
    """Perform a 180° turn by doing two point turns."""
    point_turn_left()
    point_turn_left()
    print("Turning left")

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
bot_pos = [50, 125]  # Starting position in row group 0 (rows 1 & 2)
# Our state variable will drive the behavior:
# "FORWARD_ROW1", "CHECK_PLANT", "POINT_TURN_1", "MOVE_DIAGONAL", "DETECT_RFID2",
# "POINT_TURN_180", "FORWARD_ROW2"
state = "FORWARD_ROW1"
# current_row_group: 0 for rows 1 & 2; 1 for rows 3 & 4
current_row_group = 0

# Plant settings
plant_spacing = 100          # Horizontal distance between plants
row_positions = [100, 150, 200, 250]  # Y-coordinates for rows
plants_per_row = 6
plants = [
    [(100 + i * plant_spacing, row) for i in range(plants_per_row)]
    for row in row_positions
]
checked_plants = set()

# RFID settings (simulation waypoints)
rfid_positions = [
    (650, 125),  # RFID1: End of row 1 (row group 0)
    (50, 225),   # RFID2: On the left after diagonal move (start of row group 1)
    (650, 225)   # RFID3: End of row 4 (final RFID)
]

# Simulation settings
speed = 2
check_distance = 20      # Proximity threshold for plant or RFID detection
check_timer = 0          # Timer for plant checking (in frames)
check_duration = 30      # Duration (frames) to "check" a plant

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

        # Draw plants (green if unchecked, yellow if checked)
        for row in plants:
            for pos in row:
                color = YELLOW if pos in checked_plants else GREEN
                pygame.draw.circle(screen, color, pos, 10)

        # Draw RFID markers
        for rfid in rfid_positions:
            pygame.draw.rect(screen, RED, (*rfid, 20, 20))

        # ---------------
        # State Machine
        # ---------------

        # STATE 1: Move forward along row group 0 (rows 1 & 2)
        if state == "FORWARD_ROW1":
            move_forward()
            bot_pos[0] += speed

            # Check for plants
            for plant_row in plants[current_row_group * 2 : current_row_group * 2 + 2]:
                for plant in plant_row:
                    if abs(bot_pos[0] - plant[0]) < check_distance and plant not in checked_plants:
                        stop()
                        state = "CHECK_PLANT"
                        current_plant = plant
                        check_timer = 0
                        break

            # When RFID1 is detected (x near 650)...
            if abs(bot_pos[0] - rfid_positions[0][0]) < check_distance:
                stop()
                # Transition to point turn to prepare for diagonal movement
                state = "POINT_TURN_1"

        # STATE 2: First point turn at RFID1
        elif state == "POINT_TURN_1":
            point_turn_left()  # Turn 90° left to face downward/left
            state = "MOVE_DIAGONAL"

        # STATE 3: Move Diagonally (down and left) until RFID2 is detected
        elif state == "MOVE_DIAGONAL":
            # Simulate diagonal movement: update x and y manually.
            # For a true bot, you would adjust individual motor speeds.
            bot_pos[0] -= speed  # move left
            bot_pos[1] += speed  # move down
            # (Optionally, you might send a combined motor command if available.)
            # Check if we are near RFID2:
            if (abs(bot_pos[0] - rfid_positions[1][0]) < check_distance and
                abs(bot_pos[1] - rfid_positions[1][1]) < check_distance):
                stop()
                state = "POINT_TURN_180"

        # STATE 4: Perform a 180° turn so the bot now faces right (for row group 1)
        elif state == "POINT_TURN_180":
            point_turn_180()
            # Now the bot is facing right. Switch row group to 1.
            current_row_group = 1
            state = "FORWARD_ROW2"

        # STATE 5: Move forward along row group 1 (rows 3 & 4)
        elif state == "FORWARD_ROW2":
            move_forward()
            bot_pos[0] += speed

            # Check for plants in row group 1
            for plant_row in plants[current_row_group * 2 : current_row_group * 2 + 2]:
                for plant in plant_row:
                    if abs(bot_pos[0] - plant[0]) < check_distance and plant not in checked_plants:
                        stop()
                        state = "CHECK_PLANT"
                        current_plant = plant
                        check_timer = 0
                        break

            # When the bot reaches or passes RFID3 (x >= 650)...
            if bot_pos[0] >= rfid_positions[2][0]:
                stop()
                print("✅ Task Complete: All rows checked. Stopping bot.")
                running = False

        # STATE 6: Check Plant State (common to both row groups)
        elif state == "CHECK_PLANT":
            stop()
            check_timer += 1
            pygame.draw.line(screen, BLUE, bot_pos, current_plant, 2)
            if check_timer >= check_duration:
                checked_plants.add(current_plant)
                # Resume movement based on row group
                if current_row_group == 1:
                    state = "FORWARD_ROW2"
                else:
                    state = "FORWARD_ROW1"
                check_timer = 0

        # ---------------
        # Draw the bot (as a blue square)
        pygame.draw.rect(screen, BLUE, (*bot_pos, bot_size, bot_size))

        pygame.display.flip()
        pygame.time.delay(30)

except KeyboardInterrupt:
    print("🚨 Interrupted! Cleaning up...")
finally:
    GPIO.cleanup()
    pygame.quit()
    sys.exit()
