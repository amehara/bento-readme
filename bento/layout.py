"""Bento grid: 4 columns, rows measured in half-row units.

A full row is 2 units, so `size: 2x2` is a 568x232 -> 568x480 block and `4x0.5`
is a slim band. Placement is "dense": cards are taken in config order and each one
goes into the first free spot, so a small card fills any gap left by bigger ones.
"""

COLS = 4
PAD = 24
GAP = 16
CELL_W = 276
UNIT_H = 108  # 2 units + 1 gap = 232 = one full row
CANVAS_W = PAD * 2 + COLS * CELL_W + (COLS - 1) * GAP  # 1200


class LayoutError(ValueError):
    pass


def parse_size(value, default):
    """'2x1' / '1x2' / '4x0.5' -> (cols, units)."""
    if value is None:
        value = default
    try:
        c, r = str(value).lower().replace(" ", "").split("x")
        cols, rows = int(c), float(r)
        units = rows * 2
    except ValueError:
        raise LayoutError(f"invalid size {value!r}; use COLSxROWS like 2x1, 1x2 or 4x0.5") from None
    if units != int(units) or units < 1:
        raise LayoutError(f"invalid size {value!r}: rows must be a multiple of 0.5")
    if not 1 <= cols <= COLS:
        raise LayoutError(f"invalid size {value!r}: columns must be between 1 and {COLS}")
    return cols, int(units)


def place(sizes):
    """sizes: [(cols, units)] -> ([(col, unit)], total_units)."""
    taken = set()
    spots, total = [], 0
    for cols, units in sizes:
        pos = 0  # linear position col + unit * COLS
        while True:
            u, c = divmod(pos, COLS)
            fits = c + cols <= COLS and not any(
                (c + dc, u + du) in taken for dc in range(cols) for du in range(units)
            )
            if fits:
                break
            pos += 1
        for dc in range(cols):
            for du in range(units):
                taken.add((c + dc, u + du))
        spots.append((c, u))
        total = max(total, u + units)
    return spots, total


def rect(col, unit, cols, units):
    x = PAD + col * (CELL_W + GAP)
    y = PAD + unit * (UNIT_H + GAP)
    w = cols * CELL_W + (cols - 1) * GAP
    h = units * UNIT_H + (units - 1) * GAP
    return x, y, w, h


def canvas_height(total_units):
    return PAD * 2 + total_units * UNIT_H + (total_units - 1) * GAP
