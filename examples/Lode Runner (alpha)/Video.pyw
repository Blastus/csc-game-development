#! /usr/bin/env python3
import source.main as Demo

################################################################################

class Screen(Demo.util.Screen3):

    def __init__(self, start_frame, callback, root):
        # setup history and handle buffers
        height = len(start_frame)
        width = len(start_frame[0])
        # key = environment_key, actor_key
        # handle = environment_handle, actor_handle
        self.keys = [[[None, None] for column in range(width)] for row in range(height)]
        self.hand = [[[None, None] for column in range(width)] for row in range(height)]
        self.call = callback
        # ROOT
        self.root = Demo.util.Toplevel(root)
        self.root.overrideredirect(True)
        # PIXELS
        w = width * self.IMAGE_WIDTH + 3
        h = height * self.IMAGE_HEIGHT + 3
        x = self.root.winfo_screenwidth()
        y = self.root.winfo_screenheight()
        # configure position
        self.root.geometry('%dx%d+%d+%d' % (w, h, (x - w) / 2, (y - h) / 2))
        self.root.focus_force()
        # quit program
        self.root.protocol('WM_DELETE_WINDOW', self.exit)
        self.root.bind_all('<Escape>', self.exit)
        # CANVAS
        self.canvas = Demo.util.Canvas(self.root, width=w, height=h)
        self.canvas.config(background=self.BACKGROUND_COLOR)
        self.canvas.pack()
        # Start the screen
        self.start(start_frame)
        # video loop
        self.canvas.after(125, self.after_loop)

    def exit(self, *args):
        self.root.destroy()
        raise SystemExit(True)

    def start(self, frame):
        for rnum, row in enumerate(frame):
            for cnum, key in enumerate(row):
                env, act = key
                # There will be no actors on the first frame.
                self.keys[rnum][cnum][0] = env
                if env in self.IMAGES:
                    c = self.coords(cnum, rnum)
                    handle = self.canvas.create_image(c, image=self.IMAGES[env])
                    self.hand[rnum][cnum][0] = handle
        # update the canvas
        self.canvas.update()

    def coords(self, cnum, rnum):
        x = cnum * self.IMAGE_WIDTH + self.IMAGE_WIDTH // 2 + 1
        y = rnum * self.IMAGE_HEIGHT + self.IMAGE_HEIGHT // 2 + 1
        return x, y

    def after_loop(self):
        try:
            self.call()
            self.canvas.after(125, self.after_loop)
        except AssertionError:
            self.root.destroy()
            raise SystemExit(False)
        except:
            self.exit()

    def update(self, frame):
        for rnum, row in enumerate(frame):
            for cnum, key in enumerate(row):
                env, act = key
                # DRAW ACTORS
                act_key = self.keys[rnum][cnum][1]
                act_hand = self.hand[rnum][cnum][1]
                if act != act_key: # if the keys are different
                    if act_hand is not None: # if there is an image
                        self.canvas.delete(act_hand) # delete it
                    if act is not None: # if there is a picture
                        c = self.coords(cnum, rnum)
                        handle = self.canvas.create_image(c, image=self.IMAGES[act])
                        self.hand[rnum][cnum][1] = handle
                    else:
                        self.hand[rnum][cnum][1] = None
                    self.keys[rnum][cnum][1] = act # new key
                # DRAW ENVIRONMENT
                env_key = self.keys[rnum][cnum][0]
                env_hand = self.hand[rnum][cnum][0]
                if env != env_key: # keys are different
                    if env_hand is not None: # image already there
                        self.canvas.delete(env_hand)
                    if env != ' ': # there is true environment
                        c = self.coords(cnum, rnum)
                        handle = self.canvas.create_image(c, image=self.IMAGES[env])
                        self.hand[rnum][cnum][0] = handle
                        # make sure enviroment doesn't cover actors
                        act_hand = self.hand[rnum][cnum][1]
                        if act_hand is not None:
                            self.canvas.tag_raise(act_hand, handle)
                    else:
                        self.hand[rnum][cnum][0] = None
                    self.keys[rnum][cnum][0] = env # new key
        # update the canvas
        self.canvas.update()

################################################################################

def main():
    # Provide menus and load the data.
    Demo.select_theme()
    history = load_video()
    Demo.load_images()
    load_sounds()
    # Show the video and close the buffer.
    try:
        play(history)
    finally:
        history.close()

def load_video():
    filename = Demo.tkinter.filedialog.askopenfilename(title='Open Video', filetypes=['Video .gva', 'Audio/Video .gvb'])
    if filename:
        history = Demo.tempfile.TemporaryFile()
        data = Demo.zlib.decompress(open(filename, 'rb').read())
        history.write(data)
        del data
        history.seek(0)
        return history
    else:
        raise SystemExit

def load_sounds():
    global sound
    sound = Demo.sounds.Server(Demo.util.os.path.join(Demo.util.os.getcwd(), 'themes', Screen.IMAGE_THEME, 'theme_config.xml'), Demo.DummyFile())
    Screen.BACKGROUND_COLOR = sound.BACKGROUND_COLOR

################################################################################

def play(history):
    global frames, screen, c_height, c_width, frame
    frames = history
    # setup first frame
    frame = Demo.util.cPickle.load(history)
    while True:
        c_height = len(frame)
        c_width = len(frame[0])
        # make screen
        screen = Screen(frame, updater, Demo.root)
        try:
            screen.root.mainloop()
        except SystemExit as error:
            v = error.args[0]
            if hasattr(v, 'args'):
                v = v.args[0]
            if v:
                break

def updater():
    global frame
    # load the next frame
    frame = Demo.util.cPickle.load(frames)
    # check to see if it is a sound
    while isinstance(frame, tuple):
        sound.play(*frame)
        frame = Demo.util.cPickle.load(frames)
    # frame size
    height = len(frame)
    width = len(frame[0])
    # check to see if a new screen needs to be built
    assert height == c_height and width == c_width
    # update the current frame
    screen.update(frame)

################################################################################

if __name__ == '__main__':
    main()
