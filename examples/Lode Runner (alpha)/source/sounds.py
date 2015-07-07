#! /usr/bin/env python3
import pickle as cPickle

################################################################################

class ConfigParser: # Helps parse XML documents.

    def __init__(self):
        self.sounds = {}

    def __getattr__(self, name):
        return Event

    def startElement(self, name, attrs):
        if name == 'Sound':
            self.__sound = attrs.getValue('name'), attrs.getValue('data_type')
        if name == 'Theme':
            self.__parse_background(attrs)
    
    def __parse_background(self, attrs):
        self.TITLE_COLOR = attrs.getValue('title_color')
        background_type = attrs.getValue('background_type')
        if background_type == 'color':
            self.BACKGROUND_COLOR = attrs.getValue('background_fill')
        elif background_type == 'picture':
            raise Exception('Picture backgrounds are not yet supported')
        else:
            raise Exception('Unknown background type')

    def characters(self, content):
        self.sounds[self.__sound[0]] = self.__sound[1], content

################################################################################

from .xml_stream import *

try:
    import winsound
    import _thread as thread
    import queue as Queue
    import time
    import os
except ImportError:
    class Server: # Dummy Class with Parser
        def __init__(self, path, history):
            # NEW - get needed configuration data
            stream = Stream(path)
            stream.minimize()
            parser = ConfigParser()
            stream.parse(parser)
            # make TITLE_COLOR and BACKGROUND_COLOR public
            self.TITLE_COLOR = parser.TITLE_COLOR
            self.BACKGROUND_COLOR = parser.BACKGROUND_COLOR
        def play(self, name, block=False):
            pass
else:

################################################################################

    class WAV: # Plays WAV data.

        def __init__(self, name):
            self.__name = name

        def play(self):
            winsound.PlaySound(self.__name, winsound.SND_FILENAME)
        

################################################################################

    class PIF: # Plays PIF (Python Interface Format [sound]) data.

        def __init__(self, data):
            data = data.split(' ')
            data = [data[index:index+3] for index in range(0, len(data), 3)]
            self.__data = [(float(secs), int(frequency), int(duration)) for secs, frequency, duration in data]

        def play(self):
            for secs, frequency, duration in self.__data:
                time.sleep(secs)
                winsound.Beep(frequency, duration)

################################################################################
            
    class Server:
        
        def __init__(self, path, history):
            # keep sound history
            # create a stream from the file on path
            # minimize the stream (for parsing purposes)
            # create a SoundParser helper object
            # parse the data into the SoundParser
            # create a dictionary (map) of sound to register
            # extract the sounds from the parser and build appropriate objects
            # create a playlist queue for incoming play requests
            # start the sound player
            self.__history = history
            stream = Stream(path)
            stream.minimize()
            parser = ConfigParser()
            stream.parse(parser)
            # make TITLE_COLOR and BACKGROUND_COLOR public
            self.TITLE_COLOR = parser.TITLE_COLOR
            self.BACKGROUND_COLOR = parser.BACKGROUND_COLOR
            self.__sounds = {}
            for key in parser.sounds:
                data_type, data = parser.sounds[key]
                if data_type == 'wav':
                    self.__sounds[key] = WAV(os.path.join(os.path.dirname(path), data))
                else:
                    assert data_type == 'pif'
                    self.__sounds[key] = PIF(data)
            self.__playlist = Queue.Queue()
            thread.start_new_thread(self.__player, ())
        
        def play(self, name, block=False):
            # make a sound play request
            # record sound request
            # if block, hold on a locked mutex
            cPickle.dump((name, block), self.__history, -1)
            if block:
                lock = thread.allocate_lock()
                lock.acquire()
                self.__playlist.put([name, lock])
                lock.acquire()
            else:
                self.__playlist.put([name])

        def __player(self):
            # play forever
            # if the playlist is empty, wait for a new request
            #     play the sound if possible
            #     release lock if present
            # else
            #     create a stack (list)
            #     empty the playlist into the stack
            #     (the most recent requests are at the top)
            #     go through the stack
            #         if the sound is registered, play it and break
            #         always release locks if present
            #     if there is anything left in the stack, release all locks
            while True:
                if self.__playlist.empty():
                    item = self.__playlist.get()
                    if item[0] in self.__sounds:
                        self.__sounds[item[0]].play()
                    if len(item) == 2:
                        item[1].release()
                else:
                    stack = []
                    while not self.__playlist.empty():
                        stack.append(self.__playlist.get())
                    while stack:
                        item = stack.pop()
                        if item[0] in self.__sounds:
                            self.__sounds[item[0]].play()
                            if len(item) == 2:
                                item[1].release()
                            break
                        elif len(item) == 2:
                            item[1].release()
                    while stack:
                        item = stack.pop()
                        if len(item) == 2:
                            item[1].release()

################################################################################
################################################################################

# HELPER CLASSES

class THM_Template:

    def __init__(self, title_color, background_color):
        # Imports for XML processing
        import xml.sax.xmlreader
        import xml.sax.saxutils
        import StringIO
        self.A = xml.sax.xmlreader.AttributesImpl
        self.X = xml.sax.saxutils.XMLGenerator
        self.S = StringIO.StringIO
        # Begin the document.
        self.__stream = [startDocument(),
                         startElement('Theme', self.A({'title_color': title_color, 'background_type': 'color', 'background_fill': background_color}))]

    def add_pif(self, name, pif):
        self.__stream.extend([startElement('Sound', self.A({'name': name, 'data_type': 'pif'})),
                              characters(str(pif)),
                              endElement('Sound')])

    def add_wav(self, name, filename):
        self.__stream.extend([startElement('Sound', self.A({'name': name, 'data_type': 'wav'})),
                              characters(filename),
                              endElement('Sound')])

    def write(self, filename):
        # make a copy of __stream
        # end the XML event stream
        # create a StringIO object
        # create an XML generator and pass it the StringIO object
        # run the event stream through the XML generator
        # create a new stream from StringIO object's value
        # maximize the stream with 4 spaces
        # write the XML document to file
        stream = self.__stream[:]
        stream.extend([endElement('Theme'),
                       endDocument()])
        string = self.S()
        parser = self.X(string)
        for event in stream:
            event(parser)
        stream = Stream(string.getvalue())
        stream.maximize('    ')
        stream.parse(self.X(open(filename, 'w')))

################################################################################

class PIF_Template:

    def __init__(self):
        self.__data = []

    def __str__(self):
        return ' '.join(map(str, self.__data))

    def code(self):
        return '.'.join([type(self).__name__ + '()'] + ['add(%s, %s, %s)' % tuple(args) for args in (self.__data[index:index+3] for index in range(0, len(self.__data), 3))])

    def add(self, secs, frequency, duration):
        self.__data.extend([float(secs), int(frequency), int(duration)])
        return self

    def sub(self, count=1):
        count = int(count)
        if count < 0:
            self.__data = []
        else:
            self.__data = self.__data[:-3*count]
        return self

    def play(self):
        # Listen to the current PIF information.
        PIF(str(self)).play()
