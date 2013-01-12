#ifndef objs_h
#define objs_h

//if bits 0 and 1 are unset then
//program assumes negative normals.
#define	OBJ_NORMAL_ABSOLUTE	1 //this will overide the positive bit
// Positive normals: outfacing triangles have vertices defined clockwise
// Negative normals: outfacing triangles have vertices defined anti-clockwise
#define OBJ_NORMAL_POSITIVE	2
#define OBJ_SHINY			4
#define OBJ_ALWAYS_SHOW		8
#define OBJ_NO_LIGHTING		16
#define OBJ_NO_FOG			32
#define OBJ_USE_FAST_LIGHT	64

#define OBJ_TEX_FLAG_CLAMP 0x0
#define OBJ_TEX_FLAG_REPEAT 0x1

#define MIN_FLAG 0x10
#define MAX_FLAG 0x20
#define DIM_MASK 0x3
//Don't change values of DIM_. macros as
//objPlotToTex relies on existing values
#define DIM_X 0x0
#define DIM_Y 0x1
#define DIM_Z 0x2
#define MAX_ORDER MIN_FLAG|MAX_FLAG|DIM_MASK

#define MIN_X MIN_FLAG|DIM_X
#define MAX_X MAX_FLAG|DIM_X
#define MIN_Y MIN_FLAG|DIM_Y
#define MAX_Y MAX_FLAG|DIM_Y
#define MIN_Z MIN_FLAG|DIM_Z
#define MAX_Z MAX_FLAG|DIM_Z

#define DIM(a) (sizeof(a)/sizeof(a[0]))
#define MIN(a,b) (a>b?b:a)
#define MAX(a,b) (a<b?b:a)

//all objects within this dist from viewer will be plotted.
//this ensure's that object when looking directly up or down
//are plotted ok
#define obj_min_plot_dist	10	

#ifdef WIN32
#include <windows.h>
#endif

#include <stdio.h>
#include <stdlib.h>
#include <iostream>
#include <math.h>
#include <Eigen/Geometry>
#ifdef OPEN_GL
#include <GL/glew.h>
#endif

typedef enum {line,tri,quad,empty} primitiveType;
#define PI	(22.0f/7.0f)
#define sqr(x) ((x)*(x))
#define deg_to_rad (PI/180.0f)
#define rad_to_deg (180.0f/PI)
#define absValue(x) ( (x)>=0?(x):-(x) )
#define small_number -32627.0f

#ifdef WIN32 
#define DLL_EXPORT _declspec(dllexport) 
#else
#define DLL_EXPORT 
#endif

#define PATH_LEN 256
#define TAG_LEN 32
#define PATH_MATCH "%256s"
typedef char uint8;
typedef unsigned int uint32;
typedef float float32;
typedef double float64;
//uint8** uvMap2Texture;
//uint32* uvMap2Id;

uint32 top_order_x[MAX_ORDER]={0};
uint32 top_order_y[MAX_ORDER]={0};
uint32 top_order_z[MAX_ORDER]={0};

#define UNTEXTURED 0xffffffff
//#define TEXTURED_FLAG 0xf

typedef struct {
	float				x,y,z;
	float				ax,ay,az;
} obj_plot_position;

typedef struct {
	float				x,y,z;
} obj_vector;

typedef struct {
  float32				x,y,z;
  float32				u,v;
  obj_vector			norm;		//vertex normal
  ubyte				shared;		//holds number of primitives sharing this vertex
  uint32 id;
} obj_vertex;

typedef struct OBJ_3DPRIMITIVE
{
  obj_vertex			*vertex_list;
  obj_vertex			*vert[4];
  float				r,g,b;			//primitives colour
  struct OBJ_3DPRIMITIVE	*next_ref;	//pointer to the next node
  //points to NULL if last in obj
  primitiveType		type;		//describes the type of the data held
  unsigned int		flags;		//holds details about normals/shiny surface etc.		
  //float scale;
  uint32 uv_id;
  uint32 id;
} obj_3dPrimitive;

typedef struct {
#define NO_VBO 0xffffffff
  GLuint vbo;
#define NO_IBO 0xffffffff
  GLuint ibo;
  uint32 num_prims;
  GLuint num_indices;
  uint32 num_vert_components;
  uint32 num_col_components;
  uint32 num_norm_components;
  uint32 stride;
} obj_vbo;

class obj_3dMesh {
 public:
  obj_3dPrimitive *p_prim;
  Eigen::Vector3d mid;
  obj_vertex min;
  obj_vertex max;
  uint32 num_uv_maps;
  uint32 *p_tex_ids;
  uint32 *p_tex_widths;
  uint32 *p_tex_heights;
  uint32 *p_tex_flags;
  uint8 **pp_tex_paths;
  uint8 mesh_path[PATH_LEN];
#define PRIMARY_TAG "primary"
#define WING_TAG "wing"
#define TAIL_TAG "tail"
#define FUELTANK_TAG "fueltank"
#define VICINITY_TAG "vicinity"
  uint8 tag[TAG_LEN];
  uint32 num_prims;

  //uint32 num_colliders;
  //obj_collider *p_colliders;

#define NO_VBO_GROUP 0xffffffff
#define NO_VBO_GROUP_EVER 0xfffffffe
  uint32 vbo_group;
  obj_vbo vbo;
  void *p_vert_start;
  void *p_vert_end;
  EIGEN_MAKE_ALIGNED_OPERATOR_NEW
};

typedef struct {
	// incident light source position and intensity
	float				x,y,z;
	float				intensity;
} obj_light_source;

typedef struct {
	unsigned int		index;				//current frame index
	unsigned int		speed;				//how fast should anim go
	unsigned int		last_time_index;	//holds the time the last frame was plotted
	obj_3dPrimitive		**frame;		//pointer to array of 3dPrim pointers
	unsigned int		flags;				//holds flag info
	//flags to cater for: once,loop,forward-backward,pause,playf,playb,stop(hide)
} obj_anim_data;

typedef struct OBJ_LIST_NODE {
	obj_3dPrimitive		*current;		//points to current frame/object;
	obj_plot_position	pos;			//location on map of object
	obj_anim_data		*anim;			//holds animation info;NULL if no animation
	struct OBJ_LIST_NODE *next_ref;			//link to successor
} obj_list_node;

//Funtion Prototypes
void	objRotX				(obj_vector *unit_vector_norm,float ax);
void	objRotY				(obj_vector *unit_vector_norm,float ay);
void	objRotZ				(obj_vector *unit_vector_norm,float az);

void	objSetCutOff		(float dist, float angle);


void	objSetPlotPos		(float x, float y, float z);
void	objSetPlotAttrib	(float x, float y, float z, float ax, float ay, float az);

void	objSetViewPos		(float x, float y, float z);
void	objSetViewAngle		(float ax, float ay, float az);
void	objSetPointOfView	(float x, float y, float z, float ax, float ay, float az);

void	objSetVertexNormal	(obj_vector unit_vector_norm,unsigned int flags);

void	objDelete			(obj_3dMesh **pp_mesh);
oError	objPlot				(obj_3dMesh *p_mesh, float32 alpha);
oError	vboPlot				(obj_vbo *p_vbo);
oError	objPlotToTex			(obj_3dMesh *p_mesh, float32 alpha, uint32 fbo, uint32 xSize, uint32 ySize, uint32 bgTex, uint32 boundPlane, uint32 top);
oError setupVBO(obj_3dMesh *p_meshes, uint32 num_meshes, obj_vbo *p_vbo);
  void setupRotation(float64 x,
		     float64 y,
		     float64 z,
		     Eigen::Quaternion<float64> &angle_quat,
		     Eigen::Vector3d &midPt, Eigen::Vector3d &rotOrig);
inline float32 max(float32 x, float32 y) {
  return x>y?x:y;
}

#endif
