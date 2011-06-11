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

typedef struct {
	float				x,y,z;
	float				ax,ay,az;
} obj_plot_position;

typedef struct {
	float				x,y,z;
} obj_vector;

typedef struct {
	float				x,y,z;
	float				r,g,b;		//now redundant..instead use colour in primitive
	obj_vector			norm;		//vertex normal
	ubyte				shared;		//holds number of primitives sharing this vertex
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
} obj_3dPrimitive;

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
void	objSetLight			(float x, float y,float z, float intensity);

void	objSetLoadOrigin	(float x, float y, float z);
void	objSetLoadAngle		(float ax, float ay, float az);

void	objSetPlotPos		(float x, float y, float z);
void	objSetPlotAngle		(float ax, float ay, float az);
void	objSetPlotAttrib	(float x, float y, float z, float ax, float ay, float az);

void	objSetViewPos		(float x, float y, float z);
void	objSetViewAngle		(float ax, float ay, float az);
void	objSetPointOfView	(float x, float y, float z, float ax, float ay, float az);

void	objSetVertexNormal	(obj_vector unit_vector_norm,unsigned int flags);
float	objLight			(obj_vector unit_vector_norm,unsigned int flags);
oError	objCreate			(obj_3dPrimitive **obj, char *fname, float obj_scaler, unsigned int flags);
//oError	objCloud			(obj_3dPrimitive **obj, char *fname, float obj_scaler, unsigned int flags);

void	objDelete			(obj_3dPrimitive **obj);
oError	objPlot				(obj_3dPrimitive *obj);
oError	objCreateList		(obj_list_node **list);
oError	objDeleteList		(obj_list_node **list);
obj_list_node *objAddtoList		(obj_list_node *list, obj_3dPrimitive *obj);
oError	objPlotList			(obj_list_node *list,int *temp); 
oError	objModifyListMember (obj_list_node *list);

void	objsTest			(obj_3dPrimitive *obj,obj_plot_position *pos,int browseinc2);

#endif