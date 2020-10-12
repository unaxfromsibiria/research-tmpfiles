import typing
import uuid
from datetime import datetime

from .common import NAME_X_INDEX
from .common import SIZE
from .common import BasePiece
from .common import Bishop
from .common import ColorEnum
from .common import King
from .common import Knight
from .common import Pawn
from .common import PieceSet
from .common import Queen
from .common import Rook

default_pieces = PieceSet([
    Rook(ColorEnum.WHITE, 0, 0), Rook(ColorEnum.WHITE, 7, 0),
    Rook(ColorEnum.RED, 0, 7), Rook(ColorEnum.RED, 7, 7),
    Knight(ColorEnum.WHITE, 1, 0), Knight(ColorEnum.WHITE, 6, 0),
    Knight(ColorEnum.RED, 1, 7), Knight(ColorEnum.RED, 6, 7),
    Bishop(ColorEnum.WHITE, 2, 0), Bishop(ColorEnum.WHITE, 5, 0),
    Bishop(ColorEnum.RED, 2, 7), Bishop(ColorEnum.RED, 5, 7),
    Queen(ColorEnum.WHITE, 3, 0), Queen(ColorEnum.RED, 3, 7),
    King(ColorEnum.WHITE, 4, 0),  King(ColorEnum.RED, 4, 7),
])

for i in range(SIZE):
    default_pieces.append(Pawn(ColorEnum.WHITE, i, 1))
    default_pieces.append(Pawn(ColorEnum.RED, i, 6))


class Rule:
    """Rules of game.
    """

    pieces: PieceSet

    def __get__(self, instance, instance_class: type):
        self.pieces = instance.board.pieces
        return self

    def is_check_state(self, color: ColorEnum) -> bool:
        """Chack state for king with color.
        """
        white, red = self.pieces.get_teams()
        if color == ColorEnum.WHITE:
            king = next(item for item in white if item.name == "king")
            enemies = red
        else:
            king = next(item for item in red if item.name == "king")
            enemies = white

        return any(
            piece.get_way(*king.location, strike=True) for piece in enemies
        )

    def get_super_pawn(self, color: ColorEnum) -> typing.Optional[BasePiece]:
        """Check super pawn in first line of enemies.
        """
        white, red = self.pieces.get_teams()
        if color == ColorEnum.WHITE:
            pawns = [item for item in white if item.name == "pawn"]
            line = 7
        else:
            pawns = [item for item in red if item.name == "pawn"]
            line = 0

        for pawn in pawns:
            _, y = pawn.location
            if line == y:
                return pawn

    def castling(self, color: ColorEnum) -> typing.Tuple[bool, str]:
        """Make available castling.
        """
        castling_name = None
        if self.castling_short(color, True):
            castling_name = "short"

        if self.castling_long(color, True):
            if not castling_name:
                castling_name = "long"

        if castling_name:
            if castling_name == "short":
                self.castling_short(color)
            else:
                self.castling_long(color)

            return True, castling_name
        else:
            return False, ""

    def castling_long(self, color: ColorEnum, check: bool = False) -> bool:
        """Make long castling.
        """
        result = False
        king, x, y = self.pieces["e1" if color == ColorEnum.WHITE else "e8"]
        rook, r_x, _ = self.pieces["a1" if color == ColorEnum.WHITE else "a8"]
        if king and rook and rook.name == "rook" and king.name == "king":
            way = rook.get_way(x - 1, y)
            result = bool(way and all(
                self.pieces.get_piece(t_x, t_y) is None
                for t_x, t_y in way if t_x != x and t_x != r_x
            ))
            if not check and result:
                king.move(x - 2, y)
                rook.move(x - 1, y)

        return result

    def castling_short(self, color: ColorEnum, check: bool = False) -> bool:
        """Make short castling.
        """
        result = False
        king, x, y = self.pieces["e1" if color == ColorEnum.WHITE else "e8"]
        rook, r_x, _ = self.pieces["h1" if color == ColorEnum.WHITE else "h8"]
        if king and rook and rook.name == "rook" and king.name == "king":
            way = rook.get_way(x + 1, y)
            result = bool(way and all(
                self.pieces.get_piece(t_x, t_y) is None
                for t_x, t_y in way if t_x != x and t_x != r_x
            ))
            if not check and result:
                king.move(x + 2, y)
                rook.move(x + 1, y)

        return result

    def move(self, from_cell: str, to_cell: str) -> bool:
        """Moving of piece to new position.
        """
        piece, x, y = self.pieces[from_cell]
        if not piece:
            return False

        target, to_x, to_y = self.pieces[to_cell]
        in_strike = False
        if target:
            if target.color == piece.color:
                return False
            else:
                in_strike = True
        else:
            # TODO: special case for pawns
            pass

        way = piece.get_way(to_x, to_y, in_strike)
        if not way:
            return False

        for in_x, in_y in way:
            if in_x == x and in_y == y:
                continue
            if in_x == to_x and in_y == to_y:
                continue

            step_piece, *_ = self.pieces[in_x, in_y]
            if step_piece:
                return False

        if in_strike:
            self.pieces.remove(to_x, to_y)

        piece.move(to_x, to_y)

        return True


class GameBoard:
    """State of board.
    """

    pieces: PieceSet

    # TODO: drow visitor or something else

    def __init__(self):
        self.pieces = default_pieces.copy()

    def __repr__(self) -> str:
        x_line = "".join(map(NAME_X_INDEX.get, range(SIZE)))
        lines = [f"  {x_line}"]
        for i in range(SIZE):
            line = f"{SIZE - i} "
            for j in range(SIZE):
                p = self.pieces.get_piece(j, SIZE - 1 - i)
                code = p.code if p else " "
                line = f"{line}{code}"

            lines.append(line)

        return "\n".join(lines)


class Game:
    """Game state.
    """

    code: str
    board: GameBoard
    history: typing.List[typing.Tuple[ColorEnum, str, str, datetime]]
    in_check: bool
    rules = Rule()

    def __init__(self):
        self.code = uuid.uuid4().hex
        self.board = GameBoard()
        self.history = []
        self.in_check = True

    def __hash__(self) -> int:
        return hash(self.code)

    def __repr__(self) -> str:
        if self.history:
            *_, (color, f_cell, t_cell, _) = self.history
            now_color = "white" if color == ColorEnum.RED else "red"
            current = f"{now_color} pieces moves, last step {f_cell}-{t_cell}"
        else:
            current = "white pieces moves"

        return (
            f"Game {self.code}\n"
            f"{current}\n{self.board}"
        )

    @classmethod
    def from_history(
        cls,
        code: str,
        history: typing.List[
            typing.Tuple[
                typing.Union[ColorEnum, int],
                str,
                str,
                typing.Optional[datetime]
            ]
        ]
    ):
        """Create from history log.
        """

        game = cls()
        if code:
            game.code = code

        history = [
            (ColorEnum(color), f_cell, t_cell, dt)
            for color, f_cell, t_cell, dt in history
        ]
        for _, from_cell, to_cell, dt in history:
            if from_cell == "castling":
                game.castling(short=to_cell == "short")
                if dt:
                    cl, f_cell, t_cell, _ = game.history[-1]
                    game.history[-1] = (cl, f_cell, t_cell, dt)
            else:
                game.step(from_cell, to_cell)

        return game

    def castling(self, short: typing.Optional[bool] = None) -> str:
        """Make available castling for current step.
        """
        if self.history:
            *_, (color, *_) = self.history
            color = (
                ColorEnum.WHITE if color == ColorEnum.RED else ColorEnum.RED
            )
        else:
            color = ColorEnum.WHITE

        if short is None:
            result, castling_name = self.rules.castling(color)
        elif short:
            castling_name = "short"
            result = self.rules.castling_short(color)
        else:
            castling_name = "long"
            result = self.rules.castling_long(color)

        if result:
            self.history.append(
                (color, "castling", castling_name, datetime.now())
            )
            next_color = (
                ColorEnum.WHITE if color == ColorEnum.RED else ColorEnum.RED
            )
            return f"Team {next_color.name.lower()} moves"
        else:
            return "Not possible for castling."

    def step(self, from_cell: str, to_cell: str) -> str:
        """Make next step for current team.
        """
        if self.history:
            *_, (color, *_) = self.history
            color = (
                ColorEnum.WHITE if color == ColorEnum.RED else ColorEnum.RED
            )
        else:
            color = ColorEnum.WHITE

        piece, *_ = self.board.pieces[from_cell]
        if not piece:
            return f"No piece in cell {from_cell}"

        if piece.color != color:
            return "Other team moves"

        result = self.rules.move(from_cell, to_cell)
        if not result:
            return f"Not available step {from_cell}-{to_cell}"
        else:
            self.history.append((color, from_cell, to_cell, datetime.now()))

        if self.rules.is_check_state(color):
            if self.in_check:
                return f"Mate for {color.name.lower()} team"

            self.in_check = True
            return f"Check for {color.name.lower()} team"

        if self.rules.get_super_pawn(color):
            return f"Replace pawn in {to_cell}!"

        self.in_check = False
        next_color = (
            ColorEnum.WHITE if color == ColorEnum.RED else ColorEnum.RED
        )
        return f"Team {next_color.name.lower()} moves"
