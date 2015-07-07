#! /usr/bin/env python3
import tkinter
import tkinter.ttk as ttk
import functools
import random
import tkinter.messagebox

from Logic3 import Influence
from matrix import StrictMatrix
from maps import IslandMap, FriendMap

try:
    from winsound import PlaySound, SND_FILENAME, SND_ASYNC
except ImportError:
    music = None
    play = lambda filename: None
else:
    import music
    play = lambda filename: PlaySound(filename, SND_FILENAME | SND_ASYNC)

################################################################################

class Board(ttk.Frame):

    "Board(master, island_map_callback, friend_map) -> Board instance"

    COLORS = 'red', 'green', 'yellow', 'purple', 'blue', 'orange'   # Players
    GROW_BY = 1         # Number to increment population by.
    BLINK_PAUSE = 500   # Milliseconds between blink change.
    SHIFT_PAUSE = 200   # Milliseconds between board balances.
    FINAL_PAUSE = 500   # Milliseconds between end-game balances.
    SOUND_LIMIT = 150   # Minimum speed at which blast will play.

    __slots__ = ('__island_map_callback', '__friend_map', '__island_map',
                 '__logic', '__button_frame', '__buttons', '__default_color',
                 '__options', '__id', '__new_game', '__user_settings',
                 '__people', '__spinbox', '__KO', '__check', '__done',
                 '__blink')

    # ==================================================================== #

    def __init__(self, master, island_map_callback, friend_map, **kw):
        "Initialize a board object that contains the GUI of the game."
        super().__init__(master, **kw)
        self.__island_map_callback = island_map_callback
        self.__friend_map = friend_map
        self.__build_logic()
        self.__build_islands()
        self.__build_options()
        self.__done = False
        self.__blink = None

    def __build_logic(self, people=2, knockout=True):
        "Create the island map and logic for the board."
        while True:
            try:
                island_map = self.__island_map = self.__island_map_callback()
                self.__logic = Influence(island_map, self.__friend_map,
                                         self.COLORS[:people], knockout)
            except AssertionError:
                pass
            else:
                return

    def __build_islands(self):
        "Generate the buttons that form the face of the islands."
        frame = self.__button_frame = ttk.Labelframe(self, text='Islands')
        island_map = self.__island_map
        self.__buttons = StrictMatrix(island_map.rows,
                                      island_map.columns,
                                      tkinter.Button)
        for key, value in island_map:
            button = self.__buttons[key] = tkinter.Button(frame)
            # Configure Button
            command = functools.partial(self.__click, button, key)
            button.configure(height=1, width=2, text='0', command=command)
            # Position The Button
            row, column = key
            button.grid(column=column, row=row, padx=2, pady=2)
            if not value:
                button.grid_remove()
            else:
                # Create Some Bindings
                friends = self.__logic.islands[key].friends
                enter_button = functools.partial(self.__enter, friends)
                button.bind('<Enter>', enter_button)
                exit_button = functools.partial(self.__exit, friends)
                button.bind('<Leave>', exit_button)
        self.__default_color = self.__buttons[(0, 0)]['bg']
        frame.grid(row=0, column=0, padx=4, pady=4)

    def __build_options(self):
        "Create the options at the bottom of the game frame."
        options = self.__options = ttk.Labelframe(self, text='Options')
        # Indicator
        self.__id = tkinter.Button(options, state=tkinter.DISABLED,
                                   bg=self.COLORS[0], text=' ')
        # Start New Game
        self.__id.grid(row=0, column=0, columnspan=2,
                       padx=2, pady=2, sticky=tkinter.EW)
        game = self.__new_game = tkinter.Button(options, text='New Game',
                                                command=self.__restart)
        game.grid(row=1, column=0, padx=2, pady=2, sticky=tkinter.NSEW)
        # Number Of Players & KO Settings
        user = self.__user_settings = ttk.Labelframe(options, text='Players')
            # Create The People Count
        self.__people = tkinter.StringVar(user)
        self.__spinbox = tkinter.Spinbox(user, from_=2, to=len(self.COLORS),
                                         textvariable=self.__people,
                                         width=5)
        self.__spinbox.grid(row=0, column=0, padx=2, pady=2)
            # Create The Knockout Box
        KO = self.__KO = tkinter.StringVar(user)
        KO.set('false')
        self.__check = ttk.Checkbutton(user, text='Knockout', variable=KO,
                                       onvalue='true', offvalue='false')
        self.__check.grid(row=0, column=1, padx=2, pady=2)
            # END
        user.grid(row=1, column=1, padx=2, pady=2)
        # Place The Options
        options.grid_columnconfigure(0, weight=1)
        options.grid(row=1, column=0, padx=4, pady=4, sticky=tkinter.EW)

    # ==================================================================== #

    def __enter(self, friends, event):
        "Begin blinking buttons related to button under the cursor."
        if not self.__done:
            self.__do_blink(friends, True)

    def __do_blink(self, friends, hide, repeat=True):
        "Blink the friend buttons and reschedule as necessary."
        if hide:
            for friend in friends:
                self.__buttons[friend].configure(bg='black', fg='white')
        else:
            for friend in friends:
                button = self.__buttons[friend]
                button['bg'] = self.__color(
                    self.__logic.islands[friend].faction)
                button['fg'] = 'black'
        if repeat:
            self.__blink = self.after(self.BLINK_PAUSE,
                                      self.__do_blink, friends, not hide)

    def __exit(self, friends, event):
        "Stop blinking the buttons and reset them to their original state."
        if self.__blink is not None:
            self.after_cancel(self.__blink)
            self.__blink = None
            self.__do_blink(friends, False, False)

    # ==================================================================== #

    def __restart(self):
        "Restart the game with respect to the current options."
        try:
            people = int(self.__people.get())
        except ValueError:
            self.__people.set('2')
            people = 2
        knockout = {'true': True, 'false': False}[self.__KO.get()]
        self.__build_logic(people, knockout)
        self.__button_frame.destroy()
        self.__build_islands()
        self.__done = False

    def __click(self, button, position):
        "Handle the player clicking on one of the button islands."
        self.__logic.bless(position, self.GROW_BY)
        island = self.__logic.islands[position]
        button['bg'] = self.__color(island.faction)
        button['text'] = str(island.population)
        self.__check_state()

    # ==================================================================== #

    def __check_state(self, shift_pause=None):
        "Test the state of the game and balance board if needed."
        if not self.__done and self.__logic.complete:
            self.__done = True
            color = self.__logic.current_faction.info.capitalize()
            text = color + ' has taken control of the board!'
            tkinter.messagebox.showinfo('Congratulations!', text,
                                        master=self)
        if self.__logic.critical:
            if self.__done:
                shift_pause = self.FINAL_PAUSE
            elif shift_pause is None:
                shift_pause = self.SHIFT_PAUSE
            self.after(shift_pause, self.__balance, max(shift_pause - 1, 10))
        else:
            self.__id['bg'] = self.__logic.current_faction.info
            if shift_pause is not None and shift_pause <= self.SOUND_LIMIT:
                play('blast.wav')

    def __balance(self, shift_pause):
        "Balance the board until there are no critical islands."
        if shift_pause > self.SOUND_LIMIT:
            play('blast.wav')
        self.__logic.spread()
        for key, value in self.__logic.islands:
            if value is not None:
                button = self.__buttons[key]
                button.configure(text=str(value.population),
                                 bg=self.__color(value.faction), fg='black')
        self.__check_state(shift_pause)

    # ==================================================================== #

    def __color(self, faction):
        "Help select a color based on the given faction."
        return self.__default_color if faction is None else faction.info

################################################################################

def main():
    "Start both the music and GUI of application."
    if music is not None:
        music.start('background.wav')
    tkinter.NoDefaultRoot()
    root = tkinter.Tk()
    root.resizable(False, False)
    root.title('Influence')
    root.wm_iconbitmap(default='favicon.ico')
    gui = Board(root, make_island_map, make_friend_map())
    gui.grid()
    root.mainloop()

def make_island_map(height=10, width=10, emptiness=0.4):
    "Generate a board with island positions."
    islands = IslandMap(height, width)
    for key, value in islands:
        islands[key] = random.random() > emptiness
    islands.freeze()
    return islands

def make_friend_map(height=3, width=3, x_center=1, y_center=1):
    "Create a map/cursor defining island relationships."
    friends = FriendMap(height, width, (x_center, y_center))
    for key, value in friends:
        friends[key] = bool(sum(key) & 1)
    friends.freeze()
    return friends
