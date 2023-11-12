from enum import Enum, auto

class IndexedEnum(Enum):
    @property
    def index(self):
        return list(self.__class__).index(self)

class MarkerStyles(IndexedEnum):
    NONE = "None"
    POINT = "."
    CROSS = "x"
    CIRCLE = "o"
    STAR = "*"
    DIAMOND = "D"
    PLUS = "+"
    PIXEL = ","
    TRIANGLE_DOWN = "v"
    TRIANGLE_UP = "^"
    TRIANGLE_LEFT = "<"
    TRIANGLE_RIGHT = ">"
    TRI_DOWN = "1"
    TRI_UP = "2"
    TRI_LEFT = "3"
    TRI_RIGHT = "4"
    OCTAGON = "8"
    SQUARE = "s"
    PENTAGON = "p"
    HEXAGON_1 = "h"
    HEXAGON_2 = "H"


class LineStyles(IndexedEnum):
    NONE = "None"
    SOLID = "-"
    DASHED = "--"
    DASH_DOT = "-."
    DOTTED = ":"

class ColorMode(IndexedEnum):
    AUTO = auto()
    THEME = auto()
    CUSTOM = auto()

class Delimiters(IndexedEnum):
    COMMA = ","
    TAB = r"\t"
    SPACE = r"\s+"
    SEMICOLON = ";"
    PIPE = r"\|"

class CommentCharacters(IndexedEnum):
    PYTHON = "#"
    MATLAB = "%"
    JAVASCRIPT = "//"
    FORTRAN = "!"