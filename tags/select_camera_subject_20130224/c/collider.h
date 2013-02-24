#ifndef col_h
#define col_h

#include <stdio.h>

#include <Eigen/Geometry>
#include "rtu.h"
#include "types.h"
#ifdef OPEN_GL
#include <GL/glew.h>
#include <GL/glu.h>
#else
#include "nogl.h"
#endif

#define PATH_LEN 256
#define TAG_LEN 32

typedef enum {line,tri,quad,empty} primitiveType;

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

typedef struct {
	float				x,y,z;
	float				ax,ay,az;
} obj_plot_position;

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

class obj_sphere {
 public:
  Eigen::Vector3d mid;
  float64 rad;
  EIGEN_MAKE_ALIGNED_OPERATOR_NEW
    };

class obj_collider {
 public: 
  uint32 numCols;
  obj_sphere *p_sphere;
#define PRIMARY_COL 0x1
#define WING_COL 0x2
#define TAIL_COL 0x3
#define FUELTANK_COL 0x4
#define VICINITY_COL 0x5
  uint32 *p_flags;
  float64 *p_radSquares;
  //Eigen::Vector3d *p_mid;
  //float64 rad;
  
  EIGEN_MAKE_ALIGNED_OPERATOR_NEW
};

class obj_transformedCollider {
 public:
  Eigen::Quaternion<float64> att;
  Eigen::Vector3d pos;
  uint32 numCols;
  uint32 *p_midIters;
  obj_sphere *p_sphere;
  //Eigen::Vector3d *p_lastMid;

  uint32 iteration;
  obj_collider *p_orig;
  EIGEN_MAKE_ALIGNED_OPERATOR_NEW
};

inline Eigen::Vector3d rotVert(const Eigen::Vector3d &v, const Eigen::Quaternion<float64> &att) {
  return att*SETUP_ROT*v;
}
class ColliderIt {
public:
  ColliderIt(const obj_transformedCollider *p_col, uint32 *p_numRes, uint32 results[]) {
    p_collider=p_col;
    p_resCnt=p_numRes;
    //p_resCnt=&tmpCnt;
    p_res=results;
    p_resIndices=new bool[p_collider->numCols]();
    if(!p_resIndices) {
      printf("failed to alloc result record");
    }
    reset();
  }

  ~ColliderIt() {
    if(p_resIndices) {
      delete [] p_resIndices;
    }
  }

  bool hasNext() {
    switch(colIdx) {
    case unstarted:
      return p_collider->numCols>0;
    case 0:
      if(!allowDeep && lastResult==false) {
	return false;
      }
    default:
      return p_collider->numCols>colIdx+1;
    }
  }

  void allowDeepInspection() {
    allowDeep=true;
  }

  uint32 next() {
    colIdx++;
    assert(colIdx<p_collider->numCols);
    if(p_collider->iteration!=p_collider->p_midIters[colIdx]) {
      p_collider->p_sphere[colIdx].mid=p_collider->pos+rotVert(p_collider->p_orig->p_sphere[colIdx].mid, p_collider->att);
      //p_collider->p_sphere[colIdx].rad=p_collider->p_orig->p_sphere[colIdx].rad;
      p_collider->p_midIters[colIdx]=p_collider->iteration;
    }
    return colIdx;
  }

  bool result(bool pCollided) {
    assert(p_resCnt);
    assert(colIdx<p_collider->numCols);
    if(pCollided) {
      if(p_resIndices && p_resCnt) { 
	lastResult=true;
	if(!p_resIndices[colIdx]) {
	  assert(*p_resCnt<p_collider->numCols);
	  p_resIndices[colIdx]=true;
	  p_res[(*p_resCnt)++]=p_collider->p_orig->p_flags[colIdx];
	  //printf("result %u: %u\n", (*p_resCnt)-1, p_res[(*p_resCnt)-1]);
	}
      }
    }
    return pCollided;
  }

  void reset() {
    if(!p_resCnt) {
      printf("p_numRes is null pointer. results will not be recorded");
    } else {
      *p_resCnt=0;
    }
    allowDeep=false;
    colIdx=unstarted;
    lastResult=false;
  }

  bool collided() {
    if(p_resCnt) {
      if(p_collider->numCols>1) {
	return (*p_resCnt)>1;
      } else {
	return *p_resCnt>0;
      }
    } else {
      return false;
    }
  }

private:
  static const uint32 unstarted=0xffffffff;
  const obj_transformedCollider *p_collider;
  uint32 tmpCnt;
  uint32 *p_resCnt;
  uint32 colIdx;
  bool lastResult;
  uint32 *p_res;
  bool *p_resIndices;
  bool allowDeep;
};

obj_3dMesh** col_getMeshes();
uint32 col_numMeshes();

oError	col_objCreate(obj_3dMesh **obj, char *fname, float obj_scaler, unsigned int flags, uint32 vbo_group);
void col_deleteTransCols(obj_transformedCollider *p_col);
void *col_allocTransCols(obj_collider *p_origCol);
void *col_allocColliders(uint32 num_colliders);
void col_deleteColliders(obj_collider *p_cols);
void col_identifyBigCollider(obj_collider *p_cols);
void col_rotColliders(obj_collider *p_cols, obj_transformedCollider *p_transCol, uint32 iteration, float64 xPos, float64 yPos, float64 zPos, float64 wAtt, float64 xAtt, float64 yAtt, float64 zAtt);
void col_updateColliders(obj_transformedCollider *p_transCol,
			 uint32 iteration,
			 float64 xPos, float64 yPos, float64 zPos,
			 float64 wAtt, float64 xAtt, float64 yAtt, float64 zAtt);

bool col_CheckPoint(const obj_transformedCollider *p_col, 
		    Eigen::Vector3d oldPoint, 
		    Eigen::Vector3d point, 
		    uint32 *p_resSize, uint32 results[]);
bool col_CheckCollider(const obj_transformedCollider *p_col, 
		       const obj_transformedCollider *p_other,
		       uint32 *p_mySize, uint32 myResults[],
		       uint32 *p_oSize, uint32 oResults[]);
inline bool col_PtCollisionCheck(const obj_transformedCollider *p_col, uint32 idx, const Eigen::Vector3d &oldPoint, const Eigen::Vector3d &point);
inline bool col_ColCollisionCheck(const obj_transformedCollider *p_me, uint32 meIdx, 
				  const obj_transformedCollider *p_other, uint32 oIdx);
void col_objDelete(obj_3dMesh **pp_mesh);
const obj_plot_position & col_getPos();
void col_setPosition(float plotPos[]);

#endif
