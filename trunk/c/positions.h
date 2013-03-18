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
  void updateCorrection(Eigen::Quaternion<float32> att, float32 period);
  Eigen::Quaternion<float32> getCorrection(float32 period);
 private:
  float32 lastPeriod;
  float32 nextPeriodStart;
  float32 periodLen;
  bool initialised;
  Eigen::Quaternion<float32> lastKnownAtt;
  Eigen::Quaternion<float32> nextAtt;
  Eigen::Quaternion<float32> correction;
  Eigen::Quaternion<float32> attDelta;
  Eigen::Quaternion<float32> estimated;
  Eigen::Quaternion<float32> lastEst;
  void nextInterval();
  uint32 inst;
};

#endif
