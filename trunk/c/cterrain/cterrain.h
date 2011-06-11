#ifndef cterrain_h
#define cterrain_h

#ifdef WIN32
#include <windows.h>
#endif

#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>
#include <GL/gl.h>
#include <GL/glu.h>

#define FOG_GREY (0.8f)
#define terrain_map(x,z) (*(terrain+(z)*terrain_max_z+(x)))		//macro for accessing the terrain memory by x,z coord
#define alt_var_const (cut_off_max/max_altitude) //rate at which view triangle dist increases with altitude or x angle rotation
#define ambient_light .2f
#define cut_off_max (200)	//absolute max dist of view triangle
#define max_altitude 100.0
#define lod_dist 70.0			//the thickness of the level of detail bands (should only be about 2 bands) btw, i think this is exponential ie 2^x or something similar


#define PI	(22.0f/7.0f)
#define sqr(x) ((x)*(x))
#define deg_to_rad (PI/180.0f)
#define rad_to_deg (180.0f/PI)
#define small_number -32627.0f



#ifdef WIN32 
#define DLL_EXPORT _declspec(dllexport) 
#else
#define DLL_EXPORT 
#endif

typedef unsigned char ubyte;
typedef ubyte* byte_ptr;

struct point_of_view {
	float x,y,z;		//position
	float ax,ay,az;	//angle
};


struct gl_col {
	// these are used to store gl colours
	// white is 1.0f,1.0f,1.0f
	float r,g,b;
};

struct vector {
	int x,y,z;
}; 

struct vector_dec {
	//high precision vector
	float x,y,z;
};


struct light_source {
	// incident light source position and intensity
	int x,y,z;
	float intensity;
	float ambient;
};

struct terrain_mesh_point {
	short plotted;	//dynamic: has this quad been already plotted
	double dist;	//dynamic: dist of vertex from current pov
	unsigned char y;			//y value as loaded from map definition file
	float intensity;//light intensity at current vertex. calculated on map load
	gl_col col;		//colour of vertex, calculated on map load, depends on intensity and y
	short alt_y;	//alternative y value used during variable detail level calculations to get rid of gaps in map
};

typedef struct {
	void *map;
	void *d2map;
	int size;
	float dim;
	float scale;
	int texid;
	int width;
	int height;
	short *hfield;
	unsigned char* texture;
} terrain_tile;

float getAngleForXY(float x, float y);
int preloadTerrain(char *fname);
int load_hm_colour_ref(char *fname);
int terLoadTerrain(short int*hfield,int size, 
				   float input_map_expansion_const,float input_y_scale); 
void terPrecalc_vertex_colours();
float terMap_col(terrain_mesh_point &terrain, char col);
void terPrecalc_vertex_intensities();
void terDrawLandscape(point_of_view &input_pov,float aspect,short detail_levels);
void terSort_view_triangle(vector point[]);
void terQsort_view_triangle(vector point[]);
int terQsort_vt_compare(const void *point_1_ptr, const void* point_2_ptr);
void terCalc_view_triangle(int topz,	int botz,
						float leftx,float &rightx,
						float leftm,float &rightm,
						float view_angle,point_of_view &pov,
						int detail,short min_detail_level);
float terAdd_fog(float col,float backg_col,double dist);
void terCreate_terrain_quad(int x,int z,int detail);
void terDeleteAll();

#endif
