from cocos.director import director
from cocos.scenes.transitions import SplitColsTransition, FadeTransition
import cocos.layer
import cocos.scene
import cocos.text
import cocos.actions as ac
import cocos.collision_model as cm
import cocos.euclid as eu

import MainMenu
import Actors
import UI
from Scenario import get_scenario
import MathTools as mt

import numpy as np
import random
import math


class GameLayer(cocos.layer.Layer):
    is_event_handler = True
    scenario = None
    map_width = None
    map_height = None
    map = None
    grid_size = None
    
    def __init__(self, hud, scenario):
        super(GameLayer, self).__init__()
        self.hud = hud
        
        GameLayer.scenario = scenario
        GameLayer.map_width = GameLayer.scenario.map_width
        GameLayer.map_height = GameLayer.scenario.map_height
        GameLayer.map = np.arange(GameLayer.map_width * GameLayer.map_height).reshape(GameLayer.map_width, GameLayer.map_height)
        GameLayer.grid_size = GameLayer.scenario.pixelPerGrid
        
        self.centralBase = None
        self.selecting_send_structure = False
        self.selecting_receive_structure = False
        self.collman = cm.CollisionManagerGrid(0, GameLayer.map_width * GameLayer.grid_size,
                                               0, GameLayer.map_height * GameLayer.grid_size,
                                               GameLayer.grid_size * 3, GameLayer.grid_size * 3)
        self.remaining_time = GameLayer.scenario.stage_info[0]['time']
        self.stage = 0
        self.spawn_queue = []
        self.spawn_delay = 0.5
        self.spawn_remaining_time = self.spawn_delay
        
        self.hud.init_panel()
        self.init_startingStructure()

        self.mouse = Actors.Mouse(self.grid_size)
        self.add(self.mouse)
        
        self.schedule(self.update_obj)


    def update_obj(self, dt):
        self.update_map()
        for obj in self.get_children():
            if hasattr(obj, 'update_obj'):
                obj.update_obj(dt)
                
        self.hud.update_structure_info_panel()
        self.check_collision()
        self.update_stage(dt)
        
    def update_map(self):
        for x in range(GameLayer.map_width):
            for y in range(GameLayer.map_height):
                GameLayer.map[x][y] = 0
                
        for obj in self.get_children():
            if isinstance(obj, Actors.Structure):
                offset = 0
                if obj.size % 2 == 0:
                    offset = -0.5
                grid_pos = (int((obj.position[0] + offset) // GameLayer.grid_size),
                            int((obj.position[1] + offset) // GameLayer.grid_size) )
                for x in range(grid_pos[0] - math.floor((obj.size-1)/2), grid_pos[0] + math.ceil((obj.size-1)/2) + 1):
                    for y in range(grid_pos[1] - math.floor((obj.size-1)/2), grid_pos[1] + math.ceil((obj.size-1)/2) + 1):
                        GameLayer.map[x][y] = obj.hp

    def update_stage(self, dt):
        if len(self.spawn_queue) > 0:
            self.spawn_remaining_time -= dt
            if self.spawn_remaining_time < 0:
                self.spawn_remaining_time = self.spawn_delay
                enemy_type = self.spawn_queue.pop()
                if enemy_type == 'HeavyInfantry':
                    self.add(Actors.HeavyInfantry(self.get_enemy_spawn_pos(), GameLayer.scenario.enemy_info['HeavyInfantry']))
                elif enemy_type == 'LightInfantry':
                    self.add(Actors.LightInfantry(self.get_enemy_spawn_pos(), GameLayer.scenario.enemy_info['HeavyInfantry']))
                elif enemy_type == 'Ranger':
                    self.add(Actors.Ranger(self.get_enemy_spawn_pos(), GameLayer.scenario.enemy_info['HeavyInfantry']))
        
        self.remaining_time -= dt
        if self.remaining_time < 0:
            self.next_stage()

        if self.stage >= len(GameLayer.scenario.stage_info) - 1:
            self.hud.update_remaining_time('Clear', round(self.remaining_time, 1))
        else:
            self.hud.update_remaining_time('Stage %s' % (self.stage + 1), round(self.remaining_time, 1))

    def next_stage(self):
        if self.stage < len(GameLayer.scenario.stage_info) - 1:
                self.stage += 1
                self.remaining_time = GameLayer.scenario.stage_info[self.stage]['time']
                for enemy in GameLayer.scenario.stage_info[self.stage]['enemy'].keys():
                    for i in range(GameLayer.scenario.stage_info[self.stage]['enemy'][enemy]):
                        self.spawn_queue.insert(0, enemy)
    
    def check_collision(self):
        self.collman.clear()
        for obj in self.get_children():
            if isinstance(obj, Actors.Structure) or isinstance(obj, Actors.Enemy) or isinstance(obj, Actors.Bullet):
                self.collman.add(obj)
        for obj in self.get_children():
            if obj is not None:
                if hasattr(obj, 'collide'):
                    for other in self.collman.iter_colliding(obj):
                        obj.collide(other)
        for obj in self.get_children():
            if hasattr(obj, 'dead') and obj.dead:
                self.remove(obj)


    
    def init_startingStructure(self):
        grid_pos = GameLayer.scenario.centralBase_position
        size = GameLayer.scenario.structure_info['CentralBase']['size']
        self.centralBase = Actors.CentralBase(self.hud,
                                              self.convert_pos(grid_pos, size),
                                              GameLayer.scenario.structure_info['CentralBase'])
        self.add(self.centralBase)

        
    def on_mouse_motion(self, x, y, dx, dy):
        self.mouse.move(x, y)

    def on_mouse_press(self, x, y, buttons, modifiers):
        #buttons -> LEFT : 1, MIDDLE : 2, RIGHT : 4
        #print(self.mouse.get_position())

        if buttons == 1:
            point = self.mouse.get_position()

            if self.mouse.placingStructure is not None:
                # place condition require
                real_pos = self.mouse.get_placePos()
                grid_pos = self.mouse.get_gridPos()
                structure = self.mouse.placingStructure
                
                if self.centralBase.check(GameLayer.scenario.structure_info[structure]['cost']):
                    if self.place_structure(structure, real_pos, grid_pos):
                        self.centralBase.pay(GameLayer.scenario.structure_info[structure]['cost'])
                        self.mouse.set_placingStructure(None)
                        return
            else:
                for obj in self.get_children():
                    if isinstance(obj, Actors.Structure):
                        if abs(point[0] - obj.position[0]) <= obj.width/2 and abs(point[1] - obj.position[1]) <= obj.height/2:
                            if self.selecting_send_structure:
                                if self.hud.current_structure.set_send_structure(obj):
                                    self.selecting_send_structure = False
                                    self.mouse.set_cursor(False)
                            elif self.selecting_receive_structure:
                                if self.hud.current_structure.set_receive_structure(obj):
                                    self.selecting_receive_structure = False
                                    self.mouse.set_cursor(False)
                            else:
                                self.hud.set_current_structure(obj)
                                return

            
            if abs(point[0] - 50) <= 50 and abs(point[1] - 50) <= 50:
                pass
            
            for panel in self.hud.panel.values():
                if panel is None:
                    continue
                if abs(point[0] - panel.position[0]) <= panel.width/2 and abs(point[1] - panel.position[1]) <= panel.height/2:
                    if hasattr(panel, 'onClick'):
                        event = panel.onClick(point)
                        if event != False:
                            self.manage_event(event)
                            break;
        elif buttons == 4:
            self.mouse.set_placingStructure(None)
            self.mouse.set_cursor(False)
            self.hud.set_current_structure(None)
            self.selecting_send_structure = False
            self.selecting_receive_structure = False

            

    def manage_event(self, event):
        if event == 'Menu_MiningBase_onClick':
            self.mouse.set_placingStructure('MiningBase')
        elif event == 'Menu_SupplyBase_onClick':
            self.mouse.set_placingStructure('SupplyBase')
        elif event == 'Menu_Warehouse_onClick':
            self.mouse.set_placingStructure('Warehouse')
        elif event == 'Menu_AmmoPlant_onClick':
            self.mouse.set_placingStructure('AmmoPlant')
        elif event == 'Menu_IronWall_onClick':
            self.mouse.set_placingStructure('IronWall')
        elif event == 'Menu_CrudeTower_onClick':
            self.mouse.set_placingStructure('CrudeTower')
        elif event == 'Menu_BasicTower_onClick':
            self.mouse.set_placingStructure('BasicTower')
        elif event == 'Menu_CannonTower_onClick':
            self.mouse.set_placingStructure('CannonTower')
        elif event == 'State_Skip_onClick':
            self.next_stage()
        elif event == 'Info_SendButton_onClick':
            self.selecting_send_structure = True
            self.selecting_receive_structure = False
            self.mouse.set_cursor(True)
        elif event == 'Info_ReceiveButton_onClick':
            self.selecting_send_structure = False
            self.selecting_receive_structure = True
            self.mouse.set_cursor(True)
        elif event == 'Info_copper_onClick':
            self.hud.current_structure.set_transporting_resource('copper')
        elif event == 'Info_iron_onClick':
            self.hud.current_structure.set_transporting_resource('iron')
        elif event == 'Info_titanium_onClick':
            self.hud.current_structure.set_transporting_resource('titanium')

            
    def place_structure(self, structure, real_pos, grid_pos):
        size = GameLayer.scenario.structure_info[structure]['size']
        for x in range(grid_pos[0] - math.floor((size-1)/2), grid_pos[0] + math.ceil((size-1)/2) + 1):
            if x < 0 or x >= GameLayer.map_width:
                return False
            for y in range(grid_pos[1] - math.floor((size-1)/2), grid_pos[1] + math.ceil((size-1)/2) + 1):
                if y < 0 or y >= GameLayer.map_height:
                    return False
                if GameLayer.map[x][y] != 0:
                    return False
        
        for obj in self.get_children():
            if isinstance(obj, Actors.Enemy):
                if mt.distance(real_pos, obj.position) < 64:
                    print('Place Fail : Place Position is too close with enemy')
                    return False
                
        if structure == 'MiningBase':
            for resource in GameLayer.scenario.resource_position:
                if grid_pos in GameLayer.scenario.resource_position[resource]:
                    self.add(Actors.MiningBase(real_pos, GameLayer.scenario.structure_info[structure], resource))
                    return True
            print('Place Fail(MiningBase) : There is no resource')
        elif structure == 'SupplyBase':
            self.add(Actors.SupplyBase(real_pos, GameLayer.scenario.structure_info[structure]))
            return True
        elif structure == 'Warehouse':
            self.add(Actors.Warehouse(real_pos, GameLayer.scenario.structure_info[structure]))
            return True
        elif structure == 'AmmoPlant':
            self.add(Actors.AmmoPlant(real_pos, GameLayer.scenario.structure_info[structure]))
            return True
        elif structure == 'IronWall':
            self.add(Actors.IronWall(real_pos, GameLayer.scenario.structure_info[structure]))
            return True
        elif structure == 'CrudeTower':
            self.add(Actors.CrudeTower(real_pos, GameLayer.scenario.structure_info[structure]))
            return True
        elif structure == 'BasicTower':
            self.add(Actors.BasicTower(real_pos, GameLayer.scenario.structure_info[structure]))
            return True
        elif structure == 'CannonTower':
            self.add(Actors.CannonTower(real_pos, GameLayer.scenario.structure_info[structure]))
            return True
        
        return False

    
    def convert_pos(self, grid_pos, size):
        if size % 2 == 0:
            real_pos = ((grid_pos[0] + 1) * GameLayer.grid_size, (grid_pos[1] + 1) * GameLayer.grid_size)
        else:
            real_pos = ((grid_pos[0] + 0.5) * GameLayer.grid_size, (grid_pos[1] + 0.5) * GameLayer.grid_size)
        return real_pos

    def get_enemy_spawn_pos(self):
        w = GameLayer.map_width * GameLayer.grid_size
        h = GameLayer.map_height * GameLayer.grid_size
        
        if random.random() < 0.5:
            return (random.uniform(0, w), h)
        else:
            return (w, random.uniform(0, h))
            
        
    
class HUD(cocos.layer.Layer):
    def __init__(self):
        super(HUD, self).__init__()
        self.panel = { 'state' : None,
                       'structure_menu' : None,
                       'structure_info' : None }
        self.current_structure = None

    def init_panel(self):
        self.init_state_panel()
        self.init_structure_menu_panel()
        self.init_structure_info_panel()
    
    def init_state_panel(self):
        w, h = director.get_window_size()
        state_panel = UI.Panel('assets/panel_300x300px.png', (w-160, h-160))
        self.panel['state'] = state_panel
        self.add(state_panel)
        
        state_panel.copper_image = self._create_image('assets/copper.png', (w-240, h-60), parent=state_panel)
        state_panel.copper_amount = self._create_text((w-210, h-55), 18, parent=state_panel)
        state_panel.iron_image = self._create_image('assets/iron.png', (w-240, h-100), parent=state_panel)
        state_panel.iron_amount = self._create_text((w-210, h-95), 18, parent=state_panel)
        state_panel.titanium_image = self._create_image('assets/titanium.png', (w-240, h-140), parent=state_panel)
        state_panel.titanium_amount = self._create_text((w-210, h-135), 18, parent=state_panel)
        
        state_panel.remaining_time = self._create_text((w-300, h-220), 16, contents='Until the Stage :', parent=state_panel)
        state_panel.skip_button = self._create_button('assets/skip_button.png', (w-60, h-220), 'State_Skip_onClick', parent=state_panel, scale=0.2)
        

    def init_structure_menu_panel(self):
        w, h = director.get_window_size()
        info = GameLayer.scenario.structure_info
        
        menu_panel = UI.Panel('assets/panel_300x600px.png', (w-160, 310))
        self.panel['structure_menu'] = menu_panel
        self.add(menu_panel)
        
        self._create_image('assets/copper.png', (w-120, 580), menu_panel)
        self._create_image('assets/iron.png', (w-75, 580), menu_panel)
        self._create_image('assets/titanium.png', (w-30, 580), menu_panel)

        index = 0
        for structure in info.keys():
            if structure == 'CentralBase':
                continue
            self._create_button(info[structure]['image'], (w-280, 540 - index * 50), 'Menu_%s_onClick' % structure, menu_panel, 0.1)
            self._create_text((w-240, 540 - index * 50), 12, contents='%s' % structure, parent=menu_panel)
            self._create_text((w-130, 540 - index * 50), 12, contents='%s' % info[structure]['cost']['copper'], parent=menu_panel)
            self._create_text((w-85, 540 - index * 50), 12, contents='%s' % info[structure]['cost']['iron'], parent=menu_panel)
            self._create_text((w-40, 540 - index * 50), 12, contents='%s' % info[structure]['cost']['titanium'], parent=menu_panel)
            index += 1
        
    def init_structure_info_panel(self):
        w, h = director.get_window_size()
        info = GameLayer.scenario.structure_info

        info_panel = UI.Panel('assets/panel_300x600px.png', (w-160, 310))
        self.panel['structure_info'] = info_panel
        self.add(info_panel)

        # Common
        info_panel.images = {}
        for structure in info.keys():
            info_panel.images[structure] = self._create_image(info[structure]['image'], (w-160, 530), info_panel, scale=0.2)
        info_panel.name = self._create_text((w-160, 480), 20, contents='undefined', parent=info_panel, anchor_x='center')
        info_panel.hp = self._create_text((w-260, 440), 14, contents='HP : ', parent=info_panel)
        info_panel.storage_title = self._create_text((w-260, 400), 14, contents='Storage : ', parent=info_panel)
        info_panel.storage = []
        for i in range(5):
            info_panel.storage.append(self._create_text((w-220, 380 - i * 20), 14, contents='', parent=info_panel))

        self._create_text((w-280, 100), 18, contents='Mouse Right Button', parent=info_panel)
        self._create_text((w-280, 60), 24, contents='-> Cancel', parent=info_panel)

        
        # Supply Base
        info_panel.send_button = self._create_button('assets/send_button.png', (w-220, 240), 'Info_SendButton_onClick', info_panel, 0.2)
        info_panel.receive_button = self._create_button('assets/receive_button.png', (w-100, 240), 'Info_ReceiveButton_onClick', info_panel, 0.2)
        info_panel.copper_button = self._create_button('assets/copper.png', (w-120, 160), 'Info_copper_onClick', info_panel, 1)
        info_panel.iron_button = self._create_button('assets/iron.png', (w-160, 160), 'Info_iron_onClick', info_panel, 1)
        info_panel.titanium_button = self._create_button('assets/titanium.png', (w-200, 160), 'Info_titanium_onClick', info_panel, 1)

        
        info_panel.enable(False)


    def set_current_structure(self, structure):
        # this structure is instance object
        if self.current_structure is not None:
            self.current_structure.selected(False)
            
        self.current_structure = structure
        if structure is None:
            self.panel['structure_menu'].enable(True)
            self.panel['structure_info'].enable(False)
            return

        structure.selected(True)
        self.panel['structure_menu'].enable(False)
        self.panel['structure_info'].enable(True)

        panel = self.panel['structure_info']
        for image in panel.images.values():
            image.enable(False)
        panel.images[structure.tag].enable(True)
        panel.name.element.text = structure.tag

        for i in range(5):
            panel.storage[i].element.text = ''
        if not hasattr(structure, 'storage'):
            panel.storage_title.enable(False)
            
        if structure.tag != 'SupplyBase':
            panel.send_button.enable(False)
            panel.receive_button.enable(False)
            panel.copper_button.enable(False)
            panel.iron_button.enable(False)
            panel.titanium_button.enable(False)
            

    
    def update_structure_info_panel(self):
        if self.current_structure is None:
            return
        panel = self.panel['structure_info']
        structure = self.current_structure
        panel.hp.element.text = 'HP : %s' % structure.hp

        if hasattr(structure, 'storage'):
            index = 0
            for resource in structure.storage.keys():
                panel.storage[index].element.text = '%s : %s' % (resource, structure.storage[resource])
                index += 1

    def update_remaining_time(self, stage, time):
        self.panel['state'].remaining_time.element.text = 'Until the %s... %s' % (stage, time)
            

    def _create_button(self, img, pos, event, parent=None, scale=1):
        button = UI.Button(img, pos, event, scale)
        self.add(button)
        if parent is not None:
            parent.add(button)
        return button
    
    def _create_image(self, img, pos, parent=None, scale=1):
        image = UI.Image(img, pos, scale)
        self.add(image)
        if parent is not None:
            parent.add(image)
        return image

    def _create_text(self, pos, font_size=18, color=(255,255,255,255), contents='undefined', parent=None, anchor_x='left', anchor_y='center'):
        text = UI.Text(pos, font_size, color, contents, anchor_x, anchor_y)
        self.add(text)
        if parent is not None:
            parent.add(text)
        return text

    def update_resource(self, storage):
        self.panel['state'].copper_amount.element.text = 'Copper: %s' % storage['copper']
        self.panel['state'].iron_amount.element.text = 'Iron: %s' % storage['iron']
        self.panel['state'].titanium_amount.element.text = 'Titanium: %s' % storage['titanium']


def new_game():
    scenario = get_scenario()
    background = scenario.get_background()
    hud = HUD()
    gameLayer = GameLayer(hud, scenario)
    return cocos.scene.Scene(background, gameLayer, hud)

def game_over():
    layer = cocos.layer.Layer()
    scene = cocos.scene.Scene(layer)
    new_scene = FadeTransition(mainmenu.new_menu())
    func = lambda: director.replace(new_scene)
    scene.do(ac.Delay(3) + ac.CallFunc(func))
    return scene
