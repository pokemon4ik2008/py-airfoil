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
#define OBJ_USE_TEXTURE	128

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
#include <GL/gl.h>
#include <GL/glu.h>

typedef enum {ok, noMemory,invalidPrimitive,emptyObject,nofile} oError;
typedef unsigned char ubyte;
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
#define PATH_MATCH "%256s"
typedef char uint8;
typedef unsigned int uint32;

//uint8** uvMap2Texture;
//uint32* uvMap2Id;

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
  float				x,y,z;
  float				u,v;
  obj_vector			norm;		//vertex normal
  ubyte				shared;		//holds number of primitives sharing this vertex
  ubyte reserved[3];
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
	float scale;
  uint32 uv_id;
} obj_3dPrimitive;

typedef struct {
  obj_3dPrimitive *p_prim;
  obj_vertex mid;
  uint32 num_uv_maps;
  uint32 *p_tex_ids;
  uint8 **pp_tex_paths;
  uint8 mesh_path[PATH_LEN];
  void *p_vert_start;
  void *p_vert_end;
} obj_3dMesh;

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
oError	objCreate			(obj_3dMesh **obj, char *fname, float obj_scaler, unsigned int flags);

void	objDelete			(obj_3dMesh **pp_mesh);
oError	objPlot				(obj_3dMesh *p_mesh);

#endif
