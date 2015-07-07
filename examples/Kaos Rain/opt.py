#! /usr/bin/env python3
import tkinter as _TK
import tkinter.messagebox as _MB
import winreg2 as _wi
import install as _in

################################################################################

class _Virtual:

    '_Virtual(key) -> _Virtual'

    def __init__(self, key):
        'Initialize the _Virtual object.'
        self.__map = {}
        self.__key = key
        for value in key.values:
            if value.isupper():
                data = _unpack(key.values[value])
                self[value] = data
                setattr(self, value, data)
            elif value.isdigit():
                self[int(value)] = _unpack(key.values[value])

    def __delitem__(self, name):
        return self.__map.__delitem__(name)

    def __getitem__(self, name):
        return self.__map.__getitem__(name)

    def __setitem__(self, name, value):
        return self.__map.__setitem__(name, value)

    def __del__(self):
        'Update the registry.'
        del self.__key.values
        for value in self:
            self.__key.values[str(value)] = self.__pack(self[value])

    def __iter__(self):
        'Iterate over the values in self.'
        return iter(filter(lambda value: isinstance(value, int) or isinstance(value, str) and value.isupper(), self.__map.keys()))

    __pack = staticmethod(_in.solve)

################################################################################

def _unpack(value):
    'Correctly unpack the value.'
    if isinstance(value, _wi.REG_SZ):
        return str(value.value)
    elif isinstance(value, _wi.REG_DWORD):
        return int(value.value)
    elif isinstance(value, _wi.REG_MULTI_SZ):
        return list(map(str, value.value))
    raise NotImplementedError('Cannot solve for %s' % type(value))

def _export(key, ignore):
    'Export all subkeys in key to globals.'
    try:
        GLOBAL = globals()
        root = _wi.Key(_wi.HKEY.CURRENT_USER, key)
        for key in root.keys:
            GLOBAL[key] = obj = _Virtual(_wi.Key(root, key, _wi.KEY.ALL_ACCESS))
            attr = getattr(_in, key)
            delattr(_in, key)
            if key not in ignore:
                for key in obj:
                    if isinstance(obj[key], map):
                        obj[key] = list(obj[key])
                    assert type(obj[key]) == type(attr[key]), repr(type(obj[key])) + ' != ' + repr(type(attr[key]))
                    del attr[key]
                assert not attr
        assert not sum(map(lambda name: name.isupper(), dir(_in)))
    except:
        _TK.Tk().withdraw()
        _MB.showerror('Error', 'Please install this program first.')
        raise SystemExit(1)

################################################################################

_export('Software\\Atlantis Zero\\Kaos Rain\\Version 4', ['HST'])
