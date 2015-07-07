#! /usr/bin/env python3
from winsound import PlaySound, SND_FILENAME
from multiprocessing import Process

def start(filename):
    player = Process(target=_play_loop, args=(filename, SND_FILENAME))
    player.daemon = True
    player.start()

def _play_loop(filename, flags):
    while True:
        PlaySound(filename, flags)
