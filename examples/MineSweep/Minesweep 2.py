#! /usr/bin/env python3
import tkinter
import functools
import random

class MineSweep(tkinter.Frame):

    @classmethod
    def main(cls, width, height, mines):
        root = tkinter.Tk()
        window = cls(root, width, height, mines)
        root.mainloop()

    def __init__(self, master, width, height, mines):
        super().__init__(master)
        self.__width = width
        self.__height = height
        self.__mines = mines
        self.__started = False
        self.__build_buttons()
        self.grid()

    def __build_buttons(self):
        self.__buttons = []
        for y in range(self.__height):
            row = []
            for x in range(self.__width):
                button = tkinter.Button(self)
                button.grid(column=x, row=y)
                button['text'] = '?'
                command = functools.partial(self.__push, x, y)
                button['command'] = command
                row.append(button)
            self.__buttons.append(row)

    def __push(self, x, y):
        if not self.__started:
            self.__build_mines()
            while self.__buttons[y][x].mine:
                self.__build_mines()
            self.__started = True
        button = self.__buttons[y][x]
        text = 'NY'[button.mine] + '({}, {})'.format(x, y)
        button['text'] = text

    def __build_mines(self):
        mines = [True] * self.__mines
        empty = [False] * (self.__width * self.__height - self.__mines)
        total = mines + empty
        random.shuffle(total)
        iterator = iter(total)
        for row in self.__buttons:
            for button in row:
                button.mine = next(iterator)

if __name__ == '__main__':
    MineSweep.main(10, 10, 10)
