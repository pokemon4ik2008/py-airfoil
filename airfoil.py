##//
##//    Copyright 2011 Paul White
##//
##//    This file is part of py-airfoil.
##//
##//    This is free software: you can redistribute it and/or modify
##//    it under the terms of the GNU General Public License as published by
##//    the Free Software Foundation, either version 3 of the License, or
##//    (at your option) any later version.
##
##//    This is distributed in the hope that it will be useful,
##//    but WITHOUT ANY WARRANTY; without even the implied warranty of
##//    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
##//    GNU General Public License for more details.
##//
##//    You should have received a copy of the GNU General Public License
##//    along with FtpServerMobile.  If not, see <http://www.gnu.org/licenses/>.
##//

from euclid import *
import glob
import manage
import mesh
from pyglet.gl import *
from pyglet.window import key
import time
from util import *
from math import *
#import pdb
import threading
from traceback import print_exc

##[3]Spitfire Mk.XIV
##
##Weight: 3,850 kg
##Wing area: 22.48 m^2
##Wing span: 11.23 m
##Wing AR: 5.61
##Wing Clmax: 1.36
##Cd0: 0.0229
##
##Engine power: 2,235 HP

# constants
rho = 1.29 # kg/m^3 density of air
accelDueToGravity = 9.8 # m/s/s
Y_FORCED=3.0

class Obj(object):
    in_flight=0

    def __init__(self, pos, attitude, vel, cterrain=None):
        self._pos = pos
        self._attitude=attitude
        self._lastClock = time.time()
        self._velocity = vel
        self.__elevRot=Quaternion.new_rotate_axis(0, Vector3(0.0, 0.0, 1.0))
        self.__MAX_ACROBATIC_AIRSPEED_THRESHOLD = 60 # the speed at which our flaps etc. start having maximum effect
        self.__hasHitGround = False
        self._centreOfGravity = Vector3(0.2, 0.0, 0.0)
        self._is_real=False	
        self._scales = [0.0, 0.0, 0.0]
        self._mesh = None
        self._cterrain = cterrain
        self._angularVelocity = Quaternion.new_rotate_axis(0, Vector3(0.0, 0.0, 1.0))

    def getPos(self):
        return self._pos

    def getAttitude(self):
        return self._attitude

    def getVelocity(self):
        return self._velocity

    def setPos(self, pos):
        self._pos=pos
        return self

    def setAttitude(self, att):        
        self._attitude=att
        return self

    def setVelocity(self, vel):
        self._velocity=vel
        return self    

    def _getTimeDiff(self):
        # Determine time since last frame
        now = time.time()
        previousClock = self._lastClock
        self._lastClock = now
        return self._lastClock - previousClock

    def _getVectors(self):
        zenithVector = (self._attitude * Vector3(0.0, 1.0, 0.0)).normalized()
        noseVector = (self._attitude * Vector3(1.0, 0.0, 0.0)).normalized()
        return (zenithVector, noseVector)

    #kw this will return a contant for ballistic flight
    def _getElevRot(self):
        return self.__elevRot


    def _rotateByAngularVel(self, timeDiff):
	(angle,axis)=self._angularVelocity.get_angle_axis()

        # We shall scale the application of the angular velocity to the rotation of the object
        # by the actual velocity of the object:
        # Calculate a scale between 0 and 1.0:
        maxs = 60.0
        scale = self._velocity.magnitude()/maxs
        if scale > 1.0:
            scale = 1.0

        # Apply the rotation, scale by the time, and the scale factor from above
	self._attitude = self._attitude * (Quaternion.new_rotate_axis(angle*timeDiff*scale,axis))
        # Reduce the angular velocity by a factor so that the object doesn't rotate forever.
	self._angularVelocity = Quaternion.new_rotate_axis(angle*0.99,axis)
	
    def __updateInternalMoment(self, timeDiff):
        # This will model the rotation about a vector parrallel to the ground plane caused by an
        # internal weight imbalance in the aircraft. Example, the engine at the front of the plane
        # might cause the front of the plane to tilt down. A rotation occurs because the lifting
        # force provided by the wings does not necessarily occur at the centre of gravity.
        if not self.__hasHitGround:
            # Rotate centre of gravity vector according to attitude
            cog = self._attitude * self._centreOfGravity
            # Find the axis of rotation
            rotAxis =  Vector3(0.0,1.0,0.0).cross(cog)

            # Project the normalised cog vector onto the ground plane and determine 2d distance from 
            # origin and use as to scale the max amount of rotation. Max rotation therefore occurs when
            # nose is pointing at horizon.
            cogNormalised = cog.normalized()
            rotRatio = math.hypot(cogNormalised.x, cogNormalised.z)
            angularChange = rotRatio * math.pi * 33.0 / 500.0 * timeDiff

            internalRotation = Quaternion.new_rotate_axis(angularChange, rotAxis.normalized())
            self._attitude = internalRotation * self._attitude 

    def _getSpeedRatio(self):
        # Return the current speed as a ratio of the max speed
        # Currently we'll approximate this. Ideally we would calculate the max
        # speed based upon the max thrust and steady state air resistance at that thrust.
        vel = self._velocity.magnitude()
        if vel > self.__MAX_ACROBATIC_AIRSPEED_THRESHOLD:
            return 1.0
        else:
            return vel/self.__MAX_ACROBATIC_AIRSPEED_THRESHOLD    

    def __updatePitch(self, timeDiff):
        elevNorm = (self._attitude * self._getElevRot()) * Vector3(0.0, 1.0, 0.0)
        dot = self._velocity.normalized().dot(elevNorm)
        angularChange = dot * (math.pi/3.0) * self._getSpeedRatio() * timeDiff

        self._attitude = self._attitude * Quaternion.new_rotate_axis( angularChange, Z_UNIT)
        #print 'updatePitch: '+str(self._attitude)
        
    def _updateRoll(self, timeDiff):
        pass

    def getWeightForce(self):        
        return self._mass * accelDueToGravity

    def getDragForce(self, angleOfAttack, timeDiff, drag=0.0):        
        vel = self._velocity
        vMag = vel.magnitude()

        drags = []
        drags.append(drag)

        # Calculate attitude rotation due to air resistance
        # There is no rotation if there is no wind...
        if vMag > 0.0:
            # Scale the effect of air resistance on each surface: top, side, front
            totalScale = sum(self._scales)
            normals = [Vector3(0.0, 1.0, 0.0), #plane through wings
                       Vector3(0.0, 0.0, 1.0), #plane through fuselage (vertically)
                       Vector3(1.0, 0.0, 0.0)] #plane perp. to nose vector 

            # Run through each of the planes, and calculate the contributory component
            for scale, norm in zip(self._scales, normals):
                # Rotate the normal according to attitude
                norm = self._attitude * norm

                # Use dot product to figure how much effect each plane has
                dot = norm.dot(vel.normalized())

                # Scale the drag based on the relative resistance of the associated surface
                scaledDot =  dot * scale
                componentDrag = scaledDot * vMag
                #componentDrag = scaledDot * vMag * vMag
                drags.append(math.fabs(componentDrag))
                drag += math.fabs(componentDrag)

                angularChange = math.pi * scaledDot * 0.33 * timeDiff
                rotAxis = norm.cross(vel)
                componentRotation = Quaternion.new_rotate_axis(-angularChange, rotAxis.normalized())
                self._attitude = componentRotation * self._attitude

            drags.append(drag)
            global prettyfloat
            #self.log(str(map(prettyfloat, drags)))
        #print 'getDragForce. vMag: '+str(vMag)+' drag: '+str(drag)
        #print 'getDragForce: '+str(self._attitude)
        return drag

    def _updateVelFromGrav(self, timeDiff):
        #Weight, acts T to ground plane
        dv = self.getWeightForce() * timeDiff / self._mass
        gravityVector = Vector3(0.0, -1.0, 0.0) * dv
        self._velocity += gravityVector

    def _getLiftArgs(self, zenithVector, noseVector):
        velocityNormalized = self._velocity.normalized()
        angleOfAttack = math.acos(limitToMaxValue(velocityNormalized.dot(noseVector), 1.0))
        zenithAngle = math.acos(limitToMaxValue(velocityNormalized.dot(zenithVector), 1.0))     
        if zenithAngle < math.pi/2.0:
            # Ensure AOA can go negative
            # TODO: what happens if plane goes backwards (eg. during stall?)
            angleOfAttack = -angleOfAttack
        return (velocityNormalized, angleOfAttack, zenithAngle)

    def _updateVelFromEnv(self, timeDiff, zenithVector, noseVector):
        velocityNormalized, angleOfAttack, zenithAngle=self._getLiftArgs(zenithVector, noseVector)
        self._updateVelFromGrav(timeDiff)
        #Drag, acts || to Velocity vector
        dv  = self.getDragForce(angleOfAttack, timeDiff) * timeDiff / self._mass
        dragVector = velocityNormalized * dv * -1.0
        self._velocity += dragVector

    def _updateFromEnv(self, timeDiff, zenithVector, noseVector):
        # Calculate rotations
        self.__updatePitch(timeDiff)
        self._updateRoll(timeDiff)
        self.__updateInternalMoment(timeDiff)
        self._updateVelFromEnv(timeDiff, zenithVector, noseVector)
	self._rotateByAngularVel(timeDiff)

        # Finally correct any cumulative errors in attitude
        self._attitude.normalize()

    def _hitGround(self):
        self.__hasHitGround = True      
        # Point the craft along the ground plane
        self._attitude = Quaternion.new_rotate_axis(self.getWindHeading(), Y_UNIT)

    def _reactToCollision(self):
        plane= (c_float * 3)()

        # Determine the Vector representing the plane of the face we collided with
        self._cterrain.getPlaneVectorAtPos(c_float(self._pos.x),c_float(self._pos.z),plane);
        pplane=Vector3(plane[0],plane[1],plane[2])

        # Calculate a ratio to reduce the velocity of the object. This is dependent on the 
        # angle between the plane-normal and the velocity vector of the object.
        ratio = 1.0 - abs(self._velocity.normalized().dot(pplane))
        self.initiateBounce(pplane)
        self._velocity *= ratio

        # Calculate another ratio which depends on the angle between the nosevector and the plane-normal
        (nose,zen) = self._getVectors()
        ratio = abs(nose.dot(pplane))

        # Calculate the angular velocity - a rotation applied to the object which is dependent
        # on the magnitude of the velocity and the ratio calculated above. Ensure the angle remains between
        # 0 and 2PI.
        angle = getEffectiveAngle(self._velocity.magnitude()*ratio/10.0)

        # Calculate the axis of rotation
	axis=pplane.cross(self._velocity).normalize()
	axis = self._attitude.conjugated() * axis
	axis = Quaternion.new_rotate_axis(math.pi/2*0, Y_UNIT) * axis

        # Update the angular velocity
	self._angularVelocity=self._angularVelocity*Quaternion.new_rotate_axis(angle,axis)

    def _die(self):
        print 'ooh the pain'

    def _genDelta(self, timeDiff):
        return self._velocity * timeDiff

    def _updatePos(self, timeDiff):
        self._pos += self._genDelta(timeDiff)
        #if self._collisionDetect(): 
        #    self._reactToCollision()
        #    self._pos = self._pos + Y_UNIT
        #    while self._collisionDetect():
        #        self._pos = self._pos + Y_UNIT

    def update(self):
        timeDiff=self._getTimeDiff()
        (zenithVector, noseVector)=self._getVectors()
        self._updateFromEnv(timeDiff, zenithVector, noseVector)
        self._updatePos(timeDiff)
        mesh.updateCollider(ident, self.getPos(), self.getAttitude())

    def getWindHeading(self):        
        return math.pi * 2 - getAngleForXY(self._velocity.x, self._velocity.z)            

    def initiateBounce(self, planeVector):
        self._velocity=self._velocity.reflect(planeVector.normalize())


class Airfoil(Obj):
    #_FIRING_PERIOD is in seconds
    _FIRING_PERIOD=0.2
    MAX_THRUST=20000.0

    def reset(self):
        self.__init__()
    
    def __init__(self, pos = Vector3(0,0,0), 
                 attitude = Quaternion(w=0.0, x=0.0, y=0.0, z=0.0), 
                 vel = Vector3(0, 0, 0),
                 thrust = 0, 
                 cterrain = None):
        Obj.__init__(self, pos, attitude, vel, cterrain)
        self.__thrust = thrust
        #self._scales = [40.0, 20.0, 2.0]
        self._scales = [0.62, 0.32, 0.03]
        self.__print_line = ""

        # Roll
        self.__aileronRatio = 0.0
        self.__pendingAileronAdjustment = 0.0
        self.__rollAngularVelocity = 0.0 #rad/sec          
        
        # Pitch
        self.__elevatorRatio = 0.0
        self.__pendingElevatorAdjustment = 0.0
        self.__pitchAngularVelocity = 0.0 #rad/sec                
        
        # Constants
        self.__MAX_PITCH_ANGULAR_ACCEL = math.pi /4.0# rad / s / s
        self.__MAX_ROLL_ANGULAR_ACCEL = math.pi /2.0 # rad / s / s
        self.printLiftCoeffTable()
        self.__elevatorTrimRatio = 0.2
        self.__elevatorEqualisationRatio = 0.01
        self.__aileronEqualisationRatio = 0.01

        self._mass = 3850.0 # kg3850
        self._S = 22.48 # wing planform area        
        #self._mass = 0.1 # 100g -- a guess
        #self._S = 0.0016 # meters squared? also a guess

    def __repr__(self):
        return str(self.getId())

    @property
    def thrust(self):
        return self.__thrust

    @thrust.setter
    def thrust(self, value):
        self.__thrust=value

    def getDragForce(self, angleOfAttack, timeDiff):
        vMag = self._velocity.magnitude()

        # Calculate 'induced' drag, caused by the lifting effect of the airfoil
        drag = math.fabs(Airfoil.getDragCoeff(angleOfAttack) * 0.5 * rho * vMag * vMag * self._S)
        return Obj.getDragForce(self, angleOfAttack, timeDiff, drag)

    def getLiftForce(self, angleOfAttack, vel):
        return Airfoil.getLiftCoeff(angleOfAttack) * 0.5 * rho * vel * vel * self._S

    def _updateVelFromLift(self, timeDiff, windUnitVector, angleOfAttack):
        wingUnitVector = self._attitude * Vector3(0.0, 0.0, 1.0)
        liftUnitVector = wingUnitVector.cross(windUnitVector).normalize()            
        dv = self.getLiftForce( angleOfAttack, self._velocity.magnitude() ) * timeDiff / self._mass
        liftVector = liftUnitVector * dv
        self._velocity += liftVector

    def _updateVelFromEnv(self, timeDiff, zenithVector, noseVector):
        velocityNormalized, angleOfAttack, zenithAngle=self._getLiftArgs(zenithVector, noseVector)
        
        self._updateVelFromGrav(timeDiff)
        #Lift, acts T to both Velocity vector AND the wing vector
        self._updateVelFromLift(timeDiff, velocityNormalized, angleOfAttack)

        #Drag, acts || to Velocity vector
        dv  = self.getDragForce(angleOfAttack, timeDiff) * timeDiff / self._mass
        dragVector = velocityNormalized * dv * -1.0
        #print "_updateVelFromEnv. vel: "+str(self._velocity)+' drag: '+str(dragVector)+' time: '+str(timeDiff)+' mass: '+str(self._mass)
        self._velocity += dragVector

    #kw this will return a contant for ballistic flight
    def _getElevRot(self):
        self.__elevatorRatio += self.__pendingElevatorAdjustment #accumulate the new pitch ratio
        # The angular change shall depend on the angle between the Elevator's normal
        # and the velocity vector.
        MAX_ELEV_ANGLE = math.pi / 4.0
        return Quaternion.new_rotate_axis(-self.__elevatorRatio * MAX_ELEV_ANGLE, Vector3(0.0, 0.0, 1.0))

    def _updateRoll(self, timeDiff):
        #kw this part in airfoil only
        self.__aileronRatio += self.__pendingAileronAdjustment #accumulate the new roll ratio        
        #kw this part in both
        if self.__aileronRatio == 0.0:
            # When ailerons are at 0 set the angular velocity to 0 also. This is
            # to get rid of any accumulated error in the angularVelocity.
            self.__rollAngularVelocity = 0.0
        else: 
            angularVelocityDelta = self.__pendingAileronAdjustment * self.__MAX_ROLL_ANGULAR_ACCEL * self._getSpeedRatio()
            self.__rollAngularVelocity += angularVelocityDelta       #accumulate the new angular velocity
        
            # Adjust the crafts roll
            angularChange = self.__rollAngularVelocity * timeDiff
            self._attitude = self._attitude * Quaternion.new_rotate_axis( angularChange, X_UNIT)

    def getElevatorRatio(self):
        return self.__elevatorRatio

    def getAileronRatio(self):
        return self.__aileronRatio

    def setElevatorTrimRatio(self, newValue):
        maxTrimRatio = 1.0
        if newValue > maxTrimRatio:
            self.__elevatorTrimRatio = maxTrimRatio
        elif newValue < -maxTrimRatio:
            self.__elevatorTrimRatio = -maxTrimRatio
        else:
            self.__elevatorTrimRatio = newValue            
        return

    def adjustRoll(self, adj):
        #+/- 1.0
        self.__pendingAileronAdjustment += adj
        if self.__aileronRatio + self.__pendingAileronAdjustment > 1.0:
            self.__pendingAileronAdjustment = 1.0 - self.__aileronRatio 
        if self.__aileronRatio + self.__pendingAileronAdjustment < -1.0:
            self.__pendingAileronAdjustment = -1.0 - self.__aileronRatio   
                      
    def adjustPitch(self, adj):
        #+/- 1.0
        self.__pendingElevatorAdjustment += adj
        if self.__elevatorRatio + self.__pendingElevatorAdjustment > 1.0:
            self.__pendingElevatorAdjustment = 1.0 - self.__elevatorRatio 
        if self.__elevatorRatio + self.__pendingElevatorAdjustment < -1.0:
            self.__pendingElevatorAdjustment = -1.0 - self.__elevatorRatio            

    @staticmethod
    def getLiftCoeff( angleOfAttack):
        # http://en.wikipedia.org/wiki/Lift_coefficient
        aoaDegrees = angleOfAttack / math.pi * 180.0                        
        coeffOfLift = 0.0
        if aoaDegrees < -10: # used to be -5
            coeffOfLift = 0.0
        elif aoaDegrees > 45: # used to be 25
            coeffOfLift = 0.0
        elif aoaDegrees < 17:
            coeffOfLift = (aoaDegrees * 0.1) + 0.5
        else:
            coeffOfLift = (aoaDegrees *-0.1) + 3.5
        return coeffOfLift

    def printLiftCoeffTable(self):
        for i in range(-25,25):
            angle = i/180.0*math.pi
    
    @staticmethod    
    def getDragCoeff(angleOfAttack):        
        AR = 5.61 # http://www.ww2aircraft.net/forum/aviation/bf-109-vs-spitfire-vs-fw-190-vs-p-51-a-13369.html
        e = 0.5   # efficiency factor (0 < x < 1), 1.0 for elipse
        liftCoeff = Airfoil.getLiftCoeff(angleOfAttack)
        inducedDragCoeff = (liftCoeff * liftCoeff) / (math.pi * AR * e)
        Cd0 = 0.0229 # coefficient of drag at zero lift
        return inducedDragCoeff + Cd0

    def changeThrust(self, delta):
        self.__thrust += delta
        if self.__thrust > self.__class__.MAX_THRUST:
            self.__thrust = self.__class__.MAX_THRUST
        if self.__thrust < 0.0:
            self.__thrust = 0.0        

    def getAirSpeed(self):
        return self._velocity.magnitude()

    def draw(self, view_type):
        side = 50.0
        pos = self.getPos()       
        att = self.getAttitude()

        vlist = [Vector3(0,0,0),
                 Vector3(-side/2.0, -side/2.0*0, 0),
                 Vector3(-side/2.0, side/2.0, 0),
                 Vector3(0, 0, 0),
                 Vector3(-side/2.0, 0, -side),
                 Vector3(-side/2.0, 0, side)]

        glDisable(GL_CULL_FACE)
        glTranslatef(pos.x,pos.y, pos.z)
        glBegin(GL_TRIANGLES)   

        glColor4f(1.0, 0.0, 0.0, 1.0)   
        for i in vlist[:3]:
                j = att * i
                glVertex3f(j.x, j.y, j.z)

        glColor4f(0.0, 0.0, 1.0, 1.0)
        for i in vlist[3:6]:
                j = att * i
                glVertex3f(j.x, j.y, j.z)

        glColor4f(1.0, 0.0, 1.0, 1.0)
        glVertex3f(self._velocity.x, self._velocity.y, self._velocity.z)
        j = (att * vlist[1]) /8.0
        glVertex3f(j.x, j.y, j.z)        
        j = (att * vlist[2]) /8.0
        glVertex3f(j.x, j.y, j.z)

        glColor4f(1.0, 1.0, 1.0, 1.0)
        glVertex3f(self._velocity.x, self._velocity.y, self._velocity.z)
        j = (att * vlist[4]) /8.0
        glVertex3f(j.x, j.y, j.z)        
        j = (att * vlist[5]) /8.0
        glVertex3f(j.x, j.y, j.z)        
        glEnd()

        cog = (self._attitude * self._centreOfGravity).normalize()
        rotAxis =  Vector3(0.0,1.0,0.0).cross(cog).normalize() * 100
        glColor4f(1.0, 0.0, 0.0, 1.0)
        glBegin(GL_LINES)
        glVertex3f(rotAxis.x, rotAxis.y, rotAxis.z)
        glVertex3f(-rotAxis.x, -rotAxis.y, -rotAxis.z)
        glVertex3f(0,0,0)
        glVertex3f(0,-100,0)
        glEnd()

    def _updateElevator(self):
        if self.__elevatorRatio >= (self.__elevatorTrimRatio + self.__elevatorEqualisationRatio):
            self.adjustPitch(-self.__elevatorEqualisationRatio)
        elif self.__elevatorRatio <= (self.__elevatorTrimRatio - self.__elevatorEqualisationRatio):
            self.adjustPitch(self.__elevatorEqualisationRatio)
        else:
            self.__elevatorRatio = self.__elevatorTrimRatio

    def _updateAileron(self):
        if self.__aileronRatio >= self.__aileronEqualisationRatio:
            self.adjustRoll(-self.__aileronEqualisationRatio)
        elif self.__aileronRatio <= -self.__aileronEqualisationRatio:
            self.adjustRoll(self.__aileronEqualisationRatio)
        else:
            self.__aileronRatio = 0.0

    def __getVelThrustDelta(self, timeDiff, noseVector):
        #Thrust, acts || to nose vector
        dv = self.thrust * timeDiff / self._mass #dv, the change in velocity due to thrust               
        #print 'thrust noseVector: '+str(noseVector)+' time: '+str(timeDiff)+' delta: '+str(noseVector * dv)+' dv: '+str(dv)
        return noseVector * dv

    def _updateVelFromControls(self, timeDiff, noseVector):
        # Automatically bring elevators back to trim value if no user adjustment was made
        if self.__pendingElevatorAdjustment == 0.0:
            self._updateElevator()

        # Automatically bring ailerons back to 0 if no adjustment was made        
        if self.__pendingAileronAdjustment == 0.0:               
            self._updateAileron()

        self._velocity+=self.__getVelThrustDelta(timeDiff, noseVector)

    def update(self):
        #if self.getId()[0]%2==1:
        #    return
        timeDiff=self._getTimeDiff()
        (zenithVector, noseVector)=self._getVectors()
        self._updateVelFromControls(timeDiff, noseVector)
        self._updateFromEnv(timeDiff, zenithVector, noseVector)
        self.__pendingElevatorAdjustment = 0.0 #reset the pending pitch adjustemnt
        self.__pendingAileronAdjustment = 0.0  #reset the pending roll adjustment
        self._updatePos(timeDiff)
        mesh.updateCollider(self.getId(), self._pos, self._attitude)
        self.printDetails()
        
    def log(self, line):
        self.__print_line += "[" + line + "]"

    def printDetails(self):
        if self.__print_line != "":
            print self.__print_line
            self.__print_line = "" 

    def getHeading(self):
        noseVector = self._attitude * Vector3(1.0,0.0,0.0)
        return math.pi * 2 - getAngleForXY(noseVector.x, noseVector.z)

    def collisionForType(self, ident):
        return mesh.collidedCollider(ident, self.getId())
        
        #if object3dLib.checkCollisionCol(otherModCols, self._modCols,
        #                                 byref(otherCollisionCnt), otherCollisions,
        #                                 byref(self._num_collisions), self._collisions):
        #    import pdb; pdb.set_trace()
        #    return True
        #else:
        #    return False

    def _colCheck(self, b):
        #num_cols=object3dLib.checkCollision(self._modCols, self._collisions)
        #c=checkColForBot(b)
        return b.collisionForType(getId())

    #def _resetResponses(self):
    #    pass

    def checkCols(self, bots, indestructible_types):
        #print 'check start bots: '+str(bots)
        if self.TYP in indestructible_types:
            return
        self._resetResponses()
        for b in bots:
            if b.TYP in indestructible_types:
                self._colCheck(b)
            else:
                myId=self.getId()
                botId=b.getId()
                if myId[0]==botId[0]:
                    #print 'about not to check mine: '+str(myId)+" his "+str(botId)
                    if myId[1]>botId[1]:
                        self._colCheck(b)
                    else:
                        pass
                        #print 'not checking'
                else:
                    #print 'other guy: '+str(myId)+" his "+str(botId)
                    self._colCheck(b)

        #print 'using modCols for '+str(self.getId())
        #print 'checkCollision for terrain '+str(type(self._num_collisions))
        model=mesh.getCollisionModel(self.getId())
        if self._cterrain!=None and model is not None:
            if self._cterrain.checkCollision(model.colliders, byref(model.num_collisions), model.results):
                self._forced_y_delta=+Y_FORCED
                self._reactToCollision()

    def _initCols(self):
	mesh.initCollider(self.TYP, self.getId())
        self._forced_y_delta=0.0
        self._locked=False

    def _resetResponses(self):
        self._forced_y_delta=0.0

    def _collisionRespond(self, bot):
        bPos=bot.getPos()
        if self._pos.y<bPos.y:
            self._forced_y_delta=-Y_FORCED
        else:
            self._forced_y_delta=+Y_FORCED
            
    def _genDelta(self, timeDiff):
        delta=self._velocity * timeDiff
        if self._forced_y_delta!=0.0:
            if self._forced_y_delta<0.0:
                if delta.y>self._forced_y_delta:
                    delta.y=self._forced_y_delta
            else:
                if delta.y<self._forced_y_delta:
                    delta.y=self._forced_y_delta
        return delta

