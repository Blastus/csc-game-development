#! /usr/bin/env python3
import tkinter
import functools
import random
from tkinter.simpledialog import askstring

class MineSweep(tkinter.Frame):

    @classmethod
    def main(cls, width, height, mines):
        root = tkinter.Tk()
        root.resizable(False, False)
        root.title('MineSweep')
        window = cls(root, width, height, mines)
        root.mainloop()

    def __init__(self, master, width, height, mines):
        super().__init__(master)
        self.__width = width
        self.__height = height
        self.__mines = mines
        self.__wondering = width * height
        self.__started = False
        self.__playing = True
        self.__build_timer()
        self.__build_buttons()
        self.grid()

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
        name = askstring('New Record', 'What is your name?')
        if name is not None:
            print(name, 'has won!')
        else:
            print("I don't know who you are!")
        for row in self.__buttons:
            for button in row:
                if button.mine:
                    button['text'] = 'X'
        
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

if __name__ == '__main__':
    MineSweep.main(10, 10, 10)
