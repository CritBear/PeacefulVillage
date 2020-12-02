import cocos.sprite
import cocos.text
import cocos.euclid as eu
import pyglet.image


class Panel(cocos.sprite.Sprite):
    def __init__(self, img, position):
        super(Panel, self).__init__(img, position)
        self.able = True

    def enable(self, state):
        self.able = state
        if state == True:
            self.opacity = 255
        else:
            self.opacity = 0

        for ui in self.get_children():
            if hasattr(ui, 'enable'):
                ui.enable(state)
    
    def onClick(self, point):
        if self.able == False:
            return False
        for ui in self.get_children():
            if hasattr(ui, 'onClick'):
                if abs(point[0] - ui.position[0]) <= ui.width/2 and abs(point[1] - ui.position[1]) <= ui.height/2:
                    result = ui.onClick()
                    if result != False:
                        return result
        return False
    

class Button(cocos.sprite.Sprite):
    def __init__(self, img, position, event, scale):
        super(Button, self).__init__(img, position, scale=scale)
        self.able = True
        self.event = event

    def enable(self, state):
        self.able = state
        if state == True:
            self.opacity = 255
        else:
            self.opacity = 0

    def onClick(self):
        if self.able == False:
            return False
        return self.event
        

class Image(cocos.sprite.Sprite):
    def __init__(self, img, position, scale):
        super(Image, self).__init__(img, position, scale=scale)
        self.able = True

    def enable(self, state):
        self.able = state
        if state == True:
            self.opacity = 255
        else:
            self.opacity = 0

class Text(cocos.text.Label):
    def __init__(self, position, font_size, color, contents, anchor_x, anchor_y):
        super(Text, self).__init__(font_size=font_size, font_name='Oswald', color=color,
                                   anchor_x=anchor_x, anchor_y=anchor_y)
        self.position = position
        self.element.text = contents
        self.able = True

    def enable(self, state):
        self.able = state
        if state == True:
            self.element.color = (self.element.color[0],
                                  self.element.color[1],
                                  self.element.color[2],
                                  255)
        else:
            self.element.color = (self.element.color[0],
                                  self.element.color[1],
                                  self.element.color[2],
                                  0)
