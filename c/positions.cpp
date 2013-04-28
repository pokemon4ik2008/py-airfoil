#include <iostream>
#include <math.h>
#include <stdio.h>
#include <Eigen/Geometry>
#include "positions.h"
#include "types.h"

using namespace std;

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

PositionObject::PositionObject(): correction(NULL_ROT), 
				  attDelta(NULL_ROT),
				  lastKnownAtt(NULL_ROT),
				  nextAtt(NULL_ROT),
				  estimated(NULL_ROT),
				  lastEst(NULL_ROT),
				  lastPeriod(1.0),
				  nextPeriodStart(1.0),
				  periodLen(1.0),
				  initialised(false)
{
  static uint32 insts=0;
  this->inst=insts++;
 };

void PositionObject::updateCorrection(Eigen::Quaternion<float32> att, float32 period) {
  //we need:
  //assumed att -- this->estimated
  //last att -- this->lastKnownAtt
  //current att -- att

  att.normalize();
  this->periodLen=period;
  this->nextPeriodStart=period;
  this->nextAtt=att;
  if(!this->initialised){
    this->initialised=true;
    this->estimated=att;
  }
  this->correction=att*(this->estimated.inverse());
 
  this->lastPeriod=this->nextPeriodStart;
  this->nextPeriodStart+=this->periodLen;
  this->nextInterval();
}

void PositionObject::nextInterval() {
  this->attDelta=this->nextAtt*this->lastKnownAtt.inverse();
  //this->attDelta=this->lastKnownAtt.slerp(0.75, this->nextAtt)*this->lastKnownAtt.inverse();
  this->lastEst=this->estimated;

  this->lastKnownAtt=this->nextAtt;
  this->nextAtt=this->lastKnownAtt*this->attDelta;
}

Eigen::Quaternion<float32> PositionObject::getCorrection(float32 period) {
  float32 progress=period / this->lastPeriod;
  while(progress>1.0) {
    this->nextAtt=this->nextAtt*this->attDelta;
    this->lastEst=this->estimated;

    period-=this->lastPeriod;
    progress=period/this->lastPeriod;
  }

  this->estimated=this->lastEst.slerp(progress, this->nextAtt).normalized();
  return this->estimated;
}
