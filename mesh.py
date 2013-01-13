import ctypes
from ctypes import *
from euclid import *
import glob
import itertools
from math import cos, degrees, sin
import manage
from manage import collider
from pyglet.gl import *
import random
import sys
from traceback import print_exc
from util import NULL_VEC, NULL_ROT, X_UNIT, Y_UNIT, Z_UNIT, getNativePath

import wrapper
from wrapper import *

PRIMARY_COL=0x1
WING_COL=0x2
TAIL_COL=0x3
FUELTANK_COL=0x4
VICINITY_COL=0x5

all_vbos=[]
vbos={}
vbo_meshes={}
manage.lookup_colliders={}

QUART_PI=0.25*math.pi
HALF_PI=0.5*math.pi
PI2=2*math.pi

YZ_SWAP_ROT=Quaternion.new_rotate_axis(HALF_PI, Vector3(1.0, 0.0, 0.0))
SETUP_ROT=Quaternion(0.5, -0.5, 0.5, 0.5)

MIN_FLAG=0x10
MAX_FLAG=0x20
DIM_X=0x0
DIM_Y=0x1
DIM_Z=0x2

#MAX_Y=MIN_FLAG|DIM_Z
#MIN_Z=MIN_FLAG|DIM_Y
MIN_X=MIN_FLAG|DIM_X
MAX_X=MAX_FLAG|DIM_X
MIN_Y=MIN_FLAG|DIM_Y
MAX_Y=MAX_FLAG|DIM_Y
MIN_Z=MIN_FLAG|DIM_Z
MAX_Z=MAX_FLAG|DIM_Z

def getRPMFraction(bot):
    # 195 max vel when level at full thrust
    if bot.thrust==0:
        return 0.0
    #return (bot.getVelocity().magnitude()/max_vel + t/bot.MAX_THRUST)*0.3
    #print 'rpm. '+str((bot.getVelocity().magnitude()/195.0 + (t/bot.MAX_THRUST)*6)/6)+' vel: '+str((t/bot.MAX_THRUST)*6)+' thrust: '+str(bot.getVelocity().magnitude()/max_vel)
    return (bot.getVelocity().magnitude()/195.0 + (bot.thrust/bot.MAX_THRUST)*2)/3

pos_rot_unchanged=False
def setPosRotUnchanged(flag):
    global pos_rot_unchanged
    pos_rot_unchanged=flag
    return True

def transformBot(bot):
    angleAxis = bot.frame_rot.get_angle_axis()
    axis = angleAxis[1].normalized()
    
    fpos = (c_float * 3)()
    fpos[0] = bot._pos.x
    fpos[1] = bot._pos.y
    fpos[2] = bot._pos.z
    collider.setPosition(fpos)
    
    fpos[0] = axis.x
    fpos[1] = axis.y
    fpos[2] = axis.z
    
    collider.setAngleAxisRotation(c_float(degrees(angleAxis[0])), fpos)

def draw(bot, view):
    bot.frame_rot=bot._attitude*SETUP_ROT
    v_type=view.getPlaneView(bot.getId())
    if (bot.TYP, v_type) in vbos:
        for v in vbos[(bot.TYP, v_type)]:
            glPushMatrix()
            transformBot(bot)
            wrapper.drawVBO(v)
            glPopMatrix()
    if (bot.TYP, v_type) in meshes:
        count=0
        for m in meshes[(bot.TYP, v_type)]:
            glPushMatrix()
            m.draw(bot, view.view_id)
            glPopMatrix()
    else:
        bot.draw()

NO_VBO_GROUP=0xffffffff
def loadMeshes(mesh_paths, views):
    lookup = {}
    global meshes
    meshes = {}
    global vbo_meshes
    vbo_meshes = {}
    global name_to_mesh
    name_to_mesh = {}
    paths = {}

    def genGlobbedList(glob_path, cls, scale, group, blacklisted):
        globs=glob.glob(getNativePath(glob_path))
        return [ (path, (cls, scale, group)) for path in globs if path not in blacklisted]

    for mesh_key in mesh_paths:
        all_possible_globs=mesh_paths[mesh_key][0]
        blacklist=list(itertools.chain(*[ glob.glob(getNativePath(black_glob)) for black_glob in mesh_paths[mesh_key][1]]))
        paths[mesh_key]=dict(itertools.chain(*[ genGlobbedList(glob_path, cls, scale, group, blacklist) for (glob_path, (cls, scale, group)) in all_possible_globs ])).items()

    def c_ifyGroup(group):
        if group is None:
            return NO_VBO_GROUP
        else:
            return group

    for key in mesh_paths:
        meshes[key]=[ cls(wrapper.load(path, scale, c_ifyGroup(group)),
                          views, key, group)
                           for (path, (cls, scale, group)) in paths[key]]

    for mesh_key in dict(meshes):
        [ m.finishInit() for m in meshes[mesh_key] ]
        vbo_meshes[mesh_key]=[ m for m in meshes[mesh_key] if m.group is not None and manage.vbo]
        meshes[mesh_key]=[ m for m in meshes[mesh_key] if m.group is None or not manage.vbo]

def createVBOs(mesh_map):
    if not manage.vbo:
        return
    
    global vbos
    vbos = {}
    global all_vbos

    all_vbo_groups = set()
    for key in mesh_map:
        all_vbo_groups|= set([ m.group for m in mesh_map[key] if m.group is not None ])

    vbo_map={}
    for g in all_vbo_groups:
        vbo_map[g]=wrapper.createVBO(g)
        all_vbos.append(vbo_map[g])
        
    for key in mesh_map:
        vbos[key]= list(set([ vbo_map[m.group] for m in mesh_map[key] if m.group is not None]))

all_meshes=[]

def deleteVBOs():
    global all_vbos
    for vbo in all_vbos:
        print 'deleting vbo'
        wrapper.deleteVBO(vbo)
    all_vbos=[]
    #TODO rebuild vbos dict

def deleteMeshes():
    global all_meshes
    for mesh in all_meshes:
        wrapper.deleteMesh(mesh)
    all_meshes=[]
    deleteVBOs()

class Mesh(object):
    def __init__(self, mesh, views, mesh_key, group=None):
        self.group=group
        self.mesh=mesh
        self.key=mesh_key
        all_meshes.append(mesh)
        global name_to_mesh
        if mesh_key in name_to_mesh:
            self._sibs=name_to_mesh[mesh_key]
        else:
            self._sibs={}
            name_to_mesh[mesh_key]=self._sibs
        self._mesh_path=wrapper.getMeshPath(self.mesh)
        self._sibs[self._mesh_path]=self
            
        # self.texImages exists only to maintain a reference to the textures, ensuring that it isn't deleted during garbage collection
        self.texImages=[]
        self.uvId=[]
        #print 'mesh key: '+str(mesh_key)
        self.upload_textures()
        for v in views:
            v.push_handlers(self)
        self._bot_details={}
        self.rot=0.0

    def finishInit(self):
        pass

    def __str__(self):
        return object.__str__(self)+': '+self._mesh_path

    def test_draw(self, bot):
        glPushMatrix()
        glLoadIdentity()
        #glTranslatef(bot._pos.x, bot._pos.y, bot._pos.z)
        
        #new stuff
        glDisable( GL_DEPTH_TEST);
        glDisable(GL_FOG);
        glDisable( GL_LIGHTING);
        glBegin(GL_QUADS)
        glColor3f(1.0 ,1.0 ,0.0)
        scaler=50.0
        glVertex3f(-1.0*scaler, 1.0*scaler, 1.0*scaler-100)
        glVertex3f( 1.0*scaler, 1.0*scaler, 1.0*scaler-100)
        glVertex3f( 1.0*scaler, 1.0*scaler,-1.0*scaler-100)
        glVertex3f(-1.0*scaler, 1.0*scaler,-1.0*scaler-100)
        glEnd()
        glEnable( GL_DEPTH_TEST)
        glPopMatrix()
        
    def upload_textures(self, gen_fbo=False):
        uvId=0
        c_path=wrapper.getUvPath(self.mesh, uvId)
        while c_path!=None:
            path=c_path
            img=wrapper.imageLoad(path)
            tex=img.get_texture()
            self.texImages.append((path,img))
            self.uvId.append(uvId)
            wrapper.setupTex(self.mesh, uvId, tex.id)
            #object3dLib.createTexture(self.mesh,
            #                          uvId, img.get_data('RGBA', img.width*len('RGBA')), img.width, img.height, GL_RGBA)
            uvId+=1
            c_path=wrapper.getUvPath(self.mesh, uvId)
            if c_path is not None:
                print "upload_textures: "+str(tex.target)+" id: "+str(tex.id)+" tex: "+str(tex.get_texture())+" coords: "+str(tex.tex_coords)+" path: "+c_path

    def view_change(self, view):
        new_details={}
        for (view_id, bot_id) in self._bot_details:
            if view_id is not view:
                new_details[(view_id, bot_id)]=self._bot_details[(view_id, bot_id)]
        self._bot_details=new_details

    def setupRotation(self, pos, angle_quat, midPt, rotOrig=None):
        if rotOrig is None:
            rotOrig = midPt
        #print 'python. pos: '+str(pos)
        #print 'python. angle_quat: '+str(angle_quat)
        #print 'python. midPt: '+str(midPt)
        #print 'python. rotOrig: '+str(rotOrig)
        angleAxis= angle_quat.get_angle_axis()

        rotNew=angle_quat * (midPt)
        axis = angleAxis[1].normalized()
        offset=pos-(rotNew-rotOrig)
        #print 'python. rotNew: '+str(rotNew)

        fpos = (c_float * 3)()
        fpos[0] = offset.x
        fpos[1] = offset.y
        fpos[2] = offset.z
        collider.setPosition(fpos)
        #print 'python. set pos: '+str(fpos[0])+' '+str(fpos[1])+' '+str(fpos[2])
        fpos[0] = axis.x
        fpos[1] = axis.y
        fpos[2] = axis.z
        
        collider.setAngleAxisRotation(c_float(degrees(angleAxis[0])), fpos)
        #print 'python. set rot: '+str(degrees(angleAxis[0]))+' axis: '+str(fpos[0])+' '+str(fpos[1])+' '+str(fpos[2])

    def drawRotatedToTexAlpha(self, bot, angle_quat, centre_mesh, fbo, width, height, bg, alpha, boundPlane, top):
        rot=angle_quat
        mid = (c_float * 3)()
        wrapper.getMid(centre_mesh, mid)
        #midPt=Vector3(mid[0], mid[1], mid[2])
        #self.setupRotation(NULL_VEC, rot, midPt)
        wrapper.setupRotation(
            NULL_VEC.x, NULL_VEC.y, NULL_VEC.z,
            rot.x, rot.y, rot.z,
            mid[0], mid[1], mid[2],
            mid[0], mid[1], mid[2]
            )
        wrapper.drawToTex(self.mesh, alpha, fbo, width, height, bg, boundPlane, top)

    def drawToTexAlpha(self, fbo, width, height, bgTex, alpha, boundPlane, top):
        fpos = (c_float * 3)()
        fpos[0] = 0.0
        fpos[1] = 0.0
        fpos[2] = 0.0
        collider.setPosition(fpos)
        setup_angle_axis=NULL_ROT.get_angle_axis()
        setup_axis=setup_angle_axis[1].normalized()
        fpos[0] = setup_axis.x
        fpos[1] = setup_axis.y
        fpos[2] = setup_axis.z
        collider.setAngleAxisRotation(c_float(setup_angle_axis[0]), fpos)
        wrapper.drawToTex(self.mesh, alpha, fbo, width, height, bgTex, boundPlane, top)

    def draw(self, bot, view_id):
        transformBot(bot)
        wrapper.draw(self.mesh, 1.0)

    def drawRotated(self, bot, angle_quat, centre_mesh, alpha=1.0):
        # rot=bot.getAttitude()*angle_quat*SETUP_ROT

        # mid = (c_float * 3)()
        # object3dLib.getMid(centre_mesh, mid)
        # midPt=Vector3(mid[0], mid[1], mid[2])
        # rotOrig=(bot.getAttitude() * SETUP_ROT * (midPt))
        # print 'python. pos: '+str(bot.getPos())
        # print 'python. rotOrig: '+str(rotOrig)
        # print 'python. rot: '+str(rot)
        # pos=bot.getPos()
        # object3dLib.setupRotation(
        #     pos.x, pos.y, pos.z,
        #     rot.w, rot.x, rot.y, rot.z,
        #     mid[0], mid[1], mid[2],
        #     rotOrig.x, rotOrig.y, rotOrig.z
        #     )


        p=bot.getPos();
        a=bot.getAttitude();
        wrapper.drawRotated(p.x, p.y, p.z,
                                a.w, a.x, a.y, a.z,
                                angle_quat.w, angle_quat.x, angle_quat.y, angle_quat.z,
                                centre_mesh, alpha, self.mesh);
        wrapper.draw(self.mesh, alpha)


class PropMesh(Mesh):
    def __init__(self, *args, **kwargs):
        print 'PropMesh.__init__'
        Mesh.__init__(self, *args, **kwargs)
        self.ang=0.0
        self.alpha=0.0
        self.__momentum=0.0
        self.__max_prop=60.0
        self.__max_rot=self.__max_prop/2
        
    def finishInit(self):
        pass
        #(path, img)=self._sibs['data/models/cockpit/E_PropBlend.csv'].texImages[0]
        #self.__prop=self.texImages[0][1].get_texture()
        #self.__fbo=object3dLib.createFBO(img.get_texture().id, self.__prop.width, self.__prop.height)
        
    def draw(self, bot, view_id):
        rpm_prop=getRPMFraction(bot)*self.__max_prop
        self.__momentum=max(self.__momentum, rpm_prop)-0.9*abs(self.__momentum-rpm_prop)*manage.delta
        self.alpha=self.__momentum/self.__max_prop
        if self.alpha>1.0:
            self.alpha=1.0
        if self.__momentum>self.__max_rot:
            self.ang+=self.__max_rot
        else:
            self.ang+=self.__momentum
        self.ang %= PI2
        self.drawRotated(bot, Quaternion.new_rotate_axis(-self.ang, X_UNIT), self._sibs['data/models/cockpit/E_PropPivot.csv'].mesh, 1.0-self.alpha)
        #self.drawRotatedToTexAlpha(bot, Quaternion.new_rotate_axis(-self.ang, Y_UNIT), self._sibs['data/models/cockpit/E_PropPivot.csv'].mesh, self.__fbo, self.__prop.width, self.__prop.height, self.__prop.id, 0.9, MIN_Z, MAX_Y)
        #assert(self.__fbo is not None)

class PropBlendMesh(Mesh):
    def __init__(self, *args, **kwargs):
        Mesh.__init__(self, *args, **kwargs)

    def finishInit(self):
        self.__prop=self._sibs['data/models/cockpit/E_Prop.csv']

    def draw(self, bot, view_id):
        glDepthMask(False)
        self.drawRotated(bot, Quaternion.new_rotate_axis(-self.__prop.ang, X_UNIT), self._sibs['data/models/cockpit/E_PropPivot.csv'].mesh, self.__prop.alpha)
        #Mesh.draw(self, bot, view_id)
        glDepthMask(True)

class AltMeterMesh(Mesh):
    def __init__(self, *args, **kwargs):
        Mesh.__init__(self, *args, **kwargs)

    def draw(self, bot, view_id):
        self.drawRotated(bot, Quaternion.new_rotate_axis(((bot.getPos().y % 6154.0)/6154)*(PI2), X_UNIT), self._sibs['data/models/cockpit/AltDial.csv'].mesh)

class ClimbMesh(Mesh):
    def __init__(self, *args, **kwargs):
        Mesh.__init__(self, *args, **kwargs)
        print 'ClimbMesh: '+str(args)

    def draw(self, bot, view_id):
        ident=bot.getId()
        if (view_id, ident) not in self._bot_details:
            self._bot_details[(view_id, ident)]=(manage.now, 0.0)

        (last_update, smoothed_rate) = self._bot_details[(view_id, ident)]
        interval=manage.now-last_update
        if interval>1:
            interval=1.0

        smoothed_rate+=(bot.getVelocity().y-smoothed_rate)*interval

        self.drawRotated(bot, Quaternion.new_rotate_axis(((smoothed_rate % 300)/300)*(PI2), X_UNIT), self._sibs['data/models/cockpit/Circle.002.csv'].mesh)

        self._bot_details[(view_id, ident)]=(manage.now, smoothed_rate)

class BankingMesh(Mesh):
    def __init__(self, *args, **kwargs):
        Mesh.__init__(self, *args, **kwargs)

    def draw(self, bot, view_id):
        self.drawRotated(bot, Quaternion.new_rotate_axis(-(bot.getAttitude().get_bank()), X_UNIT), self._sibs['data/models/cockpit/LRDial.csv'].mesh)

class AirSpeedMesh(Mesh):
    def __init__(self, *args, **kwargs):
        Mesh.__init__(self, *args, **kwargs)

    def draw(self, bot, view_id):
        self.drawRotated(bot, Quaternion.new_rotate_axis((bot.getVelocity().magnitude()/200.0) * PI2, X_UNIT), self._sibs['data/models/cockpit/Circle.003.csv'].mesh)

class WingAirSpeedMesh(Mesh):
    def __init__(self, *args, **kwargs):
        Mesh.__init__(self, *args, **kwargs)

    def draw(self, bot, view_id):
        self.drawRotated(bot, Quaternion.new_rotate_axis(-(bot.getVelocity().magnitude()/200.0) * QUART_PI, Z_UNIT), self._sibs['data/models/cockpit/Circle.008.csv'].mesh)

class RPMMesh(Mesh):
    def __init__(self, *args, **kwargs):
        Mesh.__init__(self, *args, **kwargs)

    def draw(self, bot, view_id):
        rpm_frac=getRPMFraction(bot)
        if rpm_frac==0:
            rnd=0
        else:
            rnd=random.uniform(-0.002, 0.002)
        self.drawRotated(bot, Quaternion.new_rotate_axis((rpm_frac+rnd) * math.pi, X_UNIT), self._sibs['data/models/cockpit/Circle.004.csv'].mesh)

class CompassMesh(Mesh):
    def __init__(self, *args, **kwargs):
        Mesh.__init__(self, *args, **kwargs)

    def draw(self, bot, view_id):
        heading=bot.getHeading()
        ident=bot.getId()
        if (view_id, ident) not in self._bot_details:
            self._bot_details[(view_id, ident)]=(heading, 0.0, manage.now)

        (last_heading, speed, last_update) = self._bot_details[(view_id, ident)]

        #handle wrapping by calculating the heading when greating than last_heading and when less
        if heading > last_heading:
            alt_heading = heading - PI2
        else:
            alt_heading = heading + PI2
        if math.fabs(heading - last_heading) > math.fabs(alt_heading - last_heading):
            heading=alt_heading

        interval=manage.now-last_update
        if heading > last_heading:
            if speed>=0:
                speed += interval*0.00075
            else:
                speed += interval*0.001            
        else:
            if heading < last_heading:
                if speed<=0:
                    speed -= interval*0.00075
                else:
                    speed -= interval*0.001
        spd_limit=math.pi/14 * interval
        #print 'comp: last: '+str(last_heading)+' cur: '+str(heading)+' spd: '+str(speed)+' tm: '+str(manage.now-last_update)+' ltd: '+str(spd_limit)
        if speed>spd_limit:
            #print 'hit spd_limit 1: '+str(interval)+' now: '+str(manage.now)+' last: '+str(last_update)
            speed=spd_limit
        else:
            if speed<-spd_limit:
                #print 'hit spd_limit 2: '+str(interval)
                speed=-spd_limit
        last_heading+=speed
        last_heading = last_heading % PI2
        last_update=manage.now
        ang=-last_heading/2
        self.drawRotated(bot, Quaternion(math.cos(ang), 0, math.sin(ang), 0), self._sibs['data/models/cockpit/Cylinder.002.csv'].mesh)
        self._bot_details[(view_id, ident)]=(last_heading, speed, last_update)

def loadColliders( colliders ):
    print 'loadColliders start'
    paths=[ (typ, glob.glob(glob_path), scale) for (typ, (glob_path, scale)) in colliders.items() ]
    lookup_paths={}
    for (typ, path_list, scale) in paths:
        if typ not in lookup_paths:
            lookup_paths[typ]=[]
        lookup_paths[typ].extend([ (getNativePath(p), scale) for p in path_list ])

    manage.lookup_colliders={}
    for (typ, path_list, scale) in paths:
        #lookup_paths[typ][:]=[ (getNativePath(p), scale)
        #                       for (p, scale) in lookup_paths[typ] ]
        num_paths=len(lookup_paths[typ])
        coll_arr=collider.allocColliders(num_paths)
        #lookup_colliders[typ]=object3dLib.allocColliders(num_paths)
        idx=0
        print 'loadColliders. in paths: '+str((typ, path_list, scale))
        for (path, scale) in lookup_paths[typ]:
            print 'loadColliders. pathScale: '+str((path,scale))
            collider.loadCollider(coll_arr, idx, path, scale)
            idx+=1
        collider.identifyBigCollider(coll_arr, num_paths)
        manage.lookup_colliders[typ]=(num_paths, coll_arr)


colModels={}
def initCollider(typ, ident):
    try:
        assert typ in manage.lookup_colliders
        if ident not in colModels:
            colModels[ident]=CollisionModel(typ)
    except AssertionError:
        print_exc()
        print 'no colliders loaded for '+str(typ)+' '+str(manage.lookup_colliders.keys())
        import pdb; pdb.set_trace()

def freeCollider(ident):
    global colModels
    if ident in colModels:
        mod=colModels[ident]
        mod.free()
        del(colModels[ident])

def deleteColliders():
    #global all_colliders
    #for (num, arr) in manage.lookup_colliders.values():
    #    object3dLib.deleteColliders(num, arr)
    #all_colliders=[]
    global colModels
    for ident in colModels:
        mod=colModels[ident]
        mod.free()
    colModels={}

def updateCollider(ident, pos, att):
    if ident in colModels:
        colModels[ident].update(pos, att)

def getCollisionModel(ident):
    if ident in colModels:
        return colModels[ident]
    return None

def collidedCollider(id1, id2):
    try:
        assert id1 in colModels and id2 in colModels
        m1=colModels[id1]
        m2=colModels[id2]
        return collider.checkCollisionCol(m1.colliders, m2.colliders,
                                             byref(m1.num_collisions), m1.results,
                                             byref(m2.num_collisions), m2.results)
    except AssertionError:
        print "id1 "+str(id1)+" id2 "+str(id2)+" "+str(colModels.keys())
        print_exc()
        return False
    
def collidedPoint(id1, oldPt, newPt):
    try:
        assert id1 in colModels
        m1=colModels[id1]
        return collider.checkCollisionPoint(m1.colliders, oldPt.x, oldPt.y, oldPt.z,
                                               newPt.x, newPt.y, newPt.z,
                                               byref(m1.num_collisions), m1.results)
    except AssertionError:
        print_exc()
        return False
    
class CollisionModel:
    def __init__(self, typ):
        self.__typ=typ
        (self._numCols, self._origCols)=manage.lookup_colliders[ typ ]
        ArrayType=ctypes.c_uint*self._numCols
        self.results=ArrayType()
        self.num_collisions=ctypes.c_uint();
        self.colliders=manage.collider.allocTransCols(self._origCols)

    def free(self):
        collider.deleteTransCols(self.colliders)

    def update(self, pos, att):
        self._forced_y_delta=0.0
        if self._numCols>0:
            collider.updateColliders( self.colliders, manage.iteration,
                                         pos.x, pos.y, pos.z,
                                         att.w, att.x,
                                         att.y, att.z )

