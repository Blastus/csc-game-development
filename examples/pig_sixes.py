# inspired by http://nrich.maths.org/1258

import random
import tkinter
import turtle

def main():
    tkinter.NoDefaultRoot()
    root = tkinter.Tk()
    patch_turtle(root)
    root.title('Pig Sixes')
    root.resizable(False, False)
    psg = PigSixesGraphic(root)
    psg.draw_pig()
    psg.grid()
##    root.mainloop()

def patch_turtle(root):
    PhotoImage = turtle.TK.PhotoImage
    turtle.TK.PhotoImage = lambda *args, **kwargs: PhotoImage(
        master=root, *args, **kwargs)

def enum(*s):
    return type('enum', (), dict(map(reversed, enumerate(s)), __slots__=()))()

class PigSixesGUI(tkinter.Frame):

    def __init__(self, master=None, cnf={}, **kw):
        super().__init__(master, cnf, **kw)
        self.build_widgets()
        self.place_widgets()
        self.setup_widgets()

    def build_widgets(self):
        self.player_1_label = tkinter.Label(self, text='Your Score')
        self.player_1_score = tkinter.Label(self, text='0')
        self.player_2_label = tkinter.Label(self, text='My Score')
        self.player_2_score = tkinter.Label(self, text='0')
        self.accumulator = tkinter.Label(self, text='0')
        self.indicator = tkinter.Button(self, text='<=', command=self.stop)
        

    def place_widgets(self):
        pass

    def setup_widgets(self):
        pass

class PigSixesGraphic(tkinter.Canvas):

    def draw_pig(self):
        global turtle_screen, raw_turtle
        turtle_screen = turtle.TurtleScreen(self)
        raw_turtle = turtle.RawTurtle(turtle_screen)
        raw_turtle.begin_fill()
        for _ in range(2):
            raw_turtle.forward(50)
            raw_turtle.circle(25, 180)
        raw_turtle.end_fill()
        self.draw_leg_pair(raw_turtle)
        raw_turtle.forward(50)
        self.draw_leg_pair(raw_turtle)
        raw_turtle.circle(25, 135)
        raw_turtle.right(90)
        raw_turtle.width(3)
        raw_turtle.circle(-10, 135)
        raw_turtle.right(135)
        raw_turtle.circle(-10, 180)
        
        raw_turtle.hideturtle()

    def draw_leg_pair(self, raw_turtle):
        raw_turtle.right(110)
        raw_turtle.width(10)
        self.draw_one_leg(raw_turtle)
        raw_turtle.left(40)
        self.draw_one_leg(raw_turtle)
        raw_turtle.left(70)
        raw_turtle.width(1)

    def draw_one_leg(self, raw_turtle):
        raw_turtle.forward(30)
        raw_turtle.backward(30)

class PigSixesAI:
    pass

class PigSixesLogic:

    STATES = enum('waiting', 'rolling', 'game_over')

    def __init__(self, players=2, dice=2, winning_score=100):
        self.reset(players, dice, winning_score)

    def reset(self, players, dice, winning_score):
        self.__scores = [0] * players
        self.__dice = [1] * dice
        self.__roll = [0] * dice
        self.__winning_score = winning_score
        self.__current_player = 0
        self.__accumulator = 0
        self.__state = self.STATES.waiting

    @property
    def scores(self):
        return tuple(self.__scores)

    @property
    def current_player(self):
        return self.__current_player

    @property
    def accumulator(self):
        return self.__accumulator

    def role(self, min_change=5, max_change=10):
        if self.__state == self.STATES.waiting:
            self.__state = self.STATES.rolling
            for index in range(len(self.__roll)):
                self.__roll[index] = random.randint(min_change, max_change)

    @property
    def role_animation(self):
        if self.__state == self.STATES.rolling:
            while any(self.__roll):
                for index, count in enumerate(self.__roll):
                    if count:
                        self.__dice[index] = random.randint(1, 6)
                        self.__roll[index] -= 1
                        yield tuple(self.__dice)
            self.__stop_animation()

    def __stop_animation(self):
        if 6 in self.__dice:
            if all(die == 6 for die in self.__dice):
                self.__scores[self.__current_player] = 0
            else:
                self.__accumulator = 0
            self.__next_player()
        else:
            self.__accumulator += sum(self.__dice)
        self.__state = self.STATES.waiting

    def __next_player(self):
        self.__current_player += 1
        self.__current_player %= len(self.__scores)

    def stop(self):
        if self.__state == self.STATES.waiting:
            self.__scores[self.__current_player] += self.__accumulator
            if self.__scores[self.__current_player] < self.__winning_score:
                self.__accumulator = 0
                self.__next_player()
            else:
                self.__state = self.STATES.game_over

    @property
    def winner(self):
        if self.__state == self.STATES.game_over:
            return self.__current_player
        return -1

if __name__ == '__main__':
    main()
