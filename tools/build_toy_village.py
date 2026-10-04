#!/usr/bin/env python3
"""Author the six editable toy-building scenes; no runtime generator required.

Only writes village/buildings and assets/toy_village/beveled_cube.obj.
Does not rewrite the village layout. Re-running overwrites the generated scenes.
"""
from itertools import product
from pathlib import Path
import math

ROOT = Path(__file__).resolve().parents[1]


def bevel_cube():
    faces = []
    q = 0.43
    for axis in range(3):
        rest = [i for i in range(3) if i != axis]
        for sign in [-1, 1]:
            face = []
            for u, v in [(-q, -q), (q, -q), (q, q), (-q, q)]:
                p = [0., 0., 0.]
                p[axis], p[rest[0]], p[rest[1]] = sign * .5, u, v
                face.append(p)
            faces.append(face)
    for a, b in [(0, 1), (0, 2), (1, 2)]:
        c = 3 - a - b
        for sa, sb in product([-1, 1], repeat=2):
            face = []
            for x, y, z in [(.5, q, -q), (.5, q, q), (q, .5, q), (q, .5, -q)]:
                p = [0., 0., 0.]
                p[a], p[b], p[c] = sa*x, sb*y, z
                face.append(p)
            faces.append(face)
    for sx, sy, sz in product([-1, 1], repeat=3):
        faces.append([[sx*.5, sy*q, sz*q], [sx*q, sy*.5, sz*q], [sx*q, sy*q, sz*.5]])
    lines = ['# Original chamfered toy block, authored for Phonics Farm', 'o BeveledCube']
    n = 1
    for face in faces:
        a, b, c = face[:3]
        u, v = [b[i]-a[i] for i in range(3)], [c[i]-a[i] for i in range(3)]
        cross = [u[1]*v[2]-u[2]*v[1], u[2]*v[0]-u[0]*v[2], u[0]*v[1]-u[1]*v[0]]
        if sum(cross[i]*a[i] for i in range(3)) < 0:
            face.reverse()
        lines += ['v ' + ' '.join(map(str, p)) for p in face]
        lines += ['f ' + ' '.join(str(n+i) for i in range(len(face)))]
        n += len(face)
    (ROOT/'assets/toy_village/beveled_cube.obj').write_text('\n'.join(lines)+'\n')


def vec(values):
    return 'Vector3(' + ', '.join(f'{v:.5f}' for v in values) + ')'


COLORS = dict(wood=(.48,.30,.17), honey=(.70,.48,.26), cream=(.88,.79,.59),
              glass=(.22,.42,.43), dark=(.22,.29,.28), leaf=(.31,.48,.29),
              pink=(.77,.39,.41), gold=(.87,.62,.22), paper=(.91,.85,.69))


class Scene:
    def __init__(self, name, paint, roof):
        self.name, self.nodes, self.resources = name, [], []
        self.count = 0
        for key, color in dict(COLORS, paint=paint, roof=roof).items():
            self.resources.append(f'[sub_resource type="StandardMaterial3D" id="{key}"]\nalbedo_color = Color({", ".join(map(str, color))}, 1)\nroughness = 0.9\nmetallic_specular = 0.15')

    def part(self, label, pos, size, mat='wood', rot=(0,0,0), shape='box'):
        self.count += 1
        name = f'{label}{self.count}'
        mesh = 'ExtResource("Cube")'
        if shape != 'box':
            rid = f'Mesh{self.count}'
            if shape == 'sphere':
                definition = 'SphereMesh"\nradius = 0.5\nheight = 1.0\nradial_segments = 12\nrings = 6'
            elif shape == 'prism':
                definition = 'PrismMesh"\nsize = Vector3(1, 1, 1)'
            else:
                definition = 'CylinderMesh"\ntop_radius = 0.5\nbottom_radius = 0.5\nheight = 1.0\nradial_segments = 20'
            kind, props = definition.split('\n', 1)
            self.resources.append(f'[sub_resource type="{kind} id="{rid}"]\n{props}')
            mesh = f'SubResource("{rid}")'
        self.nodes.append(f'[node name="{name}" type="MeshInstance3D" parent="."]\nposition = {vec(pos)}\nrotation_degrees = {vec(rot)}\nscale = {vec(size)}\nmesh = {mesh}\nmaterial_override = SubResource("{mat}")')

    def ball(self, label, pos, size, mat):
        self.part(label, pos, size, mat, shape='sphere')

    def disc(self, label, pos, diameter, mat, depth=.08):
        self.part(label, pos, (diameter,depth,diameter), mat, (90,0,0), 'cylinder')

    def window(self, x, y, z):
        self.part('WindowFrame', (x,y,z), (.63,.70,.12), 'cream')
        self.part('WindowGlass', (x,y,z-.075), (.48,.54,.04), 'glass')
        self.part('WindowMullion', (x,y,z-.105), (.055,.54,.04), 'cream')
        self.part('WindowMullion', (x,y,z-.11), (.48,.055,.04), 'cream')
        for dx in [-.43,.43]:
            self.part('Shutter', (x+dx,y,z), (.19,.65,.10), 'roof')

    def flowerbox(self, x, y, z):
        self.part('WindowBox', (x,y,z), (.85,.22,.28), 'honey')
        for i in range(3):
            self.ball('Foliage', (x+(i-1)*.24,y+.16,z), (.32,.22,.28), 'leaf')
            self.ball('Flower', (x+(i-1)*.24,y+.27,z-.03), (.14,.13,.14), 'pink' if i%2 else 'gold')

    def shell(self):
        self.part('Foundation', (0,.12,0), (2.8,.24,2.5), 'wood')
        self.part('PaintedBody', (0,1.18,0), (2.48,1.94,2.16), 'paint')
        # Horizontal timber courses and chunky corner joinery.
        for y in [.37,.75,1.13,1.51,1.89]:
            self.part('FrontCourse', (0,y,-1.086), (2.44,.027,.018), 'cream')
            self.part('SideCourse', (1.245,y,0), (.018,.027,2.12), 'cream')
            self.part('SideCourse', (-1.245,y,0), (.018,.027,2.12), 'cream')
        for x,z in product([-1.17,1.17],[-1.03,1.03]):
            self.part('CornerPost', (x,1.18,z), (.18,2.0,.18), 'honey')
        self.part('Gable', (0,2.61,0), (2.48,.96,2.15), 'paint', shape='prism')
        for sign in [-1,1]:
            self.part('Roof', (sign*.69,2.65,0), (1.88,.23,2.73), 'roof', (0,0,-sign*36))
            self.part('GableTrim', (sign*.69,2.64,-1.36), (1.9,.13,.12), 'cream', (0,0,-sign*36))
        self.part('RidgeCap', (0,3.19,0), (.22,.20,2.84), 'roof')
        self.part('DoorFrame', (0,.88,-1.14), (.70,1.35,.16), 'cream')
        self.part('Door', (0,.87,-1.235), (.52,1.18,.08), 'roof')
        self.ball('DoorKnob', (.17,.85,-1.31), (.08,.08,.08), 'gold')
        self.part('Doorstep', (0,.12,-1.40), (.95,.22,.54), 'honey')
        self.window(-.77,1.43,-1.13)
        self.window(.77,1.43,-1.13)
        self.disc('AtticFrame',(0,2.65,-1.10),.52,'cream')
        self.disc('AtticGlass',(0,2.65,-1.16),.35,'glass')
        # Side portholes read from the fixed camera even on the west row.
        for sign in [-1,1]:
            self.part('SideFrame',(sign*1.27,1.4,0),(.09,.65,.65),'cream')
            self.part('SideGlass',(sign*1.33,1.4,0),(.04,.48,.48),'glass')
            self.part('SideCross',(sign*1.36,1.4,0),(.03,.05,.48),'cream')
            self.part('SideCross',(sign*1.36,1.4,0),(.03,.48,.05),'cream')

    def awning(self):
        for i in range(7):
            x = (i-3)*.36
            mat = 'cream' if i%2 else 'roof'
            self.part('StripedAwning',(x,1.98,-1.52),(.365,.13,.78),mat,(-12,0,0))
            self.part('AwningScallop',(x,1.83,-1.89),(.35,.22,.10),mat)

    def save(self):
        header = f'[gd_scene load_steps={len(self.resources)+2} format=3]\n\n[ext_resource type="ArrayMesh" path="res://assets/toy_village/beveled_cube.obj" id="Cube"]\n\n'
        text = header + '\n\n'.join(self.resources) + f'\n\n[node name="{self.name}" type="Node3D"]\n\n' + '\n\n'.join(self.nodes) + '\n'
        (ROOT/f'village/buildings/{self.name}.tscn').write_text(text)


def build():
    bevel_cube()
    designs = [('windmill',(.75,.69,.49),(.28,.52,.49)),
               ('bakery',(.80,.65,.49),(.68,.31,.26)),
               ('clock_house',(.62,.73,.65),(.27,.43,.49)),
               ('bookshop',(.64,.69,.78),(.42,.37,.56)),
               ('flower_shop',(.74,.63,.64),(.36,.52,.40)),
               ('workshop',(.75,.66,.46),(.64,.40,.24))]
    for name, paint, roof in designs:
        s = Scene(name,paint,roof)
        s.shell()
        if name == 'windmill':
            s.part('MillTower',(0,3.24,.15),(.96,1.22,1.0),'cream')
            s.part('MillCap',(0,3.93,.15),(1.25,.55,1.3),'roof',shape='prism')
            for angle in [25,115]:
                s.part('SailSpar',(0,3.45,-.56),(.12,3.5,.13),'wood',(0,0,angle))
            for angle in [25,115,205,295]:
                a=math.radians(angle)
                s.part('Sail',(-math.sin(a)*1.02,3.45+math.cos(a)*1.02,-.64),(.42,1.18,.08),'cream',(0,0,angle))
                for t in [.67,1.0,1.33]:
                    s.part('SailRib',(-math.sin(a)*t,3.45+math.cos(a)*t,-.70),(.44,.045,.04),'honey',(0,0,angle))
            s.disc('MillHub',(0,3.45,-.78),.32,'gold',.16)
            s.flowerbox(-.77,.98,-1.28)
            s.flowerbox(.77,.98,-1.28)
        elif name == 'clock_house':
            s.part('ClockTower',(0,3.34,0),(1.20,1.6,1.12),'paint')
            s.part('TowerCap',(0,4.20,0),(1.6,.62,1.5),'roof',shape='prism')
            s.disc('ClockRim',(0,3.62,-.60),.94,'honey')
            s.disc('ClockFace',(0,3.62,-.67),.78,'paper')
            for i in range(12):
                a=i*math.tau/12
                s.disc('ClockTick',(math.sin(a)*.31,3.62+math.cos(a)*.31,-.724),.046,'wood',.02)
            s.part('ClockHand',(.075,3.70,-.76),(.05,.26,.04),'dark',(0,0,-42))
            s.part('ClockHand',(-.105,3.64,-.76),(.25,.04,.04),'dark',(0,0,10))
            s.ball('Finial',(0,4.58,0),(.18,.23,.18),'gold')
        elif name == 'bakery':
            s.awning()
            s.part('Chimney',(.76,3.10,.50),(.44,1.08,.47),'cream')
            s.part('ChimneyCap',(.76,3.64,.50),(.59,.16,.60),'wood')
            # Oversized carved loaf on the gable, with three pale score marks.
            s.ball('BreadSign',(0,2.69,-1.30),(1.10,.48,.22),'gold')
            for x in [-.27,0,.27]:
                s.part('BreadScore',(x,2.73,-1.42),(.055,.27,.035),'paper',(0,0,-20))
        elif name == 'bookshop':
            s.awning()
            for sign in [-1,1]:
                s.part('BookCover',(sign*.28,2.68,-1.24),(.60,.62,.09),'gold',(0,sign*-12,sign*-8))
                s.part('BookPages',(sign*.27,2.70,-1.31),(.49,.52,.06),'paper',(0,sign*-12,sign*-8))
            s.part('BookSpine',(0,2.66,-1.36),(.06,.63,.06),'honey')
        elif name == 'flower_shop':
            s.awning()
            s.flowerbox(-.77,.94,-1.32)
            s.flowerbox(.77,.94,-1.32)
            for i in range(6):
                a=i*math.tau/6
                s.ball('FlowerSignPetal',(math.sin(a)*.27,2.69+math.cos(a)*.27,-1.25),(.33,.33,.12),'pink')
            s.disc('FlowerSignHeart',(0,2.69,-1.34),.25,'gold')
        else:
            s.part('Chimney',(-.72,2.95,.42),(.40,.90,.46),'wood')
            s.part('ChimneyCap',(-.72,3.42,.42),(.55,.16,.58),'cream')
            s.disc('Gear',(0,2.66,-1.22),.59,'honey')
            for i in range(8):
                a=i*math.tau/8
                s.part('GearTooth',(math.sin(a)*.32,2.66+math.cos(a)*.32,-1.24),(.16,.18,.12),'honey',(0,0,-i*45))
            s.disc('GearCentre',(0,2.66,-1.32),.20,'dark')
            s.flowerbox(.77,.97,-1.25)
        s.save()

    # High, gently sagging festival bunting along the north cottage row.
    # It belongs to Buildings so the existing visual-occlusion check includes it.
    s = Scene('bunting', (.75,.69,.49), (.28,.52,.49))
    for start in [-9.0,-4.0]:
        count = 16
        for i in range(count):
            x = start + (i+.5)*5/count
            t = (i+.5)/count
            y = 3.70 - .55*math.sin(t*math.pi)
            slope = -.55*math.pi/5*math.cos(t*math.pi)
            s.part('Cord',(x,y,-11.55),(5/count+.02,.027,.027),'wood',(0,0,math.degrees(math.atan(slope))))
        for i in range(7):
            t=(i+1)/8
            x=start+t*5
            y=3.70-.55*math.sin(t*math.pi)-.19
            s.part('Pennant',(x,y,-11.55),(.31,.40,.035),['roof','gold','pink','cream'][i%4],(0,0,180),'prism')
    s.save()


if __name__ == '__main__':
    build()
