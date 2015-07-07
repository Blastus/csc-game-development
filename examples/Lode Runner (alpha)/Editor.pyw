#! /usr/bin/env python3
import pickle as cPickle
import os
import tempfile
import tkinter as Tkinter
import tkinter.filedialog as tkFileDialog
import tkinter.messagebox as tkMessageBox
import zlib

################################################################################

def main():
    global root, dialog
    root = Tkinter.Tk()
    dialog = tkFileDialog.Open(title='Game Video', filetypes=['Video .gva', 'Audio/Video .gvb'])
    root.resizable(False, False)
    root.title('Editor')
    Tkinter.Label(root, text='You can divide your video into scenes\nor merge several videos together.', padx=5, pady=5).grid(row=0, sticky=Tkinter.NSEW)
    Tkinter.Button(root, text='Divide Scenes', command=split).grid(row=1, sticky=Tkinter.NSEW)
    Tkinter.Button(root, text='Merge Videos', command=join).grid(row=2, sticky=Tkinter.NSEW)
    root.mainloop()

def split():
    # hide the main menu
    root.withdraw()
    # get source and destination information
    source = askopenfile()
    if source:
        destination = tkFileDialog.askdirectory(title='Where should the new files be saved?', mustexist=True)
        if destination:
            # decompress and cache the video
            temp = decompress_and_cache(source)
            # extract filename information
            parts = os.path.basename(source.name).split('.')
            name = '.'.join(parts[:-1])
            extention = parts[-1]
            # setup some data variables
            frame = cPickle.load(temp)
            current_height, current_width = len(frame), len(frame[0])
            EOF, scene = False, 0
            # process the scenes in the video
            while not EOF:
                # create a sink for the data
                sink = tempfile.TemporaryFile()
                while True:
                    # dump the frame
                    cPickle.dump(frame, sink, -1)
                    # load another frame
                    try:
                        frame = cPickle.load(temp)
                    except:
                        # EOF has been reached
                        EOF = True
                        break
                    # save all audio
                    while isinstance(frame, tuple):
                        # dump the audio
                        cPickle.dump(frame, sink, -1)
                        # load another frame
                        try:
                            frame = cPickle.load(temp)
                        except:
                            # EOF has been reached
                            EOF = True
                            frame = None
                    if frame is None:
                        # EOF has been reached
                        break
                    # check the dimentions
                    height, width = len(frame), len(frame[0])
                    # if height or width are not equal, the scene is over
                    if height != current_height or width != current_width:
                        # update the dimentions and save the scene
                        current_height, current_width = height, width
                        break
                # update the scene counter
                scene += 1
                # compress and save the sink
                sink.seek(0)
                open(os.path.join(destination, '%s-S%s.%s' % (name, scene, extention)), 'wb').write(zlib.compress(sink.read(), 9))
                sink.close()
    # bring the menu back
    root.deiconify()
    root.focus_force()

def askopenfile():
    # file dialog that remembers last location
    filename = dialog.show()
    if filename:
        return open(filename, 'rb')

def decompress_and_cache(video_file):
    # create a cache
    # decompress the video file and save it
    # close the video file
    # rewind and return the cache for use
    cache = tempfile.TemporaryFile()
    cache.write(zlib.decompress(video_file.read()))
    video_file.close()
    cache.seek(0)
    return cache

def join():
    # hide the main menu
    root.withdraw()
    # acquire and open videos to merge
    videos = get_videos()
    if videos:
        # merge videos and acquire sink
        sink = merge_videos(videos)
        # calculate the required file extention
        GVB = 'gvb' in [os.path.basename(video.name).split('.')[-1].lower() for video in videos]
        # open a customized "Save As" dialog box
        if GVB:
            filename = tkFileDialog.asksaveasfilename(title='Save Video As', filetypes=['Audio/Video .gvb'])
        else:
            filename = tkFileDialog.asksaveasfilename(title='Save Video As', filetypes=['Video .gva'])
        # check that a filename was entered
        if filename:
            # determine the correct extention
            if GVB:
                extention = '.gvb'
            else:
                extention = '.gva'
            # clean the filename
            if not filename.lower().endswith(extention):
                filename += extention
            # compress and save the sink
            open(filename, 'wb').write(zlib.compress(sink.read(), 9))
        # discard the sink
        sink.close()
    # bring the menu back
    root.deiconify()
    root.focus_force()

def get_videos():
    # create a list of videos
    videos = []
    # prime the acquisition mechanism
    source = askopenfile()
    if source:
        videos.append(source)
        # acquire videos while user answers "yes"
        while tkMessageBox.askyesno('Continue', 'Do you want to add another video?'):
            source = askopenfile()
            if source:
                videos.append(source)
            else:
                # the user is done
                break
    return videos

def merge_videos(videos):
    # create a sink for the merged data
    sink = tempfile.TemporaryFile()
    for video in videos:
        # decompress and cache the video
        temp = decompress_and_cache(video)
        # write the data until (EOF) error
        try:
            while True:
                cPickle.dump(cPickle.load(temp), sink, -1)
        except:
            pass
        # close the decompressed video
        temp.close()
    # rewind and return the sink
    sink.seek(0)
    return sink

################################################################################

if __name__ == '__main__':
    main()
