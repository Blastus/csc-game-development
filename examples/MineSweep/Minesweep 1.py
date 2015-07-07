#! /usr/bin/env python3
import tkinter
import functools

class MineSweep(tkinter.Frame):

    @classmethod
    def main(cls, width, height):
        root = tkinter.Tk()
        window = cls(root, width, height)
        root.mainloop()

    def __init__(self, master, width, height):
        super().__init__(master)
        self.__width = width
        self.__height = height
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
        print('Column = {}\nRow = {}'.format(x, y))

if __name__ == '__main__':
    MineSweep.main(10, 10)
