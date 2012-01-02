#include <assert.h>
#include <GL/glew.h>
#include <string.h>
#include "objects.h"

bool obj_use_gl_lighting=true;
float obj_cut_off_dist = 100;
float obj_cut_off_angle = 20;
float obj_ambient_light=0.5f;
obj_plot_position pos={0};
obj_plot_position origin_offset={0};
obj_plot_position pov={0};
obj_light_source objlight={0,0,0,1.0f};

obj_3dMesh *p_meshes[128];
uint32 num_meshes=0;

float rotAngle = 0;
float *rotAxis = NULL;

inline void memZero(void *p_mem, uint32 bytes) {
    for(uint32 *p_ptr=(uint32 *)p_mem, *p_end=(uint32 *)(((uint8 *)p_mem)+bytes); p_ptr<p_end; p_ptr++) {
    *p_ptr=0;
  }
}

extern "C" 
{
  DLL_EXPORT void *load(char *filename, float scale)
	{
		oError err = ok;		
		unsigned int objectflags=0;
		obj_3dMesh *obj = NULL;
		objectflags|=OBJ_NORMAL_POSITIVE;
		err = objCreate(&obj, filename, scale, objectflags);
		
		if (err != ok)
		{
			printf("ERROR: when loading object: %i\n", err);
		}
		return obj;
	}
  
	DLL_EXPORT void getMid(void *p_meshToPlot, float mid[])
	{
	  obj_3dMesh *p_mesh=static_cast<obj_3dMesh *>(p_meshToPlot);
	  mid[0]=static_cast<obj_3dMesh *>(p_mesh)->mid.x;
	  mid[1]=static_cast<obj_3dMesh *>(p_mesh)->mid.y;
	  mid[2]=static_cast<obj_3dMesh *>(p_mesh)->mid.z;
	}

  DLL_EXPORT uint8* getMeshPath(void *p_meshToPlot)
  {
    obj_3dMesh *p_mesh=static_cast<obj_3dMesh *>(p_meshToPlot);
    return p_mesh->mesh_path;
  }

  DLL_EXPORT uint8* getUvPath(void *p_meshToPlot, uint32 uv_id)
  {
    obj_3dMesh *p_mesh=static_cast<obj_3dMesh *>(p_meshToPlot);
    if(uv_id<p_mesh->num_uv_maps) {
      //printf("getUvPath found uv path uv_id 0x%x num 0x%x\n", uv_id, p_mesh->num_uv_maps);
      return p_mesh->pp_tex_paths[uv_id];
    }
    //printf("getUvPath uv_id larger than num maps uv_id 0x%x num 0x%x\n", uv_id, p_mesh->num_uv_maps);
    return NULL;
  }

  DLL_EXPORT uint32 setupTex(void *p_meshToPlot, uint32 uv_id, uint32 tex_id)
  {
    obj_3dMesh *p_mesh=static_cast<obj_3dMesh *>(p_meshToPlot);
    if(uv_id<p_mesh->num_uv_maps) {
      p_mesh->p_tex_ids[uv_id]=tex_id;
      //printf("setTexId 0x%x (0x%x) to 0x%x\n", uv_id, &p_mesh->p_tex_ids[uv_id], tex_id);
      return 0;
    }
    printf("setTexId failed 0x%x 0x%x\n", uv_id, p_mesh->num_uv_maps);
    return -1;
  }

  DLL_EXPORT uint32 createTexture(void *p_meshToPlot, uint32 uv_id, void *p_data, uint32 width, uint32 height, uint32 format)
  {
    GLuint texture;
    assert(format==GL_RGB || format==GL_RGBA);
    glGenTextures(1,&texture);            // Allocate space for texture
    glBindTexture(GL_TEXTURE_2D, texture); // Set our Tex handle as current
    glTexImage2D(GL_TEXTURE_2D, 0, format==GL_RGB ? 3 : 4, width, height, 0, format, GL_UNSIGNED_BYTE, p_data);
    printf("createTexture %u\n", uv_id, texture);
    return setupTex(p_meshToPlot, uv_id, texture);
  }

  DLL_EXPORT uint32 createFBO(uint32 texId, uint32 width, uint32 height) {
    printf("createFBO %i %i\n", width, height);
    uint32 rboId;
    uint32 fboId=0xffffffff;
    if(glewInit()==GLEW_OK && GLEW_ARB_framebuffer_object) {
      // create a renderbuffer object to store depth info
      glGenRenderbuffersEXT(1, &rboId);
      glBindRenderbufferEXT(GL_RENDERBUFFER_EXT, rboId);
      glRenderbufferStorageEXT(GL_RENDERBUFFER_EXT, GL_DEPTH_COMPONENT,
			       width, height);
      glBindRenderbufferEXT(GL_RENDERBUFFER_EXT, 0);

      // create a framebuffer object
      glGenFramebuffersEXT(1, &fboId);
      glBindFramebufferEXT(GL_FRAMEBUFFER_EXT, fboId);

      // attach the texture to FBO color attachment point
      glFramebufferTexture2DEXT(GL_FRAMEBUFFER_EXT, GL_COLOR_ATTACHMENT0_EXT,
				GL_TEXTURE_2D, texId, 0);

      // attach the renderbuffer to depth attachment point
      glFramebufferRenderbufferEXT(GL_FRAMEBUFFER_EXT, GL_DEPTH_ATTACHMENT_EXT,
				   GL_RENDERBUFFER_EXT, rboId);

      // check FBO status
      GLenum status = glCheckFramebufferStatusEXT(GL_FRAMEBUFFER_EXT);
      if(status != GL_FRAMEBUFFER_COMPLETE_EXT) {
	printf("objPlotToTex failed at framebuffer check\n");
	glBindFramebufferEXT(GL_FRAMEBUFFER_EXT, 0);
	return 0xffffffff;
      }
    } else {
      printf("objPlotToTex failed at vbo check\n");
      return fboId;
    }
    glClearColor(1.0, 1.0, 1.0, 0.0);
    glClearDepth(1.0);
    glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT);
    glBindFramebufferEXT(GL_FRAMEBUFFER_EXT, 0);

    uint32 dim_order_x[4]={MIN_Y, MAX_Z, MAX_Y, MIN_Z};
    uint32 dim_order_y[4]={MAX_Z, MAX_X, MIN_Z, MIN_X};
    uint32 dim_order_z[4]={MAX_Y, MAX_X, MIN_Y, MIN_X};

    for(uint32 i=0; i<DIM(dim_order_x); i++) {
      top_order_x[dim_order_x[i]]=i;
      top_order_y[dim_order_y[i]]=i;
      top_order_z[dim_order_z[i]]=i;
    }

    return fboId;
  }

	DLL_EXPORT void setAngleAxisRotation(float angle, float axis[]) 
	{
		rotAngle = angle;
		rotAxis = axis;
	}

	DLL_EXPORT void setPosition(float plotPos[])
	{
		objSetPlotPos(plotPos[0], plotPos[1], plotPos[2]);
	}
	
	DLL_EXPORT void setLightPosition(float lightPos[])
	{
		objlight.x = lightPos[0];
		objlight.y = lightPos[1];
		objlight.z = lightPos[2];
	}

  DLL_EXPORT void drawToTex(void *meshToPlot, float32 alpha, uint32 fbo, uint32 width, uint32 height, uint32 bgTex, uint32 boundPlane, uint32 top)
	{
		oError err = ok;
		err = objPlotToTex(static_cast<obj_3dMesh *>(meshToPlot), alpha, fbo, width, height, bgTex, boundPlane, top);
		if (err != ok)
		{
			printf("ERROR: when drawing object\n");
		}
	}

  DLL_EXPORT void draw(void *meshToPlot, float32 alpha)
	{
		oError err = ok;
		glTranslatef(pos.x ,pos.y ,pos.z );
		glLightfv(GL_LIGHT0, GL_POSITION, (float *)&objlight);
		if (rotAxis) {
		  glRotatef(rotAngle, rotAxis[0], rotAxis[1], rotAxis[2]);		// Rotate On The X Axis
		}
  
		err = objPlot(static_cast<obj_3dMesh *>(meshToPlot), alpha);
		if (err != ok)
		{
			printf("ERROR: when drawing object\n");
		}
	}

	DLL_EXPORT void deleteMesh(void *meshToDelete)
	{	
		obj_3dMesh *p_mesh = static_cast<obj_3dMesh *>(meshToDelete);
		if(p_mesh->ibo != NO_IBO) {
		  glDeleteBuffersARB(1, &(p_mesh->ibo));
		}
		if(p_mesh->vbo != NO_VBO) {
		  glBindBufferARB(GL_ARRAY_BUFFER_ARB, p_mesh->vbo);
		  glUnmapBufferARB(GL_ARRAY_BUFFER_ARB); 
		  glDeleteBuffersARB(1, &(p_mesh->vbo));
		}
		objDelete(&p_mesh);			
	}

  /*
  DLL_EXPORT setupRotation(x, y, z, wr, xr, yr, zr, xmid, ymid, zmid, xorig, yorig, zorig)
  {
    Vector3f pos(x, y, z), midPt(xmid, ymid, zmid), rotOrig(xorig, yorig, zorig);
    pos << x << y << z;
    Quaternion<float> angle_quat(xr, yr, zr, wr);
    angle_quat.normalize();
    AngleAxis<float> angleAxis(angle_quat);
    Vector3f rotNew=angle_quat * midPt;
  }
  */
}

void	objSetCutOff		(float dist, float angle) {
	obj_cut_off_dist=dist;
	obj_cut_off_angle=angle;
}



void objSetPlotPos(float x, float y, float z) {
	pos.x=x;
	pos.y=y;
	pos.z=z;
}

void objRotZ(obj_vector *unit_vector_norm,float az) {
	obj_vector unit_vector_norm2;
	unit_vector_norm2.x=(float)	(unit_vector_norm->x * ( cos(az) ) +
								unit_vector_norm->y *  ( sin(az) ) +
								unit_vector_norm->z *  ( 0 ));
	unit_vector_norm2.y=(float)	(unit_vector_norm->x * (-sin(az) ) +
								unit_vector_norm->y * ( cos(az) ) +
								unit_vector_norm->z * ( 0 ));
	unit_vector_norm2.z=(float)	(unit_vector_norm->x * ( 0 ) +
								unit_vector_norm->y * ( 0 ) +
								unit_vector_norm->z * ( 1 ));
	*unit_vector_norm=unit_vector_norm2;
}

void objRotY(obj_vector *unit_vector_norm,float ay) {
	obj_vector unit_vector_norm2;
	unit_vector_norm2.x=(float)	(unit_vector_norm->x * ( cos(ay) ) +
								unit_vector_norm->y *  ( 0 ) +
								unit_vector_norm->z *  (-sin(ay) ));
	unit_vector_norm2.y=(float)	(unit_vector_norm->x * ( 0 ) +
								unit_vector_norm->y * ( 1 ) +
								unit_vector_norm->z * ( 0 ));
	unit_vector_norm2.z=(float)	(unit_vector_norm->x * ( sin(ay) ) +
								unit_vector_norm->y * ( 0 ) +
								unit_vector_norm->z * ( cos(ay) ));
	*unit_vector_norm=unit_vector_norm2;
}

void objRotX(obj_vector *unit_vector_norm,float ax) {
	obj_vector unit_vector_norm2;
	unit_vector_norm2.x=(float)	(unit_vector_norm->x * ( 1 ) +
								unit_vector_norm->y *  ( 0 ) +
								unit_vector_norm->z *  ( 0 ));
	unit_vector_norm2.y=(float)	(unit_vector_norm->x * ( 0 ) +
								unit_vector_norm->y * ( cos(ax) ) +
								unit_vector_norm->z * ( sin(ax) ));
	unit_vector_norm2.z=(float)	(unit_vector_norm->x * ( 0 ) +
								unit_vector_norm->y * (-sin(ax) ) +
								unit_vector_norm->z * ( cos(ax) ));
	*unit_vector_norm=unit_vector_norm2;
}

void objSetVertexNormal(obj_vector unit_vector_norm,unsigned int flags) {
	float ax=-deg_to_rad*pos.ax;
	float ay=-deg_to_rad*pos.ay;
	float az=-deg_to_rad*pos.az;

	//Must rotate normal now same as objs rotation
	objRotZ(&unit_vector_norm,az);
	objRotY(&unit_vector_norm,ay);
	objRotX(&unit_vector_norm,ax);
	
	if (flags&OBJ_NORMAL_ABSOLUTE) {
		unit_vector_norm.x=absValue(unit_vector_norm.x);
		unit_vector_norm.y=absValue(unit_vector_norm.y);
		unit_vector_norm.z=absValue(unit_vector_norm.z);	
	}

	glNormal3f( -unit_vector_norm.x, -unit_vector_norm.y, -unit_vector_norm.z);
}

uint8 match_mesh[]="data/models/cockpit/E_Prop.csv";

void checkRange(obj_3dMesh *p_mesh, void *p_addr, bool within) {
  if(within) {
    if(p_addr<p_mesh->p_vert_start) {
      printf("checkRange too low 0x%x start 0x%x end 0x%x\n", p_addr, p_mesh->p_vert_start, p_mesh->p_vert_end);
      assert(false);
    }
    if(p_addr>=p_mesh->p_vert_end) {
      printf("checkRange too low 0x%x start 0x%x end 0x%x\n", p_addr, p_mesh->p_vert_start, p_mesh->p_vert_end);
      assert(false);
    }
  } else {
    if(p_addr>=p_mesh->p_vert_start && p_addr<p_mesh->p_vert_end) {
      printf("within range 0x%x start 0x%x end 0x%x\n", p_addr, p_mesh->p_vert_start, p_mesh->p_vert_end);
      assert(false);
    }
  }
}
void checkRange(obj_3dMesh *p_mesh, void *p_addr) {
  checkRange(p_mesh, p_addr, true);
}
void checkAllRanges(void *p_addr) {
  for(uint32 i=0; i<num_meshes; i++) {
    checkRange(p_meshes[i], p_addr, false);
  }
}

GLuint rboId=0xffffffff;
GLuint fboId=0xffffffff;
uint32 fboUsed=false;
oError objPlotToTex(obj_3dMesh *p_mesh, float32 alpha, uint32 fbo, uint32 xSize, uint32 ySize, uint32 bgTex, uint32 boundPlane, uint32 top) {
  obj_vertex eye, lookAt, zen;
  obj_vertex *p_bound, *p_opp, *p_top;
  /*
  obj_vertex *p_bg[4];
  uint32 min_faces[3][4]={{0,3,4,7},{0,1,2,3},{2,3,6,7}};
  uint32 max_faces[3][4]={{1,2,5,6},{4,5,6,7},{0,1,4,5}};
  uint32 *p_order;
  uint32 *p_bg_verts;
  obj_vertex box[8];
  for(uint32 i=0; i<DIM(box); i++) {
    switch(i) {
    case 0:
    case 3:
    case 4:
    case 7:
      box[i].x=p_mesh->min.x;
      break;
    default:
      box[i].x=p_mesh->max.x;
    }
    switch(i) {
    case 2:
    case 3:
    case 6:
    case 7:
      box[i].y=p_mesh->min.y;
      break;
    default:
      box[i].y=p_mesh->max.y;
    }
    switch(i) {
    case 0:
    case 1:
    case 2:
    case 3:
      box[i].z=p_mesh->min.z;
      break;
    default:
      box[i].z=p_mesh->max.z;
    }
  }
  */

  if(boundPlane & MIN_FLAG) {
    p_bound=&p_mesh->min;
    p_opp=&p_mesh->max;
  } else {
    p_bound=&p_mesh->max;
    p_opp=&p_mesh->min;
  }
  if(top & MIN_FLAG) {
    p_top=&p_mesh->min;
  } else {
    p_top=&p_mesh->max;
  }
  const uint32 x_dim=1;
  const uint32 y_dim=2;
  const uint32 z_dim=4;
  //uint32 otherDim=x_dim|y_dim|z_dim;

  float32 width=p_mesh->max.x-p_mesh->min.x;
  float32 depth=p_mesh->max.z-p_mesh->min.z;
  float32 height=p_mesh->max.y-p_mesh->min.y;
  float32 bound=0;
  float32 clip=0;
  uint32 dim=(boundPlane & DIM_MASK);
  /*
  p_bg_verts=(boundPlane & MIN_FLAG) ? max_faces[dim]: min_faces[dim];
  for(uint32 i=0; i<4; i++) {
    p_bg[i]=&box[p_bg_verts[i]];
  }
  */
  switch(dim) {
  case DIM_Z:
    eye.x=(p_mesh->min.x+p_mesh->max.x)/2;
    eye.y=p_bound->y;
    eye.z=(p_mesh->min.z+p_mesh->max.z)/2;
    bound=max(height, depth)/2.0;
    /*
    for(uint32 i=0; i<4; i++) {
      if(p_bg[i]->x<p_mesh->mid.x) {
	p_bg[i]->x=p_mesh->mid.x-bound;
      } else {
	p_bg[i]->x=p_mesh->mid.x+bound;
      }
      if(p_bg[i]->z<p_mesh->mid.z) {
	p_bg[i]->z=p_mesh->mid.z-bound;
      } else {
	p_bg[i]->z=p_mesh->mid.z+bound;
      }
    }
    */
    clip=depth/2.0;
    //otherDim&=~z_dim;
    //p_order=top_order_z;
    break;
  case DIM_Y:
    eye.x=(p_mesh->min.x+p_mesh->max.x)/2;
    eye.y=(p_mesh->min.y+p_mesh->max.y)/2;
    eye.z=p_bound->z;
    bound=max(height, depth)/2.0;
    /*
    for(uint32 i=0; i<4; i++) {
      if(p_bg[i]->x<p_mesh->mid.x) {
	p_bg[i]->x=p_mesh->mid.x-bound;
      } else {
	p_bg[i]->x=p_mesh->mid.x+bound;
      }
      if(p_bg[i]->y<p_mesh->mid.y) {
	p_bg[i]->y=p_mesh->mid.y-bound;
      } else {
	p_bg[i]->y=p_mesh->mid.y+bound;
      }
    }
    */
    clip=height/2.0;
    //otherDim&=~y_dim;
    //p_order=top_order_y;
    break;
  case DIM_X:
    eye.x=p_bound->x;
    eye.y=(p_mesh->min.y+p_mesh->max.y)/2;
    eye.z=(p_mesh->min.z+p_mesh->max.z)/2;
    bound=max(height, width)/2.0;
    /*
    for(uint32 i=0; i<4; i++) {
      if(p_bg[i]->z<p_mesh->mid.z) {
	p_bg[i]->z=p_mesh->mid.z-bound;
      } else {
	p_bg[i]->z=p_mesh->mid.z+bound;
      }
      if(p_bg[i]->y<p_mesh->mid.y) {
	p_bg[i]->y=p_mesh->mid.y-bound;
      } else {
	p_bg[i]->y=p_mesh->mid.y+bound;
      }
    }
    */
    clip=width/2;
    //otherDim&=~x_dim;
    //p_order=top_order_x;
    break;
  default:
    printf("invalid dim 0x%x\n", dim);
    assert(false);
  }
  lookAt.x=(p_mesh->min.x+p_mesh->max.x)/2;
  lookAt.y=(p_mesh->min.y+p_mesh->max.y)/2;
  lookAt.z=(p_mesh->min.z+p_mesh->max.z)/2;
  uint32 topDim=(top & DIM_MASK);
  switch(topDim) {
  case DIM_Z:
    zen.x=eye.x;
    zen.y=p_top->y;
    zen.z=eye.z;
    //otherDim&=~z_dim;
    break;
  case DIM_Y:
    zen.x=eye.x;
    zen.y=eye.y;
    zen.z=p_top->z;
    //otherDim&=~y_dim;
    break;
  case DIM_X:
    zen.x=p_top->x;
    zen.y=eye.y;
    zen.z=eye.z;
    //otherDim&=~x_dim;
    break;
  default:
    printf("invalid topDim 0x%x\n", topDim);
  }

  glBindFramebufferEXT(GL_FRAMEBUFFER_EXT, fbo);

  glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT);
  glMatrixMode (GL_PROJECTION);
  glPushMatrix();
  glLoadIdentity ();
  glOrtho(-bound, bound, -bound, bound, -clip, clip);
  glMatrixMode(GL_MODELVIEW);
  glPushMatrix();
  glLoadIdentity();
  
  //GLint viewport[4];
  //glGetIntegerv(GL_VIEWPORT, viewport);
  //printf("viewport: x %u y %u width %u height %u\n", viewport[0], viewport[1], viewport[2], viewport[3]);
  glViewport(0, 0, xSize, ySize);
  gluLookAt(eye.x, eye.y, eye.z, lookAt.x, lookAt.y, lookAt.z, zen.x, zen.y, zen.z);
  //printf("pos x %f y %f z %f\n", pos.x, pos.y, pos.z);
  if(alpha!=1.0) {
    glEnable(GL_BLEND); 
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA);
  } else {
    glDisable(GL_BLEND);
  }
  glLightfv(GL_LIGHT0, GL_POSITION, (float *)&objlight);

  /*
  glDisable( GL_DEPTH_TEST);
  glDisable(GL_CULL_FACE);
  glEnable(GL_TEXTURE_2D);
  glBindTexture(GL_TEXTURE_2D, bgTex);
  glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MIN_FILTER,GL_LINEAR);
  glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MAG_FILTER,GL_LINEAR);
  glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_WRAP_S,GL_CLAMP_TO_EDGE);
  glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_WRAP_T,GL_CLAMP_TO_EDGE);
  GLfloat col[]={1.0f,
		 1.0f,
		 1.0f,1.0f};
  glMaterialfv(GL_FRONT, GL_DIFFUSE, col); 
  glColor4f(1.0, 1.0, 1.0, 1.0);

  glDisable(GL_LIGHTING);
  //if(alpha!=1.0) {
  //  glEnable(GL_BLEND); 
  //  glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA);
  //} else {
    glDisable(GL_BLEND);
    //}
  uint32 dimBg=DIM(p_bg);
  glBegin( GL_TRIANGLES );
  uint32 idx;
  uint32 i;

  uint32 verts[]={0,1,2,1,2,3};
  for(uint32 el=0; el<6; el++) {
    i=verts[el];
    glTexCoord2f(i>>1, (i==1 || i==2)?1.0:0.0);
    idx=(i+p_order[top])%dimBg;
    printf("i: %u x %f y %f z %f\n", i, p_bg[idx]->x, p_bg[idx]->y, p_bg[idx]->z);
    glVertex3f(p_bg[idx]->x, p_bg[idx]->y, p_bg[idx]->z);	
  }
  glEnd();
  */  
  
  glTranslatef(pos.x ,pos.y ,pos.z );
  if(rotAxis) {
    glRotatef(rotAngle, rotAxis[0], rotAxis[1], rotAxis[2]);
  }
  oError error=objPlot(p_mesh, alpha);
  if(alpha!=1.0) {
    glDisable(GL_BLEND);
  }
  
  glBindTexture(GL_TEXTURE_2D,bgTex);
  glCopyTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, 0,0, xSize, ySize, 0);
  glDisable(GL_TEXTURE_2D);

  glMatrixMode(GL_PROJECTION);
  glPopMatrix();
  glMatrixMode(GL_MODELVIEW);
  glPopMatrix();
  glBindFramebufferEXT(GL_FRAMEBUFFER_EXT, 0);
  return ok;
}

oError createVBO(obj_3dMesh *p_mesh, uint32 num_prims) {
  obj_3dPrimitive *p_prim=p_mesh->p_prim;
  uint32 num_verts=num_prims*3;
  GLuint tri_map[num_verts];
  //GLuint *tri_map;
  //tri_map=(GLuint *)malloc(num_verts*sizeof(GLuint));
  //if(!tri_map) {
  //  return noMemory;
  //}
  // memZero(verts, sizeof(verts));

  if(glewInit()!=GLEW_OK || !GL_ARB_vertex_buffer_object) {
    printf("createVBO. no vertex buffer support\n");
    return unsupported;
  }
  p_mesh->vbo=NO_VBO;
  p_mesh->ibo=NO_IBO;
  //return unsupported;

  glGenBuffersARB(1, &(p_mesh->vbo));
  glBindBufferARB(GL_ARRAY_BUFFER_ARB, p_mesh->vbo);
  p_mesh->num_vert_components=3;
  p_mesh->num_col_components=4;
  p_mesh->num_norm_components=3;
  p_mesh->stride=p_mesh->num_vert_components*sizeof(GLfloat)+
    p_mesh->num_col_components*sizeof(GLfloat)+
    p_mesh->num_norm_components*sizeof(GLfloat);

  const GLsizeiptr vertex_size = num_verts*p_mesh->num_vert_components*sizeof(GLfloat);
  const GLsizeiptr color_size = num_verts*p_mesh->num_col_components*sizeof(GLfloat);
  const GLsizeiptr norm_size = num_verts*p_mesh->num_norm_components*sizeof(GLfloat);
  //printf("size alloced: %u\n", num_verts*(num_vert_components+num_col_components));
  glBufferDataARB(GL_ARRAY_BUFFER_ARB, vertex_size+color_size+norm_size, 0, GL_STATIC_DRAW_ARB);
  //printf("assigning buffer size: verts %u cols %u %u\n", vertex_size, color_size, vertex_size+color_size);
  GLvoid* vbo_buf = glMapBufferARB(GL_ARRAY_BUFFER_ARB, GL_WRITE_ONLY_ARB);
  if(!vbo_buf) {
    printf("createVBO. failed to map\n");
    return noMemory;
  }

  GLfloat *p_comp=(GLfloat *)vbo_buf;



  oError error=ok;
  uint32 i;
  uint32 prim=0;
  while(p_prim->next_ref!=NULL) {
    p_prim=p_prim->next_ref;
    //for(uint32 prim=0; prim<num_prims; prim++) {
    assert(p_prim->type==tri);
    // if(curr_prim->uv_id!=UNTEXTURED) {
    //   glEnd();
    //   glEnable(GL_TEXTURE_2D);
    //   glBindTexture(GL_TEXTURE_2D, p_mesh->p_tex_ids[curr_prim->uv_id]);
    //   glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MIN_FILTER,GL_LINEAR);
    //   glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MAG_FILTER,GL_LINEAR);
    //   if(p_mesh->p_tex_flags[curr_prim->uv_id] & OBJ_TEX_FLAG_REPEAT) {
    // 	glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_WRAP_S,GL_REPEAT);
    // 	glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_WRAP_T,GL_REPEAT);
    //   } else {
    // 	glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_WRAP_S,GL_CLAMP_TO_EDGE);
    // 	glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_WRAP_T,GL_CLAMP_TO_EDGE);
    //   }
    //   glBegin(GL_TRIANGLES);
    // }
    for (i=0;i<3;i++) {
      tri_map[prim*3+i]=prim*3+i;
      //glNormal3f( curr_prim->vert[i]->norm.x, curr_prim->vert[i]->norm.y, curr_prim->vert[i]->norm.z);
      
      *(p_comp++)=p_prim->vert[i]->norm.x;
      *(p_comp++)=p_prim->vert[i]->norm.y;
      *(p_comp++)=p_prim->vert[i]->norm.z;

      // if(curr_prim->uv_id != UNTEXTURED) {
      // 	glColor4f(1.0, 1.0, 1.0, alpha);
      // 	glTexCoord2f(curr_prim->vert[i]->u, curr_prim->vert[i]->v);
      // } else {
      //glColor4f(curr_prim->r, curr_prim->g, curr_prim->b, alpha);
 

      *(p_comp++)=p_prim->r;
      *(p_comp++)=p_prim->g;
      *(p_comp++)=p_prim->b;
      *(p_comp++)=1.0;

	//}
	//glVertex3f(	curr_prim->vert[i]->x, 
	//		curr_prim->vert[i]->y, 
	//	curr_prim->vert[i]->z);
      *(p_comp++)=p_prim->vert[i]->x;
      *(p_comp++)=p_prim->vert[i]->y;
      //printf("byte offset %u comp offset %u\n", (uint8 *)p_comp-(uint8 *)vbo_buf, p_comp-(GLfloat *)vbo_buf);
      *(p_comp++)=p_prim->vert[i]->z;
      //printf("x %f y %f z %f r %f g %f b %f\n", p_prim->vert[i]->x, p_prim->vert[i]->y, p_prim->vert[i]->z, p_prim->r, p_prim->g, p_prim->b);
    }
    // if(curr_prim->uv_id!=UNTEXTURED) {
    //   glEnd();
    //   glDisable(GL_TEXTURE_2D);
    //   uint32 error=glGetError();
    //   if(error) {
    // 	printf("err %u\n", error);
    //   }
    //   glBegin(GL_TRIANGLES);
    // }
    prim++;
  }




  // transfer the vertex data to the VBO
  //memcpy(vbo_buffer, s_cubeVertices, vertex_size);
  
  // append color data to vertex data. To be optimal, 
  // data should probably be interleaved and not appended
  //vbo_buffer += vertex_size;
  //memcpy(vbo_buffer, s_cubeColors, color_size);
  //glUnmapBufferARB(GL_ARRAY_BUFFER); 

  // Describe to OpenGL where the color data is in the buffer
  // Describe to OpenGL where the vertex data is in the buffer
  glBindBuffer(GL_ARRAY_BUFFER_ARB, 0);

  glGenBuffers(1, &(p_mesh->ibo));
  glBindBufferARB(GL_ELEMENT_ARRAY_BUFFER_ARB, p_mesh->ibo);
  glBufferDataARB(GL_ELEMENT_ARRAY_BUFFER_ARB, num_verts*sizeof(GLuint), tri_map, GL_STATIC_DRAW_ARB);
  glBindBufferARB(GL_ELEMENT_ARRAY_BUFFER_ARB, 0);
  p_mesh->num_indices=num_verts;
  return ok;
}

//Pre: call to objSetPlotPos/Angle to set plotting position
oError objPlot(obj_3dMesh *p_mesh, float32 alpha) {
  obj_3dPrimitive *obj=p_mesh->p_prim;
  oError error=ok;
  obj_3dPrimitive* curr_prim=obj;
  uint32 i;
	
  //unsigned int flags;
  /*
  glTranslatef(pos.x ,pos.y ,pos.z );
  glLightfv(GL_LIGHT0, GL_POSITION, (float *)&objlight);
  if (rotAxis) {
      glRotatef(rotAngle, rotAxis[0], rotAxis[1], rotAxis[2]);		// Rotate On The X Axis
  }
  */
  //flags=curr_prim->flags;

  glEnable(GL_DEPTH_TEST);
  glEnable(GL_LIGHTING);
  //glEnable(GL_CULL_FACE);
	
  if(p_mesh->vbo != NO_VBO && p_mesh->ibo != NO_IBO) {
    // Activate the VBOs to draw
    glBindBuffer(GL_ARRAY_BUFFER, p_mesh->vbo);
    glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, p_mesh->ibo);

    glEnableClientState(GL_VERTEX_ARRAY);
    glEnableClientState(GL_COLOR_ARRAY);
    glEnableClientState(GL_NORMAL_ARRAY);

    glVertexPointer(p_mesh->num_vert_components, GL_FLOAT, p_mesh->stride, (GLvoid*)((char*)NULL+p_mesh->num_col_components*sizeof(GLfloat)+p_mesh->num_norm_components*sizeof(GLfloat)));
    glColorPointer(p_mesh->num_col_components, GL_FLOAT, p_mesh->stride, (GLvoid*)((char*)NULL+p_mesh->num_norm_components*sizeof(GLfloat)));
    glNormalPointer(GL_FLOAT, p_mesh->stride, (GLvoid*)((char*)NULL));
    //glColor4f(1.0, 1.0, 1.0, 1.0);
    // This is the actual draw command
    glDrawElements(GL_TRIANGLES, p_mesh->num_indices, 
		   GL_UNSIGNED_INT, (GLvoid*)((char*)NULL));

    glDisableClientState(GL_NORMAL_ARRAY);
    glDisableClientState(GL_COLOR_ARRAY);
    glDisableClientState(GL_VERTEX_ARRAY);

    glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, 0);
    glBindBuffer(GL_ARRAY_BUFFER, 0);

    uint32 error=glGetError();
    if(error) {
      printf("err %u\n", error);
    }
  } else {
    uint32 last_textured=false;
    glBegin(  GL_TRIANGLES );
    while(curr_prim->next_ref!=NULL) {
      curr_prim=curr_prim->next_ref;
      if(curr_prim->uv_id!=UNTEXTURED) {
	glEnd();
	glEnable(GL_TEXTURE_2D);
	glBindTexture(GL_TEXTURE_2D, p_mesh->p_tex_ids[curr_prim->uv_id]);
	glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MIN_FILTER,GL_LINEAR);
	glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MAG_FILTER,GL_LINEAR);
	if(p_mesh->p_tex_flags[curr_prim->uv_id] & OBJ_TEX_FLAG_REPEAT) {
	  glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_WRAP_S,GL_REPEAT);
	  glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_WRAP_T,GL_REPEAT);
	} else {
	  glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_WRAP_S,GL_CLAMP_TO_EDGE);
	  glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_WRAP_T,GL_CLAMP_TO_EDGE);
	}
	//glTexParameteri(GL_TEXTURE_2D, GL_GENERATE_MIPMAP, GL_TRUE);
	glBegin(GL_TRIANGLES);
      }
      for (i=0;i<3;i++) {
	glNormal3f( curr_prim->vert[i]->norm.x, curr_prim->vert[i]->norm.y, curr_prim->vert[i]->norm.z);				
	if(curr_prim->uv_id != UNTEXTURED) {
	  glColor4f(1.0, 1.0, 1.0, alpha);
	  glTexCoord2f(curr_prim->vert[i]->u, curr_prim->vert[i]->v);
	} else {
	  glColor4f(curr_prim->r, curr_prim->g, curr_prim->b, alpha);
	}
	glVertex3f(	curr_prim->vert[i]->x, 
			curr_prim->vert[i]->y, 
			curr_prim->vert[i]->z);	
      }
      if(curr_prim->uv_id!=UNTEXTURED) {
	glEnd();
	glDisable(GL_TEXTURE_2D);
	//glEnable( GL_DEPTH_TEST);
	uint32 error=glGetError();
	if(error) {
	  printf("err %u\n", error);
	}
	glBegin(GL_TRIANGLES);
      }
    }
    glEnd();
  }
  return error;
}

//Pre: call to objSetLoadPos.. angle not yet supported
oError objCreate(obj_3dMesh **pp_mesh, 
					char *fname,float obj_scaler
		 , unsigned int flags ) {
  //printf("objCreate for %s\n", fname);
  *pp_mesh=new obj_3dMesh;
  p_meshes[num_meshes++]=*pp_mesh;

  strncpy((*pp_mesh)->mesh_path, fname, PATH_LEN);
  obj_3dPrimitive **obj=&((*pp_mesh)->p_prim);
	oError error=ok;
	obj_3dPrimitive *curr_obj;
	FILE *file=fopen(fname,"rb");
	if (file==NULL) return nofile;
	int i,j;
	int temp;
	obj_vertex mid, min, max;
	obj_vertex *inverts=NULL;
	int inverts_max;
	obj_3dPrimitive *inprims;
	int inprims_max;

	//skip a comma
	while (fgetc(file)!=',');
	//read number of objects
	fscanf(file,"%i",&temp);

	//skip 2 lines
	while (fgetc(file)!=0x0a);
	while (fgetc(file)!=0x0a);

	//skip objects+1 newlines
	for (i=0;i<=temp;i++) {
		while (fgetc(file)!=0x0a);
	}

	//skip a comma
	while (fgetc(file)!=',');

	fscanf(file,"%i",&inverts_max); //scan in number of vertices in obj
	inverts= new obj_vertex[inverts_max];
	(*pp_mesh)->p_vert_start=inverts;
	(*pp_mesh)->p_vert_end=inverts+inverts_max;

	//skip 2 lines
	while (fgetc(file)!=0x0a);
	while (fgetc(file)!=0x0a);

	mid.x=0;
	mid.y=0;
	mid.z=0;

	//begin reading in vertex coords
	for (i=0;i<inverts_max;i++) {
	  while (fgetc(file)!=','); //skip first comma
	  fscanf(file,"%f",&(inverts[i].x));
	  inverts[i].x-=origin_offset.x;
	  inverts[i].x*=obj_scaler;
	  if(inverts_max) {
	    mid.x+=inverts[i].x/inverts_max;
	  }
	  while (fgetc(file)!=','); //skip second comma
	  fscanf(file,"%f",&(inverts[i].y));
	  inverts[i].y-=origin_offset.y;
	  inverts[i].y*=obj_scaler;
	  if(inverts_max) {
	    mid.y+=inverts[i].y/inverts_max;
	  }
	  while (fgetc(file)!=','); //skip third comma
	  fscanf(file,"%f",&(inverts[i].z));
	  inverts[i].z-=origin_offset.z;
	  inverts[i].z*=obj_scaler;
	  if(inverts_max) {
	    mid.z+=inverts[i].z/inverts_max;
	  }
	  while (fgetc(file)!=0x0a);//skip to next line
	  inverts[i].shared=0;

	  inverts[i].norm.x=0.0f;
	  inverts[i].norm.y=0.0f;
	  inverts[i].norm.z=0.0f;

	  if(i==0) {
	    min.x=inverts[i].x;
	    min.y=inverts[i].y;
	    min.z=inverts[i].z;
	    max.x=inverts[i].x;
	    max.y=inverts[i].y;
	    max.z=inverts[i].z;
	  } else {
	    if(inverts[i].x<min.x) {
	      min.x=inverts[i].x;
	    }
	    if(inverts[i].x>max.x) {
	      max.x=inverts[i].x;
	    }
	    if(inverts[i].y<min.y) {
	      min.y=inverts[i].y;
	    }
	    if(inverts[i].y>max.y) {
	      max.y=inverts[i].y;
	    }
	    if(inverts[i].z<min.z) {
	      min.z=inverts[i].z;
	    }
	    if(inverts[i].z>max.z) {
	      max.z=inverts[i].z;
	    }
	  }
	  inverts[i].id=i;
	}
	if(!strncmp((*pp_mesh)->mesh_path, match_mesh, PATH_LEN)) {
	  printf("min %s: %f %f %f\n", (*pp_mesh)->mesh_path, min.x, min.y, min.z);
	  printf("max: %f %f %f\n", max.x, max.y, max.z);
	  printf("mid: %f %f %f\n", mid.x, mid.y, mid.z);
	}			
	//printf("mid: %f %f %f\n", mid.x, mid.y, mid.z);
	//skip 1 lines
	while (fgetc(file)!=0x0a);
	//skip a comma
	while (fgetc(file)!=',');

	fscanf(file,"%i",&inprims_max); //scan in number of triangles in obj
	inprims= new obj_3dPrimitive[inprims_max];

	//skip 2 lines
	while (fgetc(file)!=0x0a);
	while (fgetc(file)!=0x0a);
	
	//start reading in triangles
	for (i=0;i<inprims_max;i++) {
		for (j=0;j<3;j++) {
			while (fgetc(file)!=','); //skip comma
			fscanf(file,"%i",&temp);
			inprims[i].vert[j]=&inverts[temp-1];
		}

		//***************************************************
		obj_vector v1,v2,vector_normal,unit_vector_norm;
		float vector_mag;
		obj_vertex **vert=inprims[i].vert;
		//get two vector which point in the direction of the surface
		v1.x=vert[1]->x-vert[0]->x;
		v1.y=vert[1]->y-vert[0]->y;
		v1.z=vert[1]->z-vert[0]->z;
		
		v2.x=vert[2]->x-vert[0]->x;
		v2.y=vert[2]->y-vert[0]->y;
		v2.z=vert[2]->z-vert[0]->z;
		
		//find the normal to the surface ie. v1 x v2 (cross product)
		vector_normal.x=v1.y * v2.z  -  v1.z * v2.y;
		vector_normal.y=v1.z * v2.x  -  v1.x * v2.z;
		vector_normal.z=v1.x * v2.y  -  v1.y * v2.x;
		
		vector_mag=(float) sqrt(	sqr(vector_normal.x) + 
			sqr(vector_normal.y) +
			sqr(vector_normal.z)  );
		
		//normalise the normal
		if (vector_mag==0) vector_mag=1;//prevent div 0
		unit_vector_norm.x=vector_normal.x/vector_mag;
		unit_vector_norm.y=vector_normal.y/vector_mag;
		unit_vector_norm.z=vector_normal.z/vector_mag;
		
		if (!(flags&OBJ_NORMAL_POSITIVE)) {
			unit_vector_norm.x*=-1;
			unit_vector_norm.y*=-1;
			unit_vector_norm.z*=-1;	
		}
		
		for (j=0;j<3;j++) {
			vert[j]->norm.x*=vert[j]->shared;
			//if(!strncmp((*pp_mesh)->mesh_path, match_mesh, PATH_LEN)) {
			//}			
			vert[j]->norm.y*=vert[j]->shared;
			vert[j]->norm.z*=vert[j]->shared;

			vert[j]->norm.x+=unit_vector_norm.x;
			vert[j]->norm.y+=unit_vector_norm.y;
			vert[j]->norm.z+=unit_vector_norm.z;
			
			vert[j]->shared++;
			
			vert[j]->norm.x/=vert[j]->shared;
			vert[j]->norm.y/=vert[j]->shared;
			vert[j]->norm.z/=vert[j]->shared;
			
		}

		inprims[i].vertex_list=NULL; //only valid for first prim in list
		inprims[i].flags=0;
		inprims[i].uv_id=UNTEXTURED;
		checkAllRanges(&inprims[i].uv_id);
		while (fgetc(file)!=0x0a);
		inprims[i].id=i;
	}

	//skip to colours definitions
	while (fgetc(file)!=0x0a);
	while (fgetc(file)!=0x0a);
	while (fgetc(file)!=0x0a);

	//begin assigning colours to triangles
	for (i=0;i<inprims_max;i++) {
		
		while (fgetc(file)!=','); //skip comma
		fscanf(file,"%i",&temp); //read red value
		inprims[i].r=(float) temp/255.0f;

		while (fgetc(file)!=','); //skip comma
		fscanf(file,"%i",&temp); //read green value
		inprims[i].g=(float) temp/255.0f;

		while (fgetc(file)!=','); //skip comma
		fscanf(file,"%i",&temp); //read blue value
		inprims[i].b=(float) temp/255.0f;

		while (fgetc(file)!=0x0a);
	}

	//skip 1 lines
	while (fgetc(file)!=0x0a);
	//skip a comma
	while (fgetc(file)!=',');
	fscanf(file,"%i",&((*pp_mesh)->num_uv_maps));
	(*pp_mesh)->p_tex_ids=new uint32[(*pp_mesh)->num_uv_maps];
	(*pp_mesh)->p_tex_flags=new uint32[(*pp_mesh)->num_uv_maps];
	(*pp_mesh)->pp_tex_paths=new uint8*[(*pp_mesh)->num_uv_maps];
	//skip 2 lines
	while (fgetc(file)!=0x0a);
	while (fgetc(file)!=0x0a);

	uint32 max_uv_id=0;
	uint32 pathLen;
	uint32 uvId;
	uint32 texFlags;
	uint8 path[PATH_LEN];
	for (i=0;i<(*pp_mesh)->num_uv_maps;i++) {
	  fscanf(file,"%i",&uvId);
	  while (fgetc(file)!=','); //skip comma
	  fscanf(file,"%i",&texFlags);
	  (*pp_mesh)->p_tex_flags[uvId]=texFlags;
	  while (fgetc(file)!=','); //skip comma
	  fscanf(file, PATH_MATCH, path);
	  pathLen=strnlen(path, PATH_LEN-1);
	  (*pp_mesh)->pp_tex_paths[uvId]=new uint8[PATH_LEN];
	  strncpy((*pp_mesh)->pp_tex_paths[uvId], path, pathLen+1);
	  while (fgetc(file)!=0x0a);
	}
	
	uint32 num_uv_mapped_faces=0;
	uint32 face_id, map_id;
	while (fgetc(file)!=0x0a);
	while (fgetc(file)!=',');
	fscanf(file,"%i",&num_uv_mapped_faces); //scan in number of triangles in obj
	while (fgetc(file)!=0x0a);
	while (fgetc(file)!=0x0a);
	for(uint32 face=0; face<num_uv_mapped_faces; face++) {
	  fscanf(file,"%i",&face_id);
	  while (fgetc(file)!=',');
	  fscanf(file,"%i",&map_id);
	  inprims[face_id-1].uv_id=map_id;
	  //printf("setting uv_id face %u (0x%x) to %u\n", face_id, &(inprims[face_id-1].uv_id), map_id);
	  for(uint32 vert_idx=0; vert_idx<3; vert_idx++) {
	    while (fgetc(file)!=',');
	    fscanf(file,"%f", &(*(inprims[face_id-1].vert[vert_idx])).u);
	    while (fgetc(file)!=',');
	    fscanf(file,"%f", &(*(inprims[face_id-1].vert[vert_idx])).v);
	  }
	  while (fgetc(file)!=0x0a);
	}

	fclose(file);
//-----------------------------------------------------------
	(*pp_mesh)->mid=mid;
	(*pp_mesh)->min=min;
	(*pp_mesh)->max=max;
	*obj= new obj_3dPrimitive;
	if (*obj==NULL) return noMemory;
	(*obj)->flags=flags;
	(*obj)->type=empty;
	curr_obj=*obj;
	curr_obj->uv_id=UNTEXTURED;
	curr_obj->vertex_list=inverts;
	
	i=0;
	while (i<inprims_max) {
		curr_obj->next_ref=new obj_3dPrimitive[1];
		if (curr_obj->next_ref==NULL) return noMemory;
		curr_obj=curr_obj->next_ref;
		inprims[i].type=tri;
		*curr_obj=inprims[i];
		curr_obj->next_ref=NULL;
		i++;
	}
	
	createVBO(*pp_mesh, inprims_max);
	delete [] inprims;
	
	return error;
}

void objDelete(obj_3dMesh **pp_mesh) {
  obj_3dPrimitive *obj=(*pp_mesh)->p_prim;
  glDeleteTextures((*pp_mesh)->num_uv_maps, (*pp_mesh)->p_tex_ids);
  delete *pp_mesh;
  *pp_mesh=NULL;
  obj_3dPrimitive *next;
  delete obj->vertex_list;
  while (obj!=NULL) {
    next=obj->next_ref;
    delete obj; 
    obj=next;
  }
  obj=NULL;
}


