#! /usr/bin/env python3
import toolbox

################################################################################

def version(major, minor=0, micro=0):
    return bytes((major, minor, micro))

################################################################################

class Service(toolbox.Struct):

    __slots__ = '__vendor', '__application', '__range'

    FORMAT = '!2p3s3sH'

    def __init__(self, vendor, application, min_version, max_version=None, *,
                 encoding='utf-8', errors='strict'):
        vendor = vendor.encode(encoding, errors)
        application = application.encode(encoding, errors)
        assert len(vendor) < 256 and len(application) < 256, \
               'Check the length of your strings!'
        self.__vendor = vendor
        self.__application = application
        self.__range = Range(min_version, max_version)

    def encode(self, port):
        return self.pack(self.FORMAT, self.__vendor, self.__application,
                         self.min_version, self.max_version, port)

    @classmethod
    def decode(cls, data):
        vendor, application, min_version, max_version, port = \
                cls.unpack(cls.FORMAT, data)
        service = cls('', '', min_version, max_version)
        service.__vendor, service.__application = vendor, application
        return service, port

    def __eq__(self, other):
        return (self.__vendor, self.__application, self.__range) == \
               (other.__vendor, other.__application, other.__range)

    @property
    def min_version(self):
        return self.__range.min_version

    @property
    def max_version(self):
        return self.__range.max_version

################################################################################

class Range:

    __slots__ = '__min_version', '__max_version'

    def __init__(self, min_version, max_version=None):
        assert isinstance(min_version, bytes) and len(min_version) == 3, \
               'Check type and length of min_version!'
        self.__min_version = min_version
        if max_version is None:
            self.__max_version = min_version
        else:
            assert isinstance(max_version, bytes) and len(max_version) == 3, \
                   'Check type and length of min_version!'
            self.__max_version = max_version
        assert self.min_version <= self.max_version, \
               'max_version may not be less than min_version!'

    def __eq__(self, other):
        # http://c2.com/cgi/wiki?TestIfDateRangesOverlap
        return self.min_version <= other.max_version and \
               other.min_version <= self.max_version

    @property
    def min_version(self):
        return self.__min_version

    @property
    def max_version(self):
        return self.__max_version
