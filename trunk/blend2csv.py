# Usage: ./blend data/models/cockpit.blend blend2csv.py 
import bpy
from mathutils import Color, Vector
import os
from os.path import exists, join, splitext
import sys
from traceback import print_exc

blender_file=sys.argv[2]
dest_dir=splitext(blender_file)[0]
print('dest_dir: '+dest_dir)
for path in os.listdir(dest_dir):
    try:
        os.remove(join(*(dest_dir,path)))
    except OSError:
        pass

if not os.path.isdir(dest_dir):
    os.mkdir(dest_dir)

scene=bpy.context.scene
obs=scene.objects
for o in obs:
    try:
        if o.data.vertices and o.is_visible(scene):
            out=open(join(*(dest_dir, o.name)), "w")
        else:
            continue
    except AttributeError:
        continue

    out.write('Objects, 1\n')
    out.write('Object:, First Vertice:, Vertices:, First Triangle:, Triangles:\n')

    v_tot=0
    t_tot=0
    v_next=1
    t_next=1
    tri2vert={}

    m=o.data
    out.write(m.name + ', ' + str(v_next) + ', ' + str(len(m.vertices)) + ', ' + str(t_next) + ', ' + str(len(m.faces)*2)+'\n')
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

    out.write('\n')
    out.write('Vertices, '+str(v_tot)+'\n')
    out.write('Vertice:, X:, Y:, Z:\n')
    v_num=0

    m=o.data
    for v in m.vertices:
        v_num+=1
        tri2vert[m,v.index]=v_num
        s=o.scale
        l=o.location
        r=o.rotation_euler.to_quaternion()
        vsr=r*Vector((v.co.x*s.x, v.co.y*s.y, v.co.z*s.z))
        out.write(str(v_num) +str(', ')+ str(vsr.x+l.x)+ ', '+ str(vsr.y+l.y)+ ', '+ str(vsr.z+l.z)+'\n')

    out.write('\n')
    out.write('Triangles, '+str(t_tot)+'\n')
    out.write('Triangle:, Side1:, Side2:, Side3:\n')

    t_num=0

    m=o.data
    for f in m.faces:
        verts=[]
        for v_ref in f.vertices:
            verts.append(v_ref)
        try:
            t_num+=1
            out.write(str(t_num)+', '+str(tri2vert[m,verts[0]])+', '+str(tri2vert[m,verts[1]])+', '+str(tri2vert[m,verts[2]])+'\n')
            if len(verts)==4:
                t_num+=1
                out.write(str(t_num)+', '+str(tri2vert[m,verts[0]])+', '+str(tri2vert[m,verts[2]])+', '+str(tri2vert[m,verts[3]])+'\n')
            assert len(verts)<=4
        except AssertionError:
            print('Expecting 4 verts in triangles: ', verts, ' m: ', m, ' f: ', f)
            exit(-1)

    out.write('\n')
    out.write('Colors, '+str(t_tot)+'\n')
    out.write('Triangle:, Red:, Green:, Blue:\n')

    t_num=0
    BLACK=Color((0,0,0))

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
            out.write(str(t_num)+', '+str(round(c.r*0xff))+', '+str(round(c.g*0xff))+', '+str(round(c.b*0xff))+'\n')
            if len(verts)==4:
                t_num+=1
                out.write(str(t_num)+', '+str(round(c.r*0xff))+', '+str(round(c.g*0xff))+', '+str(round(c.b*0xff))+'\n')
            assert len(verts)<=4
        except AssertionError:
            print('Expecting 4 verts in colours: ', verts, ' m: ', m, ' f: ', f)
            exit(-1)
    out.close()
