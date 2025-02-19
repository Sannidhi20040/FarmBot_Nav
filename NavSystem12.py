import pygame
import RPi.GPIO as GPIO
import sys
import time

# --------------------------
# GPIO Setup and Motor Functions
# --------------------------
GPIO.setmode(GPIO.BOARD)
GPIO.setup(7, GPIO.OUT)   # Left Motor Forward
GPIO.setup(11, GPIO.OUT)  # Left Motor Backward
GPIO.setup(13, GPIO.OUT)  # Right Motor Forward
GPIO.setup(15, GPIO.OUT)  # Right Motor Backward

def move_forward():
    GPIO.output(7, False)
    GPIO.output(11, True)
    GPIO.output(13, True)
    GPIO.output(15, False)

def move_backward():
    GPIO.output(7, True)
    GPIO.output(11, False)
    GPIO.output(13, False)
    GPIO.output(15, True)

def point_turn_left():
    """Spin in place counterclockwise."""
    GPIO.output(7, True)
    GPIO.output(11, False)
    GPIO.output(13, True)
    GPIO.output(15, False)
    time.sleep(1)  # Adjust this duration based on your bot's turning speed
    stop()

def point_turn_right():
    """Spin in place clockwise."""
    GPIO.output(7, False)
    GPIO.output(11, True)
    GPIO.output(13, False)
    GPIO.output(15, True)
    time.sleep(1)  # Adjust this duration based on your bot's turning speed
    stop()

def stop():
    GPIO.output(7, False)
    GPIO.output(11, False)
    GPIO.output(13, False)
    GPIO.output(15, False)

# --------------------------
# Pygame Initialization & Simulation Setup
# --------------------------
pygame.init()
screen_width, screen_height = 800, 400
screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption("Farmbot Navigation Simulation")

WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
YELLOW = (255, 255, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)

# Bot settings
bot_size = 15
bot_pos = [50, 125]  # Start position
direction = "FORWARD"
current_row_group = 0  

# Plant settings
plant_spacing = 100
row_positions = [100, 150, 200, 250]
plants_per_row = 6
plants = [[(100 + i * plant_spacing, row) for i in range(plants_per_row)] for row in row_positions]
checked_plants = set()

# RFID positions
rfid_positions = [
    (650, 125),  # End of row 1
    (50, 225),   # Midpoint RFID after first turn
    (650, 225)   # End of final row 3 & 4
]

# Simulation settings
speed = 2
check_distance = 20
check_timer = 0
check_duration = 30
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

        # Draw plants and RFID markers
        for row in plants:
            for pos in row:
                color = YELLOW if pos in checked_plants else GREEN
                pygame.draw.circle(screen, color, pos, 10)
        for rfid in rfid_positions:
            pygame.draw.rect(screen, RED, (*rfid, 20, 20))

        # --------------------------
        # Navigation State Machine
        # --------------------------
        if direction == "FORWARD" and not turning:
            move_forward()
            bot_pos[0] += speed

            # Check for plant
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

        # --------------------------
        # First Point Turn
        # --------------------------
        elif direction == "POINT_TURN_1":
            point_turn_left()
            direction = "MOVE_DOWN"

        # --------------------------
        # Move Down & Detect RFID
        # --------------------------
        elif direction == "MOVE_DOWN":
            if bot_pos[1] < 225:
                move_backward()
                bot_pos[1] += speed
            else:
                stop()
                direction = "POINT_TURN_2"

        # --------------------------
        # Second Point Turn
        # --------------------------
        elif direction == "POINT_TURN_2":
            point_turn_right()
            direction = "FORWARD_TO_ROW_3"

        # --------------------------
        # Move Forward Again in Row 3 & 4
        # --------------------------
        elif direction == "FORWARD_TO_ROW_3":
            move_forward()
            bot_pos[0] += speed

            # Check for plant
            for plant_row in plants[current_row_group * 2 : current_row_group * 2 + 2]:
                for plant in plant_row:
                    if abs(bot_pos[0] - plant[0]) < check_distance and plant not in checked_plants:
                        stop()
                        direction = "CHECK_PLANT"
                        current_plant = plant
                        check_timer = 0
                        break

            # Check if RFID at end of final row is detected
            if abs(bot_pos[0] - rfid_positions[2][0]) < check_distance:
                stop()
                print("✅ Task Complete: All rows checked. Stopping bot.")
                running = False

        # --------------------------
        # Plant Checking State
        # --------------------------
        elif direction == "CHECK_PLANT":
            check_timer += 1
            if check_timer < check_duration:
                pygame.draw.line(screen, BLUE, bot_pos, current_plant, 2)
            else:
                checked_plants.add(current_plant)
                direction = "FORWARD_TO_ROW_3" if current_row_group == 1 else "FORWARD"
                check_timer = 0

        # Draw the bot
        pygame.draw.rect(screen, BLUE, (*bot_pos, bot_size, bot_size))

        # Update display and frame rate
        pygame.display.flip()
        pygame.time.delay(30)

except KeyboardInterrupt:
    print("🚨 Interrupted! Cleaning up...")
finally:
    GPIO.cleanup()
    pygame.quit()
    sys.exit()
