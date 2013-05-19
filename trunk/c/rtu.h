#ifndef rtu_h
#define rtu_h

#include <Eigen/Geometry>
#include "types.h"

#define DIM(a) (sizeof(a)/sizeof(a[0]))
#define MIN(a,b) (a>b?b:a)
#define MAX(a,b) (a<b?b:a)

static Eigen::Quaternion<float32> SETUP_ROT(0.5, -0.5, 0.5, 0.5);

inline void memZero(void *p_mem, uint32 bytes) {
    for(uint32 *p_ptr=(uint32 *)p_mem, *p_end=(uint32 *)(((uint8 *)p_mem)+bytes); p_ptr<p_end; p_ptr++) {
    *p_ptr=0;
  }
}

#endif
