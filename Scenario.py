import cocos.tiles
import cocos.actions as ac
import cocos.euclid as eu

class Scenario(object):
    def __init__(self, settings):
        self.tmx_map = settings['tmx_map']
        self.structure_info = settings['structure_info']
        self.enemy_info = settings['enemy_info']
        self.bullet_info = settings['bullet_info']
        self.stage_info = settings['stage_info']
        self.centralBase_position = settings['centralBase_position']
        self.resource_position = settings['resource_position']

        self.pixelPerGrid = 32
        self.map_width = 30
        self.map_height = 30
        self._actions = None

    def get_background(self):
        tmx_map = cocos.tiles.load('assets/desert_map_30x30.tmx')
        bg = tmx_map[self.tmx_map]
        bg.set_view(0, 0, bg.px_width, bg.px_height)
        return bg

def get_scenario():
    settings = { 'tmx_map' : 'Floor' }
    structure_info = {
        'CentralBase' : {
            'image' : 'assets/CentralBase.png',
            'size' : 2,
            'cost' : None,
            'range' : 160,
            'hp' : 200 },
        'Warehouse' : {
            'image' : 'assets/Warehouse.png',
            'size' : 1,
            'cost' : { 'copper' : 10, 'iron' : 10, 'titanium' : 0 },
            'range' : 160,
            'hp' : 100 },
        'SupplyBase' : {
            'image' : 'assets/SupplyBase.png',
            'size' : 1,
            'cost' : { 'copper' : 10, 'iron' : 10, 'titanium' : 0 },
            'range' : 360,
            'hp' : 100 },
        'MiningBase' : {
            'image' : 'assets/MiningBase.png',
            'size' : 1,
            'cost' : { 'copper' : 10, 'iron' : 10, 'titanium' : 0 },
            'range' : 160,
            'hp' : 100 },
        'AmmoPlant' : {
            'image' : 'assets/AmmoPlant.png',
            'size' : 1,
            'cost' : { 'copper' : 10, 'iron' : 10, 'titanium' : 0 },
            'range' : 160,
            'hp' : 100 },
        'IronWall' : {
            'image' : 'assets/IronWall.png',
            'size' : 1,
            'cost' : { 'copper' : 10, 'iron' : 120, 'titanium' : 0 },
            'hp' : 800 },
        'CrudeTower' : {
            'image' : 'assets/CrudeTower.png',
            'size' : 2,
            'cost' : { 'copper' : 40, 'iron' : 0, 'titanium' : 0 },
            'range' : 160,
            'hp' : 100 },
        'BasicTower' : {
            'image' : 'assets/BasicTower.png',
            'size' : 2,
            'cost' : { 'copper' : 120, 'iron' : 30, 'titanium' : 0 },
            'range' : 260,
            'hp' : 100 },
        'CannonTower' : {
            'image' : 'assets/CannonTower.png',
            'size' : 2,
            'cost' : { 'copper' : 200, 'iron' : 70, 'titanium' : 30 },
            'range' : 300,
            'hp' : 100 }
        }
    settings['structure_info'] = structure_info

    enemy_info = {
        'HeavyInfantry' : {
            'image' : 'assets/HeavyInfantry.png',
            'size' : 2,
            'hp' : 100,
            'damage' : 20,
            'speed' : 30 },
        'LightInfantry' : {
            'image' : 'assets/LightInfantry.png',
            'size' : 1,
            'hp' : 100,
            'damage' : 20,
            'speed' : 60,
            'range' : 128 },
        'Ranger' : {
            'image' : 'assets/Ranger.png',
            'size' : 1,
            'hp' : 100,
            'damage' : 20,
            'speed' : 80,
            'range' : 192 }
        }
    settings['enemy_info'] = enemy_info

    bullet_info = {
        'CrudeBullet' : {
            'image' : 'assets/CrudeBullet.png',
            'size' : 1,
            'speed' : 800,
            'damage' : 10 },
        'BasicBullet' : {
            'image' : 'assets/BasicBullet.png',
            'size' : 1,
            'speed' : 1000,
            'damage' : 10 },
        'CannonBullet' : {
            'image' : 'assets/CannonBullet.png',
            'size' : 1,
            'speed' : 600,
            'damage' : 60 }
        }
    settings['bullet_info'] = bullet_info

    stage_info = [
        { 'time' : 60,
          'enemy' : { 'HeavyInfantry' : 0,
                      'LightInfantry' : 0,
                      'Ranger' : 0 } },
        { 'time' : 30,
          'enemy' : { 'HeavyInfantry' : 2,
                      'LightInfantry' : 0,
                      'Ranger' : 0 } },
        { 'time' : 30,
          'enemy' : { 'HeavyInfantry' : 5,
                      'LightInfantry' : 0,
                      'Ranger' : 0 } },
        { 'time' : 30,
          'enemy' : { 'HeavyInfantry' : 8,
                      'LightInfantry' : 0,
                      'Ranger' : 0 } },
        { 'time' : 30,
          'enemy' : { 'HeavyInfantry' : 15,
                      'LightInfantry' : 0,
                      'Ranger' : 0 } }
        ]
    settings['stage_info'] = stage_info
    
    resource_position = { 'copper' : [(0, 4), (11, 3), (12, 4), (25, 12), (4, 15), (4, 16), (6, 16), (10, 26), (14, 23)],
                          'iron' : [(0, 2), (19, 2), (20, 2), (20, 3), (1, 12), (11, 19)],
                          'titanium' : [(0, 0), (17, 17), (22, 20)] }
    settings['resource_position'] = resource_position
    
    centralBase_position = (3, 2)
    settings['centralBase_position'] = centralBase_position
        
    sc = Scenario(settings)
    return sc
