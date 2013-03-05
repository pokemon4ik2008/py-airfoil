#ifndef euclid_h
#define euclid_h

#include <stdio.h>
#include <Eigen/Geometry>
#include "rtu.h"
#include "types.h"

typedef struct {
  float32 w;
  float32 x;
  float32 y;
  float32 z;
} Quat;

class PositionObject {
 public:
  PositionObject();
  void updateCorrection(Eigen::Quaternion<float32> att, uint32 period);
  Eigen::Quaternion<float32> getCorrection(uint32 period);
 private:
  float32 lastPeriod;
  Eigen::Quaternion<float32> lastKnownAtt;
  Eigen::Quaternion<float32> nextAtt;
};

#endif
