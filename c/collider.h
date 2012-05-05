#ifndef col_h
#define col_h

#include <stdio.h>

#include <Eigen/Geometry>
#include "rtu.h"
#include "types.h"

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
#define PRIMARY_FLAG 0x1
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
      if(lastResult==false) {
	return false;
      }
    default:
      return p_collider->numCols>colIdx+1;
    }
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
    if(*p_resCnt>=p_collider->numCols) {
      printf("hmmm incorrect p_resCnt, %p, %u, %u\n", p_resCnt, *p_resCnt, p_collider->numCols);
    }
    assert(p_resCnt && *p_resCnt<p_collider->numCols);
    assert(colIdx<p_collider->numCols);
    lastResult=pCollided;
    if(pCollided) {
      if(p_resIndices && p_resCnt) { 
	if(!p_resIndices[colIdx]) {
	  p_resIndices[colIdx]=true;
	  p_res[(*p_resCnt)++]=p_collider->p_orig->p_flags[colIdx];
	  //printf("result %u: %u\n", (*p_resCnt)-1, p_res[(*p_resCnt)-1]);
	}
      } else {
	lastResult=false;
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
};

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
#endif
