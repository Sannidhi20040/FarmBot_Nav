import pygame
import sys

# Initialize Pygame
pygame.init()

# Screen settings
screen_width, screen_height = 800, 400
screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption("Row Navigation Simulation with RFID")

# Colors
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
YELLOW = (255, 255, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)

# Bot settings
bot_size = 15
bot_pos = [50, 125]  # Start position
direction = "FORWARD"  # Initial movement direction
current_row_group = 0  # 0 for rows 1 & 2, 1 for rows 3 & 4

# Plant settings
plant_spacing = 100  # Distance between plants
row_positions = [100, 150, 200, 250]  # Y-coordinates of rows
plants_per_row = 6
plants = [
    [(100 + i * plant_spacing, row) for i in range(plants_per_row)]
    for row in row_positions
]
checked_plants = set()

# RFID settings
rfid_positions = [
    (650, 125),  # End of row 1
    (50, 225),   # Start of row 3 (after U-turn)
    (650, 225)   # End of row 4
]

# Simulation settings
speed = 2
check_distance = 20  # Proximity to check plants
turning = False  # Flag to handle turning
check_timer = 0  # Timer for plant checking
check_duration = 30  # Duration for checking a plant (in frames)

# Main simulation loop
running = True
while running:
    screen.fill(WHITE)

    # Event handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Draw plants
    for row in plants:
        for pos in row:
            color = YELLOW if pos in checked_plants else GREEN
            pygame.draw.circle(screen, color, pos, 10)

    # Draw RFIDs
    for rfid in rfid_positions:
        pygame.draw.rect(screen, RED, (*rfid, 20, 20))

    # Bot movement logic for rows 1 & 2 (left to right)
    if direction == "FORWARD" and not turning:
        bot_pos[0] += speed

        # Check if bot is near a plant
        for plant_row in plants[current_row_group * 2 : current_row_group * 2 + 2]:
            for plant in plant_row:
                if abs(bot_pos[0] - plant[0]) < check_distance and plant not in checked_plants:
                    direction = "CHECK_PLANT"
                    current_plant = plant
                    check_timer = 0
                    break

        # Check if bot reached the RFID at the end of the row group
        if current_row_group == 0 and abs(bot_pos[0] - rfid_positions[0][0]) < check_distance:
            turning = True
            direction = "ALIGN_DOWN"

    # Checking plants
    elif direction == "CHECK_PLANT":
        check_timer += 1
        if check_timer < check_duration:
            pygame.draw.line(screen, BLUE, bot_pos, current_plant, 2)
        else:
            checked_plants.add(current_plant)
            if current_row_group == 0:
                direction = "FORWARD"
            else:
                direction = "BACKWARD"
            check_timer = 0

    # Moving down after first row group
    elif direction == "ALIGN_DOWN":
        if bot_pos[1] < 225:
            bot_pos[1] += speed
        else:
            direction = "MOVE_TO_RIGHT"

    # Moving to rightmost position for rows 3 & 4
    elif direction == "MOVE_TO_RIGHT":
        if bot_pos[0] < rfid_positions[2][0]:
            bot_pos[0] += speed
        else:
            turning = False
            direction = "BACKWARD"
            current_row_group = 1

    # Moving left in rows 3 & 4
    elif direction == "BACKWARD":
        bot_pos[0] -= speed

        # Check if bot is near a plant
        for plant_row in plants[current_row_group * 2 : current_row_group * 2 + 2]:
            for plant in plant_row[::-1]:  # Check plants right to left
                if abs(bot_pos[0] - plant[0]) < check_distance and plant not in checked_plants:
                    direction = "CHECK_PLANT"
                    current_plant = plant
                    check_timer = 0
                    break

        # Stop at leftmost RFID
        if abs(bot_pos[0] - rfid_positions[1][0]) < check_distance:
            print("Simulation complete. All rows checked.")
            running = False

    # Draw the bot
    pygame.draw.rect(screen, BLUE, (*bot_pos, bot_size, bot_size))

    # Update display and delay
    pygame.display.flip()
    pygame.time.delay(30)

pygame.quit()
sys.exit()
