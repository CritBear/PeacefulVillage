# coding=<utf-8>
from cocos.director import director

import pyglet.font
import pyglet.resource

from MainMenu import new_menu


if __name__ == '__main__':
    pyglet.resource.path.append('assets')
    pyglet.resource.reindex()
    pyglet.font.add_file('assets/Oswald-Regular.ttf')

    director.init(width=1280, height=960, caption='Peaceful Village')
    director.run(new_menu())
