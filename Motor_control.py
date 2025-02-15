# import curses and GPIO
import pygame
import RPi.GPIO as GPIO
import os #added so we can shut down OK

#Open a Pygame window to allow it to detect user events
screen = pygame.display.set_mode([240, 160])

#set GPIO numbering mode and define output pins
GPIO.setmode(GPIO.BOARD)
GPIO.setup(7,GPIO.OUT)
GPIO.setup(11,GPIO.OUT)
GPIO.setup(13,GPIO.OUT)
GPIO.setup(15,GPIO.OUT)

try:
	while True:
		for event in pygame.event.get():
			if event.type == pygame.KEYDOWN:
				if event.key == pygame.K_q:
					pygame.quit()
				#if event.key == pygame.K_s:
				#	os.system ('sudo shutdown now') # shutdown right now!
				elif event.key == pygame.K_RIGHT:
					GPIO.output(7,True)
					GPIO.output(11,False)
					GPIO.output(13,True)
					GPIO.output(15,False)
				elif event.key == pygame.K_LEFT:
					GPIO.output(7,False)
					GPIO.output(11,True)
					GPIO.output(13,False)
					GPIO.output(15,True)
				elif event.key == pygame.K_UP:
					GPIO.output(7,False)
					GPIO.output(11,True)
					GPIO.output(13,True)
					GPIO.output(15,False)					
				elif event.key == pygame.K_DOWN:
					GPIO.output(7,True)
					GPIO.output(11,False)
					GPIO.output(13,False)
					GPIO.output(15,True)
				
			elif event.type == pygame.KEYUP:
				GPIO.output(7,False)
				GPIO.output(11,False)
				GPIO.output(13,False)
				GPIO.output(15,False)
			             
finally:
    #GPIO cleanup
    GPIO.cleanup()
    
