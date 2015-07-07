#! /usr/bin/env python3
import tkinter
import functools
import random
from tkinter.simpledialog import askstring
from tkinter.messagebox import showinfo
import pickle
import os.path

################################################################################

class MineSweep(tkinter.Frame):

    @classmethod
    def main(cls, width, height, mines, scores):
        root = tkinter.Tk()
        root.resizable(False, False)
        root.title('MineSweep')
        window = cls(root, width, height, mines, scores)
        root.protocol('WM_DELETE_WINDOW', window.close)
        root.mainloop()

################################################################################

    def __init__(self, master, width, height, mines, scores):
        super().__init__(master)
        self.__width = width
        self.__height = height
        self.__mines = mines
        self.__wondering = width * height
        self.__started = False
        self.__playing = True
        self.__scores = ScoreTable()
        self.__record_file = scores
        if os.path.isfile(scores):
            self.__scores.load(scores)
        self.__build_timer()
        self.__build_buttons()
        self.grid()

    def close(self):
        self.__scores.save(self.__record_file)
        self.quit()

    def __build_timer(self):
        self.__secs = tkinter.IntVar()
        self.__timer = tkinter.Label(textvariable=self.__secs)
        self.__timer.grid(columnspan=10, sticky=tkinter.EW)
        self.__after_handle = None

    def __build_buttons(self):
        self.__reset_button = tkinter.Button(self)
        self.__reset_button['text'] = 'Reset'
        self.__reset_button['command'] = self.__reset
        self.__reset_button.grid(column=0, row=1,
                                 columnspan=10, sticky=tkinter.EW)
        self.__buttons = []
        for y in range(self.__height):
            row = []
            for x in range(self.__width):
                button = tkinter.Button(self, width=2, height=1, text='?')
                button.grid(column=x, row=y+2)
                command = functools.partial(self.__push, x, y)
                button['command'] = command
                row.append(button)
            self.__buttons.append(row)

    def __reset(self):
        for row in self.__buttons:
            for button in row:
                button['text'] = '?'
        self.__started = False
        self.__playing = True
        self.__wondering = self.__width * self.__height
        if self.__after_handle is not None:
            self.after_cancel(self.__after_handle)
            self.__after_handle = None
        self.__secs.set(0)

    def __push(self, x, y):
        if self.__playing:
            if not self.__started:
                self.__build_mines()
                while self.__buttons[y][x].mine:
                    self.__build_mines()
                self.__started = True
                self.__after_handle = self.after(1000, self.__tick)
            button = self.__buttons[y][x]
            if not button.pushed:
                self.__push_button(button, x, y)

    def __tick(self):
        self.__after_handle = self.after(1000, self.__tick)
        self.__secs.set(self.__secs.get() + 1)

    def __push_button(self, button, x, y):
        button.pushed = True
        if button.mine:
            button['text'] = 'X'
            self.__playing = False
            self.after_cancel(self.__after_handle)
            self.__after_handle = None
        else:
            count = self.__total(x, y)
            button['text'] = count and str(count) or ' '
            self.__wondering -= 1
            if self.__wondering == self.__mines:
                self.after_cancel(self.__after_handle)
                self.__after_handle = None
                self.__finish_game()

    def __finish_game(self):
        self.__playing = False
        score = self.__secs.get()
        if self.__scores.eligible(score):
            name = askstring('New Record', 'What is your name?')
            if name is None:
                name = 'Anonymous'
            self.__scores.add(name, score)
        else:
            showinfo('You did not get on the high score table.')
        for row in self.__buttons:
            for button in row:
                if button.mine:
                    button['text'] = 'X'
        for name, score in self.__scores.listing():
            print('{:20}{}'.format(name, score))
        
    def __total(self, x, y):
        count = 0
        for x_offset in range(-1, 2):
            x_index = x + x_offset
            for y_offset in range(-1, 2):
                y_index = y + y_offset
                if 0 <= x_index < self.__width and 0 <= y_index < self.__height:
                    count += self.__buttons[y_index][x_index].mine
        if not count:
            self.__propagate(x, y)
        return count

    def __propagate(self, x, y):
        for x_offset in range(-1, 2):
            x_index = x + x_offset
            for y_offset in range(-1, 2):
                y_index = y + y_offset
                if 0 <= x_index < self.__width and 0 <= y_index < self.__height:
                    self.__push(x_index, y_index)

    def __build_mines(self):
        mines = [True] * self.__mines
        empty = [False] * (self.__width * self.__height - self.__mines)
        total = mines + empty
        random.shuffle(total)
        iterator = iter(total)
        for row in self.__buttons:
            for button in row:
                button.mine = next(iterator)
                button.pushed = False

################################################################################

class ScoreTable:

    def __init__(self, size=10):
        self.__data = {999: [''] * size}

    def add(self, name, score):
        assert self.eligible(score)
        if score in self.__data:
            self.__data[score].insert(0, name)
        else:
            self.__data[score] = [name]
        if len(self.__data[max(self.__data)]) == 1:
            del self.__data[max(self.__data)]
        else:
            del self.__data[max(self.__data)][-1]

    def eligible(self, score):
        return score <= max(self.__data)

    def listing(self):
        for key in sorted(self.__data.keys()):
            for name in self.__data[key]:
                yield name, key

    def load(self, filename):
        self.__data = pickle.load(open(filename, 'rb'))

    def save(self, filename):
        pickle.dump(self.__data, open(filename, 'wb'))

################################################################################

if __name__ == '__main__':
    MineSweep.main(10, 10, 10, 'scores.dat')
