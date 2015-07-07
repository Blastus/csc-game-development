#! /usr/bin/env python3
from tkinter import *
import pickle as cPickle
import os

################################################################################

class Screen3:

    IMAGE_SIZE = '17x17'
    IMAGE_MAP = {'^': 'you',
                 '&': 'robot',
                 '_': 'floor',
                 '*': 'load',
                 '|': 'ladder',
                 '@': 'portal'}

    def __init__(self, board, callback, check, keys, root):
        self.__cache = [list(row) for row in board.board().splitlines()[1:]]
        self.__cache_rows = len(self.__cache) # NUMBER OF ROWS
        self.__cache_columns = len(self.__cache[0]) # NUMBER OF COLUMNS
        self.__hand = [[None] * len(self.__cache[0]) for x in range(len(self.__cache))]
        self.__board()
        self.__callback = callback
        self.__check = check
        # ROOT
        self.__root = Toplevel(root)
        # PHOTO_IMAGE
        self.__images = self.IMAGES
        # MORE ROOT
        self.__root.overrideredirect(True)
        w = len(self.__cache[0]) * self.IMAGE_WIDTH + 3 # PIXELS
        h = len(self.__cache) * self.IMAGE_HEIGHT + 3 # PIXELS
        x = self.__root.winfo_screenwidth()
        y = self.__root.winfo_screenheight()
        self.__root.geometry('%dx%d+%d+%d' % (w, h, (x - w) / 2, (y - h) / 2))
        self.__root.focus_force()
        # HOW TO END EXECUTION
        self.__root.protocol('WM_DELETE_WINDOW', self.__exit)
        # BINDINGS (CONTROLS)
        self.root = self.__root
        self.__create_bindings(keys)
        # CANVAS
        self.__canvas = Canvas(self.__root, width=w, height=h)
        self.__canvas.config(background=self.BACKGROUND_COLOR)
        self.__canvas.pack()
        # Show the screen.
        self.__start()
        # Paint the board name.
        self.__name = self.__canvas.create_text((w / 2, h / 2), text=board.name(), font='verdana 48 bold', fill=self.TITLE_COLOR)
        # Prepare for game loop.
        self.__fun = self.__canvas.after(3000, self.__clear_name)

    def __create_bindings(self, dispatch): # NEW - V7
        binding = False
        for line in open(os.path.join('source', 'bind.ini')).read().splitlines():
            if binding:
                command, binding = line.split()
                if command == 'exit':
                    self.root.bind_all(binding, self.__exit)
                else:
                    self.root.bind_all(binding, Call(dispatch, command))
            elif not line:
                binding = True

    def __exit(self, *args):
        self.__root.destroy()
        raise SystemExit(True)

    def __clear_name(self):
        self.__canvas.delete(self.__name)
        self.__after()

    def __after(self):
        self.__callback()
        if self.__check():
            self.__fun = self.__canvas.after(125, self.__after)
        else:
            self.__root.destroy()
            raise SystemExit(False)

    def __start(self):
        for rnum, row in enumerate(self.__temp):
            for cnum, key in enumerate(row):
                if key in self.__images:
                    x = cnum * self.IMAGE_WIDTH + self.IMAGE_WIDTH // 2 + 1
                    y = rnum * self.IMAGE_HEIGHT + self.IMAGE_HEIGHT // 2 + 1
                    coords = x, y
                    hand = self.__canvas.create_image(coords, image=self.__images[key])
                    self.__hand[rnum][cnum] = [(hand, key), (None, None)] # [(environment_handle, environment_key), (actor_handle, actor_key)]
                else:
                    self.__hand[rnum][cnum] = [(None, ' '), (None, None)] # [(environment_handle, environment_key), (actor_handle, actor_key)]

    def cache_write(self, row, column, character):
        try:
            assert 0 <= row < self.__cache_rows and 0 <= column < self.__cache_columns
            self.__cache[row][column] = character[0]
            self.write(row, column, character)
        except:
            pass

    def cache_read(self, row, column):
        try:
            assert 0 <= row < self.__cache_rows and 0 <= column < self.__cache_columns
            return self.__cache[row][column]
        except:
            pass

    def find(self, char):
        answers = []
        for num, row in enumerate(self.__cache):
            add = 0
            while char in row:
                column = row.index(char)
                answers.append((num, column + add))
                size = column + 1
                row = row[size:]
                add += size
        return answers

    def write(self, row, column, character):
        try:
            assert 0 <= row < self.__cache_rows and 0 <= column < self.__cache_columns
            self.__temp[row][column] = character[0]
        except:
            pass

    def read(self, row, column):
        try:
            assert 0 <= row < self.__cache_rows and 0 <= column < self.__cache_columns
            return self.__temp[row][column]
        except:
            pass

    def update(self):
        # self.__clear()
        try:
            self.__print()
        except:
            pass
        self.__board()

    def __print(self):
        for row in range(len(self.__cache)):
            for column in range(len(self.__cache[0])):
                env, obj = self.__hand[row][column]  # [(environment_handle, environment_key), (actor_handle, actor_key)]
                # DRAW ACTORS
                obj_hand, obj_key = obj
                temp_key = self.__temp[row][column]
                if obj_key != temp_key:
                    if obj_hand is not None:
                        self.__canvas.delete(obj_hand)
                    if temp_key in '^&':
                        x = column * self.IMAGE_WIDTH + self.IMAGE_WIDTH // 2 + 1
                        y = row * self.IMAGE_HEIGHT + self.IMAGE_HEIGHT // 2 + 1
                        coords = x, y
                        hand = self.__canvas.create_image(coords, image=self.__images[temp_key])
                        self.__hand[row][column][1] = (hand, temp_key)
                    else:
                        self.__hand[row][column][1] = (None, None)
                # DRAW ENVIRONMENT
                env_hand, env_key = env
                cache_key = self.__cache[row][column]
                if env_key != cache_key:
                    if env_hand is not None:
                        self.__canvas.delete(env_hand)
                    if cache_key == ' ':
                        self.__hand[row][column][0] = (None, cache_key)
                    else:
                        x = column * self.IMAGE_WIDTH + self.IMAGE_WIDTH // 2 + 1
                        y = row * self.IMAGE_HEIGHT + self.IMAGE_HEIGHT // 2 + 1
                        coords = x, y
                        hand = self.__canvas.create_image(coords, image=self.__images[cache_key])
                        self.__hand[row][column][0] = (hand, cache_key)
                        # MAKE SURE THE ENVIRONMENT IS NOT COVERING THE ACTOR
                        actor_handle = self.__hand[row][column][1][0]
                        if actor_handle is not None:
                            self.__canvas.tag_raise(actor_handle, hand)
        # UPDATE THE CANVAS
        self.__canvas.update()
        # save the screen's state
        cPickle.dump([[(env[1], act[1]) for env, act in row] for row in self.__hand], self.HISTORY, -1)
        
    def __board(self):
        self.__temp = [list(row) for row in self.__cache]
