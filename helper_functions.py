def linear_two_points(p1, p2):
    x1, y1 = p1
    x2, y2 = p2
    slope = (y2-y1)/float(x2-x1)
    return lambda x: slope*(x-x1)+y1