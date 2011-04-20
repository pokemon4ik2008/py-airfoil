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
import time
from pyglet.gl import *
from pyglet.window import key
from util import *
import pdb
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

class Airfoil:
    def reset(self):
        self.__init__()
    
    def __init__(self, pos = Vector3(0,0,0), 
                 attitude = Vector3(0,0,0), 
                 vel = Vector3(0, 0, 0),
                 thrust = 0):
        self.__pos = pos
        self.__attitude = attitude
        self.__thrust = thrust
        self.__lastClock = time.time()
        self.__velocity = vel
        self.__print_line = ""
        self.__wasOnGround = False

        # Roll
        self.__aileronRatio = 0.0
        self.__pendingAileronAdjustment = 0.0
        self.__rollAngularVelocity = 0.0 #rad/sec          
        
        # Pitch
        self.__elevatorRatio = 0.0
        self.__pendingElevatorAdjustment = 0.0
        self.__pitchAngularVelocity = 0.0 #rad/sec                
        
        # Constants
        self.__S = 22.48 # wing planform area        
        self.__mass = 3850.0 # kg3850
        self.__maxThrust = 20000 # newtons of thrust
        self.__MAX_PITCH_ANGULAR_ACCEL = math.pi /4.0# rad / s / s
        self.__MAX_ROLL_ANGULAR_ACCEL = math.pi /2.0 # rad / s / s
        self.__MAX_ACROBATIC_AIRSPEED_THRESHOLD = 60 # the speed at which our flaps etc. start having maximum effect
        self.printLiftCoeffTable()
        self.__centreOfGravity = Vector3(0.2, 0.0, 0.0)
        self.__elevatorTrimRatio = 0.2
        self.__elevatorEqualisationRatio = 0.01
        self.__aileronEqualisationRatio = 0.01

    def getPos(self):
        return self.__pos

    def __getSpeedRatio(self):
        # Return the current speed as a ratio of the max speed
        # Currently we'll approximate this. Ideally we would calculate the max
        # speed based upon the max thrust and steady state air resistance at that thrust.
        vel = self.__velocity.magnitude()
        if vel > self.__MAX_ACROBATIC_AIRSPEED_THRESHOLD:
            return 1.0
        else:
            return vel/self.__MAX_ACROBATIC_AIRSPEED_THRESHOLD    

    def __updateRoll(self, timeDiff):
        self.__aileronRatio += self.__pendingAileronAdjustment #accumulate the new roll ratio        
        if self.__aileronRatio == 0.0:
            # When ailerons are at 0 set the angular velocity to 0 also. This is
            # to get rid of any accumulated error in the angularVelocity.
            self.__rollAngularVelocity = 0.0
        else: 
            angularVelocityDelta = self.__pendingAileronAdjustment * self.__MAX_ROLL_ANGULAR_ACCEL * self.__getSpeedRatio()
            self.__rollAngularVelocity += angularVelocityDelta       #accumulate the new angular velocity
        
            # Adjust the crafts roll
            angularChange = self.__rollAngularVelocity * timeDiff
            self.__attitude = self.__attitude * Quaternion.new_rotate_euler( 0.0, 0.0, angularChange)
        
        self.__pendingAileronAdjustment = 0.0                     #reset the pending roll adjustment


    def __updatePitch(self, timeDiff):
        self.__elevatorRatio += self.__pendingElevatorAdjustment #accumulate the new pitch ratio

        # The angular change shall depend on the angle between the Elevator's normal
        # and the velocity vector.
        MAX_ELEV_ANGLE = math.pi / 4.0
        elevRot = Quaternion.new_rotate_axis(-self.__elevatorRatio * MAX_ELEV_ANGLE, Vector3(0.0, 0.0, 1.0))
        elevNorm = (self.__attitude * elevRot) * Vector3(0.0, 1.0, 0.0)
        dot = self.__velocity.normalized().dot(elevNorm)
        angularChange = dot * (math.pi/3.0) * self.__getSpeedRatio() * timeDiff

        self.__attitude = self.__attitude * Quaternion.new_rotate_euler( 0.0, angularChange, 0.0)
        self.__pendingElevatorAdjustment = 0.0                     #reset the pending pitch adjustment        
        

    def __updateInternalMoment(self, timeDiff):
        # This will model the rotation about a vector parrallel to the ground plane caused by an
        # internal weight imbalance in the aircraft. Example, the engine at the front of the plane
        # might cause the front of the plane to tilt down. A rotation occurs because the lifting
        # force provided by the wings does not necessarily occur at the centre of gravity.
        if not self.__wasOnGround:
            # Rotate centre of gravity vector according to attitude
            cog = self.__attitude * self.__centreOfGravity
            # Find the axis of rotation
            rotAxis =  Vector3(0.0,1.0,0.0).cross(cog)

            # Project the normalised cog vector onto the ground plane and determine 2d distance from 
            # origin and use as to scale the max amount of rotation. Max rotation therefore occurs when
            # nose is pointing at horizon.
            cogNormalised = cog.normalized()
            rotRatio = math.hypot(cogNormalised.x, cogNormalised.z)
            angularChange = rotRatio * math.pi * 33.0 / 500.0 * timeDiff

            internalRotation = Quaternion.new_rotate_axis(angularChange, rotAxis)
            self.__attitude = internalRotation * self.__attitude 
            return

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

    def getAttitude(self):
        return self.__attitude

    def getVelocity(self):
        return self.__velocity

    def setPos(self, pos):
        self.__pos=pos
        return self

    def setAttitude(self, att):
        self.__attitude=att
        return self

    def setVelocity(self, vel):
        self.__velocity=vel
        return self

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

    def getLiftForce(self, angleOfAttack, vel):
        return Airfoil.getLiftCoeff(angleOfAttack) * 0.5 * rho * vel * vel * self.__S

    def getDragForce(self, angleOfAttack, zenithAngle, timeDiff):        
        vel = self.__velocity
        vMag = vel.magnitude()

        # Calculate 'induced' drag, caused by the lifting effect of the airfoil
        drag = math.fabs(Airfoil.getDragCoeff(angleOfAttack) * 0.5 * rho * vMag * vMag * self.__S)
        drags = []
        drags.append(drag)

        # Calculate attitude rotation due to air resistance
        # There is no rotation if there is no wind...
        if vMag > 0.0:
            # Scale the effect of air resistance on each surface: top, side, front
            scales = [40.0, 20.0, 2.0]
            totalScale = sum(scales)
            normals = [Vector3(0.0, 1.0, 0.0), #plane through wings
                       Vector3(0.0, 0.0, 1.0), #plane through fuselage (vertically)
                       Vector3(1.0, 0.0, 0.0)] #plane perp. to nose vector 

            # Run through each of the planes, and calculate the contributory component
            for scale, norm in zip(scales, normals):
                # Rotate the normal according to attitude
                norm = self.__attitude * norm

                # Use dot product to figure how much effect each plane has
                dot = norm.dot(vel.normalized())

                # Scale the drag based on the relative resistance of the associated surface
                scaledDot =  dot * scale / totalScale
                componentDrag = scaledDot * vMag * vMag
                drags.append(math.fabs(componentDrag))
                drag += math.fabs(componentDrag)

                angularChange = math.pi * scaledDot * 0.33 * timeDiff
                rotAxis = norm.cross(vel)
                componentRotation = Quaternion.new_rotate_axis(-angularChange, rotAxis)
                self.__attitude = componentRotation * self.__attitude

            drags.append(drag)
            global prettyfloat
            #self.log(str(map(prettyfloat, drags)))
        return drag

    def getWeightForce(self):        
        return self.__mass * accelDueToGravity

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
        return self.__velocity.magnitude()

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
        glVertex3f(self.__velocity.x, self.__velocity.y, self.__velocity.z)
        j = (att * vlist[1]) /8.0
        glVertex3f(j.x, j.y, j.z)        
        j = (att * vlist[2]) /8.0
        glVertex3f(j.x, j.y, j.z)
        
        glColor4f(1.0, 1.0, 1.0, 1.0)
        glVertex3f(self.__velocity.x, self.__velocity.y, self.__velocity.z)
        j = (att * vlist[4]) /8.0
        glVertex3f(j.x, j.y, j.z)        
        j = (att * vlist[5]) /8.0
        glVertex3f(j.x, j.y, j.z)        
        glEnd()

        cog = (self.__attitude * self.__centreOfGravity).normalize()
        rotAxis =  Vector3(0.0,1.0,0.0).cross(cog).normalize() * 100
        glColor4f(1.0, 0.0, 0.0, 1.0)
        glBegin(GL_LINES)
        glVertex3f(rotAxis.x, rotAxis.y, rotAxis.z)
        glVertex3f(-rotAxis.x, -rotAxis.y, -rotAxis.z)
        glVertex3f(0,0,0)
        glVertex3f(0,-100,0)
        glEnd()

        return

    def __collisionDetect(self):
        # Check collision with ground
        if self.__pos.y <= 0.0:
            self.__pos.y = 0.0
            self.__velocity.y = 0.0
            if not self.__wasOnGround:
                self.__hitGround()
        else:
            self.__wasOnGround = False


    def update(self):
        # Determine time since last frame
        now = time.time()
        previousClock = self.__lastClock
        self.__lastClock = now
        timeDiff = self.__lastClock - previousClock

        velocity = self.__velocity
        velocityNormalized = velocity.normalized()
        zenithVector = (self.__attitude * Vector3(0.0, 1.0, 0.0)).normalized()
        noseVector = (self.__attitude * Vector3(1.0, 0.0, 0.0)).normalized()
        angleOfAttack = math.acos(limitToMaxValue(velocityNormalized.dot(noseVector), 1.0))
        zenithAngle = math.acos(limitToMaxValue(velocityNormalized.dot(zenithVector), 1.0))     
        if zenithAngle < math.pi/2.0:
            # Ensure AOA can go negative
            # TODO: what happens if plane goes backwards (eg. during stall?)
            angleOfAttack = -angleOfAttack

        # Automatically bring elevators back to trim value if no user adjustment was made
        if self.__pendingElevatorAdjustment == 0.0:
            if self.__elevatorRatio >= (self.__elevatorTrimRatio + self.__elevatorEqualisationRatio):
                self.adjustPitch(-self.__elevatorEqualisationRatio)
            elif self.__elevatorRatio <= (self.__elevatorTrimRatio - self.__elevatorEqualisationRatio):
                self.adjustPitch(self.__elevatorEqualisationRatio)
            else:
                self.__elevatorRatio = self.__elevatorTrimRatio

        # Automatically bring ailerons back to 0 if no adjustment was made        
        if self.__pendingAileronAdjustment == 0.0:               
            if self.__aileronRatio >= self.__aileronEqualisationRatio:
                self.adjustRoll(-self.__aileronEqualisationRatio)
            elif self.__aileronRatio <= -self.__aileronEqualisationRatio:
                self.adjustRoll(self.__aileronEqualisationRatio)
            else:
                self.__aileronRatio = 0.0

        # Calculate rotations
        self.__updatePitch(timeDiff)
        self.__updateRoll(timeDiff)
        self.__updateInternalMoment(timeDiff)

        #Thrust, acts || to nose vector
        dv = self.getThrust() * timeDiff / self.__mass #dv, the change in velocity due to thrust               
        thrustVector = noseVector * dv
        self.__velocity += thrustVector       

        #Weight, acts T to ground plane
        dv = self.getWeightForce() * timeDiff / self.__mass
        gravityVector = Vector3(0.0, -1.0, 0.0) * dv
        self.__velocity += gravityVector        

        #Lift, acts T to both Velocity vector AND the wing vector
        windUnitVector = velocityNormalized
        wingUnitVector = self.__attitude * Vector3(0.0, 0.0, 1.0)
        liftUnitVector = wingUnitVector.cross(windUnitVector).normalize()            
        dv = self.getLiftForce( angleOfAttack, velocity.magnitude() ) * timeDiff / self.__mass
        liftVector = liftUnitVector * dv
        self.__velocity += liftVector
        
        #Drag, acts || to Velocity vector
        dv  = self.getDragForce(angleOfAttack, zenithAngle, timeDiff) * timeDiff / self.__mass
        dragVector = windUnitVector * dv * -1.0

        self.__velocity += dragVector
        self.__pos += (self.__velocity * timeDiff)
        self.__collisionDetect()
        self.printDetails()

    def __hitGround(self):
        print 'Hit ground'
        self.__wasOnGround = True      
        # Point the craft along the ground plane
        self.__attitude = Quaternion.new_rotate_euler(self.getWindHeading(),0,0)   

    def log(self, line):
        self.__print_line += "[" + line + "]"

    def printDetails(self):
        if self.__print_line != "":
            print self.__print_line
            self.__print_line = "" 

    def getWindHeading(self):        
        return math.pi * 2 - self.__getAngleForXY(self.__velocity.x, self.__velocity.z)            

    def getHeading(self):
        noseVector = self.__attitude * Vector3(1.0,0.0,0.0)
        return math.pi * 2 - self.__getAngleForXY(noseVector.x, noseVector.z)

    def __getAngleForXY(self, x, y):
        angle = 0.0
        if x == 0:
            angle = 90.0
        else:
            angle = math.atan(math.fabs(y/x))
        if x <= 0.0 and y >= 0.0:
            angle = math.pi - angle
        elif x <= 0.0 and y < 0.0:
            angle = math.pi + angle
        elif x > 0.0 and y < 0.0:
            angle = math.pi * 2 - angle
        return angle        
