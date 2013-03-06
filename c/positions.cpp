#include <math.h>
#include <stdio.h>
#include <Eigen/Geometry>
#include "positions.h"
#include "types.h"

Eigen::Quaternion<float32> NULL_ROT=Eigen::Quaternion<float32>(1.0, 0.0, 0.0, 0.0);
Quat result;

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

  Quat* getCorrection(PositionObject* p_object, 
					       float32 period) {
    //Quat result;
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
    return &result;
  }

  void delObj(PositionObject* p_obj) {
    if(p_obj==NULL) {
      printf("delObj. null position object\n");
    } else {
      delete p_obj;
    }
  }
}

PositionObject::PositionObject(): attDelta(NULL_ROT), 
				  lastKnownAtt(NULL_ROT),
				  nextAtt(NULL_ROT),
				  lastPeriod(0.0),
				  nextPeriodStart(0.0),
				  periodLen(0.0)
{
  static uint32 insts=0;
  this->inst=insts++;
 };

void PositionObject::nextInterval() {
  this->lastPeriod=this->nextPeriodStart;
  this->nextPeriodStart+=this->periodLen;
  this->lastKnownAtt=this->nextAtt;
  this->nextAtt=this->lastKnownAtt*this->attDelta;
}

void PositionObject::updateCorrection(Eigen::Quaternion<float32> att, float32 period) {
  this->periodLen=period;
  this->nextPeriodStart=period;
  this->attDelta=att*this->lastKnownAtt.inverse();
  this->nextAtt=att;
  
  this->nextInterval();
}

Eigen::Quaternion<float32> PositionObject::getCorrection(float32 period) {
  //printf("getCorrection %u w %f x %f y %f z %f\n", this->inst, result.w, result.x, result.y, result.z);
  float32 progress=fmod(((float32)period), this->lastPeriod);
  if(period>this->nextPeriodStart) {
    this->nextInterval();
  }
  return this->lastKnownAtt.slerp(progress, this->nextAtt);
}
