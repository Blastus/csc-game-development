#! /usr/bin/env python3
import re
import struct
import random
import socket
import _thread
import sys
import traceback

################################################################################

class Abstract:

    __slots__ = ()

    def __init__(self, *args, **kwargs):
        raise NotImplementedError('This is an abstract class!')

################################################################################

class Struct(Abstract):

    __slots__ = ()

    VALID = re.compile('^[@=<>!]?([0-9]*[xcbB?hHiIlLqQfdspP])+$')
    TOKEN = re.compile('^[@=<>!]?|[0-9]*[xcbB?hHiIlLqQfdspP]')

    @classmethod
    def pack(cls, fmt, *vs):
        prefix, tokens = cls.__tokenize(fmt)
        vs = cls.__patch(tokens, list(vs))
        return struct.pack(prefix + ''.join(tokens), *vs)

    @classmethod
    def unpack(cls, fmt, buffer):
        prefix, tokens = cls.__tokenize(fmt)
        cls.__resolve(prefix, tokens, buffer)
        return struct.unpack(prefix + ''.join(tokens), buffer)

    @classmethod
    def __tokenize(cls, fmt):
        if not cls.VALID.match(fmt):
            raise struct.error('Invalid struct format!')
        prefix, *tokens = cls.TOKEN.findall(fmt)
        cls.__expand(tokens)
        return prefix, tokens

    @staticmethod
    def __expand(tokens):
        for index, token in enumerate(tokens):
            if token.endswith('p') and len(token) > 1:
                tokens[index:index+1] = ['p'] * int(token[:-1])

    @staticmethod
    def __patch(tokens, vs):
        if len(tokens) != len(vs):
            raise struct.error('Invalid argument count!')
        for index, (token, v) in enumerate(zip(tokens, vs)):
            if token == 'p':
                size = len(v)
                tokens[index:index+1] = ['B', str(size) + 's']
                vs[index:index+1] = [size, v]
        return vs

    @staticmethod
    def __resolve(prefix, tokens, buffer):
        for index, token in enumerate(tokens):
            if token == 'p':
                char = struct.calcsize(prefix + ''.join(tokens[:index]))
                try:
                    size = buffer[char]
                except IndexError:
                    raise struct.error('Invalid data stream!')
                tokens[index:index+1] = ['x', str(size) + 's']

################################################################################

class Utility(Abstract):

    __slots__ = ()

    # http://www.iana.org/assignments/port-numbers

    LO_USER = 1024
    HI_USER = 49151
    LO_DYNA = 49152
    HI_DYNA = 65535
    RANDINT = random.SystemRandom().randint
    RECEIVE = 520

    @classmethod
    def assert_user(cls, port):
        assert cls.LO_USER <= port <= cls.HI_USER, 'Out of range port!'

    @classmethod
    def create_dyna(cls, max_tries):
        host_name = socket.gethostname()
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        for attempt in range(max_tries):
            port = cls.RANDINT(cls.LO_DYNA, cls.HI_DYNA)
            try:
                server.bind((host_name, port))
            except socket.error as exception:
                error = exception
            else:
                server.listen(5)
                return server, port
        server.close()
        raise error

    @staticmethod
    def send(address, data):
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            client.connect(address)
        except socket.error:
            pass
        else:
            client.sendall(data)
            client.shutdown(socket.SHUT_RDWR)
        client.close()

    @classmethod
    def start_thread(cls, function, *args, **kwargs):
        _thread.start_new_thread(cls.__bootstrap, (function, args, kwargs))

    @staticmethod
    def __bootstrap(function, args, kwargs):
        try:
            function(*args, **kwargs)
        except Exception:
            etype, value, tb = sys.exc_info()
            traceback.print_exception(etype, value, tb.tb_next)
            del tb
        except:
            pass
