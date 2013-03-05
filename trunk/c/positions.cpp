#include <stdio.h>
#include <Eigen/Geometry>
#include "positions.h"
#include "types.h"

extern "C" 
{
  void updateCorrection(PositionObject* p_object, Quat* p_att, float32 period) {
    if(p_object==NULL) {
      printf("updateCorrection. null position object\n");
    } else {
      p_object->updateCorrection(Eigen::Quaternion<float32>(p_att->w, p_att->x, p_att->y, p_att->z), period);
    }
  }

  void* newObj() {
    return new PositionObject();
  }

  Quat getCorrection(PositionObject* p_object, 
					       float32 period) {
    Quat result;
    if(p_object==NULL) {
      printf("getCorrection. null position object\n");
      result.w=0;
      result.x=0;
      result.y=0;
      result.z=0;
    } else {
      Eigen::Quaternion<float32> correction=p_object->getCorrection(period);
      result.w=correction.w();
      result.x=correction.x();
      result.y=correction.y();
      result.z=correction.z();
    }
    return result;
  }

  void delObj(PositionObject* p_obj) {
    if(p_obj==NULL) {
      printf("delObj. null position object\n");
    } else {
      delete p_obj;
    }
  }
}

PositionObject::PositionObject(): lastKnownAtt(1.0, 0.0, 0.0, 0.0),
    nextAtt(1.0, 0.0, 0.0, 0.0) {
 };

void PositionObject::updateCorrection(Eigen::Quaternion<float32> att, float32 period) {
  Eigen::Quaternion<float32> attDelta=att*this->lastKnownAtt.inverse();
  this->nextAtt=att*attDelta;
  this->lastPeriod=period;
  this->lastKnownAtt=att;
}

Eigen::Quaternion<float32> PositionObject::getCorrection(float32 period) {
  float32 progress=((float32)period)/(this->lastPeriod);
  if(progress<=1) {
    return this->lastKnownAtt.slerp(progress, this->nextAtt);
  }
}
