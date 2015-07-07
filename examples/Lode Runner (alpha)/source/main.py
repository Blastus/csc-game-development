#! /usr/bin/env python3
from . import boards
from . import sounds
from . import util
import random
import tempfile
import tkinter.filedialog
import tkinter.messagebox
import zlib

################################################################################

class Player:

    def __init__(self, screen, face, row=1, column=10):
        self.screen = screen
        self.face = face
        self.row = row
        self.column = column
        self.vector = 0, 0

    def move(self):
        global playing, you, players
        context = self.screen.read(self.row, self.column)
        left = self.screen.read(self.row, self.column - 1)
        right = self.screen.read(self.row, self.column + 1)
        x, y = self.vector
        x_move = False
        # if on the floor
        if context == '_' or context == '*':
            self.column += x
            x_move = True
        # if on transporter
        elif context == '@':
            if left is not None and left in '_*|' and x == -1:
                self.column += x
            elif right is not None and right in '_*|' and x == 1:
                self.column += x
            else:
                if self.screen.read(self.row + 1, self.column) == '|' and y == 1:
                    self.row += y
                elif self.screen.read(self.row - 1, self.column) == '|' and y == -1:
                    self.row += y
                else:
                    self.row += 1
        # if on a ladder
        elif context == '|':
            self.row += y
        # if in the air
        elif context == ' ':
            if self.screen.read(self.row + 1, self.column) != '|' or y == 1:
                # you may go down a ladder or fall
                self.row += 1
            else:
                # you may jump off a ladder
                self.column += x
        # you may get off a ladder
        if not x_move and context != ' ':
            if left is not None and left in '_*' and x == -1:
                self.column += x
            elif right is not None and right in '_*' and x == 1:
                self.column += x
        # show the new position
        self.screen.write(self.row, self.column, self.face)
        # if off the screen
        if self.screen.read(self.row, self.column) is None:
            if self is you:
                # kill the game
                playing = False
            else:
                # kill the robot
                players.remove(self)
                sound.play('kill')
        # if at a teleporter
        elif self.screen.cache_read(self.row, self.column) == '@':
            first, second = self.screen.find('@')
            if first[0] == self.row and first[1] == self.column:
                # transfer to second teleporter
                self.row, self.column = second
            else:
                # goto first teleporter
                self.row, self.column = first
            # show the new position as well
            self.screen.write(self.row, self.column, self.face)
            # play a sound
            sound.play('zip')

################################################################################

class You(Player):

    def __init__(self, screen, face, row=0, column=10):
        Player.__init__(self, screen, face, row, column)
        self.score = 0

    def setDirection(self, command): # REVISED - V7
        context = self.screen.read(self.row, self.column)
        if context == '*':
            self.score += 10
            self.screen.cache_write(self.row, self.column, '_')
            sound.play('score')
        if command == 'up':
            self.vector = 0, -1
        elif command == 'down':
            self.vector = 0, +1
        elif command == 'left':
            self.vector = -1, 0
        elif command == 'right':
            self.vector = +1, 0
        elif command == 'stop':       # NEW - V7
            self.vector = 0, 0
        elif command == 'cut_left':
            if self.screen.cache_read(self.row, self.column - 1) != '@':
                self.screen.cache_write(self.row, self.column - 1, ' ')
        elif command == 'cut_right':
            if self.screen.cache_read(self.row, self.column + 1) != '@':
                self.screen.cache_write(self.row, self.column + 1, ' ')

class Robot(Player):

    def __init__(self, screen, face, row=0, column=10):
        Player.__init__(self, screen, face, row, column)
        self.move_count = 0

    def move(self):
        if self.screen.read(self.row, self.column) == ' ':
            Player.move(self)
        else:
            self.move_count += 1
            if self.move_count % 2:
                Player.move(self)
            else:
                self.screen.write(self.row, self.column, self.face)

    def setDirection(self, key):
        global playing, you
        # The robot caught you (player).
        if you.row == self.row and you.column == self.column:
            playing = False
        # Change columns (horizontal direction) if needed.
        if self.column > you.column:
            self.vector = -1, 0
        elif self.column < you.column:
            self.vector = +1, 0
        # Changing rows (height) takes priority.
        if self.row != you.row:
            context = self.screen.read(self.row, self.column)
            below = self.screen.read(self.row + 1, self.column) or ''
            if context == '|' or (below == '|' and context not in '_*' and self.row < you.row):
                # You are higher -- robot goes up.
                if self.row > you.row:
                    self.vector = 0, -1
                # There is a floor, load, ladder, or portal under the robot
                # -- or you are under the robot -- the robot goes down.
                elif below in '_*|@' or self.column == you.column:
                    self.vector = 0, +1
                else:
                    # Find out if there is anything to land on.
                    look_down = 2
                    eye = self.screen.read(self.row + look_down, self.column)
                    while eye and eye not in '_*|@':
                        look_down += 1
                        eye = self.screen.read(self.row + look_down, self.column)
                    # If so, go through with "jumping" down.
                    if eye and eye in '_*|@':
                        self.vector = 0, +1

################################################################################

ROBOTS = 3

def check():
    return run and playing

def callback():
    global clock, screen, win_condition, run, keys, note
    clock += 1
    if clock > 40 and len(players) - 1 < ROBOTS:
        players.append(Robot(screen, '&', column=random.randrange(width))) # NEW - V6
    key = keys
    keys = ''
    for player in players:
        player.setDirection(key)
        player.move()
    screen.update()
    if you.score == win_condition:
        run = False
    if note:
        sound.play('move_high')
    else:
        sound.play('move_low')
    note = not note

def dispatch(string, event=None):
    global keys
    keys += string

def engine(SELECT):
    global playing, you, players, clock, screen, win_condition, run, keys, note, width
    keys = ''
    run = True
    screen = util.Screen3(boards.boards[SELECT], callback, check, dispatch, root)
    width = len(boards.boards[SELECT].board().splitlines()[1]) # NEW - V6
    win_condition = boards.boards[SELECT].board().count('*') * 10
    you = You(screen, '^')
    screen.update()
    players = [you]
    clock = 0
    playing = True
    note = False
    # Game Loop
    try:
        screen.root.mainloop()
    except SystemExit as error:
        v = error.args[0]
        if hasattr(v, 'args'):
            v = v.args[0]
        if v:
            raise
    # End Game Loop
    screen.update()
    if you.score == win_condition:
        sound.play('win', True)
    else:
        sound.play('lose', True)

################################################################################

class Call:

    def __init__(self, function, *args):
        self.__function = function
        self.__args = args

    def __call__(self, *args):
        self.__function(*self.__args)

util.Call = Call # Py3.X fix

def set_theme(theme):
    util.Screen3.IMAGE_THEME = theme
    root.withdraw()
    raise SystemExit(False)

def shutdown():
    root.destroy()
    raise SystemExit(True)

def select_theme():
    global root
    # "imports"
    os = util.os
    Tkinter = util
    # Menu Code
    root = Tkinter.Tk()
    root.resizable(False, False)
    root.title('Main Menu')
    root.protocol('WM_DELETE_WINDOW', shutdown)
    Tkinter.Label(root, text='Choose a theme to use during game play.', padx=5, pady=5).grid(row=0, sticky='news')
    # Dynamic Menu
    for row, theme in enumerate(path for path in sorted(os.listdir('themes')) if os.path.isdir(os.path.join('themes', path))):
        Tkinter.Button(root, text=theme.replace('_', ' ').title(), command=Call(set_theme, theme)).grid(row=row+1, sticky='news')
    try:
        root.mainloop()
    except SystemExit as error:
        v = error.args[0]
        if hasattr(v, 'args'):
            v = v.args[0]
        if v:
            raise

################################################################################

def load_images():
    # __load_images
    Tkinter, os = util, util.os
    util.Screen3.IMAGES = dict((key, Tkinter.PhotoImage(file=os.path.join(os.getcwd(), 'themes', util.Screen3.IMAGE_THEME, util.Screen3.IMAGE_SIZE, util.Screen3.IMAGE_MAP[key] + '.gif'))) for key in util.Screen3.IMAGE_MAP)
    # __check_and_config
    first = True
    for key in util.Screen3.IMAGES:
        image = util.Screen3.IMAGES[key]
        if first:
            first = False
            h = image.height()
            w = image.width()
        else:
            assert image.height() == h
            assert image.width() == w
    util.Screen3.IMAGE_WIDTH = w
    util.Screen3.IMAGE_HEIGHT = h

def load_sounds(history):
    global sound
    sound = sounds.Server(util.os.path.join(util.os.getcwd(), 'themes', util.Screen3.IMAGE_THEME, 'theme_config.xml'), history)
    # NEW - load theme's colors as well
    util.Screen3.TITLE_COLOR = sound.TITLE_COLOR
    util.Screen3.BACKGROUND_COLOR = sound.BACKGROUND_COLOR

################################################################################

# NEW - Version 6

class DummyFile: # Create a fake file.
    def __getattr__(self, name):
        return self.method
    def method(self, *args, **kwargs):
        pass

def main():
    select_theme()
    load_images()
    history = setup_save()
    load_sounds(history)
    try:
        for SELECT in range(len(boards.boards)):
            engine(SELECT)
    finally:
        save_game_play()

def setup_save():
    # Find out if the user wishes to save a video.
    if tkinter.messagebox.askyesno('Video', 'Do you want to record your game?'):
        util.Screen3.HISTORY = tempfile.TemporaryFile()
    else:
        util.Screen3.HISTORY = DummyFile()
    return util.Screen3.HISTORY

def save_game_play():
    if not isinstance(util.Screen3.HISTORY, DummyFile):
        # get and close buffer
        util.Screen3.HISTORY.seek(0)
        value = util.Screen3.HISTORY.read()
        util.Screen3.HISTORY.close()
        # only process buffer if it has data
        if value:
            # get the filename
            filename = tkinter.filedialog.asksaveasfilename(title='Save Video As', filetypes=['Audio/Video .gvb'])
            if filename:
                # clean the filename
                if not filename.lower().endswith('.gvb'):
                    filename += '.gvb'
                open(filename, 'wb').write(zlib.compress(value, 9))
