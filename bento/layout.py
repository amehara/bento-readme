"""Bento grid: 4 columns, rows measured in half-row units.

A full row is always 232 px tall; `gap` and `padding` are configurable and the cell
sizes adapt around them. `size: 2x2` is a big block and `4x0.5` is a slim band.
Placement is "dense": cards are taken in config order and each one goes into the
first free spot, so a small card fills any gap left by bigger ones.
"""
from collections import namedtuple

COLS = 4
CANVAS_W = 1200
ROW_H = 232

Geometry = namedtuple("Geometry", "pad gap cell_w unit_h")


class LayoutError(ValueError):
    pass


def geometry(pad=24, gap=16):
    cell_w = (CANVAS_W - 2 * pad - (COLS - 1) * gap) / COLS
    unit_h = (ROW_H - gap) / 2  # 2 units + 1 gap = one full row
    return Geometry(pad, gap, cell_w, unit_h)


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


def rect(geo, col, unit, cols, units):
    x = geo.pad + col * (geo.cell_w + geo.gap)
    y = geo.pad + unit * (geo.unit_h + geo.gap)
    w = cols * geo.cell_w + (cols - 1) * geo.gap
    h = units * geo.unit_h + (units - 1) * geo.gap
    return round(x, 2), round(y, 2), round(w, 2), round(h, 2)


def canvas_height(geo, total_units):
    return round(geo.pad * 2 + total_units * geo.unit_h + (total_units - 1) * geo.gap)
