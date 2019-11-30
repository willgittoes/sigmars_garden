import PIL.ImageGrab
import pyautogui
import numpy as np
import matplotlib.pyplot as plt
import skimage.metrics
import copy
import time
import argparse

GOLD = 'gold'
METALS_ORDER = [GOLD, 'silver', 'copper', 'iron', 'tin', 'lead']
METALS = set(METALS_ORDER)
THE_4 = set(['air', 'earth', 'water', 'fire'])
ANNOYING_TWO = set(['mors', 'vitae'])
SALT = 'salt'
QUICKSILVER = 'quicksilver'
BLANK = 'blank'
ELEMENTS = list(THE_4) + list(ANNOYING_TWO) + \
    METALS_ORDER + [SALT, QUICKSILVER]
ELEMENTS_SHORT = {
    'air': 'A',
    'earth': 'E',
    'water': 'W',
    'fire': 'F',
    'lead': 'L',
    'tin': 'T',
    'iron': 'I',
    'copper': 'C',
    'silver': 'S',
    'gold': 'G',
    'mors': 'M',
    'vitae': 'V',
    'salt': 'Y',
    'quicksilver': 'Q',
    'blank': '.'
}
ELEM_IMGS = [(elem, np.asarray(PIL.Image.open('copyright_violations/{}.png'.format(f,)))) for elem, f in ([
    (e, '{}{}'.format(e, suf)) for suf in ['', '_lit'] for e in ELEMENTS] + [(BLANK, BLANK)])]
ANCHOR_IMG = 'copyright_violations/magic.png'
NEW_GAME_IMG = 'copyright_violations/new_game.png'

CELL_W = 66
CELL_H = 57
MARGIN_T = 19
MARGIN_LR = 17


def actuallyClick(slow=False):
    pyautogui.mouseDown()
    time.sleep(0.25 if slow else 0.02)
    pyautogui.mouseUp()


class Board(object):

    @staticmethod
    def fromScreenCap(edge_length=6):
        cap_np = np.asarray(pyautogui.screenshot())
        loc = pyautogui.locateOnScreen(ANCHOR_IMG)
        if loc is None:
            raise("Found no game, make sure it's on monitor #1")
        loc = (loc.left, loc.top)

        EDGE = edge_length
        SIZE = EDGE * 2 - 1
        board_img = cap_np[loc[1]:loc[1] + SIZE *
                           CELL_H, loc[0]:loc[0] + SIZE * CELL_W]

        def buildRow(board, row):
            top_px = row * CELL_H
            left_px = ((EDGE - 1 - row) * CELL_W //
                       2) if row < EDGE else (row-EDGE + 1) * CELL_W // 2
            width_cells = EDGE + row if row < EDGE else SIZE + EDGE - row - 1
            elems = []
            for n in range(0, width_cells):
                cell = board[top_px + MARGIN_T:top_px+CELL_H, left_px +
                             n*CELL_W + MARGIN_LR:left_px+(n + 1)*CELL_W - MARGIN_LR]
                _, elem = max([(skimage.metrics.structural_similarity(
                    img, cell, multichannel=True), elem) for elem, img in ELEM_IMGS])
                elems.append(elem)
            return elems

        board = []
        for row in range(0, SIZE):
            board.append(buildRow(board_img, row))

        return Board(board, loc)

    def makeMove(self, move):
        elems = copy.deepcopy(self.elems)
        salted = copy.deepcopy(self.salted)
        # Check for salt usage
        if len(move) == 2:
            (r1, c1), (r2, c2) = move
            a, b = elems[r1][c1], elems[r2][c2]
            if a == SALT or b == SALT:
                other = b if a == SALT else a
                if other == SALT:
                    pass  # Both salt, balance unaffected
                elif other in salted:
                    salted.remove(other)  # Balance restored
                else:
                    salted.add(other)  # Unbalanced
        # Make move
        for row, col in move:
            elems[row][col] = BLANK
        return Board(elems, self.board_pos, salted=salted, n_moves=self.n_moves+1)

    def __init__(self, elems, board_pos, salted=set(), n_moves=0):
        self.board_pos = board_pos
        self.n_moves = n_moves
        self.elems = elems
        self.n_metals = sum(
            1 if elem in METALS else 0 for row in elems for elem in row)
        self.salted = salted
        self.salt_left = sum(
            1 if elem == SALT else 0 for row in elems for elem in row)

    def __eq__(self, other):
        if self.n_moves != other.n_moves:
            return False
        if self.n_metals != other.n_metals:
            return False
        if self.salt_left != other.salt_left:
            return False
        if self.salted != other.salted:
            return False
        if self.elems != other.elems:
            return False
        return True

    def __hash__(self):
        return hash((
            tuple([tuple(row) for row in self.elems]),
            tuple(self.board_pos),
            self.n_moves, self.n_metals, self.salt_left,
            tuple(self.salted)))

    def isWon(self):
        left = sum(
            1 if elem != BLANK else 0 for row in self.elems for elem in row)
        return left == 0

    def orderedNeighbours(self, row, col):
        #   5 6
        #  4 O 1
        #   3 2
        b = row >= len(self.elems) // 2  # Middle or bottom half
        t = row <= len(self.elems) // 2  # Middle or top half
        ns = [
            (row, col+1),
            (row+1, col if b else col + 1),
            (row+1, col-1 if b else col),
            (row, col-1),
            (row-1, col-1 if t else col),
            (row-1, col if t else col+1)]
        ns = [(r, c,
               r >= 0 and r < len(self.elems) and
               c >= 0 and c < len(self.elems[r]))
              for (r, c) in ns]
        return ns

    def elementReachable(self, row, col):
        elem = self.elems[row][col]
        if elem == BLANK:
            return False
        ns = self.orderedNeighbours(row, col)
        ns = ns + ns  # To catch gaps that "wrap around"
        emptyRun = 0
        for (nR, nC, exists) in ns:
            if not exists or self.elems[nR][nC] == BLANK:
                emptyRun += 1
                if emptyRun >= 3:
                    return True
                continue
            emptyRun = 0
        return False

    def active(self, also_print=False):
        activeElems = []
        reprActive = []
        for row, _ in enumerate(self.elems):
            rowElems = []
            for col, elem in enumerate(self.elems[row]):
                if self.elementReachable(row, col):
                    if elem not in METALS or elem == METALS_ORDER[self.n_metals - 1]:
                        activeElems.append((row, col, elem))
                if also_print:
                    char = ELEMENTS_SHORT[elem]
                    if not self.elementReachable(row, col):
                        char = char.lower()
                    rowElems.append(char)
            if also_print:
                reprActive.append(rowElems)
        return activeElems, reprActive

    def movePossible(self, a, b):
        if a in THE_4 or b in THE_4:
            if a == b:
                return True
            if a == SALT or b == SALT:
                not_salt = b if a == SALT else a
                # Can we use this salt?
                if not_salt in self.salted or self.salt_left >= len(self.salted) + 1:
                    return True
        if a == SALT and a == b and self.salt_left >= len(self.salted) + 2:
            return True
        if a in ANNOYING_TWO and b in ANNOYING_TWO and a != b:
            return True
        currentMetal = METALS_ORDER[self.n_metals -
                                    1] if self.n_metals != 0 else None
        if (a == currentMetal and b == QUICKSILVER or
                b == currentMetal and a == QUICKSILVER):
            return True
        return False

    def possibleMoves(self):
        active, _ = self.active()
        moves = list()
        for i, (a_row, a_col, a_elem) in enumerate(active):
            if a_elem == GOLD:
                moves.append([(a_row, a_col)])
            for b_row, b_col, b_elem in active[i+1:]:
                if self.movePossible(a_elem, b_elem):
                    moves.append([(a_row, a_col), (b_row, b_col)])
        return moves

    def automateMove(self, move, slow=False):
        D = len(self.elems)
        R = D // 2 + 1
        l, t = self.board_pos
        for row, col in move:
            offset = (R - row - 1 if row < R else row - R + 1) * CELL_W // 2
            x = l + offset + col * CELL_W + CELL_W // 2
            y = t + row * CELL_H + CELL_H // 2
            pyautogui.moveTo(x, y, duration=0.25 if slow else 0.05)
            actuallyClick(slow=slow)

    def __str__(self):
        _, activeRepr = self.active(also_print=True)
        return self.__printIndented(activeRepr)

    def __printIndented(self, rows):
        rows = [''.join(' {}'.format(e) for e in row) + '\n' for row in rows]
        size = len(rows)
        s = ''
        for i, rowRepr in enumerate(rows):
            s += ' ' * \
                (size // 2 - i) if i < size//2 else (i-size // 2) * ' '
            s += rowRepr
        return s

    def solve(self):
        stack = [self]
        steps = {}
        while stack:
            b = stack.pop()
            print(b)
            for move in b.possibleMoves():
                n = b.makeMove(move)
                if n in steps:
                    continue
                steps[n] = (b, move)
                if n.isWon():
                    trace = []
                    while n in steps:
                        n, move = steps[n]
                        trace.append(move)
                    trace.reverse()
                    return trace
                stack.append(n)
        return None

    def automateSolve(self, slow=False):
        trace = self.solve()
        if trace == None:
            raise("Didn't find a solution?!?!!")
        pyautogui.moveTo(
            self.board_pos[0], self.board_pos[1], duration=0.25 if slow else 0.05)
        actuallyClick(slow=slow)
        for move in trace:
            self.automateMove(move, slow=slow)
        time.sleep(0.5)
        loc = pyautogui.locateOnScreen(NEW_GAME_IMG)
        if loc is None:
            raise("Found no new-game, make sure it's on monitor #1")
        pyautogui.moveTo(loc.left, loc.top, duration=0.25 if slow else 0.05)
        actuallyClick(slow=slow)
        time.sleep(4)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--n_games', default=1,
                        help="Automate this many games")
    parser.add_argument('--slow', default=False,
                        help="Set to False if your computer is too crap, or you want time to think")
    args = parser.parse_args()

    for i in range(int(args.n_games)):
        b = Board.fromScreenCap()
        b.automateSolve(slow=args.slow)
