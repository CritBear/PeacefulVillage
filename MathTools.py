import math
import cocos.euclid as eu

def distance(pos_a, pos_b):
    return math.sqrt( pow(pos_a[0] - pos_b[0], 2) + pow(pos_a[1] - pos_b[1], 2) )

def get_angle(pos_a, pos_b):
    radian = math.atan2(pos_b[1] - pos_a[1], pos_b[0] - pos_a[0])
    return - radian * 180 / math.pi

def rotate_vector2(vec, rotation):
    # rotation is not radian, sprite rotation(-degree)
    # rotate by origin(0, 0)
    radian = - rotation / 180 * math.pi
    return eu.Vector2(math.cos(radian) * vec.x - math.sin(radian) * vec.y,
                      math.sin(radian) * vec.x + math.cos(radian) * vec.y)
