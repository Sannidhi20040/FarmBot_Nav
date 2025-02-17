import pygame
import sys

# Dummy motor functions (for simulation only)
def motor_forward():
    # For simulation, we simply print or pass.
    pass

def motor_backward():
    pass

def motor_down():
    pass

def motor_stop():
    pass

# --------------------------
# Pygame Initialization & Simulation Setup
# --------------------------
pygame.init()

# Screen settings for simulation
screen_width, screen_height = 800, 400
screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption("Row Navigation Simulation with RFID (Simulation Only)")

# Colors
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
YELLOW = (255, 255, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)

# Bot settings (simulation representation)
bot_size = 15
bot_pos = [50, 125]   # Start position on screen
direction = "FORWARD" # Initial state: "FORWARD", "ALIGN_DOWN", "MOVE_TO_RIGHT", "BACKWARD", "CHECK_PLANT"
current_row_group = 0 # 0 for rows 1 & 2, 1 for rows 3 & 4

# Plant settings
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
    (650, 225)   # Rightmost RFID for rows 3 & 4 (not used here)
]

# Simulation settings
speed = 2
check_distance = 20      # Proximity threshold for plant or RFID detection
check_timer = 0          # Timer for plant checking (in frames)
check_duration = 30      # Frames to "check" a plant

# --------------------------
# Main Simulation Loop (Pygame Only)
# --------------------------
running = True
try:
    while running:
        screen.fill(WHITE)

        # Process events (only handling quit event here)
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
            motor_forward()  # Dummy call (does nothing in simulation)
            bot_pos[0] += speed

            # Check for nearby plant to inspect
            for plant_row in plants[current_row_group * 2: current_row_group * 2 + 2]:
                for plant in plant_row:
                    if abs(bot_pos[0] - plant[0]) < check_distance and plant not in checked_plants:
                        motor_stop()
                        direction = "CHECK_PLANT"
                        current_plant = plant
                        check_timer = 0
                        break

            # When reaching RFID at the end of row 1, begin turning maneuver
            if abs(bot_pos[0] - rfid_positions[0][0]) < check_distance:
                motor_stop()
                direction = "ALIGN_DOWN"

        elif direction == "ALIGN_DOWN":
            # Point-turn maneuver at the end of row 1.
            if bot_pos[1] < 225:
                motor_down()
                bot_pos[1] += speed
            elif bot_pos[0] > 100:
                motor_backward()
                bot_pos[0] -= speed
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

            # Check for nearby plant (scanning right-to-left)
            for plant_row in plants[current_row_group * 2: current_row_group * 2 + 2]:
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
            # Simulate plant inspection.
            motor_stop()
            check_timer += 1
            pygame.draw.line(screen, BLUE, bot_pos, current_plant, 2)
            if check_timer >= check_duration:
                checked_plants.add(current_plant)
                if current_row_group == 0:
                    direction = "FORWARD"
                else:
                    direction = "BACKWARD"
                check_timer = 0

        # --------------------------
        # Draw the bot (simulation representation)
        pygame.draw.rect(screen, BLUE, (*bot_pos, bot_size, bot_size))

        # Update display and delay for frame rate control
        pygame.display.flip()
        pygame.time.delay(30)

except KeyboardInterrupt:
    print("Interrupted! Exiting simulation...")
finally:
    pygame.quit()
    sys.exit()
