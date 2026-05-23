# winrules

`src/bingo_trivia_system/winrules.py`

Pure-functional win-condition checks over a stamped 5×5 grid.

| Rule | Description |
|---|---|
| `line` | Any row, column, or full diagonal stamped |
| `blackout` | Every cell stamped |
| `corners` | All four corners stamped |
| `x_pattern` | Both diagonals stamped |
| `two_lines` | Two or more lines (rows / cols / diagonals) simultaneously |

The center FREE cell is always pre-stamped by `winrules.empty_grid()`.

## Adding a new rule

1. Add a `has_<name>(grid: Grid) -> bool` function in `winrules.py`.
2. Register it in `_DISPATCH`.
3. Extend the `WinRule` Literal in `models.py`.
4. Add a unit test fixture in `tests/test_winrules.py`.
