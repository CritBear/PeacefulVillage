import math

def distance(pos_a, pos_b):
    return math.sqrt( pow(pos_a[0] - pos_b[0], 2) + pow(pos_a[1] - pos_b[1], 2) )

def get_angle(pos_a, pos_b):
    radian = math.atan2(pos_b[1] - pos_a[1], pos_b[0] - pos_a[0])
    return - radian * 180 / math.pi
