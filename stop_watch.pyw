import pygame
import time
import threading
import pystray
import keyboard
import traceback
from PIL import Image, ImageDraw


# Initialize pygame font
pygame.init()
pygame.font.init()

# Color class for different states
class Colour:
	STOPPED = (111, 199, 190)
	PLAYING = (141, 209, 109)
	RESET = (240, 20, 20)

# Global settings and utility class
class Global:
	APPLICATION_RUN = True
	GUI_RUN = False
	PROJ_ROOT = "C://Dev/Tools/StopWatch"
	FONT = pygame.font.SysFont('Comic Sans MS', 30)
	ICON = None
	WINDOW = None
	KBD_START = "f22"
	KBD_STOP = "f23"
	LOG_FILE = "stopwatch-backup.log"
	ERROR_LOG_FILE = "error.log"

# Timer singleton class for time management
class Timer:
	START_TIME = 0
	TOTAL_TIME = 0
	COUNTING = False
	LAST_STOP_PRESS_TIME = 0
	STOP_COUNT = 0

	@staticmethod
	def start():
		if Timer.COUNTING:
			return
		Timer.START_TIME = time.time()
		Timer.COUNTING = True
		Global.ICON.start()

	@staticmethod
	def stop():
		if Timer.COUNTING:
			Timer.TOTAL_TIME += time.time() - Timer.START_TIME
			Timer.COUNTING = False
			Global.ICON.stop()
			return

		if Timer.LAST_STOP_PRESS_TIME + 0.5 > time.time():
			Timer.STOP_COUNT += 1
		else:
			Timer.STOP_COUNT = 0

		Timer.LAST_STOP_PRESS_TIME = time.time()

		if Timer.STOP_COUNT >= 10:
			Timer.reset()
	
	@staticmethod
	def reset():
		if Timer.COUNTING:
			Timer.TOTAL_TIME += time.time() - Timer.START_TIME
			Timer.COUNTING = False
		backup_time_to_file()
		Timer.TOTAL_TIME = 0
		Global.ICON.reset()

	@staticmethod
	def get_string():
		elapsed_time = Timer.TOTAL_TIME
		if Timer.COUNTING:
			elapsed_time += time.time() - Timer.START_TIME
		hours, remainder = divmod(elapsed_time, 3600)
		minutes, seconds = divmod(remainder, 60)
		return f"{int(hours):02}:{int(minutes):02}:{int(seconds):02}"

# Function to backup time to a log file
def backup_time_to_file():
	with open(f"{Global.PROJ_ROOT}/{Global.LOG_FILE}", "a") as file:
		file.write(f"{time.ctime()}\t{Timer.get_string()}\n")

# GUI loop function
def open_gui():
	if Global.GUI_RUN:
		return

	Global.WINDOW = pygame.display.set_mode((160, 80))
	pygame.display.set_caption("Stopwatch")
	Global.GUI_RUN = True


def update_gui():

	# set background colour
	bg_color = Colour.STOPPED
	if Timer.COUNTING:
		bg_color = Colour.PLAYING
	elif Timer.TOTAL_TIME == 0:
		bg_color = Colour.RESET

	Global.WINDOW.fill(bg_color)

	# set text
	text_surface = Global.FONT.render(Timer.get_string(), False, (0, 0, 0))
	Global.WINDOW.blit(text_surface, (10, 10))

	pygame.display.update()

# System tray icon class
class SysTray:
	def __init__(self):
		self.menu = pystray.Menu(
			pystray.MenuItem("Open GUI", open_gui),
			pystray.MenuItem("Reset", Timer.reset),
			pystray.MenuItem("Quit", self.quit)
		)

		self.pic_play = self.create_image(Colour.PLAYING)
		self.pic_paused = self.create_image(Colour.STOPPED)
		self.pic_reset = self.create_image(Colour.RESET)

		self.icon = pystray.Icon("Icon", self.pic_reset, menu=self.menu)
		self.thread = threading.Thread(target=self.icon.run)
		self.thread.start()

	def create_image(self, bg_color):
		base_image = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
		draw = ImageDraw.Draw(base_image)
		draw.ellipse([0, 0, 64, 64], fill=bg_color)
		icon_image = Image.open(f"{Global.PROJ_ROOT}/assets/time_black.ico").convert("RGBA")
		icon_image = icon_image.resize((48, 48), Image.Resampling.LANCZOS)
		base_image.paste(icon_image, (8, 8), icon_image)
		return base_image

	def start(self):
		self.icon.icon = self.pic_play

	def stop(self):
		self.icon.icon = self.pic_paused

	def reset(self):
		self.icon.icon = self.pic_reset

	def quit(self):
		self.icon.stop()
		Global.APPLICATION_RUN = False


# Main loop function
def main():
	Global.ICON = SysTray()
	open_gui()

	# Main loop for event handling and GUI
	while Global.APPLICATION_RUN:

		if Global.GUI_RUN:
			update_gui()
			for event in pygame.event.get():
				if event.type == pygame.QUIT:
					Global.GUI_RUN = False
					pygame.display.quit()


		if keyboard.is_pressed(Global.KBD_START):
		   Timer.start()
		if keyboard.is_pressed(Global.KBD_STOP):
		   Timer.stop()

		# Backup time to file periodically
		time.sleep(1/20)
	
	# most important first
	backup_time_to_file()

	# application is exiting
	if Global.GUI_RUN:
		pygame.display.quit()
	
	pygame.quit()
		

if __name__ == "__main__":
	try:
		main()
	except Exception as e:
		err_file = f"{Global.PROJ_ROOT}/{Global.ERROR_LOG_FILE}"
		with open(err_file, "w") as file:
			print(f"\nPlease check the error file {err_file}\nError {e}\n")
			file.write(f"Error: {e}\n\n")
			traceback.print_exc(file=file)
