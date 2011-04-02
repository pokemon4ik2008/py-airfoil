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
from pyglet.gl import *
from util import *
import array
import itertools
import random
import pyglet
from ctypes import pointer, sizeof

class MeshVertex:
    def __init__(self):
	self.plotted = False	#dynamic: has this quad been already plotted
        self.dist = 0.0      #dynamic: dist of vertex from current pov
	self.y = 0.0         #y value as loaded from map definition file
        self.intensity = 0.0      #light intensity at current vertex. calculated on map load
	self.col = Vector3(0,0,0) #colour of vertex, calculated on map load, depends on intensity and y
        self.alt_y = 0.0     #alternative y value used during variable detail level calculations to get rid of gaps in map        
        self.norm = Vector3(0,0,0)
        return
    

class MeshVertexArray:
    def __init__(self, x, z):
        self.x = x
        self.z = z
        print 'Init terrain mesh (x,z) = ', x,z
        self.data = []
        for i in range(self.x):
            for j in range(self.z):
                self.data.append(MeshVertex())
        return
    def get(self, x, z):
        return self.data[x*self.x + z]   

    def getVertex(self, x, z):
        return Point3(x, self.get(x,z).y, z)

class Terrain(object):
    def __init__(self, heightMap, size, scale, yScale, colourMap):
        self.mesh = MeshVertexArray(size,size)
        self.size = size
        self.scale = scale
        self.yScale = yScale
        self.colourMap = colourMap   
        self.wireframe = False
        self.useVbo = False

        # Copy over the altitude values
        for x in range(size):
            for z in range(size):
                self.mesh.get(x,z).y = heightMap[x][z]

        # Calculate the normals for each vertex    
        vertexList = []
        vertexColList = []
        for x in range(size):
            for z in range(size):
                if x == 0 or x == size-1 or z == 0 or z == size-1 :
                    self.mesh.get(x,z).norm = Vector3(0,1,0)
                else:
                    # Find the vector between the vertex and each of its 4 neighbours
                    v = range(4)
                    v[0] = self.mesh.getVertex(x+1,z) - self.mesh.getVertex(x,z)
                    v[1] = self.mesh.getVertex(x-1,z) - self.mesh.getVertex(x,z)
                    v[2] = self.mesh.getVertex(x,z+1) - self.mesh.getVertex(x,z)
                    v[3] = self.mesh.getVertex(x,z-1) - self.mesh.getVertex(x,z)

                    # Get the two cross products (normals), combine, and normalise
                    self.mesh.get(x,z).norm = (v[0].cross(v[1]) + v[2].cross(v[3])).normalized()                                           

                # Calculate the light intensity at this point
                self.mesh.get(x,z).intensity = self.__calcIntensity(self.mesh.get(x,z).norm)           

                # Determine the colour of this vertex
                self.mesh.get(x,z).col = self.__getColourAtHeight(self.mesh.get(x,z).y)

                if self.useVbo:
                    # Build our list of vertices and colours, these shall be uploaded to the GPU
                    vertexList.extend([x * self.scale, self.mesh.get(x,z).y * self.yScale, z * self.scale])
                    vertexList.extend(self.__getColourAtHeight(self.mesh.get(x,z).y))


        # Calc the default intensity for the area surrounding the map
        self.defaultIntensity = self.__calcIntensity(Vector3(0,1,0))

        # Setup some constants
        # TODO: derive this from somewhere
        #self.__maxAltitude = 1000.0
        #self.__maxCutOffDist = 1000.0
        #self.__altitudeVariationConst = self.__maxCutOffDist / self.__maxAltitude

        if self.useVbo:
            # Populate the list of vertices:
            # Convert vertex list to c array
            data = (GLfloat*len(vertexList))(*vertexList)

            # Setup the vertex buffer object
            self.vboIdVertices = GLuint()
            if self.useVbo:
                glGenBuffers(1, pointer(self.vboIdVertices))
                # Select which VBO to use
                glBindBuffer(GL_ARRAY_BUFFER, self.vboIdVertices)
                # Load the data into the VBO
                glBufferData(GL_ARRAY_BUFFER, sizeof(data), data, GL_STATIC_DRAW)
            else:
                self.__vertexList = data

            IndexArrayType = GLuint * 25000
            self.cIndices = IndexArrayType()

        return

    def __getColourAtHeight(self, height):
        index = math.trunc(height)
        if index >= len(self.colourMap[0]):
            print "ERROR: colour map value out of range", height
            index = len(self.colourMap[0]) - 1
        return [thisCol[index] for thisCol in self.colourMap]

    def __calcIntensity(self, normal):
        # Constants
        lightSource = Point3(-500,5000,-500)
        ambientLight = 0.2

        calcInt = math.fabs(normal.dot(lightSource))
        if calcInt > 0.3:
            # Clip it so that things don't get too shiny
            calcInt = 0.3
        totalInt = ambientLight + calcInt

        # Ensure total intensity isn't more than 1
        if totalInt > 1.0:
            totalInt = 1.0 
        return totalInt

    def draw(self, view):
        glPushMatrix()
        glEnable(GL_DEPTH_TEST)
        glColor3f(1,1,1)
        if not self.useVbo:
            glBegin(GL_QUADS)

        cameraVectors = view.getCamera().getCameraVectors()
        cameraCenter = cameraVectors[0]
        cameraPosition = cameraVectors[1]

        # Calculate the perspective angle
        perspAngle = math.atan(view.getAspectRatio() / 1.0)

        # Calculate the view angle
        viewVector = cameraCenter - cameraPosition  
        flatViewVector = Vector3(viewVector.x, 0.0, viewVector.z).normalized()
        viewVector = viewVector.normalized()
        viewAngle = getAngleForXY(viewVector.z, viewVector.x) 
        
        detailLevels = 4

        # pull back the base coord a bit behind the point of view
        towardGroundRatio = math.fabs(Vector3(0.0, 1.0, 0.0).dot(viewVector))
        #cameraPosition -= flatViewVector * (11 + towardGroundRatio * cameraPosition.y * 1.4)

        # Determine the cut off distance, it shall vary with camera height
        # TODO : hardcode this for the moment.
        cutOffDist = 10.0 # measured in quads
        self.drawnQuads = 0

        # Start picking out the 3 corners of the view triangle
        mapPosition = cameraPosition / self.scale
        point = [Point3(), Point3(), mapPosition]        
        point[0].x = mapPosition.x + (cutOffDist * math.sin(viewAngle - perspAngle))
        point[0].y = 0.0
        point[0].z = mapPosition.z + (cutOffDist * math.cos(viewAngle - perspAngle))
        point[1].x = mapPosition.x + (cutOffDist * math.sin(viewAngle + perspAngle))
        point[1].y = 0.0
        point[1].z = mapPosition.z + (cutOffDist * math.cos(viewAngle + perspAngle))        
        
        #print cameraPosition

        # Sort the 3 points of the view triangle by decending Z 
        #print point, cutOffDist, math.degrees(viewAngle), math.degrees(perspAngle)
        point.sort(sortVectorsByZ)
        #print point, cutOffDist, math.degrees(viewAngle), math.degrees(perspAngle)

        # TODO: handle detail levels
        #minDetailLevel = detailLevels / 2
        
        # Clear the list of index we must draw
        self.cIndexes = 0

        # Calculate the slopes for the view triangle
        leftm = 0
        if point[1].z - point[0].z != 0:
            leftm = (point[1].x - point[0].x) / (point[1].z - point[0].z)
        rightm = 0
        if point[2].z - point[0].z != 0:
            rightm = (point[2].x - point[0].x) / (point[2].z - point[0].z)

        # Calculate the starting X coord:
        leftx = rightx = point[0].x
        if point[1].z - point[0].z != 0:
            # Draw the first part of the view triangle if it exists:
            rightx = self.__drawPartOfViewTriangle(point[0].z, point[1].z, leftx, rightx, leftm, rightm)
        else:
            rightx = point[0].x
        leftx = point[1].x        
        if point[2].z - point[1].z != 0:
            leftm = (point[2].x - point[1].x) / (point[2].z - point[1].z)
        self.__drawPartOfViewTriangle(point[1].z, point[2].z, leftx, rightx, leftm, rightm)

        
        if self.useVbo:
            # Draw our VBO:
            # Select which vbo to use
            glBindBuffer(GL_ARRAY_BUFFER, self.vboIdVertices)

            # Specify the format of the data in the vbo
            glEnableClientState(GL_VERTEX_ARRAY)
            glVertexPointer(3, GL_FLOAT, 24, 0)
            glEnableClientState(GL_COLOR_ARRAY)
            glColorPointer(3, GL_FLOAT, 24, 12)

            # Draw specific indices from the vbo
            if self.wireframe:
                glDrawElements( GL_LINES, len(cIndices), GL_UNSIGNED_INT, self.cIndices) 
            else:
                glDrawElements( GL_QUADS, self.cIndexes, GL_UNSIGNED_INT, self.cIndices) 
            
            glDisableClientState(GL_VERTEX_ARRAY)
            #glDisableClientState(GL_COLOR_ARRAY)
        else:
            glEnd()
        glPopMatrix()  
        return self.drawnQuads

    def __drawPartOfViewTriangle(self, topz, botz, leftx, rightx, leftm, rightm):
        #print 'draw part ', topz, botz, leftx, rightx, leftm, rightm

        # Perform scan conversion
        z = topz
        drawn = 0
        while (z >= botz):
            if leftx < rightx:
                inc = 1
            else:
                inc = -1

            i = math.trunc(leftx * inc)
            while (i < math.trunc(rightx * inc)):
                x = i * inc
                if self.__drawQuad(x,math.trunc(z)):
                    drawn += 1
                i += 1

            leftx -= leftm
            rightx -= rightm
            z -= 1.0
        return rightx

    def __drawVertex(self, x, z):
        if x < 0 or x >= self.mesh.x or z < 0 or z >= self.mesh.z:
            return  

        if self.useVbo:
            index = self.cIndexes
            (self.cIndices)[index+0] = (GLuint) (self.getIndexForXZ(x,z))
            (self.cIndices)[index+1] = (GLuint) (self.getIndexForXZ(x,z+1))
            (self.cIndices)[index+2] = (GLuint) (self.getIndexForXZ(x+1,z+1))
            (self.cIndices)[index+3] = (GLuint) (self.getIndexForXZ(x+1,z))
            self.cIndexes += 4
        else:
            mesh = self.mesh.get(x,z)
            col = mesh.col
            glColor4f(col[0], col[1], col[2], 1.0)
            glVertex3f(x * self.scale, mesh.y * self.yScale, z * self.scale)

    def __drawQuad(self, x, z):
        if x < 0 or x >= self.mesh.x-1 or z < 0 or z >= self.mesh.z-1:
            return False 

        self.__drawVertex(x,z)
        self.__drawVertex(x,z+1)
        self.__drawVertex(x+1,z+1)
        self.__drawVertex(x+1,z)
        
        return True

    def getIndexForXZ(self,x,z):
        return x * self.size + z

def sortVectorsByZ(itemA, itemB):
    if itemA.z > itemB.z:
        return -1
    elif itemA.z < itemB.z:
        return 1
    else:
        return 0

class RandomTerrain(Terrain):
    def __init__(self, iterations, scale, yScale):
        seed = 239.0
        deviation = 10.0
        start = 0.0
        edge_smooth=1000.0
        smooth = 3.5
        smooth_step = (smooth - 1.0) / iterations

        width = size = 2**iterations + 1                
        vertcount = width**2
        vert = [array.array('f', itertools.repeat(0.0, width)) for i in range(width)]               
        random.seed(seed)
        vert[0][0] = random.gauss(start, deviation)
        vert[0][-1] = random.gauss(start, deviation)
        vert[-1][0] = random.gauss(start, deviation)
        vert[-1][-1] = random.gauss(start, deviation)
        span = width
        right = width - 1
       
        for i in range(iterations):
                span /= 2
                span2 = span * 2
                r = range(2**i)
                # Diamond pass
                for x in r:
                        for y in r:
                                cx = x * span2 # corner x
                                cy = y * span2 # corner y
                                mean = (
                                        vert[cx][cy] +
                                        vert[cx + span2][cy] +
                                        vert[cx + span2][cy + span2] +
                                        vert[cx][cy + span2]) / 4.0
                                vert[cx + span][cy + span] = random.gauss(mean, deviation)
                # Square pass
                r = range(2**i + 1)
                for x in r:
                        for y in r:
                                if x == 0 or x == right or y == 0 or y == right:
                                        dev = deviation / edge_smooth
                                else:
                                        dev = deviation
                                left_adjust = (x==0)
                                top_adjust = (y==0)
                                cx = x * span2 # corner x
                                cy = y * span2 # corner y
                                # vert above corner
                                mean = (
                                        vert[cx][cy] +
                                        vert[cx][cy - span2 - top_adjust] +
                                        vert[(cx + span) % right][cy - span - top_adjust] +
                                        vert[cx - span - left_adjust][cy - span - top_adjust]) / 4.0
                                vert[cx][cy - span - top_adjust] = random.gauss(mean, dev)
                                # vert to left of corner
                                mean = (
                                        vert[cx][cy] +
                                        vert[cx - span2 - left_adjust][cy] +
                                        vert[cx - span - left_adjust][(cy + span) % right] +
                                        vert[cx - span - left_adjust][cy - span - top_adjust]) / 4.0
                                vert[cx - span - left_adjust][cy] = random.gauss(mean, dev)
                deviation /= 1.0 + smooth_step * i

        # Find the highest altitude
        max = 0.0
        for x in range(size):
            for z in range(size):
                if vert[x][z] > max:
                    max = vert[x][z]

        # Scale the whole array to the desired altitude range
        for x in range(size):
            for z in range(size):
                vert[x][z] = vert[x][z] / max * 255.0

        # Build a linear colour map
        colourMap = []
        for i in range(3):
            thisCol = []
            for j in range(256):
                thisCol.extend([1.0 / 255.0 * j])            
            colourMap.extend([thisCol])

        super(RandomTerrain, self).__init__(vert, size, scale, yScale, colourMap)
        
