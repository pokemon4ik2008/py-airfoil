from pyglet import image
from wrapper import *

class Skybox:
	FOG_GREY=0.8

	def __init__(self):
		textureDir = 'data/textures/'
		print imageLoad(textureDir + 'top.bmp')
		self.top = imageLoad(textureDir + 'top.bmp').get_texture()
		self.left = imageLoad(textureDir + 'lt.bmp').get_texture()
		self.right = imageLoad(textureDir + 'rt.bmp').get_texture()
		self.back = imageLoad(textureDir + 'bk.bmp').get_texture()
		self.front = imageLoad(textureDir + 'ft.bmp').get_texture()
		print self.top.tex_coords

        def setTexParams(self):                
                glTexParameteri(self.top.target, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
                glTexParameteri(self.top.target, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
                glTexParameteri(self.top.target, GL_TEXTURE_WRAP_R, GL_CLAMP_TO_EDGE)
                glTexParameteri(self.top.target, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
                glTexParameteri(self.top.target, GL_TEXTURE_MIN_FILTER, GL_LINEAR)

	def draw(self, view):
		glPushMatrix()
		glDisable( GL_DEPTH_TEST)
		glDisable(GL_FOG)
		glDisable( GL_LIGHTING)
		glDisable(GL_CULL_FACE)


		cloudsize=100.0
		offset=0.01
		texOffset = 0.624

		pos = view.getCamera().getCameraVectors()[1]
		glTranslatef( pos.x, 5.0+pos.y, pos.z)
		glColor3f(Skybox.FOG_GREY ,Skybox.FOG_GREY ,Skybox.FOG_GREY)						
		glEnable(self.top.target)        # typically target is GL_TEXTURE_2D		

		#top
		glBindTexture(self.top.target, self.top.id)
		self.setTexParams()
		glBegin(GL_QUADS)
	      	glTexCoord2f( 0.0, texOffset )
		glVertex3f( cloudsize, cloudsize-offset, cloudsize )
	     	glTexCoord2f( texOffset, texOffset )
		glVertex3f(  -cloudsize, cloudsize-offset , cloudsize )
	      	glTexCoord2f( texOffset, 0.0 )
		glVertex3f(  -cloudsize, cloudsize-offset , -cloudsize )
	      	glTexCoord2f( 0.0, 0.0 )
		glVertex3f( cloudsize, cloudsize-offset , -cloudsize )
		glEnd()

		#front
		glBindTexture(self.front.target, self.front.id)
		self.setTexParams()
		glBegin(GL_QUADS)
	      	glTexCoord2f( 0.0, texOffset )
		glVertex3f( cloudsize, cloudsize , cloudsize )
	     	glTexCoord2f( texOffset, texOffset )
		glVertex3f(  -cloudsize, cloudsize , cloudsize )
	      	glTexCoord2f( texOffset, 0.0 )
		glVertex3f(  -cloudsize, -cloudsize , cloudsize )
	      	glTexCoord2f( 0.0, 0.0 )
		glVertex3f( cloudsize, -cloudsize , cloudsize)
		glEnd()

		#right
		glBindTexture(self.right.target, self.right.id)
		self.setTexParams()
		glBegin(GL_QUADS)
	      	glTexCoord2f( 0.0, texOffset )
		glVertex3f( -cloudsize, cloudsize , cloudsize )
	     	glTexCoord2f( texOffset, texOffset )
		glVertex3f(  -cloudsize, cloudsize , -cloudsize )
	      	glTexCoord2f( texOffset, 0.0 )
		glVertex3f(  -cloudsize, -cloudsize , -cloudsize )
	      	glTexCoord2f( 0.0, 0.0 )
		glVertex3f( -cloudsize, -cloudsize ,cloudsize )
		glEnd()

		#left
		glBindTexture(self.left.target, self.left.id)
		self.setTexParams()
		glBegin(GL_QUADS)
	      	glTexCoord2f( 0.0, texOffset )
		glVertex3f( cloudsize, cloudsize , -cloudsize )
	     	glTexCoord2f( texOffset, texOffset )
		glVertex3f(  cloudsize, cloudsize , cloudsize )
	      	glTexCoord2f( texOffset, 0.0 )
		glVertex3f(  cloudsize, -cloudsize ,cloudsize  )
	      	glTexCoord2f( 0.0, 0.0 )
		glVertex3f( cloudsize, -cloudsize ,-cloudsize )
		glEnd()		

		#back
		glBindTexture(self.back.target, self.back.id)
		self.setTexParams()
		glBegin(GL_QUADS)
	      	glTexCoord2f( 0.0, texOffset )
		glVertex3f( -cloudsize, cloudsize , -cloudsize )
	     	glTexCoord2f( texOffset, texOffset )
		glVertex3f(  cloudsize, cloudsize , -cloudsize )
	      	glTexCoord2f( texOffset, 0.0 )
		glVertex3f(  cloudsize, -cloudsize , -cloudsize )
	      	glTexCoord2f( 0.0, 0.0 )
		glVertex3f( -cloudsize, -cloudsize , -cloudsize )
		glEnd()	

		glDisable(self.top.target)
		glEnable( GL_DEPTH_TEST)
		glPopMatrix()
