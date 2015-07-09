import random
import tkinter


def main():
    tkinter.NoDefaultRoot()
    simon = Game()
    simon.resizable(False, False)
    simon.title('Simon Says')
    simon.mainloop()


class Game(tkinter.Tk):

    def __init__(self, screen_name=None, base_name=None, class_name='Tk',
                 use_tk=1, sync=0, use=None):
        super().__init__(screen_name, base_name, class_name, use_tk, sync, use)
        defaults = dict(font='Courier 10', width=10, height=5)
        self.red_button = tkinter.Button(self, bg='red', **defaults)
        self.yellow_button = tkinter.Button(self, bg='yellow', **defaults)
        self.green_button = tkinter.Button(self, bg='green', **defaults)
        self.blue_button = tkinter.Button(self, bg='blue', **defaults)
        self.status_message = tkinter.StringVar(self)
        self.pattern = []
        self.status = tkinter.Label(self, textvariable=self.status_message)
        self.red_button.grid(row=0, column=0, padx=5, pady=5)
        self.yellow_button.grid(row=0, column=1, padx=5, pady=5)
        self.green_button.grid(row=1, column=0, padx=5, pady=5)
        self.blue_button.grid(row=1, column=1, padx=5, pady=5)
        self.status.grid(row=2, column=0, columnspan=2)
        self.startup_sequence = ('Welcome to the game Simon Says!',
                                 'Let us play a game together.',
                                 self.next_level)
        self.animation_sequence = (self.show_level,
                                   'Watch the following sequence.',
                                   self.blink_buttons,
                                   'Try to repeat the same sequence.',
                                   self.wait_input)
        self.after_idle(self.run, self.startup_sequence)

    def run(self, sequence):
        head, *sequence = sequence
        if isinstance(head, str):
            self.status_message.set(head)
            self.after(5000, self.run, sequence)
        elif callable(head):
            head(sequence)

    def next_level(self, _):
        self.pattern.append(random.choice('red yellow green blue'.split()))
        self.after_idle(self.run, self.animation_sequence)

    def show_level(self, sequence):
        self.disable_buttons()
        self.status_message.set('Level ' + str(len(self.pattern)))
        self.after(5000, self.run, sequence)

    def disable_buttons(self):
        self.red_button['state'] = tkinter.DISABLED
        self.yellow_button['state'] = tkinter.DISABLED
        self.green_button['state'] = tkinter.DISABLED
        self.blue_button['state'] = tkinter.DISABLED

    def blink_buttons(self, sequence, index=0, restore=False):
        if index < len(self.pattern):
            color = self.pattern[index]
            if restore:
                self.set_button_color(color, color)
                self.after(500, self.blink_buttons, sequence, index + 1)
            else:
                self.set_button_color(color, 'white')
                self.after(500, self.blink_buttons, sequence, index, True)
        else:
            self.after(1000, self.run, sequence)

    def set_button_color(self, button_name, button_color):
        getattr(self, button_name + '_button')['background'] = button_color

    def wait_input(self, sequence):
        pass

if __name__ == '__main__':
    main()
