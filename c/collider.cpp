#include <stdio.h>
#include "collider.h"
#include "types.h"

  void col_deleteTransCols(obj_transformedCollider *p_col) {
    if(p_col) {
      if(p_col->p_sphere) {
	printf("col_deleteTransCols p_sphere %p\n", p_col->p_sphere);
	delete [] p_col->p_sphere;
	p_col->p_sphere=NULL;
      }
      //if(p_col->p_lastMid) {
      //delete [] p_col->p_lastMid;
      //p_col->p_lastMid=NULL;
      //}
      if(p_col->p_midIters) {
	printf("col_deleteTransCols p_midIters %p\n", p_col->p_midIters);
	delete [] p_col->p_midIters;
	p_col->p_midIters=NULL;
      }
      printf("col_deleteTransCols p_col %p\n", p_col);
      delete p_col;
      printf("col_deleteTransCols end\n");
      p_col=NULL;
    }
  }

  void *col_allocTransCols(obj_collider *p_origCol) {
    obj_transformedCollider *p_col=new obj_transformedCollider;
    printf("col_allocTransCols. alloced transcol %p\n", p_col);
    if(p_col) {
      uint32 num_colliders;
      p_col->p_sphere=NULL;
      p_col->p_midIters=NULL;
      if(p_origCol && p_origCol->numCols) {
	//p_col->p_mid=new Eigen::Vector3d[num_colliders];
	p_col->p_midIters=new uint32[p_origCol->numCols];
	printf("col_allocTransCols. alloced %u iters %p\n", p_origCol->numCols, p_col->p_midIters);
	p_col->p_sphere=new obj_sphere[p_origCol->numCols];
	printf("col_allocTransCols. alloced %u spheres %p\n", p_origCol->numCols, p_col->p_sphere);
	if(p_col->p_midIters && p_col->p_sphere) {
	  num_colliders=p_origCol->numCols;
	  
	} else {
	  if(p_col->p_midIters) {
	    delete [] p_col->p_midIters;
	    p_col->p_midIters=NULL;
	  }
	  if(p_col->p_sphere) {
	    delete [] p_col->p_sphere;
	    p_col->p_sphere=NULL;
	  }
	}
      }
      p_col->numCols=num_colliders;
      p_col->iteration=-1;
      p_col->p_orig=p_origCol;
      return p_col;
    } else {
      printf("allocTransCols failed to alloc collider\n");
      return NULL;
    }
  }

  void *col_allocColliders(uint32 num_colliders) {
    obj_collider *p_cols=new obj_collider;
    if(!p_cols) {
      printf("allocColliders. failed to alloc collider\n");
      return NULL;
    }
    p_cols->p_sphere=new obj_sphere[num_colliders];
    p_cols->p_flags=new uint32[num_colliders];
    p_cols->p_radSquares=new float64[num_colliders];
    if(p_cols->p_sphere && p_cols->p_flags && p_cols->p_radSquares) {
      p_cols->numCols=num_colliders;
    } else {
      printf("allocColliders. failed to alloc sub-colliders\n");
      if(p_cols->p_sphere) {
	delete [] p_cols->p_sphere;
	p_cols->p_sphere=NULL;
      }
      if(p_cols->p_flags) {
	delete [] p_cols->p_flags;
	p_cols->p_flags=NULL;
      }
      if(p_cols->p_radSquares) {
	delete [] p_cols->p_radSquares;
	p_cols->p_radSquares=NULL;
      }
      p_cols->numCols=0;
    }
    return p_cols;
  }

  void col_deleteColliders(obj_collider *p_cols) {
    if(!p_cols) {
      return;
    }
    if(p_cols->p_sphere) {
      delete [] p_cols->p_sphere;
    }
    if(p_cols->p_flags) {
      delete [] p_cols->p_flags;
    }
    if(p_cols->p_radSquares) {
      delete [] p_cols->p_radSquares;
    }

    delete p_cols;
    p_cols=NULL;
  }

  void col_identifyBigCollider(obj_collider *p_cols) {
    if(!p_cols) {
      return;
    }
    int num_cols=p_cols->numCols;
    if(num_cols<2) {
      return;
    }

    obj_sphere tmp;
    uint32 flags;
    float64 radSquare;

    uint32 largest=0;
    printf("col 0: %f\n", p_cols->p_sphere[0].rad);
    for(uint32 i=1; i<num_cols; i++) {
      printf("col %u: %f\n", i, p_cols->p_sphere[i].rad);
      if(p_cols->p_sphere[i].rad>p_cols->p_sphere[largest].rad) {
	largest=i;
      }
    }
    if(largest!=0) {
      tmp=p_cols->p_sphere[largest];
      flags=p_cols->p_flags[largest];
      radSquare=p_cols->p_radSquares[largest];

      p_cols->p_sphere[largest]=p_cols->p_sphere[0];
      p_cols->p_flags[largest]=p_cols->p_flags[0];
      p_cols->p_radSquares[largest]=p_cols->p_radSquares[0];

      p_cols->p_sphere[0]=tmp;
      p_cols->p_flags[0]=flags;
      p_cols->p_radSquares[0]=radSquare;
    }
  }

inline bool col_PtCollisionCheck(const obj_transformedCollider *p_col, uint32 idx, const Eigen::Vector3d &oldPoint, const Eigen::Vector3d &point) {
  float64 denom=(point-oldPoint).squaredNorm();
  Eigen::Vector3d pPos=p_col->p_sphere[idx].mid;
  float64 t=-(((oldPoint-pPos).dot(point-oldPoint))/denom);
  
  //see http://mathworld.wolfram.com/Point-LineDistance3-Dimensional.html for explanation of how we calculated distance to line
  //we require that .5<=t<=1.5 as the time index of p_sphere[idx]->mid corresponds to where t=1.0 (the middle of this interval)
  //This is obviously a projected range.
  //return 0.50<=t && t<=1.50 && ((point-oldPoint).cross(oldPoint-p_col->p_sphere[idx].mid).squaredNorm()/denom)<=p_col->p_orig->p_radSquares[idx];
  float64 dist=((point-oldPoint).cross(oldPoint-pPos).squaredNorm()/denom);
  bool result=0.50<=t && t<=1.50 && dist<=p_col->p_orig->p_radSquares[idx];
  if(result) {
    //printf("hit. idx: %u dist: %f t: %f \t plane %f %f %f oldBull %f %f %f bull %f %f %f\n", idx, dist, t, pPos.x(), pPos.y(), pPos.z(), oldPoint.x(), oldPoint.y(), oldPoint.z(), point.x(), point.y(), point.z());
  } else {
    //printf("miss. idx: %u dist %f t: %f \t plane %f %f %f oldBull %f %f %f bull %f %f %f\n", idx, dist, t, pPos.x(), pPos.y(), pPos.z(), oldPoint.x(), oldPoint.y(), oldPoint.z(), point.x(), point.y(), point.z());
  }
  return result;
}

inline bool col_ColCollisionCheck(const obj_transformedCollider *p_me, uint32 meIdx, 
			   const obj_transformedCollider *p_other, uint32 oIdx) {
  float64 sum=(p_me->p_orig->p_sphere[meIdx].rad+p_other->p_orig->p_sphere[oIdx].rad);
  float64 sumSquare=sum*sum;
  float64 dist=(p_me->p_sphere[meIdx].mid-p_other->p_sphere[oIdx].mid).squaredNorm();
  //printf("dist: %f rad1: %f rad2: %f sumsq: %f\n", dist, p_me->p_sphere[meIdx].rad, p_other->p_sphere[oIdx].rad, sumSquare);
  return dist<=sumSquare;
}

bool col_CheckPoint(const obj_transformedCollider *p_col, 
		    const Eigen::Vector3d oldPoint, 
		    const Eigen::Vector3d point, 
		    uint32 *p_resSize, uint32 results[]) {
  ColliderIt it(p_col, p_resSize, results);
  while(it.hasNext()) {
    it.result(col_PtCollisionCheck(p_col, it.next(), oldPoint, point));
  }
  return it.collided();
}

bool col_CheckCollider(const obj_transformedCollider *p_col, 
		       const obj_transformedCollider *p_other,
		       uint32 *p_mySize, uint32 myResults[],
		       uint32 *p_oSize, uint32 oResults[]) {
  ColliderIt it(p_col, p_mySize, myResults);
  ColliderIt oIt(p_other, p_oSize, oResults);
  while(it.hasNext()) {
    uint32 itIdx=it.next();
    while(oIt.hasNext()) {
      oIt.result(it.result(col_ColCollisionCheck(p_col, itIdx, p_other, oIt.next())));
    }
    oIt.reset();
  }
  //if one has collided so has the other (as both collided with each other)
  return it.collided();
}

//returns number of collided colliders (n), results has n valid elements from idx 0 to n-1
//results[idx], where n>idx is the tag flag of a collider that has collided
//results[0], where n>0 is the tag flag of big collider
/*
uint32 col_CollisionCheck(obj_transformedCollider *p_transCol,
			  //bool (*colCheck)(obj_sphere *p_sphere),
			  uint32 *p_resCnt, uint32[] results) {
  if(!p_transCol || !p_transCol->numCols) {
    return 0;
  }
  ColliderIt it(p_transCol, p_resSize, results);
  while(it.hasNext()) {
    uint32 colIdx=it.next();
    it.result(checkSimpleColl(p_col, it.next(), point))
  }
  return it.collided();
*/
  /*
  uint32 resultIdx=0;
  if(p_transCol->iteration!=p_transCol->p_midIters[0]) {
    p_transCol->p_sphere[0].mid=p_transCol->pos+rotVert(p_transCol->p_orig->p_sphere[0].mid, p_transCol->att);
    p_transCol->p_midIters[0]=p_transCol->iteration;
  }
  if(colCheck(&p_transCol->p_sphere[0])) {
    results[resultIdx++]=p_transCol->p_orig->p_flags[0];
    if(p_transCol->numCols>1) {
      for(int i=1; i<p_transCol->numCols; i++) {
	if(p_transCol->iteration!=p_transCol->p_midIters[i]) {
	  p_transCol->p_sphere[i].mid=p_transCol->pos+rotVert(p_transCol->p_orig->p_sphere[i].mid, p_transCol->att);
	  p_transCol->p_midIters[i]=p_transCol->iteration;
	}
	if(colCheck(*p_transCol->p_sphere[i])) {
	  results[resultIdx++]=p_transCol->p_orig->p_flags[i];
	  break;
	}
      }
    }
  }
  return resultIdx;
  */
//}

void col_updateColliders(obj_transformedCollider *p_transCol,
			 uint32 iteration,
			 float64 xPos, float64 yPos, float64 zPos,
			 float64 wAtt, float64 xAtt, float64 yAtt, float64 zAtt) {
  using namespace Eigen;
  if(!p_transCol) {
    return;
  }
  obj_collider *p_cols = p_transCol->p_orig;
  p_transCol->att=Quaternion<float64>(wAtt, xAtt, yAtt, zAtt);
  p_transCol->pos=Vector3d(xPos, yPos, zPos);
  p_transCol->iteration=iteration;

  if(p_transCol->numCols) {
    p_transCol->p_sphere[0].mid=p_transCol->pos+rotVert(p_cols->p_sphere[0].mid, p_transCol->att);
    //p_transCol->p_sphere[0].rad=p_cols->p_sphere[0].rad;
    //Eigen::Vector3d pos=p_transCol->pos;
    //printf("col_updateColliders %f %f %f\n", pos.x(), pos.y(), pos.z());
    p_transCol->p_midIters[0]=iteration;
  }
}
