#! /usr/bin/env python3
import description
import toolbox
import broadcast
import time
import socket
import struct

################################################################################

service = description.Service('\0' * 255, '\0' * 255, description.version(0))
assert toolbox.Utility.RECEIVE == len(service.encode(0)), \
       'Please correct the RECEIVE value!'
del service

################################################################################

class Subscriber(toolbox.Utility):

    __slots__ = '__client'

    LO_TIME = 0.01
    HI_TIME = 60.0
    ATTEMPT = 10

    def __init__(self, channel):
        self.assert_user(channel)
        self.__client = broadcast.Beacon(channel)

    def discover(self, service, callback, timeout):
        assert self.LO_TIME <= timeout <= self.HI_TIME, 'Out of range timeout!'
        server, port = self.create_dyna(self.ATTEMPT)
        self.__client.send(service.encode(port))
        self.start_thread(self.__listen, callback, timeout, server)

    @classmethod
    def __listen(cls, callback, timeout, server):
        target = timeout + time.clock()
        while timeout > 0:
            server.settimeout(timeout)
            try:
                client, (ip, port) = server.accept()
                data = client.recv(cls.RECEIVE)
                client.shutdown(socket.SHUT_RDWR)
                client.close()
                service, port = description.Service.decode(data)
            except socket.error:
                break
            except struct.error:
                pass
            else:
                callback(service, (ip, port))
            timeout = target - time.clock()
        server.listen(0)
        server.close()

################################################################################

class Publisher(toolbox.Utility):

    __slots__ = '__services'

    TIMEOUT = 0.1

    def __init__(self, channel):
        self.assert_user(channel)
        server = broadcast.Beacon(channel)
        server.timeout = self.TIMEOUT
        self.__services = {object(): None}
        self.start_thread(self.__listen, self.__services, server)

    def __del__(self):
        self.__services.clear()

    @classmethod
    def __listen(cls, services, server):
        while services:
            try:
                data, (ip, port) = server.recv(cls.RECEIVE)
                request, port = description.Service.decode(data)
            except (socket.error, struct.error):
                pass
            else:
                cls.__find(services, request, (ip, port))

    @classmethod
    def __find(cls, services, request, address):
        for port, item in services.copy().items():
            if item is not None and item == request:
                cls.send(address, item.encode(port))

    def register(self, port, service):
        self.__services[port] = service

    def unregister(self, port):
        del self.__services[port]

################################################################################

def test():
    p = Publisher(4000)
    p.register(80, description.Service('IANA', 'HTTP',
                                       description.version(1),
                                       description.version(1, 1)))
    p.register(21, description.Service('IANA', 'FTP',
                                       description.version(1)))
    p.register(8080, description.Service('IANA', 'HTTP',
                                         description.version(1),
                                         description.version(2)))

    s = Subscriber(4000)
    s.discover(description.Service('IANA', 'HTTP',
                                   description.version(1, 0, 5)), echo, 0.5)

    time.sleep(1)

def echo(service, address):
    print('Found service at:', address)
    print('min_version =', tuple(service.min_version))
    print('max_version =', tuple(service.max_version))

################################################################################

if __name__ == '__main__':
    test()
