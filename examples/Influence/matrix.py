#! /usr/bin/env python3
from copy import copy as copier

def _slots(names=''):
    return tuple('__' + name for name in names.replace(',', ' ').split())

################################################################################

class Matrix:

    __slots__ = _slots('data, rows, columns')

    def __init__(self, rows, columns):
        self.__data = tuple([None] * columns for row in range(rows))
        self.__rows, self.__columns = rows, columns

    def __repr__(self):
        table = Matrix(self.rows, self.columns)
        rows, columns = [0] * self.rows, [0] * self.columns
        for (row, column), value in self:
            lines = tuple(repr(value).replace('\r\n', '\n')
                          .replace('\r', '\n').split('\n'))
            table[(row, column)] = self.__yield(lines)
            rows[row] = max(rows[row], len(lines))
            columns[column] = max(columns[column], max(map(len, lines)))
        return ('\n' + '+'.join('-' * column for column in columns) + '\n') \
               .join('\n'.join('|'.join(next(table[(row, column)])
               .ljust(columns[column]) for column in range(table.columns))
               for line in range(rows[row])) for row in range(table.rows))

    def __len__(self):
        return self.rows * self.columns

    def __getitem__(self, key):
        row, column = key
        return self.__data[row][column]

    def __setitem__(self, key, value):
        row, column = key
        self.__data[row][column] = value

    def __delitem__(self, key):
        self[key] = None

    def __iter__(self):
        for row in range(self.rows):
            for column in range(self.columns):
                key = row, column
                yield key, self[key]

    def __reversed__(self):
        for row in range(self.rows - 1, -1, -1):
            for column in range(self.columns - 1, -1, -1):
                key = row, column
                yield key, self[key]

    def __contains__(self, item):
        for row in self.__data:
            if item in row:
                return True
        return False

    def freeze(self):
        self.__data = tuple(map(tuple, self.__data))

    def thaw(self):
        self.__data = tuple(map(list, self.__data))

    @property
    def rows(self):
        return self.__rows

    @property
    def columns(self):
        return self.__columns

    @staticmethod
    def __yield(lines):
        for line in lines:
            yield line
        while True:
            yield ''

################################################################################

class StrictMatrix(Matrix):

    __slots__ = _slots('klass')

    def __init__(self, rows, columns, klass):
        assert rows > 0 and columns > 0
        super().__init__(rows, columns)
        self.__klass = klass

    def __getitem__(self, key):
        row, column = key
        assert row >= 0 and column >= 0
        return super().__getitem__(key)

    def __setitem__(self, key, value):
        row, column = key
        assert row >= 0 and column >= 0
        assert value is None or isinstance(value, self.__klass)
        super().__setitem__(key, value)

    def copy(self):
        copy = type(self)(self.rows, self.columns, self.__klass)
        for key, value in self:
            if value is not None:
                copy[key] = copier(value)
        return copy

################################################################################

class Bitmap(StrictMatrix):

    __slots__ = _slots()

    def __init__(self, rows, columns):
        super().__init__(rows, columns, bool)
