#! /usr/bin/env python3
import matrix

################################################################################

class IslandMap(matrix.Bitmap):

    __slots__ = matrix._slots()

################################################################################

class Cursor(matrix.Bitmap):

    __slots__ = matrix._slots('x, y')

    def __init__(self, rows, columns, center):
        x, y = self.__x, self.__y = center
        assert 0 <= x < columns and 0 <= y < rows
        super().__init__(rows, columns)

    def freeze(self):
        rows, columns = self.rows, self.columns
        assert any(self[(i, 0)] for i in range(rows))
        assert any(self[(0, i)] for i in range(columns))
        r, c = rows - 1, columns - 1
        assert not r or any(self[(r, i)] for i in range(columns))
        assert not c or any(self[(i, c)] for i in range(rows))
        super().freeze()

    @property
    def x(self):
        return self.__x

    @property
    def y(self):
        return self.__y

################################################################################

class FriendMap(Cursor):

    __slots__ = matrix._slots()
