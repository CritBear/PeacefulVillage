import cocos.sprite
import cocos.audio
import cocos.text
import cocos.actions as ac
import cocos.euclid as eu
import cocos.collision_model as cm

import pyglet.image
from pyglet.image import Animation

import math
import random

import GameLayer
import MathTools as mt

class Actor(cocos.sprite.Sprite):
    def __init__(self, img, position=(0, 0), scale=1, rotation=0):
        super(Actor, self).__init__(img, position, scale=scale, rotation=rotation)
        self.cshape = cm.CircleShape(self.position, self.width * 0.5)
        self.cshape.center = eu.Vector2(self.position[0], self.position[1])
        
    '''
    @property
    def cshape(self):
        self._cshape.center = self.pos
        return self._cshape
    '''
    
class Mouse(Actor):
    def __init__(self, gridSize):
        super(Mouse, self).__init__('assets/mouse_cursor.png', (0, 0))
        self.rangeImg = cocos.sprite.Sprite('assets/range_320px.png', opacity=0, scale=1)
        self.add(self.rangeImg)
        self.opacity = 0
        self.gridSize = gridSize
        self.structure_info = GameLayer.GameLayer.scenario.structure_info
        self.gridPos = (0, 0)
        self.placePos = (0, 0)
        self.previewStructure = None
        self.placingStructure = None

    def move(self, x, y):
        self.set_position(x, y)
        if self.placingStructure is not None:
            self.set_placePos()

    def set_cursor(self, state):
        if state:
            self.opacity = 255
        else:
            self.opacity = 0
        
    def set_position(self, x, y):
        self.position = (x, y)
        self.gridPos = (x // self.gridSize, y // self.gridSize)

    def get_position(self):
        pos = self.position
        return pos

    def get_gridPos(self):
        pos = self.gridPos
        return pos

    def set_placingStructure(self, structure):
        if structure != None:
            self.placingStructure = structure
            if 'range' in self.structure_info[structure]:
                self.rangeImg.scale = self.structure_info[structure]['range']/160
                self.rangeImg.opacity = 50
            self.previewStructure = cocos.sprite.Sprite(self.structure_info[structure]['image'],
                                                        scale=0.1*self.structure_info[structure]['size'],
                                                        opacity=160)
            self.add(self.previewStructure)
        else:
            self.placingStructure = None
            self.rangeImg.opacity = 0
            if self.previewStructure is not None:
                self.remove(self.previewStructure)
                self.previewStructure = None

    def set_placePos(self):
        if self.structure_info[self.placingStructure]['size'] % 2 == 0:
            offset = 1
        else:
            offset = 0.5
        self.placePos = ((self.gridPos[0] + offset) * self.gridSize - self.position[0],
               (self.gridPos[1] + offset) * self.gridSize - self.position[1])
        self.previewStructure.position = self.placePos
        self.rangeImg.position = self.placePos

    def get_placePos(self):
        pos = (self.placePos[0] + self.position[0],
               self.placePos[1] + self.position[1])
        return pos

class SimpleActionActor(cocos.sprite.Sprite):
    def __init__(self, img, position, actions, scale=1, opacity=255):
        super(SimpleActionActor, self).__init__(img, position=position, scale=scale, opacity=opacity)
        actions += ac.CallFunc(self.kill)
        self.do(actions)

class Structure(Actor):
    def __init__(self, position, settings):
        super(Structure, self).__init__(settings['image'], position, scale=0.1*settings['size'])
        self.hp = settings['hp']
        self.size = settings['size']
        if 'range' in settings:
            self.range = settings['range']
            if settings['range'] is not None:
                self.rangeImg = cocos.sprite.Sprite('assets/range_320px.png', opacity=0, scale=settings['range']/160/self.scale)
                self.add(self.rangeImg)

    def update_obj(self, dt):
        pass

    def selected(self, state):
        if hasattr(self, 'rangeImg'):
            self.rangeImg.opacity = state * 50

    def damaged(self, damage):
        self.hp -= damage
        if self.hp <= 0:
            self.kill()
    
    def collide(self, other):
        #enemy, bullet
        if isinstance(other, Bullet):
            if other.shooter == 'enemy':
                other.kill()
                self.damaged(other.damage)

    def get_instance(self):
        return self

class CentralBase(Structure):
    def __init__(self, hud, position, settings):
        super(CentralBase, self).__init__(position, settings)
        self.tag = 'CentralBase'
        self.hud = hud
        self.cshape = cm.AARectShape(self.position, self.width * 0.5, self.height * 0.5)
        self.cshape.center = eu.Vector2(self.position[0], self.position[1])
        self.capacity = 1000
        self.storage = { 'copper' : 200,
                         'iron' : 70,
                         'titanium' : 0 }
        self.hud.update_resource(self.storage)

    def damaged(self, damage):
        self.hp -= damage
        if self.hp <= 0:
            self.parent.game_over()
    
    def update_obj(self, dt):
        pass

    def check(self, cost):
        for resource in cost.keys():
            if self.storage[resource] < cost[resource]:
                return False
        return True
    
    def pay(self, cost):
        for resource in cost.keys():
            if self.storage[resource] < cost[resource]:
                return False
    
        for resource in cost.keys():
            self.storage[resource] -= cost[resource]
        self.hud.update_resource(self.storage)
        return True

    def send(self, resource):
        if self.storage[resource] <= 0:
            return False

        self.storage[resource] -= 1
        self.hud.update_resource(self.storage)
        return True
    
    def receive(self, resource):
        if resource not in self.storage:
            return False
        
        amount = 0
        for value in self.storage.values():
            amount += value
        if amount >= self.capacity:
            return False

        self.storage[resource] += 1
        self.hud.update_resource(self.storage)
        return True


class Warehouse(Structure):
    def __init__(self, position, settings):
        super(Warehouse, self).__init__(position, settings)
        self.tag = 'Warehouse'
        self.cshape = cm.AARectShape(self.position, self.width * 0.5, self.height * 0.5)
        self.cshape.center = eu.Vector2(self.position[0], self.position[1])
        self.capacity = 200
        self.storage = { 'copper' : 0,
                         'iron' : 0,
                         'titanium' : 0,
                         'BasicBullet' : 0,
                         'CannonBullet' : 0 }

        self.isOpen = False
        self.distribute_delay = 20
        self.distribute_count = 0

    def update_obj(self, dt):
        if self.distribute_count > self.distribute_delay:
            self.distribute_count = 0
            self.distribute()
        else:
            self.distribute_count += 1

    def distribute(self):
        for obj in self.parent.get_children():
            if hasattr(obj, 'receive'):
                if isinstance(obj, Warehouse):
                    continue
                if mt.distance(self.position, obj.position) > self.range:
                    continue

                if self.storage['copper'] >= 1:
                    if obj.receive('copper'):
                        self.storage['copper'] -= 1
                        self.parent.add(SimpleActionActor('assets/copper.png', self.position,
                                                          ac.FadeIn(0.5) | ac.MoveTo(obj.position, 1),
                                                          opacity=0))
                if self.storage['iron'] >= 1:
                    if obj.receive('iron'):
                        self.storage['iron'] -= 1
                        self.parent.add(SimpleActionActor('assets/iron.png', self.position,
                                                          ac.FadeIn(0.5) | ac.MoveTo(obj.position, 1),
                                                          opacity=0))
                if self.storage['titanium'] >= 1:
                    if obj.receive('titanium'):
                        self.storage['titanium'] -= 1
                        self.parent.add(SimpleActionActor('assets/titanium.png', self.position,
                                                          ac.FadeIn(0.5) | ac.MoveTo(obj.position, 1),
                                                          opacity=0))
                if self.storage['BasicBullet'] >= 1:
                    if obj.receive('BasicBullet'):
                        self.storage['BasicBullet'] -= 1
                        self.parent.add(SimpleActionActor('assets/BasicBullet.png', self.position,
                                                          ac.FadeIn(0.5) | ac.MoveTo(obj.position, 1),
                                                          opacity=0))
                if self.storage['CannonBullet'] >= 1:
                    if obj.receive('CannonBullet'):
                        self.storage['CannonBullet'] -= 1
                        self.parent.add(SimpleActionActor('assets/CannonBullet.png', self.position,
                                                          ac.FadeIn(0.5) | ac.MoveTo(obj.position, 1),
                                                          opacity=0))

    def send(self, resource):
        if self.storage[resource] <= 0:
            return False

        self.storage[resource] -= 1
        return True
    
    def receive(self, resource):
        if resource not in self.storage:
            return False
        
        amount = 0
        for value in self.storage.values():
            amount += value
        if amount >= self.capacity:
            return False

        self.storage[resource] += 1
        return True

class SupplyBase(Structure):
    def __init__(self, position, settings):
        super(SupplyBase, self).__init__(position, settings)
        self.tag = 'SupplyBase'
        self.cshape = cm.AARectShape(self.position, self.width * 0.5, self.height * 0.5)
        self.cshape.center = eu.Vector2(self.position[0], self.position[1])
        self.receive_structure = None
        self.send_structure = None
        self.transporting_resource = None
        self.tempStorage = 0
        self.transport_delay = 12
        self.transport_count = 0

    def update_obj(self, dt):
        if self.transport_count > self.transport_delay:
            self.transport_count = 0
            self.transport()
        else:
            self.transport_count += 1

    def transport(self):
        if self.receive_structure is None or self.send_structure is None or self.transporting_resource is None:
            return
        if self.transporting_resource not in self.send_structure.storage.keys():
            return
        if self.transporting_resource not in self.receive_structure.storage.keys():
            return
        
        if self.tempStorage == 0:
            if self.send_structure.send(self.transporting_resource):
                self.tempStorage = 1
                self.parent.add(SimpleActionActor('assets/%s.png' % self.transporting_resource, self.send_structure.position,
                                                  ac.FadeIn(0.5) | ac.MoveTo(self.position, 1),
                                                  opacity=0))
        if self.tempStorage == 1:
            if self.receive_structure.receive(self.transporting_resource):
                self.tempStorage = 0
                self.parent.add(SimpleActionActor('assets/%s.png' % self.transporting_resource, self.position,
                                                  ac.FadeIn(0.5) | ac.MoveTo(self.receive_structure.position, 1),
                                                  opacity=0))

    def set_receive_structure(self, structure):
        if hasattr(structure, 'receive'):
            if mt.distance(self.position, structure.position) < self.range:
                self.receive_structure = structure
                return True
        return False
        
    def set_send_structure(self, structure):
        if hasattr(structure, 'send'):
            if mt.distance(self.position, structure.position) < self.range:
                self.send_structure = structure
                return True
        return False

    def set_transporting_resource(self, resource):
        self.transporting_resource = resource



class MiningBase(Structure):
    def __init__(self, position, settings, miningResource=None):
        super(MiningBase, self).__init__(position, settings)
        self.tag = 'MiningBase'
        self.cshape = cm.AARectShape(self.position, self.width * 0.5, self.height * 0.5)
        self.cshape.center = eu.Vector2(self.position[0], self.position[1])
        self.miningResource = miningResource
        self.capacity = 10
        self.storage = { miningResource : 0 }
        self.distribute_delay = 20
        self.distribute_count = 0
        self.mine_delay = 20
        self.mine_count = 0

    def update_obj(self, dt):
        if self.distribute_count > self.distribute_delay:
            self.distribute_count = 0
            self.distribute()
        else:
            self.distribute_count += 1

        if self.mine_count > self.mine_delay:
            self.mine_count = 0
            self.mine()
        else:
            self.mine_count += 1

    def distribute(self):
        if self.storage[self.miningResource] <= 0:
            return False
        
        for obj in self.parent.get_children():
            if hasattr(obj, 'receive'):
                if mt.distance(self.position, obj.position) > self.range:
                    continue
                if obj.receive(self.miningResource):
                    self.storage[self.miningResource] -= 1
                    self.parent.add(SimpleActionActor('assets/%s.png' % self.miningResource, self.position,
                                                      ac.FadeIn(0.5) | ac.MoveTo(obj.position, 1),
                                                      opacity=0))

    def mine(self):
        if self.miningResource is None:
            return
        
        amount = 0
        for value in self.storage.values():
            amount += value
        if amount < self.capacity:
            self.storage[self.miningResource] += 1

    def send(self, resource):
        if self.storage[resource] <= 0:
            return False

        self.storage[resource] -= 1
        return True


class AmmoPlant(Structure):
    def __init__(self, position, settings):
        super(AmmoPlant, self).__init__(position, settings)
        self.tag = 'AmmoPlant'
        self.cshape = cm.AARectShape(self.position, self.width * 0.5, self.height * 0.5)
        self.cshape.center = eu.Vector2(self.position[0], self.position[1])
        self.capacity = 200
        self.storage = { 'copper' : 0,
                         'iron' : 0,
                         'titanium' : 0,
                         'BasicBullet' : 0,
                         'CannonBullet' : 0 }
        self.produce_delay = 10
        self.produce_count = 0
        self.distribute_delay = 20
        self.distribute_count = 0

    def update_obj(self, dt):
        if self.produce_count > self.produce_delay:
            self.produce_count = 0
            self.produce()
        else:
            self.produce_count += 1

        if self.distribute_count > self.distribute_delay:
            self.distribute_count = 0
            self.distribute()
        else:
            self.distribute_count += 1

    def distribute(self):
        for obj in self.parent.get_children():
            if hasattr(obj, 'receive'):
                if mt.distance(self.position, obj.position) > self.range:
                    continue

                    if obj.receive('BasicBullet'):
                        self.storage['BasicBullet'] -= 1
                        self.parent.add(SimpleActionActor('assets/BasicBullet.png', self.position,
                                                          ac.FadeIn(0.5) | ac.MoveTo(obj.position, 1),
                                                          opacity=0))
                if self.storage['CannonBullet'] >= 1:
                    if obj.receive('CannonBullet'):
                        self.storage['CannonBullet'] -= 1
                        self.parent.add(SimpleActionActor('assets/CannonBullet.png', self.position,
                                                          ac.FadeIn(0.5) | ac.MoveTo(obj.position, 1),
                                                          opacity=0))

    def produce(self):
        if self.storage['copper'] >= 1:
            self.storage['copper'] -= 1
            self.storage['BasicBullet'] += 1
        if self.storage['iron'] >= 1:
            self.storage['iron'] -= 1
            self.storage['CannonBullet'] += 1

    def send(self, resource):
        if self.storage[resource] <= 0:
            return False

        self.storage[resource] -= 1
        return True

    def receive(self, resource):
        if resource not in self.storage:
            return False
        
        amount = 0
        for value in self.storage.values():
            amount += value
        if amount >= self.capacity:
            return False

        self.storage[resource] += 1
        return True

    

class IronWall(Structure):
    def __init__(self, position, settings):
        super(IronWall, self).__init__(position, settings)
        self.tag = 'IronWall'






class Tower(Structure):
    def __init__(self, position, settings):
        super(Tower, self).__init__(position, settings)

    def update_obj(self, dt):
        pass


class CrudeTower(Tower):
    def __init__(self, position, settings):
        super(CrudeTower, self).__init__(position, settings)
        self.tag = 'CrudeTower'
        self.capacity = 20
        self.storage = { 'copper' : 0,
                         'BasicBullet' : 0 }
        self.target_pos = None
        self.shoot_delay = 5
        self.shoot_count = 0
        self.shoot_pos_offset = eu.Vector2(16, 0) * settings['size']

    def update_obj(self, dt):
        self.set_target()

        if self.shoot_count > self.shoot_delay:
            self.shoot_count = 0
            self.shoot()
        else:
            self.shoot_count += 1

    def shoot(self):
        if self.target_pos is None:
            return

        if self.storage['BasicBullet'] >= 1:
            self.storage['BasicBullet'] -= 1
            offset_rotation = (random.random() - 0.5) * 10
            offset_position = mt.rotate_vector2(self.shoot_pos_offset, self.rotation)
            self.parent.add(BasicBullet('player', self.position + offset_position, self.rotation + offset_rotation))

        if self.storage['copper'] >= 2:
            self.storage['copper'] -= 2
            offset_rotation = (random.random() - 0.5) * 10
            offset_position = mt.rotate_vector2(self.shoot_pos_offset, self.rotation)
            self.parent.add(CrudeBullet('player', self.position + offset_position, self.rotation + offset_rotation))

    def set_target(self):
        self.target_pos = None
        for obj in self.parent.get_children():
            if hasattr(obj, 'tag') and obj.tag == 'enemy':
                if mt.distance(self.position, obj.position) <= self.range:
                    self.target_pos = obj.position
                    self.rotation = mt.get_angle(self.position, self.target_pos)

    def receive(self, resource):
        if resource not in self.storage:
            return False
        
        amount = 0
        for value in self.storage.values():
            amount += value
        if amount >= self.capacity:
            return False

        self.storage[resource] += 1
        return True


class BasicTower(Tower):
    def __init__(self, position, settings):
        super(BasicTower, self).__init__(position, settings)
        self.tag = 'BasicTower'
        self.capacity = 20
        self.storage = { 'BasicBullet' : 0 }
        self.target_pos = None
        self.shoot_delay = 5
        self.shoot_count = 0

    def update_obj(self, dt):
        self.set_target()

        if self.shoot_count > self.shoot_delay:
            self.shoot_count = 0
            self.shoot()
        else:
            self.shoot_count += 1

    def shoot(self):
        if self.target_pos is None:
            return
        if self.storage['BasicBullet'] < 1:
            return

        self.storage['BasicBullet'] -= 1
        offset_rotation = (random.random() - 0.5) * 10
        self.parent.add(BasicBullet('player', self.position, self.rotation + offset_rotation))

    def set_target(self):
        self.target_pos = None
        for obj in self.parent.get_children():
            if hasattr(obj, 'tag') and obj.tag == 'enemy':
                if mt.distance(self.position, obj.position) <= self.range:
                    self.target_pos = obj.position
                    self.rotation = mt.get_angle(self.position, self.target_pos)

    def receive(self, resource):
        if resource not in self.storage:
            return False
        
        amount = 0
        for value in self.storage.values():
            amount += value
        if amount >= self.capacity:
            return False

        self.storage[resource] += 1
        return True


class CannonTower(Tower):
    def __init__(self, position, settings):
        super(CannonTower, self).__init__(position, settings)
        self.tag = 'CannonTower'
        self.capacity = 20
        self.storage = { 'CannonBullet' : 0 }
        self.target_pos = None
        self.shoot_delay = 5
        self.shoot_count = 0

    def update_obj(self, dt):
        self.set_target()

        if self.shoot_count > self.shoot_delay:
            self.shoot_count = 0
            self.shoot()
        else:
            self.shoot_count += 1

    def shoot(self):
        if self.target_pos is None:
            return
        if self.storage['CannonBullet'] < 1:
            return

        self.storage['CannonBullet'] -= 1
        offset_rotation = (random.random() - 0.5) * 10
        self.parent.add(CannonBullet('player', self.position, self.rotation + offset_rotation))

    def set_target(self):
        self.target_pos = None
        for obj in self.parent.get_children():
            if hasattr(obj, 'tag') and obj.tag == 'enemy':
                if mt.distance(self.position, obj.position) <= self.range:
                    self.target_pos = obj.position
                    self.rotation = mt.get_angle(self.position, self.target_pos)

    def receive(self, resource):
        if resource not in self.storage:
            return False
        
        amount = 0
        for value in self.storage.values():
            amount += value
        if amount >= self.capacity:
            return False

        self.storage[resource] += 1
        return True






class Enemy(Actor):
    def __init__(self, position, settings):
        super(Enemy, self).__init__(settings['image'], position, scale=0.1*settings['size'])
        self.tag = 'enemy'
        self.hp = settings['hp']
        self.damage = settings['damage']
        self.speed = settings['speed']
        self.dead = False
        if 'range' in settings:
            self.range = settings['range']

    def update_obj(self, dt):
        pass

    def move(self, offset):
        self.position += offset
        self.cshape.center = eu.Vector2(self.position[0], self.position[1])

    def damaged(self, damage):
        self.hp -= damage
        if self.hp <= 0:
            self.dead = True

    def collide(self, other):
        #structure, bullet
        if isinstance(other, Bullet):
            if other.shooter == 'player':
                other.dead = True
                self.damaged(other.damage)

        if isinstance(other, Structure):
            if hasattr(other, 'damaged'):
                other.damaged(self.damage)
                self.move(self.velocity * -1)


class HeavyInfantry(Enemy):
    def __init__(self, position, settings):
        super(HeavyInfantry, self).__init__(position, settings)

    def update_obj(self, dt):
        radian = math.atan2(self.parent.centralBase.position[1] - self.position[1],
                            self.parent.centralBase.position[0] - self.position[0])
        self.velocity = eu.Vector2(math.cos(radian), math.sin(radian)).normalize() * self.speed

        self.move(self.velocity * dt)
        


class LightInfantry(Enemy):
    def __init__(self, position, settings):
        super(LightInfantry, self).__init__(position, settings)

    def update_obj(self, dt):
        radian = math.atan2(self.parent.centralBase.position[1] - self.position[1],
                            self.parent.centralBase.position[0] - self.position[0])
        self.velocity = eu.Vector2(math.cos(radian), math.sin(radian)).normalize() * self.speed
        
        self.move(self.velocity * dt)


class Ranger(Enemy):
    def __init__(self, position, settings):
        super(Ranger, self).__init__(position, settings)
        self.target_pos = None;
        self.shoot_delay = 20
        self.shoot_count = 0

    def update_obj(self, dt):
        self.set_target()
        radian = math.atan2(self.target_pos[1] - self.position[1],
                            self.target_pos[0] - self.position[0])
        self.velocity = eu.Vector2(math.cos(radian), math.sin(radian)).normalize() * self.speed
        self.move(self.velocity * dt)

        if self.shoot_count > self.shoot_delay:
            self.shoot_count = 0
            self.shoot()
        else:
            self.shoot_count += 1
        
    def set_target(self):
        self.target_pos = None
        minDistance = 9999
        for obj in self.parent.get_children():
            if isinstance(obj, MiningBase) or isinstance(obj, Warehouse) or isinstance(obj, SupplyBase) or isinstance(obj, AmmoPlant):
                distance = mt.distance(self.position, obj.position)
                if minDistance > distance:
                    self.target_pos = obj.position
                    minDistance = distance
                    self.rotation = mt.get_angle(self.position, self.target_pos)
        if self.target_pos is None:
            for obj in self.parent.get_children():
                if isinstance(obj, Structure):
                    distance = mt.distance(self.position, obj.position)
                    if minDistance > distance:
                        self.target_pos = obj.position
                        minDistance = distance
                        self.rotation = mt.get_angle(self.position, self.target_pos)

    def shoot(self):
        if self.target_pos is None:
            return

        if self.range > mt.distance(self.position, self.target_pos):
            offset_rotation = (random.random() - 0.5) * 10
            self.parent.add(CrudeBullet('enemy', self.position, self.rotation + offset_rotation))
            
        

class Bullet(Actor):
    def __init__(self, settings, shooter, position, rotation):
        super(Bullet, self).__init__(settings['image'], position, rotation=rotation, scale=1*settings['size'])
        self.shooter = shooter
        radian = -self.rotation / 180 * math.pi
        self.velocity = eu.Vector2(math.cos(radian), math.sin(radian)).normalize() * settings['speed']
        self.damage = settings['damage']
        self.dead = False

    def update_obj(self, dt):
        self.position += self.velocity * dt
        self.cshape.center = eu.Vector2(self.position[0], self.position[1])
        # 960 : Temporary Game size(not hud)
        if abs(480 - self.position[0]) > 480 or abs(480 - self.position[1]) > 480:
            self.dead = True


class CrudeBullet(Bullet):
    def __init__(self, shooter, position, rotation):
        super(CrudeBullet, self).__init__(GameLayer.GameLayer.scenario.bullet_info['CrudeBullet'], shooter, position, rotation)

class BasicBullet(Bullet):
    def __init__(self, shooter, position, rotation):
        super(BasicBullet, self).__init__(GameLayer.GameLayer.scenario.bullet_info['BasicBullet'], shooter, position, rotation)

class CannonBullet(Bullet):
    def __init__(self, shooter, position, rotation):
        super(CannonBullet, self).__init__(GameLayer.GameLayer.scenario.bullet_info['CannonBullet'], shooter, position, rotation)
