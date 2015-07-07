#! /usr/bin/env python3
from tkinter import *
from tkinter.font import Font
import random
import functools
import math
import time

################################################################################

class Pong(Canvas):

    DEFAULTS = dict(width=640,
                    height=480,
                    background='black',
                    highlightthickness=0)

    @classmethod
    def main(cls):
        root = Tk()
        root.title('Pong')
        root.resizable(False, False)
        root.bind_all('<Escape>', lambda event: root.destroy())
        game = cls(Font(family='Book Antiqua', size=15, weight='bold'), 5, 100,
                   background='black', width=640, height=480)
        game.grid()
        root.mainloop()

    def __init__(self, font, lives, fps, master=None, cnf={}, **kw):
        for item in self.DEFAULTS.items():
            kw.setdefault(*item)
        super().__init__(master, cnf, **kw)
        self.font = font
        self.p1 = Paddle(lives, 'blue', 10,
                         self.height, 120, 15, 5)
        self.p2 = Paddle(lives, 'blue', self.width - 10,
                         self.height, 120, 15, 5)
        self.wait = 1000 // fps
        self.separator = Box(Point(self.width // 2 - 2, 0),
                             Point(self.width // 2 + 2, self.height))
        self.new_rect(self.separator, 'white')
        self.bind('<p>', self.pause)
        self.p1.bind(self, 'w', 's')
        self.p2.bind(self, 'Up', 'Down')
        self.draw_high = True
        self.after_idle(self.startup)
        self.focus_force()

    def pause(self, event):
        if not self.running_startup:
            self.refresh = self.after_cancel(self.refresh) \
                           if self.refresh else self.after_idle(self.animate)

    def startup(self, countdown=3, target=None):
        if target is None:
            self.running_startup = True
            self.ball = Ball('white', self.width, self.height, 20)
            self.refresh = None
            target = time.clock() + countdown
        for paddle in self.p1, self.p2:
            paddle.center()
        self.draw_all()
        remaining = math.ceil(target - time.clock())
        if remaining:
            self.new_text(Point(self.width >> 1, self.height >> 1),
                          self.random_color(), str(remaining), CENTER)
            self.after(self.wait, self.startup, None, target)
        else:
            self.running_startup = False
            self.after_idle(self.animate)

    @classmethod
    def random_color(cls):
        return '#{:02X}{:02X}{:02X}'.format(*cls.random_bytes(3))

    @staticmethod
    def random_bytes(n):
        return bytes(random.randrange(1 << 8) for _ in range(n))

    def animate(self):
        self.move_all()
        if self.in_bounds():
            self.draw_all()
            self.refresh = self.after(self.wait, self.animate)

    def move_all(self):
        for obj in self.p1, self.p2, self.ball:
            obj.move()
            if obj is not self.ball:
                obj.bounce(self.ball)

    def in_bounds(self):
        if self.boundary.intersects(self.ball.boundary):
            return True
        if (self.p2 if self.ball.position.x > 0 else self.p1).kill():
            self.after_idle(self.startup)
        else:
            self.draw_all()
            self.after(5000, self.quit)
        return False

    def draw_all(self):
        self.delete('actor')
        for obj in self.p1, self.p2, self.ball:
            obj.render(self)
        self.render_status()

    def render_status(self, x_margin=4, y_margin=4):
        self.draw_high = high = (self.ball.position.y > self.height * 0.25) \
                                if self.draw_high else \
                                (self.ball.position.y >= self.height * 0.75)
        if high:
            self.new_text(self.separator.NW + Point(-x_margin, +y_margin),
                          'white', self.p1.status, NE)
            self.new_text(self.separator.NE + Point(+x_margin, +y_margin),
                          'white', self.p2.status, NW)
        else:
            self.new_text(self.separator.SW + Point(-x_margin, -y_margin),
                          'white', self.p1.status, SE)
            self.new_text(self.separator.SE + Point(+x_margin, -y_margin),
                          'white', self.p2.status, SW)

    def new_rect(self, box, color, tag='static'):
        self.create_rectangle(box, fill=color, outline=color, tag=tag)

    def new_oval(self, box, color, tag='static'):
        self.create_oval(box, fill=color, outline=color, tag=tag)

    def new_text(self, point, color, text, anchor, tag='actor'):
        self.create_text(point, fill=color, tag=tag,
                         text=text, anchor=anchor, font=self.font)
        
    @property
    def width(self):
        return int(self['width'])

    @property
    def height(self):
        return int(self['height'])

    @property
    def boundary(self):
        return Box(Point(0, 0), Point(self.width, self.height))

################################################################################

def enum(names):
    return type('enum', (), dict(map(reversed, enumerate(
        names.replace(',', ' ').split())), __slots__=()))()

def copy_sign(x, y):
    return type(x)(math.copysign(x, y))

################################################################################

class Paddle:

    PART = enum('null, upper, center, lower')

    def __init__(self, lives, color, alignment, board_height,
                 paddle_height, paddle_width, move_by):
        self.lives = lives
        self.color = color
        self.height = board_height
        self.position = Point(alignment, board_height >> 1)
        self.size = Point(paddle_width >> 1, paddle_height >> 1)
        self.move_by = move_by
        self.score = 0
        self.just_bounced = False

    def kill(self):
        self.lives -= 1
        self.score >>= 1
        return self.lives > 0

    def center(self):
        y, middle = self.position.y, self.height >> 1
        if y < middle:
            self.move(down=True)
        elif y > middle:
            self.move(up=True)

    def move(self, *, up=False, down=False):
        if up or (not down and self.keys.up and
                  self.position.y - self.size.y > 0):
            self.position -= Point(0, self.move_by)
        if down or (not up and self.keys.down and
                    self.position.y + self.size.y < self.height):
            self.position += Point(0, self.move_by)

    def bounce(self, ball):
        minimum = self.size.x + ball.radius
        if self.position.x != ball.position.x and self.overlap(ball, minimum):
            if not self.just_bounced:
                self.just_bounced = True
                self.score += abs(ball.velocity.y)
            sign = +1 if self.position.x < ball.position.x else -1
            if self.collision_area == self.PART.center:
                ball.position.x = self.position.x + minimum * sign
            else:
                ball.position.adjust(self.middle_point, minimum)
            ball.velocity.x = copy_sign(ball.velocity.x, sign)
            ball.change_speed()
        else:
            self.just_bounced = False

    def overlap(self, ball, minimum):
        box = self.boundary
        if box.intersects(ball.boundary):
            self.collision_area = self.PART.center
        elif (self.hi_mid(box) - ball.position).magnitude <= minimum:
            self.collision_area = self.PART.upper
        elif (self.lo_mid(box) - ball.position).magnitude <= minimum:
            self.collision_area = self.PART.lower
        else:
            self.collision_area = self.PART.null
        return self.collision_area

    def render(self, surface):
        box = self.boundary
        surface.new_rect(box, self.color, 'actor')
        surface.new_oval(Box.from_point(self.hi_mid(box), self.size.x),
                         self.color, 'actor')
        surface.new_oval(Box.from_point(self.lo_mid(box), self.size.x),
                         self.color, 'actor')

    def hi_mid(self, boundary):
        self.middle_point = Point(self.position.x, boundary.a.y)
        return self.middle_point

    def lo_mid(self, boundary):
        self.middle_point = Point(self.position.x, boundary.b.y)
        return self.middle_point

    def bind(self, surface, up, down):
        self.keys = KeyListener(surface, up=up, down=down)

    @property
    def boundary(self):
        return Box.from_point(self.position, self.size)

    @property
    def status(self):
        return 'Lives: {}\nScore: {}'.format(self.lives, self.score)

Player = Paddle

################################################################################

class KeyListener:

    def __init__(self, widget, **kwargs):
        self.__state = dict.fromkeys(kwargs, False)
        for name, key in kwargs.items():
            widget.bind('<KeyPress-{}>'.format(key), self.__set(name, True))
            widget.bind('<KeyRelease-{}>'.format(key), self.__set(name, False))

    def __set(self, name, value):
        def handler(event):
            self.__state[name] = value
        return handler

    def __getattr__(self, name):
        return self.__state[name]

################################################################################

class Ball:

    def __init__(self, color, width, height, size):
        self.color = color
        self.board = Point(width, height)
        self.position = self.board / 2
        self.radius = size >> 1
        self.velocity = Point(1 - 2 * random.randrange(2),
                              1 - 2 * random.randrange(2))
        self.change_speed()

    def change_speed(self, max_x=10, max_y=10):
        speed = self.velocity
        speed.x = copy_sign(random.randint(1, max_x), speed.x)
        speed.y = copy_sign(random.randint(1, max_y), speed.y)

    def move(self):
        self.position += self.velocity
        self.bounce()

    def bounce(self):
        if self.position.y - self.radius < 0:
            self.position.y = self.radius
            self.velocity.y = copy_sign(self.velocity.y, +1)
            self.change_speed()
        elif self.position.y + self.radius > self.board.y:
            self.position.y = self.board.y - self.radius
            self.velocity.y = copy_sign(self.velocity.y, -1)
            self.change_speed()

    def render(self, surface):
        surface.new_oval(self.boundary, self.color, 'actor')

    @property
    def boundary(self):
        return Box.from_point(self.position, self.radius)

################################################################################

def autocast(function):
    @functools.wraps(function)
    def cast(self, other):
        if not isinstance(other, self.__class__):
            other = self.__class__(other, other)
        return function(self, other)
    return cast

################################################################################

class Point(list):

    def __init__(self, x, y):
        super().__init__((x, y))

    def __repr__(self):
        return '{}({})'.format(self.__class__.__name__,
                               ', '.join(map(repr, self)))

    @autocast
    def __add__(self, other):
        return self.__class__(self.x + other.x, self.y + other.y)

    @autocast
    def __sub__(self, other):
        return self.__class__(self.x - other.x, self.y - other.y)

    @autocast
    def __mul__(self, other):
        return self.__class__(self.x * other.x, self.y * other.y)

    @autocast
    def __truediv__(self, other):
        return self.__class__(self.x / other.x, self.y / other.y)

    @autocast
    def __floordiv__(self, other):
        return self.__class__(self.x // other.x, self.y // other.y)

    @autocast
    def __iadd__(self, other):
        self.x += other.x
        self.y += other.y
        return self

    @autocast
    def __isub__(self, other):
        self.x -= other.x
        self.y -= other.y
        return self

    def __get_x(self):
        return self[0]

    def __set_x(self, value):
        self[0] = value

    x = property(__get_x, __set_x)

    def __get_y(self):
        return self[1]

    def __set_y(self, value):
        self[1] = value
    
    y = property(__get_y, __set_y)

    def __get_magnitude(self):
        return math.hypot(self.x, self.y)

    def __set_magnitude(self, value):
        magnitude = self.magnitude
        self.x *= value / magnitude
        self.y *= value / magnitude

    magnitude = property(__get_magnitude, __set_magnitude)

    def adjust(self, projected_from, distance):
        vector = self - projected_from
        vector.magnitude = distance
        self.x = round(projected_from.x + vector.x)
        self.y = round(projected_from.y + vector.y)

################################################################################

class Box(list):

    @classmethod
    def from_point(cls, point, extension):
        return cls(point - extension, point + extension)

    def __init__(self, a, b):
        super().__init__((a, b))

    def __repr__(self):
        return '{}({})'.format(self.__class__.__name__,
                               ', '.join(map(repr, self)))

    def intersects(self, other):
        return not (self.a.x > other.b.x or other.a.x > self.b.x or
                    self.a.y > other.b.y or other.a.y > self.b.y)

    def __get_a(self):
        return self[0]

    def __set_a(self, value):
        self[0] = value

    a = NW = property(__get_a, __set_a)

    def __get_b(self):
        return self[1]

    def __set_b(self, value):
        self[1] = value
    
    b = SE = property(__get_b, __set_b)
    
    @property
    def NE(self):
        return Point(self.b.x, self.a.y)
    
    @property
    def SW(self):
        return Point(self.a.x, self.b.y)

################################################################################

if __name__ == '__main__':
    Pong.main()
