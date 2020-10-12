import typing
from copy import deepcopy
from enum import Enum
from enum import IntEnum

SIZE: int = 8


class ColorEnum(IntEnum):
    WHITE = 1
    RED = 2


X_NANES = {
    # a b c d e f g h
    ch: i for i, ch in enumerate("abcdefgh")
}

NAME_X_INDEX = {key: val for val, key in X_NANES.items()}

CODES: typing.Dict[typing.Tuple[str, ColorEnum], str] = {
    ("queen", ColorEnum.RED): "♛",
    ("queen", ColorEnum.WHITE): "♕",
    ("king", ColorEnum.RED): "♚",
    ("king", ColorEnum.WHITE): "♔",
    ("pawn", ColorEnum.RED): "♟",
    ("pawn", ColorEnum.WHITE): "♙",
    ("rook", ColorEnum.RED): "♜",
    ("rook", ColorEnum.WHITE): "♖",
    ("bishop", ColorEnum.RED): "♝",
    ("bishop", ColorEnum.WHITE): "♗",
    ("knight", ColorEnum.RED): "♞",
    ("knight", ColorEnum.WHITE): "♘",
}


class DirectionEnum(Enum):
    """
    [  ][ 9][  ][10][  ]
    [16][ 1][ 2][ 3][11]
    [  ][ 8][xx][ 4][  ]
    [15][ 7][ 6][ 5][12]
    [  ][14][  ][13][  ]
    """

    DIAG_LEFT_FORWARD = (-1, 1)  # 1
    VERT_FORWARD = (0, 1)  # 2
    DIAG_RIGHT_FORWARD = (1, 1)  # 3
    HORI_RIGHT = (1, 0)  # 4
    DIAG_RIGHT_BACK = (1, -1)  # 5
    VERT_BACK = (0, -1)  # 6
    DIAG_LEFT_BACK = (-1, -1)  # 7
    HORI_LEFT = (-1, 0)  # 8
    L_VERT_LEFT_FORWARD = (-1, 2)  # 9
    L_VERT_RIGHT_FORWARD = (1, 2)  # 10
    L_HORI_RIGHT_FORWARD = (2, 1)  # 11
    L_HORI_RIGHT_BACK = (2, -1)  # 12
    L_VERT_RIGHT_BACK = (1, -2)  # 13
    L_VERT_LEFT_BACK = (-1, -2)  # 14
    L_HORI_LEFT_BACK = (-2, -1)  # 15
    L_HORI_LEFT_FORWARD = (1, 2)  # 16


class BasePiece:
    """Base piece.
    """

    strike: typing.Dict[DirectionEnum, int] = {}
    step: typing.Dict[DirectionEnum, int] = {}
    location = (0, 0)
    color: ColorEnum
    name: str

    def __init__(self, color: ColorEnum, x: int, y: int):
        self.move(x, y)
        self.color = ColorEnum(color)

    @property
    def code(self) -> str:
        code = CODES[self.name, self.color]
        return code

    def move(self, x: int, y: int) -> bool:
        if y < 0 or x < 0 or y >= SIZE or x >= SIZE:
            return False

        self.location = (x, y)
        return True

    def __repr__(self) -> str:
        x, y = self.location
        x_name = NAME_X_INDEX.get(x)
        loc = f"{x_name}{y + 1}"
        return f"{self.name} - {self.code} {loc}"

    def __hash__(self) -> int:
        return hash((self.name, self.color, self.location))

    def get_way(
        self, x: int, y: int, strike: bool = False
    ) -> typing.List[typing.Tuple[int, int]]:
        """Location track for piece if it possible.
        """
        directions = self.strike if strike else self.step
        step = 0
        way = []
        for direction, max_steps in directions.items():
            way.clear()
            step = 0
            delta_x, delta_y = direction.value
            in_direction = False
            cur_x, cur_y = self.location
            way.append((cur_x, cur_y))
            while step < max_steps and not in_direction:
                step += 1
                if self.color == ColorEnum.WHITE:
                    cur_x += delta_x
                    cur_y += delta_y
                else:
                    cur_x -= delta_x
                    cur_y -= delta_y

                if cur_y < 0 or cur_x < 0 or cur_y >= SIZE or cur_x >= SIZE:
                    step = max_steps
                else:
                    way.append((cur_x, cur_y))
                    if cur_x == x and cur_y == y:
                        in_direction = True

            if in_direction:
                break
            else:
                way.clear()

        return way


class Pawn(BasePiece):
    """Pawns
    """
    name = "pawn"
    strike = {
        DirectionEnum.DIAG_LEFT_FORWARD: 1,
        DirectionEnum.DIAG_RIGHT_FORWARD: 1,
        DirectionEnum.DIAG_RIGHT_BACK: 1,
        DirectionEnum.DIAG_LEFT_BACK: 1,
    }

    step = {
        DirectionEnum.VERT_FORWARD: 2,
    }


class King(BasePiece):
    """Kings
    """
    name = "king"
    step = strike = {
        DirectionEnum.DIAG_LEFT_FORWARD: 1,
        DirectionEnum.VERT_FORWARD: 1,
        DirectionEnum.DIAG_RIGHT_FORWARD: 1,
        DirectionEnum.HORI_RIGHT: 1,
        DirectionEnum.DIAG_RIGHT_BACK: 1,
        DirectionEnum.VERT_BACK: 1,
        DirectionEnum.DIAG_LEFT_BACK: 1,
        DirectionEnum.HORI_LEFT: 1,
    }


class Rook(BasePiece):
    """Rooks
    """
    name = "rook"
    step = strike = {
        DirectionEnum.VERT_FORWARD: SIZE,
        DirectionEnum.HORI_RIGHT: SIZE,
        DirectionEnum.VERT_BACK: SIZE,
        DirectionEnum.HORI_LEFT: SIZE,
    }


class Bishop(BasePiece):
    """Bishops
    """
    name = "bishop"
    step = strike = {
        DirectionEnum.DIAG_LEFT_BACK: SIZE,
        DirectionEnum.DIAG_LEFT_FORWARD: SIZE,
        DirectionEnum.DIAG_RIGHT_BACK: SIZE,
        DirectionEnum.DIAG_RIGHT_FORWARD: SIZE,
    }


class Queen(BasePiece):
    """Queen
    """
    name = "queen"
    step = strike = {
        DirectionEnum.VERT_FORWARD: SIZE,
        DirectionEnum.HORI_RIGHT: SIZE,
        DirectionEnum.VERT_BACK: SIZE,
        DirectionEnum.HORI_LEFT: SIZE,
        DirectionEnum.DIAG_LEFT_BACK: SIZE,
        DirectionEnum.DIAG_LEFT_FORWARD: SIZE,
        DirectionEnum.DIAG_RIGHT_BACK: SIZE,
        DirectionEnum.DIAG_RIGHT_FORWARD: SIZE,
    }


class Knight(BasePiece):
    """Knights
    """
    name = "knight"
    step = strike = {
        DirectionEnum.L_VERT_LEFT_FORWARD: 1,
        DirectionEnum.L_VERT_RIGHT_FORWARD: 1,
        DirectionEnum.L_HORI_RIGHT_FORWARD: 1,
        DirectionEnum.L_HORI_RIGHT_BACK: 1,
        DirectionEnum.L_VERT_RIGHT_BACK: 1,
        DirectionEnum.L_VERT_LEFT_BACK: 1,
        DirectionEnum.L_HORI_LEFT_BACK: 1,
        DirectionEnum.L_HORI_LEFT_FORWARD: 1,
    }


class PieceSet:
    """Container for pieces access.
    """

    content: typing.List[BasePiece]

    def __init__(self, data: list = []):
        self.content = []
        for piece in data:
            self.append(piece)

    def __repr__(self) -> str:
        return repr(self.content)

    def __getitem__(
        self, key: typing.Union[typing.Tuple[int, int], str]
    ) -> typing.Tuple[typing.Optional[BasePiece], int, int]:
        if isinstance(key, str):
            ch_index, y_index = key
            x_index = X_NANES.get(ch_index, -1)
            y_index = int(y_index) - 1
        else:
            x_index, y_index = key

        return self.get_piece(x_index, y_index), x_index, y_index

    def copy(self):
        data = self.__class__(data=[])
        data.content = deepcopy(self.content)
        return data

    def append(self, piece: BasePiece):
        assert hash(piece) not in (hash(item) for item in self.content)
        self.content.append(piece)

    def remove(self, x: int, y: int):
        """Delete piece by location.
        """
        loc = (x, y)
        target = None
        for piece in self.content:
            if loc == piece.location:
                target = piece

        if target:
            self.content.remove(target)

    def get_piece(self, x: int, y: int) -> typing.Optional[BasePiece]:
        """Get piece by location.
        """
        loc = (x, y)
        for piece in self.content:
            if loc == piece.location:
                return piece

    def get_teams(
        self
    ) -> typing.Tuple[typing.List[BasePiece], typing.List[BasePiece]]:
        """Select teams.
        Return [wite team], [red team]
        """
        team_red = [
            item for item in self.content
            if item.color == ColorEnum.RED
        ]
        team_white = [
            item for item in self.content
            if item.color == ColorEnum.WHITE
        ]
        return team_white, team_red
