from bingo_trivia_system import winrules


def grid(rows):
    return [list(r) for r in rows]


def test_empty_grid_has_only_free():
    g = winrules.empty_grid()
    assert g[2][2] is True
    assert not winrules.has_line(g)


def test_horizontal_line_detected():
    g = winrules.empty_grid()
    for c in range(5):
        g[0][c] = True
    assert winrules.has_line(g)


def test_vertical_line_detected():
    g = winrules.empty_grid()
    for r in range(5):
        g[r][3] = True
    assert winrules.has_line(g)


def test_diagonal_line_via_free():
    g = winrules.empty_grid()
    for i in range(5):
        g[i][i] = True
    assert winrules.has_line(g)


def test_corners_rule():
    g = winrules.empty_grid()
    g[0][0] = g[0][-1] = g[-1][0] = g[-1][-1] = True
    assert winrules.has_corners(g)
    assert not winrules.has_blackout(g)


def test_blackout():
    g = [[True] * 5 for _ in range(5)]
    assert winrules.has_blackout(g)


def test_x_pattern_requires_both_diagonals():
    g = winrules.empty_grid()
    for i in range(5):
        g[i][i] = True
    assert not winrules.has_x_pattern(g)
    for i in range(5):
        g[i][4 - i] = True
    assert winrules.has_x_pattern(g)
