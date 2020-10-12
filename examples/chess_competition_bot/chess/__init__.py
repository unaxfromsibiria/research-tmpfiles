#In [1]: from chess import Game
#
#In [2]: history = [
#   ...: (1, 'b1', 'a3', None),
#   ...: (2, 'g8', 'h6', None),
#   ...: (1, 'd2', 'd3', None),
#   ...: (2, 'd7', 'd6', None),
#   ...: (1, 'c1', 'e3', None),
#   ...: (2, 'e7', 'e6', None),
#   ...: (1, 'd1', 'd2', None),
#   ...: (2, 'f8', 'e7', None)
#   ...: ]
#
#In [3]: game = Game.from_history("test", history)
#
#In [4]: game.castling()
#Out[4]: 'Team red moves'
#
#In [5]: game
#Out[5]: 
#Game test
#red pieces moves, last step castling-long
#  abcdefgh
#8 ♜♞♝♛♚  ♜
#7 ♟♟♟ ♝♟♟♟
#6    ♟♟  ♞
#5         
#4         
#3 ♘  ♙♗   
#2 ♙♙♙♕♙♙♙♙
#1   ♔♖ ♗♘♖

from .game import Game
