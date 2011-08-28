#!./blender_script data/models/sphere.blend  

import bpy
from mathutils import Color

print('Objects, ', len(bpy.data.meshes))
print('Object:, First Vertice:, Vertices:, First Triangle:, Triangles:')

v_tot=0
f_tot=0
v_next=1
t_next=1
tri2vert={}
for m in bpy.data.meshes:
    print(m.name, ', ', v_next, ', ', len(m.vertices), ', ', t_next, ', ', len(m.faces)*2)
    v_next+=len(m.vertices)
    t_next+=len(m.faces)*2
    for v in m.vertices:
        v_tot+=1

    for f in m.faces:
        f_tot+=1

print()
print('Vertices, ',v_tot)
print('Vertice:, X:, Y:, Z:')
v_num=0
for m in bpy.data.meshes:
    for v in m.vertices:
        v_num+=1
        tri2vert[m,v.index]=v_num
        print(v_num, v.co.x, v.co.y, v.co.z)
        #if m.name == 'Circle':
        #    print('lookup: m ', m, 'v ', v, 'v_num ', v_num)

print()
print('Triangles, ', f_tot*2)
print('Triangle:, Side1:, Side2:, Side3:')

f_num=0
for m in bpy.data.meshes:
    for f in m.faces:
        verts=[]
        for v_ref in f.vertices:
            verts.append(v_ref)
        f_num+=1
        try:
            print(f_num*2-1, ', ', tri2vert[m,verts[0]], ', ', tri2vert[m,verts[1]], ', ', tri2vert[m,verts[2]])
            if len(verts)==4:
                print(f_num*2, ', ', tri2vert[m,verts[1]], ', ', tri2vert[m,verts[2]], ', ', tri2vert[m,verts[3]])
            assert len(verts)<=4
        except AssertionError:
            print('Expecting 4 verts: ', verts, ' m: ', m, ' f: ', f)
            exit(-1)

print()
print('Colors, ', f_num*2)
print('Triangle:, Red:, Green:, Blue:')

f_num=0
BLACK=Color((0,0,0))
for m in bpy.data.meshes:
    if len(m.materials):
        c=m.materials[0].diffuse_color
    else:
        c=BLACK
    for f in m.faces:
        verts=[]
        for v_ref in f.vertices:
            verts.append(v_ref)
        f_num+=1
        print(f_num*2-1, ', ', round(c.r*0xff), ', ', round(c.g*0xff), ', ', round(c.b*0xff))
        print(f_num*2, ', ', round(c.r*0xff), ', ', round(c.g*0xff), ', ', round(c.b*0xff))
