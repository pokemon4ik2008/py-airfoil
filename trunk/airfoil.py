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
import manage
from proxy import ControlledSer
from pyglet.gl import *
from pyglet.window import key
import time
from util import *
#import pdb

import threading
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

class Obj:
    in_flight=0

    def __init__(self, pos, attitude, vel):
        self._pos = pos
        self._attitude = attitude
        self._lastClock = time.time()
        self._velocity = vel
        self.__elevRot=Quaternion.new_rotate_axis(0, Vector3(0.0, 0.0, 1.0))
        self.__MAX_ACROBATIC_AIRSPEED_THRESHOLD = 60 # the speed at which our flaps etc. start having maximum effect
        self.__wasOnGround = False
        self._centreOfGravity = Vector3(0.2, 0.0, 0.0)
        self._is_real=False
        self._scales = [0.0, 0.0, 0.0]

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

    def __updateInternalMoment(self, timeDiff):
        # This will model the rotation about a vector parrallel to the ground plane caused by an
        # internal weight imbalance in the aircraft. Example, the engine at the front of the plane
        # might cause the front of the plane to tilt down. A rotation occurs because the lifting
        # force provided by the wings does not necessarily occur at the centre of gravity.
        if not self.__wasOnGround:
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

            internalRotation = Quaternion.new_rotate_axis(angularChange, rotAxis)
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

        self._attitude = self._attitude * Quaternion.new_rotate_euler( 0.0, angularChange, 0.0)
        
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
                componentRotation = Quaternion.new_rotate_axis(-angularChange, rotAxis)
                self._attitude = componentRotation * self._attitude

            drags.append(drag)
            global prettyfloat
            #self.log(str(map(prettyfloat, drags)))
        #print 'getDragForce. vMag: '+str(vMag)+' drag: '+str(drag)
        return drag

    def _updateVelFromGrav(self, timeDiff):
        #Weight, acts T to ground plane
        dv = self.getWeightForce() * timeDiff / self._mass
        gravityVector = Vector3(0.0, -1.0, 0.0) * dv
        #print 'grav: '+str(gravityVector)
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

    def __hitGround(self):
        self.__wasOnGround = True      
        # Point the craft along the ground plane
        self._attitude = Quaternion.new_rotate_euler(self.getWindHeading(),0,0)   

    def __collisionDetect(self):
        # Check collision with ground
        if self._pos.y <= 0.0:
            self._pos.y = 0.0
            self._velocity.y = 0.0
            if not self.__wasOnGround:
                self.__hitGround()
        else:
            self.__wasOnGround = False

    def _updatePos(self, timeDiff):
        self._pos += (self._velocity * timeDiff)
        self.__collisionDetect()

    def update(self):
        timeDiff=self._getTimeDiff()
        (zenithVector, noseVector)=self._getVectors()
        self._updateFromEnv(timeDiff, zenithVector, noseVector)
        self._updatePos(timeDiff)
      
    def getWindHeading(self):        
        return math.pi * 2 - getAngleForXY(self._velocity.x, self._velocity.z)            

class Bullet(Obj, ControlledSer):
    TYP=3
    __IN_FLIGHT=set()

    def record(self):
        try:
            assert self.local()
            if self in Bullet.__IN_FLIGHT:
                if not self.alive():
                    Bullet.__IN_FLIGHT.remove(self)
                    if(len(self.__class__.__IN_FLIGHT)%25==0):
                        print 'num bullets (fewer): '+str(len(self.__class__.__IN_FLIGHT))
                return
            else:
                Bullet.__IN_FLIGHT.add(self)
                if(len(self.__class__.__IN_FLIGHT)%25==0):
                    print 'num bullets (more): '+str(len(self.__class__.__IN_FLIGHT))
        except AssertionError:
            print_exc()

    def isClose(self, obj):
        return obj.getId()==self.getId()

    def update(self):
        if self.getId() in self._proxy:
            rs=self._proxy.getObj(self.getId()) #rs = remote_self
            (self._pos, self._attitude, self._velocity)=(rs._pos, rs._attitude, rs._velocity)
        if self.getPos().y<=0:
            self.markDead()
            self.markChanged()
            self.record()

    def estUpdate(self):
        Obj.update(self)

    @classmethod
    def getInFlight(cls):
        return cls.__IN_FLIGHT

    def __init__(self, ident=None, pos = Vector3(0,0,0), attitude = Vector3(0,0,0), vel = Vector3(0,0,0), proxy=None):
        Obj.__init__(self, pos=pos, attitude=attitude, vel=vel)
        self._mass = 0.1 # 100g -- a guess
        self._scales = [0.062, 0.032, 0.003]
        ControlledSer.__init__(self, Bullet.TYP, ident, proxy=proxy)

    def localInit(self):
        ControlledSer.localInit(self)
        self.record()

    def draw(self):
        try:
            assert self.alive()

            side = 10.0
            att=self.getAttitude()
            pos = self.getPos()

            vlist = [Vector3(0,0,0),
                     Vector3(-side/2.0, -side/2.0*0, 0),
                     Vector3(-side/2.0, side/2.0, 0),
                     Vector3(0, 0, 0),
                     Vector3(-side/2.0, 0, -side),
                     Vector3(-side/4.0, 0, side)]

            glDisable(GL_CULL_FACE)
            glTranslatef(pos.x, pos.y, pos.z)
            glBegin(GL_TRIANGLES)
            glColor4f(0.0,0.0,0.0,1.0)

            for i in vlist[3:6]:
                    j = att * i
                    glVertex3f(j.x, j.y, j.z)
            glEnd()
        except AssertionError:
            print_exc()

class Airfoil(Obj):
    #_FIRING_PERIOD is in seconds
    _FIRING_PERIOD=0.2

    def reset(self):
        self.__init__()
    
    def __init__(self, pos = Vector3(0,0,0), 
                 attitude = Vector3(0,0,0), 
                 vel = Vector3(0, 0, 0),
                 thrust = 0):
        Obj.__init__(self, pos, attitude, vel)
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
        self.__maxThrust = 20000 # newtons of thrust
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
            self._attitude = self._attitude * Quaternion.new_rotate_euler( 0.0, 0.0, angularChange)

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

    def setThrust(self, thrust):
        self.__thrust=thrust
        return self

    def changeThrust(self, delta):
        self.__thrust += delta
        if self.__thrust > self.__maxThrust:
            self.__thrust = self.__maxThrust
        if self.__thrust < 0.0:
            self.__thrust = 0.0        

    def getThrust(self):
        return self.__thrust
        
    def getAirSpeed(self):
        return self._velocity.magnitude()

    def draw(self):
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

        return

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
        dv = self.getThrust() * timeDiff / self._mass #dv, the change in velocity due to thrust               
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
        timeDiff=self._getTimeDiff()
        (zenithVector, noseVector)=self._getVectors()
        self._updateVelFromControls(timeDiff, noseVector)
        self._updateFromEnv(timeDiff, zenithVector, noseVector)
        self.__pendingElevatorAdjustment = 0.0                     #reset the pending pitch adjustemnt
        self.__pendingAileronAdjustment = 0.0                     #reset the pending roll adjustment
        self._updatePos(timeDiff)
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
