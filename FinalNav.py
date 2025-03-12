import pygame
import sys
import time

# --------------------------
# Motor Control Functions (Placeholder implementations)
# --------------------------
def move_forward():
    pass  # Implement GPIO logic here

def move_backward():
    pass  # Implement GPIO logic here

def point_turn_left():
    pass
    time.sleep(1)
    stop()

def point_turn_right():
    pass
    time.sleep(1)
    stop()

def turn_180():
    pass
    time.sleep(2)
    stop()

def stop():
    pass

# --------------------------
# Pygame Initialization & Simulation Setup
# --------------------------
pygame.init()
screen_width, screen_height = 800, 400
screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption("Farmbot Navigation Simulation")

WHITE = (255,255,255)
GREEN = (0,255,0)
YELLOW = (255,255,0)
RED = (255,0,0)
BLUE = (0,0,255)

bot_size = 15
bot_pos = [50,125]
direction = "FORWARD_ROWS_1_2"
current_row_group = 0

plant_spacing = 100
row_positions = [100,150,200,250]
plants_per_row = 6
plants = [[(100 + i*plant_spacing,row) for i in range(plants_per_row)] for row in row_positions]
checked_plants = set()

rfid_positions = [
    (650,125),   # RFID 1 (end of rows 1-2)
    (650,225),   # RFID 2 (right side between rows 3-4)
    (50,225)     # RFID 3 (left side between rows 3-4)
]

speed = 2
check_distance = 20
check_timer = 0
check_duration =30

bot_path=[]

current_plant=None
plant_check_state=None
turning_to_rows_3_and_4=False

running=True

try:
    while running:
        screen.fill(WHITE)

        for event in pygame.event.get():
            if event.type==pygame.QUIT:
                running=False

        # Draw plants and RFID markers
        for row in plants:
            for pos in row:
                color=YELLOW if pos in checked_plants else GREEN
                pygame.draw.circle(screen,color,pos,10)

        for rfid in rfid_positions:
            pygame.draw.rect(screen,RED,(*rfid,20,20))

        bot_path.append(tuple(bot_pos))
        if len(bot_path)>2:
            pygame.draw.lines(screen,(200,200,200),False,bot_path)

        # Navigation Logic:
        if direction=="FORWARD_ROWS_1_2":
            move_forward()
            bot_pos[0]+=speed

            # Check plants in rows 1-2
            for plant_row in plants[0:2]:
                for plant in plant_row:
                    if abs(bot_pos[0]-plant[0])<check_distance and plant not in checked_plants:
                        stop()
                        current_plant=plant
                        plant_check_state="TURN_LEFT"
                        check_timer=0
                        direction="CHECK_PLANT"
                        next_direction="FORWARD_ROWS_1_2"
                        break

            # Detect RFID 1 at end of rows 1-2 path
            if abs(bot_pos[0]-rfid_positions[0][0])<check_distance:
                stop()
                direction="POINT_TURN_LEFT"

        elif direction=="POINT_TURN_LEFT":
            point_turn_left()
            direction="MOVE_DOWN_TO_RFID_2"

        elif direction=="MOVE_DOWN_TO_RFID_2":
            move_backward()
            bot_pos[1]+=speed

            if abs(bot_pos[1]-rfid_positions[1][1])<check_distance:
                stop()
                direction="POINT_TURN_RIGHT_TO_ROWS_3_4"

        elif direction=="POINT_TURN_RIGHT_TO_ROWS_3_4":
            point_turn_right()
            turning_to_rows_3_and_4=True
            direction="FORWARD_ROWS_3_4"

        elif direction=="FORWARD_ROWS_3_4":
            move_forward()
            bot_pos[0]-=speed

            # Check plants in rows 3-4 while moving towards RFID 3
            for plant_row in plants[2:4]:
                for plant in plant_row:
                    if abs(bot_pos[0]-plant[0])<check_distance and plant not in checked_plants:
                        stop()
                        current_plant=plant
                        plant_check_state="TURN_LEFT"
                        check_timer=0
                        direction="CHECK_PLANT"
                        next_direction="FORWARD_ROWS_3_4"
                        break

            # Detect RFID 3 at end of rows 3-4 path to stop finally
            if abs(bot_pos[0]-rfid_positions[2][0])<check_distance:
                stop()
                print("✅ Task Complete: All rows checked.")
                running=False

        elif direction=="CHECK_PLANT":
            check_timer+=1

            if plant_check_state=="TURN_LEFT":
                point_turn_left()
                plant_check_state="CHECK_LEFT"

            elif plant_check_state=="CHECK_LEFT":
                pygame.draw.line(screen,BLUE,bot_pos,current_plant)
                if check_timer>=check_duration:
                    checked_plants.add(current_plant)
                    check_timer=0
                    point_turn_right() # return to center from left side
                    plant_check_state="TURN_RIGHT"

            elif plant_check_state=="TURN_RIGHT":
                point_turn_right() # now facing right side from center position
                plant_check_state="CHECK_RIGHT"

            elif plant_check_state=="CHECK_RIGHT":
                pygame.draw.line(screen,BLUE,bot_pos,current_plant)
                if check_timer>=check_duration:
                    checked_plants.add(current_plant)
                    check_timer=0
                    point_turn_left() # return to original forward orientation after right side check
                    direction=next_direction # Continue previous state after checking both sides.

        pygame.draw.rect(screen,BLUE,(*bot_pos,bot_size,bot_size))

        font=pygame.font.SysFont(None,24)
        state_text=font.render(f"State: {direction}",True,(0,0,0))
        screen.blit(state_text,(10,10))

        pygame.display.flip()
        pygame.time.delay(30)

except KeyboardInterrupt:
    print("🚨 Interrupted! Exiting...")

finally:
    pygame.quit()
    sys.exit()
