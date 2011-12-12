# Usage: ./blend data/models/cockpit.blend blend2csv.py 
import bpy
from mathutils import Color, Vector
import os
from os.path import exists, join, splitext
import re
import sys
from traceback import print_exc

prec="%.8f"

#texture path:
#bpy.context.scene.objects[20].material_slots[0].material.texture_slots[0].texture.image.filepath
#bpy.context.scene.objects[20].data.uv_textures[0].name give uv map name
# material index of face: bpy.context.scene.objects[20].data.faces[0].material_index
# if material_index==textured material face.index give index then
# bpy.context.scene.objects[20].data.uv_textures[0].data[face.index].uv is the uv mapping
# material: bpy.context.scene.objects[20].data.materials[0]
# array of uv mappings (see api ref p646): bpy.context.scene.objects[20].data.uv_textures[0].data[face_id].uv[4][2]

blender_file=sys.argv[2]
dest_dir=splitext(blender_file)[0]
print('dest_dir: '+dest_dir)
for path in os.listdir(dest_dir):
    try:
        os.remove(join(*(dest_dir,path))+'.csv')
    except OSError:
        pass

if not os.path.isdir(dest_dir):
    os.mkdir(dest_dir)

bpy.ops.file.make_paths_absolute()
scene=bpy.context.scene
obs=scene.objects
for obj_i in range(0, len(obs)):
    o=obs[obj_i]
    try:
        if o.data.vertices and o.is_visible(scene):
            out=open(join(*(dest_dir, o.name))+'.csv', "w")
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
            sys.exit(-1)

    out.write('\n')
    out.write('Colors, '+str(t_tot)+'\n')
    out.write('Triangle:, Red:, Green:, Blue:\n')

    t_num=0
    BLACK=Color((0,0,0))

    m=o.data
    for f in m.faces:
        try:
            if len(o.data.materials)>f.material_index:
                c=o.data.materials[f.material_index].diffuse_color
            else:
                c=BLACK
                assert False
            verts=[]
            for v_ref in f.vertices:
                verts.append(v_ref)
            t_num+=1
            out.write(str(t_num)+', '+str(round(c.r*0xff))+', '+str(round(c.g*0xff))+', '+str(round(c.b*0xff))+'\n')
            if len(verts)==4:
                t_num+=1
                out.write(str(t_num)+', '+str(round(c.r*0xff))+', '+str(round(c.g*0xff))+', '+str(round(c.b*0xff))+'\n')
            assert len(verts)<=4
        except AssertionError:
            print('Expecting 4 verts in colours: ', verts, ' m: ', m, ' f: ', f, ' mesh: ', m.name, ' num materials: ', str(len(o.data.materials)), ' mat idx: ', str(f.material_index))
            sys.exit(-1)

    texture_count=0
    for t in o.material_slots:
        for s in t.material.texture_slots:
            if s is not None:
                texture_count+=1

    map2Idx={}
    mapIdx=0
    out.write('\nTextures, '+ str(texture_count)+'\n')
    out.write('UV Map Id:, Texture_Path\n')
    tex_slots=[]
    for matIdx in range(0, len(o.material_slots)):
        t=o.material_slots[matIdx]
        for s in t.material.texture_slots:
            if s is None:
                continue
            path=s.texture.image.filepath
            match=re.search('(data/textures/.*$)', path)
            if match is not None:
                map2Idx[(matIdx, s.uv_layer)]=mapIdx
                out.write(str(mapIdx)+ ', '+ match.group(0) +'\n')
                tex_slots.append(mapIdx)
                mapIdx+=1
    m=o.data
    t_num=0
    for uv_map in m.uv_textures:
        t_num=0
        for uv_face in range(0, len(uv_map.data)):
            f=uv_map.data[uv_face]
            face=o.data.faces[uv_face]
            verts=[]
            for v_ref in face.vertices:
                verts.append(v_ref)
            try:
                if (face.material_index, uv_map.name) in map2Idx:
                    t_num+=1
                    if len(verts)==4:
                        t_num+=1
                    assert len(verts)<=4
            except AssertionError:
                print('Expecting 4 verts in triangles: ', verts, ' m: ', m, ' f: ', f)
                exit(-1)

    out.write('\nUVMaps, '+str(t_num)+'\n')
    out.write('Triangle:, UV Map Id:, vector1_uv_x, vector1_uv_y, vector2_uv_x, vector2_uv_y, vector3_uv_x, vector3_uv_x\n')
    for uv_map in m.uv_textures:
        t_num=0
        for uv_face in range(0, len(uv_map.data)):
            f=uv_map.data[uv_face]
            face=o.data.faces[uv_face]
            verts=[]
            for v_ref in face.vertices:
                verts.append(v_ref)
            t_num+=1
            tri=t_num
            if len(verts)==4:
                t_num+=1
            try:
                if (face.material_index, uv_map.name) in map2Idx:
                    out.write(str(tri)+', '+str(map2Idx[face.material_index, uv_map.name])+', '+ prec % f.uv[0][0] +', '+ prec % f.uv[0][1]+', '+ prec % f.uv[1][0]+', '+ prec % f.uv[1][1]+', '+ prec % f.uv[2][0]+', '+ prec % f.uv[2][1]+'\n')
                    if len(verts)==4:
                        out.write(str(tri+1)+', '+str(map2Idx[face.material_index, uv_map.name])+', '+ prec % f.uv[0][0]+', '+prec % f.uv[0][1]+', '+prec % f.uv[2][0]+', '+prec % f.uv[2][1]+', '+ prec % f.uv[3][0]+', '+ prec % f.uv[3][1]+'\n')
                    assert len(verts)<=4
            except AssertionError:
                print('Expecting 4 verts in triangles: ', verts, ' m: ', m, ' f: ', f)
                exit(-1)

    out.close()
