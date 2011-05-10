from pyglet.gl import *
from pyglet import image

class Skybox:
	def __init__(self):
		textureDir = 'data/textures/'
		print image.load(textureDir + 'top.bmp')
		self.top = image.load(textureDir + 'top.bmp').get_texture()
		self.left = image.load(textureDir + 'lt.bmp').get_texture()
		self.right = image.load(textureDir + 'rt.bmp').get_texture()
		self.back = image.load(textureDir + 'bk.bmp').get_texture()
		self.front = image.load(textureDir + 'ft.bmp').get_texture()
		print self.top.tex_coords

	def draw(self, view):
		glPushMatrix()
		glDisable( GL_DEPTH_TEST)
		glDisable(GL_FOG)
		glDisable( GL_LIGHTING)

		cloudsize=100.0
		offset=0.01
		texOffset = 0.625

		pos = view.getCamera().getCameraVectors()[1]
		glTranslatef( pos.x, pos.y, pos.z)
		glColor3f(1.0 ,1.0 ,1.0)						
		glEnable(self.top.target)        # typically target is GL_TEXTURE_2D		

		#top
		glBindTexture(self.top.target, self.top.id)
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
