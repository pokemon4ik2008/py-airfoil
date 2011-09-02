#!./blender_script data/models/sphere.blend  

import bpy
#from euclid import *
from mathutils import Color, Vector

print('Objects, ', len(bpy.data.meshes))
print('Object:, First Vertice:, Vertices:, First Triangle:, Triangles:')

obs=bpy.context.scene.objects

v_tot=0
t_tot=0
v_next=1
t_next=1
tri2vert={}
for o in obs:
    m=o.data
    print(m.name, ', ', v_next, ', ', len(m.vertices), ', ', t_next, ', ', len(m.faces)*2)
    v_next+=len(m.vertices)
    t_next+=len(m.faces)*2
    for v in m.vertices:
        v_tot+=1

    for f in m.faces:
        verts=[]
        for v_ref in f.vertices:
            verts.append(v_ref)
        try:
            t_tot+=1
            if len(verts)==4:
                t_tot+=1
            assert len(verts)<=4
        except AssertionError:
            print('Expecting 4 verts while counting: ', verts, ' m: ', m, ' f: ', f)
            exit(-1)

print()
print('Vertices, ',v_tot)
print('Vertice:, X:, Y:, Z:')
v_num=0
for o in obs:
    m=o.data
    for v in m.vertices:
        v_num+=1
        tri2vert[m,v.index]=v_num
        s=o.scale
        l=o.location
        r=o.rotation_euler.to_quaternion()
        vsr=r*Vector((v.co.x*s.x, v.co.y*s.y, v.co.z*s.z))
        print(v_num,', ', vsr.x+l.x, ', ', vsr.y+l.y, ', ', vsr.z+l.z)
        #if m.name == 'Circle':
        #    print('lookup: m ', m, 'v ', v, 'v_num ', v_num)

print()
print('Triangles, ', t_tot)
print('Triangle:, Side1:, Side2:, Side3:')

t_num=0
for o in obs:
    m=o.data
    for f in m.faces:
        verts=[]
        for v_ref in f.vertices:
            verts.append(v_ref)
        try:
            t_num+=1
            print(t_num, ', ', tri2vert[m,verts[0]], ', ', tri2vert[m,verts[1]], ', ', tri2vert[m,verts[2]])
            if len(verts)==4:
                t_num+=1
                print(t_num, ', ', tri2vert[m,verts[0]], ', ', tri2vert[m,verts[2]], ', ', tri2vert[m,verts[3]])
            assert len(verts)<=4
        except AssertionError:
            print('Expecting 4 verts in triangles: ', verts, ' m: ', m, ' f: ', f)
            exit(-1)

print()
print('Colors, ', t_tot)
print('Triangle:, Red:, Green:, Blue:')

t_num=0
BLACK=Color((0,0,0))
for o in obs:
    m=o.data
    if len(m.materials):
        c=m.materials[0].diffuse_color
    else:
        c=BLACK
    for f in m.faces:
        verts=[]
        for v_ref in f.vertices:
            verts.append(v_ref)
        try:
            t_num+=1
            print(t_num, ', ', round(c.r*0xff), ', ', round(c.g*0xff), ', ', round(c.b*0xff))
            if len(verts)==4:
                t_num+=1
                print(t_num, ', ', round(c.r*0xff), ', ', round(c.g*0xff), ', ', round(c.b*0xff))
            assert len(verts)<=4
        except AssertionError:
            print('Expecting 4 verts in colours: ', verts, ' m: ', m, ' f: ', f)
            exit(-1)
