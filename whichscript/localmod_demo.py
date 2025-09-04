def transform_points(xs, ys, offset=0):
    return [x + offset for x in xs], [y + offset for y in ys]
