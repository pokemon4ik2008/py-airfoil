#include <assert.h>
#include <Eigen/Geometry>

#ifdef OPEN_GL
#include <GL/glew.h>
#endif

#include <string.h>
#include "collider.h"
#include "objects.h"
#include "types.h"

extern uint32 top_order_x[MAX_ORDER]={0};
extern uint32 top_order_y[MAX_ORDER]={0};
extern uint32 top_order_z[MAX_ORDER]={0};

float rotAngle = 0;
float *rotAxis = NULL;

bool obj_use_gl_lighting=true;
float obj_cut_off_dist = 100;
float obj_cut_off_angle = 20;
float obj_ambient_light=0.5f;
obj_light_source objlight={0,0,0,1.0f};

extern "C" 
{
  DLL_EXPORT void setAngleAxisRotation(float angle, float axis[]) 
  {
    rotAngle = angle;
    rotAxis = axis;
  }

  DLL_EXPORT void getMid(void *p_meshToPlot, float mid[])
  {
    obj_3dMesh *p_mesh=static_cast<obj_3dMesh *>(p_meshToPlot);
    mid[0]=static_cast<obj_3dMesh *>(p_mesh)->mid.x();
    mid[1]=static_cast<obj_3dMesh *>(p_mesh)->mid.y();
    mid[2]=static_cast<obj_3dMesh *>(p_mesh)->mid.z();
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

  DLL_EXPORT void draw(obj_3dMesh *p_meshToPlot, float32 alpha)
	{
		oError err = ok;
		glTranslatef(col_getPos().x , col_getPos().y, col_getPos().z );
		glLightfv(GL_LIGHT0, GL_POSITION, (float *)&objlight);
		if (rotAxis) {
		  glRotatef(rotAngle, rotAxis[0], rotAxis[1], rotAxis[2]);		// Rotate On The X Axis
		}
  
		err = objPlot(p_meshToPlot, alpha);
		if (err != ok)
		{
			printf("ERROR: when drawing object\n");
		}
	}

  DLL_EXPORT void drawVBO(void *p_vboToPlot)
	{
		oError err = ok;
		glTranslatef(col_getPos().x, col_getPos().y, col_getPos().z );
		glLightfv(GL_LIGHT0, GL_POSITION, (float *)&objlight);
		if (rotAxis) {
		  glRotatef(rotAngle, rotAxis[0], rotAxis[1], rotAxis[2]);		// Rotate On The X Axis
		}
  
		err = vboPlot(static_cast<obj_vbo *>(p_vboToPlot));
		if (err != ok)
		{
			printf("ERROR: when drawing object\n");
		}
	}

  void deleteVBOBuffers(obj_vbo *p_vbo) {
    if(!p_vbo) {
      printf("deleteVBOBuffers. vbo does not exist\n");
      return;
    }
    //printf("deleteVBOBuffers. num prims %i\n", p_vbo->num_prims);
    if(p_vbo->ibo != NO_IBO) {
      printf("deleteVBOBuffers. ibo %i\n", p_vbo->ibo);
      glBindBufferARB(GL_ELEMENT_ARRAY_BUFFER_ARB, p_vbo->ibo);
      glUnmapBufferARB(GL_ELEMENT_ARRAY_BUFFER_ARB); 
      glBindBufferARB(GL_ELEMENT_ARRAY_BUFFER_ARB, 0);
      glDeleteBuffersARB(1, &(p_vbo->ibo));
    }
    if(p_vbo->vbo != NO_VBO) {
      printf("deleteVBOBuffers. vbo %i\n", p_vbo->vbo);
      glBindBufferARB(GL_ARRAY_BUFFER_ARB, p_vbo->vbo);
      glUnmapBufferARB(GL_ARRAY_BUFFER_ARB); 
      glBindBuffer(GL_ARRAY_BUFFER_ARB, 0);
      glDeleteBuffersARB(1, &(p_vbo->vbo));
    }
  }

	DLL_EXPORT void deleteMesh(void *meshToDelete)
	{	
		obj_3dMesh *p_mesh = static_cast<obj_3dMesh *>(meshToDelete);
		deleteVBOBuffers(&(p_mesh->vbo));
		col_objDelete(&p_mesh);			
	}
  
	DLL_EXPORT void deleteVBO(void *vboToDelete)
	{	
		obj_vbo *p_vbo = static_cast<obj_vbo *>(vboToDelete);
		deleteVBOBuffers(p_vbo);
		free(p_vbo);			
	}
  
  DLL_EXPORT void *createVBO(uint32 vbo_group)
  {
    assert(vbo_group!=NO_VBO_GROUP_EVER && vbo_group!=NO_VBO_GROUP);
    uint32 group_size=0;
    for(uint32 i=0; i<col_numMeshes(); i++) {
      obj_3dMesh *p_mesh=col_getMeshes()[i];
      assert(p_mesh->vbo_group!=NO_VBO_GROUP_EVER);
      if(p_mesh->vbo_group!=NO_VBO_GROUP && p_mesh->vbo_group==vbo_group) {
	group_size++;
      }
    }
    obj_3dMesh *p_group_meshes=(obj_3dMesh *)malloc(sizeof(obj_3dMesh)*group_size);
    if(p_group_meshes) {
      uint32 group_idx=0;
      for(uint32 i=0; i<col_numMeshes(); i++) {
	obj_3dMesh *p_mesh=col_getMeshes()[i];
	if(p_mesh->vbo_group!=NO_VBO_GROUP && p_mesh->vbo_group==vbo_group) {
	  p_group_meshes[group_idx]=*p_mesh;
	  group_idx++;
	}
      }
    
      obj_vbo *p_vbo=(obj_vbo *)malloc(sizeof(obj_vbo));
      setupVBO(p_group_meshes, group_size, p_vbo);
      free(p_group_meshes);
      return p_vbo;
    } else {
      printf("createVBO. failed to allocate mem\n");
      return NULL;
    }
  }

  DLL_EXPORT void *createMeshVBO(obj_3dMesh *p_mesh) {
    setupVBO(p_mesh, 1, &(p_mesh->vbo));
  }

  DLL_EXPORT void drawRotated(float64 xPos, float64 yPos, float64 zPos,
			      float64 wAtt, float64 xAtt, float64 yAtt, float64 zAtt,
			      float64 wAng, float64 xAng, float64 yAng, float64 zAng,
			      obj_3dMesh *p_centre_mesh, float32 alpha, obj_3dMesh *p_mesh) {
    using namespace Eigen;
    Quaternion<float64> att(wAtt, xAtt, yAtt, zAtt);
    Quaternion<float64> angle_quat(wAng, xAng, yAng, zAng);
    Quaternion<float64> rot=att*angle_quat*SETUP_ROT;
    Vector3d rotOrig=rotVert(p_centre_mesh->mid, att);
    //printf("c. pos: %f %f %f\n", xPos, yPos, zPos);
    //printf("c. rotOrig: %f %f %f\n", rotOrig.x(), rotOrig.y(), rotOrig.z());
    //printf("c. rot: %f %f %f %f\n", rot.w(), rot.x(), rot.y(), rot.z());
    setupRotation(xPos, yPos, zPos,
		  rot, p_centre_mesh->mid, rotOrig);
    //draw(p_mesh, alpha);
 }

  DLL_EXPORT void setupRotation(float64 x, 
			   float64 y, 
			   float64 z, 
			   float64 wr, 
			   float64 xr, 
			   float64 yr, 
			   float64 zr, 
			   float64 xmid, 
			   float64 ymid, 
			   float64 zmid, 
			   float64 xorig, 
			   float64 yorig, 
			   float64 zorig)
  {
    //printf("c: pos %f %f %f\n", x, y, z);
    //printf("c: angle_quat %f %f %f %f\n", wr, xr, yr, zr);
    //printf("c: midPt %f %f %f\n", xmid, ymid, zmid);
    //printf("c: rotOrig %f %f %f\n", xorig, yorig, zorig);
    using namespace Eigen;
    Vector3d pos(x, y, z), midPt(xmid, ymid, zmid), rotOrig(xorig, yorig, zorig);
    Quaternion<float64> angle_quat(wr, xr, yr, zr);
    setupRotation(x, y, z, angle_quat, midPt, rotOrig);
    /*
    angle_quat.normalize();
    AngleAxis<float64> angleAxis(angle_quat);

    Vector3d rotNew=angle_quat * midPt;
    Vector3d axis=angleAxis.axis();
    Vector3d offset=pos-(rotNew-rotOrig);
    //printf("c: rotNew %f %f %f\n", rotNew.x(), rotNew.y(), rotNew.z());

    float32 fpos[3];
    fpos[0]=offset.x();
    fpos[1]=offset.y();
    fpos[2]=offset.z();
    setPosition(fpos);
    //printf("c: set pos %f %f %f\n", fpos[0], fpos[1], fpos[2]);

    fpos[0]=axis.x();
    fpos[1]=axis.y();
    fpos[2]=axis.z();

    setAngleAxisRotation(angleAxis.angle() * (180.0/3.141592653589793), fpos);
    //printf("c: set rot %f axis: %f %f %f\n", angleAxis.angle() * (180.0/3.141592653589793), fpos[0], fpos[1], fpos[2]);
    */
  }

}

  void setupRotation(float64 x,
		     float64 y,
		     float64 z,
		     Eigen::Quaternion<float64> &angle_quat,
		     Eigen::Vector3d &midPt, Eigen::Vector3d &rotOrig) {
    //printf("c: pos %f %f %f\n", x, y, z);
    //printf("c: angle_quat %f %f %f %f\n", wr, xr, yr, zr);
    //printf("c: midPt %f %f %f\n", xmid, ymid, zmid);
    //printf("c: rotOrig %f %f %f\n", xorig, yorig, zorig);
    using namespace Eigen;
    Vector3d pos(x, y, z);
    angle_quat.normalize();
    AngleAxis<float64> angleAxis(angle_quat);

    Vector3d rotNew=angle_quat * midPt;
    Vector3d axis=angleAxis.axis();
    Vector3d offset=pos-(rotNew-rotOrig);
    //printf("c: rotNew %f %f %f\n", rotNew.x(), rotNew.y(), rotNew.z());

    float32 fpos[3];
    fpos[0]=offset.x();
    fpos[1]=offset.y();
    fpos[2]=offset.z();
    col_setPosition(fpos);
    //printf("c: set pos %f %f %f\n", fpos[0], fpos[1], fpos[2]);

    fpos[0]=axis.x();
    fpos[1]=axis.y();
    fpos[2]=axis.z();

    setAngleAxisRotation(angleAxis.angle() * (180.0/3.141592653589793), fpos);
    //printf("c: set rot %f axis: %f %f %f\n", angleAxis.angle() * (180.0/3.141592653589793), fpos[0], fpos[1], fpos[2]);
  }

void	objSetCutOff		(float dist, float angle) {
	obj_cut_off_dist=dist;
	obj_cut_off_angle=angle;
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
	float ax=-deg_to_rad*col_getPos().ax;
	float ay=-deg_to_rad*col_getPos().ay;
	float az=-deg_to_rad*col_getPos().az;

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
  
  glTranslatef(col_getPos().x, col_getPos().y, col_getPos().z );
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

oError setupVBO(obj_3dMesh *p_meshes, uint32 num_meshes, obj_vbo *p_vbo) {
  if(glewInit()!=GLEW_OK || !GL_ARB_vertex_buffer_object) {
    printf("createVBO. no vertex buffer support\n");
    return unsupported;
  }

  obj_3dMesh *p_mesh;
  uint32 num_prims=0;
  for(uint32 m=0; m<num_meshes; m++) {
    p_mesh=&p_meshes[m];
    num_prims+=p_mesh->num_prims;
  }

  uint32 num_verts=num_prims*3;
  GLuint *tri_map;

  glGenBuffers(1, &(p_vbo->ibo));
  glBindBufferARB(GL_ELEMENT_ARRAY_BUFFER_ARB, p_vbo->ibo);
  glBufferDataARB(GL_ELEMENT_ARRAY_BUFFER_ARB, num_verts*sizeof(GLuint), 0, GL_STATIC_DRAW_ARB);
  tri_map=(GLuint *)glMapBufferARB(GL_ELEMENT_ARRAY_BUFFER_ARB, GL_WRITE_ONLY_ARB);
  if(!tri_map) {
    printf("createVBO. failed to map indices\n");
    return noMemory;
  }
  memZero(tri_map, sizeof(tri_map));

  glGenBuffersARB(1, &(p_vbo->vbo));
  glBindBufferARB(GL_ARRAY_BUFFER_ARB, p_vbo->vbo);
  p_vbo->num_vert_components=3;
  p_vbo->num_col_components=4;
  p_vbo->num_norm_components=3;
  p_vbo->stride=p_vbo->num_vert_components*sizeof(GLfloat)+
    p_vbo->num_col_components*sizeof(GLfloat)+
    p_vbo->num_norm_components*sizeof(GLfloat);

  const GLsizeiptr vertex_size = num_verts*p_vbo->num_vert_components*sizeof(GLfloat);
  const GLsizeiptr color_size = num_verts*p_vbo->num_col_components*sizeof(GLfloat);
  const GLsizeiptr norm_size = num_verts*p_vbo->num_norm_components*sizeof(GLfloat);
  glBufferDataARB(GL_ARRAY_BUFFER_ARB, vertex_size+color_size+norm_size, 0, GL_STATIC_DRAW_ARB);
  GLvoid* vbo_buf = glMapBufferARB(GL_ARRAY_BUFFER_ARB, GL_WRITE_ONLY_ARB);
  if(!vbo_buf) {
    printf("createVBO. failed to map\n");
    return noMemory;
  }

  oError error=ok;
  uint32 i;
  uint32 prim=0;
  GLfloat *p_comp=(GLfloat *)vbo_buf;

  for(uint32 m=0; m<num_meshes; m++) {
    obj_3dPrimitive *p_prim=p_meshes[m].p_prim;
    while(p_prim->next_ref!=NULL) {
      p_prim=p_prim->next_ref;
      assert(p_prim->type==tri);
      for (i=0;i<3;i++) {
	tri_map[prim*3+i]=prim*3+i;
      
	*(p_comp++)=p_prim->vert[i]->norm.x;
	*(p_comp++)=p_prim->vert[i]->norm.y;
	*(p_comp++)=p_prim->vert[i]->norm.z;

	*(p_comp++)=p_prim->r;
	*(p_comp++)=p_prim->g;
	*(p_comp++)=p_prim->b;
	*(p_comp++)=1.0;

	*(p_comp++)=p_prim->vert[i]->x;
	*(p_comp++)=p_prim->vert[i]->y;
	*(p_comp++)=p_prim->vert[i]->z;
      }
      prim++;
    }
  }

  glBindBuffer(GL_ARRAY_BUFFER_ARB, 0);
  glBindBufferARB(GL_ELEMENT_ARRAY_BUFFER_ARB, 0);
  p_vbo->num_indices=num_verts;
  p_vbo->num_prims=num_prims;

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
	
  if(p_mesh->vbo.vbo == NO_VBO) {
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
	uint32 gl_error=glGetError();
	if(gl_error) {
	  printf("err %u\n", error);
	  error=glErr;
	}
	glBegin(GL_TRIANGLES);
      }
    }
    glEnd();
  } else {
    assert(p_mesh->vbo.ibo!=NO_IBO);
    // Activate the VBOs to draw
    glBindBuffer(GL_ARRAY_BUFFER, p_mesh->vbo.vbo);
    glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, p_mesh->vbo.ibo);

    glEnableClientState(GL_VERTEX_ARRAY);
    glEnableClientState(GL_COLOR_ARRAY);
    glEnableClientState(GL_NORMAL_ARRAY);

    glVertexPointer(p_mesh->vbo.num_vert_components, GL_FLOAT, p_mesh->vbo.stride, (GLvoid*)((char*)NULL+p_mesh->vbo.num_col_components*sizeof(GLfloat)+p_mesh->vbo.num_norm_components*sizeof(GLfloat)));
    glColorPointer(p_mesh->vbo.num_col_components, GL_FLOAT, p_mesh->vbo.stride, (GLvoid*)((char*)NULL+p_mesh->vbo.num_norm_components*sizeof(GLfloat)));
    glNormalPointer(GL_FLOAT, p_mesh->vbo.stride, (GLvoid*)((char*)NULL));
    //glColor4f(1.0, 1.0, 1.0, 1.0);
    // This is the actual draw command
    glDrawElements(GL_TRIANGLES, p_mesh->vbo.num_indices, 
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
  }
  return error;
}

//Pre: call to objSetPlotPos/Angle to set plotting position
oError vboPlot(obj_vbo *p_vbo) {
  oError error=ok;
  glEnable(GL_DEPTH_TEST);
  glEnable(GL_LIGHTING);
  //glEnable(GL_CULL_FACE);
	
  assert(p_vbo->vbo != NO_VBO);
  assert(p_vbo->ibo!=NO_IBO);
  assert(glIsBuffer(p_vbo->vbo)==GL_TRUE);
  assert(glIsBuffer(p_vbo->ibo)==GL_TRUE);

  //printf("vboPlot %u %u\n", p_vbo->vbo, p_vbo->ibo);

  // Activate the VBOs to draw
  glBindBuffer(GL_ARRAY_BUFFER, p_vbo->vbo);
  glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, p_vbo->ibo);

  glEnableClientState(GL_VERTEX_ARRAY);
  glEnableClientState(GL_COLOR_ARRAY);
  glEnableClientState(GL_NORMAL_ARRAY);

  glVertexPointer(p_vbo->num_vert_components, GL_FLOAT, p_vbo->stride, (GLvoid*)((char*)NULL+p_vbo->num_col_components*sizeof(GLfloat)+p_vbo->num_norm_components*sizeof(GLfloat)));
  glColorPointer(p_vbo->num_col_components, GL_FLOAT, p_vbo->stride, (GLvoid*)((char*)NULL+p_vbo->num_norm_components*sizeof(GLfloat)));
  glNormalPointer(GL_FLOAT, p_vbo->stride, (GLvoid*)((char*)NULL));
  //glColor4f(1.0, 1.0, 1.0, 1.0);
  // This is the actual draw command
  glDrawElements(GL_TRIANGLES, p_vbo->num_indices, 
		 GL_UNSIGNED_INT, (GLvoid*)((char*)NULL));

  glDisableClientState(GL_NORMAL_ARRAY);
  glDisableClientState(GL_COLOR_ARRAY);
  glDisableClientState(GL_VERTEX_ARRAY);

  glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, 0);
  glBindBuffer(GL_ARRAY_BUFFER, 0);

  uint32 gl_error=glGetError();
  if(gl_error) {
    printf("err %u\n", error);
    error=glErr;
  }
  return error;
}

