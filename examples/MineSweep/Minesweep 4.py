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
        if not button.pushed:
            button.pushed = True
            if button.mine:
                button['text'] = 'X'
            else:
                count = self.__total(x, y)
                button['text'] = count and str(count) or ' '
        
    def __total(self, x, y):
        count = 0
        for x_offset in range(-1, 2):
            x_index = x + x_offset
            for y_offset in range(-1, 2):
                y_index = y + y_offset
                if 0 <= x_index < self.__width and 0 <= y_index < self.__height:
                    count += self.__buttons[y_index][x_index].mine
        if not count:
            for x_offset in range(-1, 2):
                x_index = x + x_offset
                for y_offset in range(-1, 2):
                    y_index = y + y_offset
                    if 0 <= x_index < self.__width and 0 <= y_index < self.__height:
                        self.__push(x_index, y_index)
        return count

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
