# -*- coding: utf-8 -*-

from psychopy import visual, event, core
import multiprocessing as mp
import pygame as pg
import pandas as pd
import filterlib as flt
import blink as blk
import random
import pygame
from pygame.locals import *
from actors import *
#from pyOpenBCI import OpenBCIGanglion


def blinks_detector(quit_program, blink_det, blinks_num, blink,):
    def detect_blinks(sample):
        if SYMULACJA_SYGNALU:
            smp_flted = sample
        else:
            smp = sample.channels_data[0]
            smp_flted = frt.filterIIR(smp, 0)
        #print(smp_flted)

        brt.blink_detect(smp_flted, -38000)
        if brt.new_blink:
            if brt.blinks_num == 1:
                #connected.set()
                print('CONNECTED. Speller starts detecting blinks.')
            else:
                blink_det.put(brt.blinks_num)
                blinks_num.value = brt.blinks_num
                blink.value = 1

        if quit_program.is_set():
            if not SYMULACJA_SYGNALU:
                print('Disconnect signal sent...')
                board.stop_stream()


####################################################
    SYMULACJA_SYGNALU = True
####################################################
    mac_adress = 'd2:b4:11:81:48:ad'
####################################################

    clock = pg.time.Clock()
    frt = flt.FltRealTime()
    brt = blk.BlinkRealTime()

    if SYMULACJA_SYGNALU:
        df = pd.read_csv('dane_do_symulacji/data.csv')
        for sample in df['signal']:
            if quit_program.is_set():
                break
            detect_blinks(sample)
            clock.tick(200)
        print('KONIEC SYGNAŁU')
        quit_program.set()
    else:
        board = OpenBCIGanglion(mac=mac_adress)
        board.start_stream(detect_blinks)

if __name__ == "__main__":


    blink_det = mp.Queue()
    blink = mp.Value('i', 0)
    blinks_num = mp.Value('i', 0)
    #connected = mp.Event()
    quit_program = mp.Event()

    proc_blink_det = mp.Process(
        name='proc_',
        target=blinks_detector,
        args=(quit_program, blink_det, blinks_num, blink,)
        )

    # rozpoczęcie podprocesu
    proc_blink_det.start()
    print('subprocess started')

g_vars = {}
g_vars['width'] = 416
g_vars['height'] = 416
g_vars['fps'] = 30
g_vars['grid'] = 32
g_vars['window'] = pygame.display.set_mode( [g_vars['width'], g_vars['height']], pygame.HWSURFACE)


class App:

	def __init__(self):
		pygame.init()
		pygame.display.set_caption("Frogger")

		self.running = None
		self.state = None
		self.frog = None
		self.score = None
		self.lanes = None

		self.clock = pygame.time.Clock()
		self.font = pygame.font.SysFont('Courier New', 16)

	def init(self):
		self.running = True
		self.state = 'START'

		self.frog = Frog(g_vars['width']/2 - g_vars['grid']/2, 12 * g_vars['grid'], g_vars['grid'])
		self.frog.attach(None)
		self.score = Score()

		self.lanes = []
		self.lanes.append( Lane( 1, c=( 50, 192, 122) ) )
		self.lanes.append( Lane( 2, t='log', c=(153, 217, 234), n=2, l=6, spc=350, spd=0.2) )
		self.lanes.append( Lane( 3, t='log', c=(153, 217, 234), n=3, l=2, spc=180, spd=-0.6) )
		self.lanes.append( Lane( 4, t='log', c=(153, 217, 234), n=4, l=2, spc=140, spd=0.6) )
		self.lanes.append( Lane( 5, t='log', c=(153, 217, 234), n=2, l=3, spc=230, spd=-0.2) )
		self.lanes.append( Lane( 6, c=(50, 192, 122) ) )
		self.lanes.append( Lane( 7, c=(50, 192, 122) ) )
		self.lanes.append( Lane( 8, t='car', c=(195, 195, 195), n=3, l=2, spc=180, spd=-0.5) )
		self.lanes.append( Lane( 9, t='car', c=(195, 195, 195), n=2, l=4, spc=240, spd=-0.1) )
		self.lanes.append( Lane( 10, t='car', c=(195, 195, 195), n=4, l=1, spc=130, spd=0.5) )
		self.lanes.append( Lane( 11, t='car', c=(195, 195, 195), n=3, l=3, spc=200, spd=0.1) )
		self.lanes.append( Lane( 12, c=(50, 192, 122) ) )

	def event(self, event):
		if event.type == QUIT:
			self.running = False

		if event.type == KEYDOWN and event.key == K_ESCAPE:
			self.running = False

		if self.state == 'START':
			if event.type == KEYDOWN and event.key == K_RETURN:
				self.state = 'PLAYING'

		if self.state == 'PLAYING':
			if event.type == KEYDOWN and event.key == K_LEFT:
				self.frog.move(-1, 0)
			if event.type == KEYDOWN and event.key == K_RIGHT:
				self.frog.move(1, 0)
			if blink.value == 1:
				self.frog.move(0, -1)
				blink.value = 0
			if event.type == KEYDOWN and event.key == K_DOWN:
				self.frog.move(0, 1)

	def update(self):
		for lane in self.lanes:
			lane.update()

		lane_index = self.frog.y // g_vars['grid'] - 1
		if self.lanes[lane_index].check(self.frog):
			self.score.lives -= 1
			self.score.score = 0

		self.frog.update()

		if (g_vars['height']-self.frog.y)//g_vars['grid'] > self.score.high_lane:
			if self.score.high_lane == 11:
				self.frog.reset()
				self.score.update(200)
			else:
				self.score.update(10)
				self.score.high_lane = (g_vars['height']-self.frog.y)//g_vars['grid']

		if self.score.lives == 0:
			self.frog.reset()
			self.score.reset()
			self.state = 'START'

	def draw(self):
		g_vars['window'].fill( (0, 0, 0) )
		if self.state == 'START':

			self.draw_text("Frogger!", g_vars['width']/2, g_vars['height']/2 - 15, 'center')
			self.draw_text("Press ENTER to start playing.", g_vars['width']/2, g_vars['height']/2 + 15, 'center')

		if self.state == 'PLAYING':

			self.draw_text("Lives: {0}".format(self.score.lives), 5, 8, 'left')
			self.draw_text("Score: {0}".format(self.score.score), 120, 8, 'left')
			self.draw_text("High Score: {0}".format(self.score.high_score), 240, 8, 'left')

			for lane in self.lanes:
				lane.draw()
			self.frog.draw()

		pygame.display.flip()

	def draw_text(self, t, x, y, a):
		text = self.font.render(t, False, (255, 255, 255))
		if a == 'center':
			x -= text.get_rect().width / 2
		elif a == 'right':
			x += text.get_rect().width
		g_vars['window'].blit( text , [x, y])

	def cleanup(self):
		pygame.quit()
		quit()

	def execute(self):
		if self.init() == False:
			self.running = False
		while self.running:
			for event in pygame.event.get():
				self.event( event )
			self.update()
			self.draw()
			self.clock.tick(g_vars['fps'])
		self.cleanup()


if __name__ == "__main__":
	gameApp = App()
	gameApp.execute()

# Zakończenie podprocesów
    proc_blink_det.join()
