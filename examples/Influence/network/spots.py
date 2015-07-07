#! /usr/bin/env python3
# Send Python Object Through Socket

import os
import pickle
import threading
import time

class SPOTS:

    __slots__ = 'dump', 'load'

    def __init__(self, socket):
        self.dump = pickle.Pickler(socket.makefile('wb', 0)).dump
        self.load = pickle.Unpickler(socket.makefile('rb', 0)).load

class TimeoutError(Exception): pass

class Processor (threading.Thread):

    def __init__(self, spots, **event_handlers):
        super().__init__()
        self.__spots = spots
        self.__error = event_handlers.pop('error', lambda _: None)
        self.__event = event_handlers

    def run(self):
        while True:
            event, arg = self.__spots.load()
            try:
                self.__event[event](arg)
            except Exception as error:
                self.__error(error)

    def new(self, event, arg):
        self.__spots.dump((event, arg))

    def register(self, event, handler):
        self.__event[event] = handler

    def unregister(self, event):
        del self.__event[event]

class Dispatcher:

    def __init__(self, spots, **services):
        self.__services = services
        self.__requests = {}
        self.__processor = Processor(spots, error=self.error,
                                     request=self.handle_request,
                                     response=self.handle_response)
        self.__processor.start()

    def error(self, exception):
        print('Error:', exception)

    def handle_request(self, data):
        uuid, name, args, kwargs = data
        try:
            value = True, self.__services[name](*args, **kwargs)
        except Exception as error:
            value = False, error
        self.__processor.new('response', (uuid, value))

    def handle_response(self, data):
        uuid, value = data
        request = self.__requests.pop(uuid, None)
        if request is not None:
            request.put(value)

    def call(self, name, args=(), kwargs={}, timeout=-1):
        uuid = os.urandom(16)
        self.__requests[uuid] = request = Courier()
        self.__processor.new('request', (uuid, name, args, kwargs))
        if request.wait(timeout):
            okay, value = request.get()
            if okay:
                return value
            raise value
        self.__requests.pop(uuid, None)
        raise TimeoutError()

class Courier:

    def __init__(self):
        self.__lock = threading.Lock()
        self.__lock.acquire()
        self.__value = None

    def wait(self, timeout=-1):
        return self.__lock.acquire(True, timeout)

    def put(self, value):
        self.__value = value
        self.__lock.release()

    def get(self):
        return self.__value

################################################################################

import socket

if True:
    server = socket.socket()
    server.bind(('', 8080))
    server.listen(5)
    connection, address = server.accept()
    spot = SPOTS(connection)
else:
    client = socket.socket()
    client.connect(('localhost', 8080))
    spot = SPOTS(client)

d = Dispatcher(spot, max=max, min=min, sum=sum, all=all, any=any,
               sleep=time.sleep, print=print)
