"""Win-rule engine — pure functions over a stamped 5x5 grid.

A stamped grid is `list[list[bool]]` of shape 5x5; True means the cell has
been stamped (either FREE or matched a revealed answer).
"""

from __future__ import annotations

from collections.abc import Callable

from .models import FREE_COL, FREE_ROW, GRID_SIZE, WinRule

Grid = list[list[bool]]


def _row(g: Grid, r: int) -> bool:
    return all(g[r])


def _col(g: Grid, c: int) -> bool:
    return all(g[r][c] for r in range(GRID_SIZE))


def _diag_main(g: Grid) -> bool:
    return all(g[i][i] for i in range(GRID_SIZE))


def _diag_anti(g: Grid) -> bool:
    return all(g[i][GRID_SIZE - 1 - i] for i in range(GRID_SIZE))


def has_line(g: Grid) -> bool:
    """Any single row, column, or diagonal fully stamped."""
    if any(_row(g, r) for r in range(GRID_SIZE)):
        return True
    if any(_col(g, c) for c in range(GRID_SIZE)):
        return True
    return _diag_main(g) or _diag_anti(g)


def has_blackout(g: Grid) -> bool:
    return all(all(row) for row in g)


def has_corners(g: Grid) -> bool:
    return g[0][0] and g[0][-1] and g[-1][0] and g[-1][-1]


def has_x_pattern(g: Grid) -> bool:
    return _diag_main(g) and _diag_anti(g)


def has_two_lines(g: Grid) -> bool:
    lines = sum(_row(g, r) for r in range(GRID_SIZE))
    lines += sum(_col(g, c) for c in range(GRID_SIZE))
    lines += int(_diag_main(g)) + int(_diag_anti(g))
    return lines >= 2


_DISPATCH: dict[WinRule, Callable[[Grid], bool]] = {
    "line": has_line,
    "blackout": has_blackout,
    "corners": has_corners,
    "x_pattern": has_x_pattern,
    "two_lines": has_two_lines,
}


def check(rule: WinRule, grid: Grid) -> bool:
    return _DISPATCH[rule](grid)


def empty_grid(free_center: bool = True) -> Grid:
    g = [[False] * GRID_SIZE for _ in range(GRID_SIZE)]
    if free_center:
        g[FREE_ROW][FREE_COL] = True
    return g
