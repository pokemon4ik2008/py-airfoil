#include <stdio.h>
#include "collider.h"
#include "objects.h"
#include "types.h"

obj_plot_position pos={0};

obj_3dMesh *p_meshes[128];
uint32 num_meshes=0;
obj_plot_position origin_offset={0};
uint8 match_mesh[]="data/models/cockpit/E_Prop.csv";

extern "C" {
  DLL_EXPORT void deleteColliders(obj_collider *p_cols) {
    col_deleteColliders(p_cols);
  }

  DLL_EXPORT void *load(char *filename, float scale, uint32 vbo_group)
  {
    oError err = ok;		
    unsigned int objectflags=0;
    obj_3dMesh *obj = NULL;
    objectflags|=OBJ_NORMAL_POSITIVE;
    err = col_objCreate(&obj, filename, scale, objectflags, vbo_group);
		
    if (err != ok)
      {
	printf("ERROR: when loading object: %i\n", err);
      }
    return obj;
  }

  DLL_EXPORT uint8* getMeshPath(void *p_meshToPlot)
  {
    obj_3dMesh *p_mesh=static_cast<obj_3dMesh *>(p_meshToPlot);
    return p_mesh->mesh_path;
  }

  DLL_EXPORT void *allocTransCols(obj_collider *p_origCol) {
    return col_allocTransCols(p_origCol);
  }

  DLL_EXPORT void *allocColliders(uint32 num_colliders) {
    return col_allocColliders(num_colliders);
  }

  DLL_EXPORT void identifyBigCollider(obj_collider *p_cols) {
    col_identifyBigCollider(p_cols);
  }
  
  DLL_EXPORT void updateColliders(obj_transformedCollider *p_transCol, uint32 iteration, float64 xPos, float64 yPos, float64 zPos, float64 wAtt, float64 xAtt, float64 yAtt, float64 zAtt) {
    col_updateColliders(p_transCol, iteration, xPos, yPos, zPos, wAtt, xAtt, yAtt, zAtt);
  }

DLL_EXPORT bool checkCollisionPoint(const obj_transformedCollider *p_cols,
				    float64 oldX, float64 oldY, float64 oldZ,
				    float64 x, float64 y, float64 z,
				    uint32 *p_resCnt, uint32 results[]) {
  if(!p_cols || !p_cols->numCols) {
    return false;
  }
  return col_CheckPoint(p_cols, Eigen::Vector3d(oldX, oldY, oldZ), Eigen::Vector3d(x,y,z), p_resCnt, results);
}

  DLL_EXPORT bool checkCollisionCol(const obj_transformedCollider *p_cols,
				    const obj_transformedCollider *p_oCols,
				    uint32 *p_resCnt, uint32 results[],
				    uint32 *p_oResCnt, uint32 oResults[]) {
    if(!p_cols || !p_cols->numCols || !p_oCols || !p_oCols->numCols) {
      return false;
    }
    bool res=col_CheckCollider(p_cols, p_oCols, p_resCnt, results, p_oResCnt, oResults);
    return res;
  }

  DLL_EXPORT void deleteTransCols(obj_transformedCollider *p_col) {
    col_deleteTransCols(p_col);
  }

	DLL_EXPORT void setPosition(float plotPos[])
	{
	  pos.x=plotPos[0];
	  pos.y=plotPos[1];
	  pos.z=plotPos[2];
	}

  DLL_EXPORT uint32 loadCollider(obj_collider *p_cols, uint32 idx, char *filename, float scale) {
    if(!p_cols) {
      printf("loadCollider. not allocated\n");
      return noMemory;
    }
    if(idx>=p_cols->numCols) {
      printf("loadCollider. index %u to unallocated sub-collider out of %u\n", idx, p_cols->numCols);
      return noMemory;
    }
    oError err = ok;		
    unsigned int objectflags=0;
    obj_3dMesh *p_obj = NULL;
    objectflags|=OBJ_NORMAL_POSITIVE;
    err = col_objCreate(&p_obj, filename, scale, objectflags, NO_VBO_GROUP_EVER);
    if (err != ok) {
      printf("ERROR: when loading object: %i\n", err);
      return err;
    }
    p_cols->p_sphere[idx].mid=p_obj->mid;
    float64 rad=MAX(MAX(p_obj->max.x-p_obj->min.x, p_obj->max.y-p_obj->min.y),
 p_obj->max.z-p_obj->min.z)/2;
    p_cols->p_sphere[idx].rad=rad;
    p_cols->p_radSquares[idx]=rad*rad;
    p_cols->p_flags[idx]=0;
    if(strcmp(PRIMARY_TAG, p_obj->tag)==0) {
      p_cols->p_flags[idx]=PRIMARY_COL;
      printf("loadCollider. primary tag at %u\n", idx);
    }
    if(strcmp(WING_TAG, p_obj->tag)==0) {
      p_cols->p_flags[idx]=WING_COL;
      printf("loadCollider. wing tag at %u\n", idx);
    }
    if(strcmp(TAIL_TAG, p_obj->tag)==0) {
      p_cols->p_flags[idx]=TAIL_COL;
      printf("loadCollider. tail tag at %u\n", idx);
    }
    if(strcmp(FUELTANK_TAG, p_obj->tag)==0) {
      p_cols->p_flags[idx]=FUELTANK_COL;
      printf("loadCollider. fueltank tag at %u\n", idx);
    }
    if(strcmp(VICINITY_TAG, p_obj->tag)==0) {
      p_cols->p_flags[idx]=VICINITY_COL;
      printf("loadCollider. vicinity tag at %u\n", idx);
    }
    col_objDelete(&p_obj);
    return ok;
  }
  
}

void col_setPosition(float plotPos[])
{
  pos.x=plotPos[0];
  pos.y=plotPos[1];
  pos.z=plotPos[2];
}

obj_3dMesh** col_getMeshes() {
  return p_meshes;
}

uint32 col_numMeshes() {
  return num_meshes;
}

const obj_plot_position& col_getPos() {
  return pos;
}

void checkRange(obj_3dMesh *p_mesh, void *p_addr, bool within) {
  if(within) {
    if(p_addr<p_mesh->p_vert_start) {
      printf("checkRange too low 0x%p start 0x%p end 0x%p\n", p_addr, p_mesh->p_vert_start, p_mesh->p_vert_end);
      assert(false);
    }
    if(p_addr>=p_mesh->p_vert_end) {
      printf("checkRange too low 0x%p start 0x%p end 0x%p\n", p_addr, p_mesh->p_vert_start, p_mesh->p_vert_end);
      assert(false);
    }
  } else {
    if(p_addr>=p_mesh->p_vert_start && p_addr<p_mesh->p_vert_end) {
      printf("within range 0x%p start 0x%p end 0x%p\n", p_addr, p_mesh->p_vert_start, p_mesh->p_vert_end);
      assert(false);
    }
  }
}

void checkRange(obj_3dMesh *p_mesh, void *p_addr) {
  checkRange(p_mesh, p_addr, true);
}

void checkAllRanges(void *p_addr) {
  for(uint32 i=0; i<col_numMeshes(); i++) {
    checkRange(col_getMeshes()[i], p_addr, false);
  }
}

//Pre: call to objSetLoadPos.. angle not yet supported
oError col_objCreate(obj_3dMesh **pp_mesh, 
					char *fname,float obj_scaler
		 , unsigned int flags, uint32 vbo_group ) {
  //printf("objCreate for %s\n", fname);
  uint32 max_uv_id=0;
  uint32 pathLen;
  uint32 uvId;
  uint32 texFlags;
  uint8 path[PATH_LEN];
  uint32 num_uv_mapped_faces=0;
  uint32 face_id, map_id;
  FILE *file=fopen(fname,"rb");
  if (file==NULL) {
    return nofile;
  }
  *pp_mesh=new obj_3dMesh;
  if(!*pp_mesh) {
    return noMemory;
  }

  if(vbo_group!=NO_VBO_GROUP_EVER) {
    p_meshes[num_meshes++]=*pp_mesh;
  } else {
    printf("objCreate. no vbo group ever\n");
  }

  strncpy((*pp_mesh)->mesh_path, fname, PATH_LEN);
  obj_3dPrimitive **obj=&((*pp_mesh)->p_prim);
	obj_3dPrimitive *curr_obj;
	int i,j;
	int temp;
	obj_vertex mid, min, max;
	obj_vertex *inverts=NULL;
	int inverts_max;
	obj_3dPrimitive *inprims;
	int inprims_max;

	//skip a comma
	while (fgetc(file)!=',');
	//read number of objects
	fscanf(file,"%i",&temp);

	//skip 2 lines
	while (fgetc(file)!=0x0a);
	while (fgetc(file)!=0x0a);

	//skip objects+1 newlines
	for (i=0;i<temp;i++) {
	  for(uint32 f=0;f<5;f++) { //skip 5 fields
	    uint8 c;
	    while ((c=fgetc(file))!=',');
	  }
	  fscanf(file,"%31s",(*pp_mesh)->tag);
	  while (fgetc(file)!=0x0a);
	}

	//skip a comma
	while (fgetc(file)!=',');

	fscanf(file,"%i",&inverts_max); //scan in number of vertices in obj
	inverts= new obj_vertex[inverts_max];
	if(!inverts) {
	  goto noInverts;
	}
	(*pp_mesh)->p_vert_start=inverts;
	(*pp_mesh)->p_vert_end=inverts+inverts_max;

	//skip 2 lines
	while (fgetc(file)!=0x0a);
	while (fgetc(file)!=0x0a);

	mid.x=0;
	mid.y=0;
	mid.z=0;

	//begin reading in vertex coords
	for (i=0;i<inverts_max;i++) {
	  while (fgetc(file)!=','); //skip first comma
	  fscanf(file,"%f",&(inverts[i].x));
	  inverts[i].x-=origin_offset.x;
	  inverts[i].x*=obj_scaler;
	  if(inverts_max) {
	    mid.x+=inverts[i].x/inverts_max;
	  }
	  while (fgetc(file)!=','); //skip second comma
	  fscanf(file,"%f",&(inverts[i].y));
	  inverts[i].y-=origin_offset.y;
	  inverts[i].y*=obj_scaler;
	  if(inverts_max) {
	    mid.y+=inverts[i].y/inverts_max;
	  }
	  while (fgetc(file)!=','); //skip third comma
	  fscanf(file,"%f",&(inverts[i].z));
	  inverts[i].z-=origin_offset.z;
	  inverts[i].z*=obj_scaler;
	  if(inverts_max) {
	    mid.z+=inverts[i].z/inverts_max;
	  }
	  while (fgetc(file)!=0x0a);//skip to next line
	  inverts[i].shared=0;

	  inverts[i].norm.x=0.0f;
	  inverts[i].norm.y=0.0f;
	  inverts[i].norm.z=0.0f;

	  if(i==0) {
	    min.x=inverts[i].x;
	    min.y=inverts[i].y;
	    min.z=inverts[i].z;
	    max.x=inverts[i].x;
	    max.y=inverts[i].y;
	    max.z=inverts[i].z;
	  } else {
	    if(inverts[i].x<min.x) {
	      min.x=inverts[i].x;
	    }
	    if(inverts[i].x>max.x) {
	      max.x=inverts[i].x;
	    }
	    if(inverts[i].y<min.y) {
	      min.y=inverts[i].y;
	    }
	    if(inverts[i].y>max.y) {
	      max.y=inverts[i].y;
	    }
	    if(inverts[i].z<min.z) {
	      min.z=inverts[i].z;
	    }
	    if(inverts[i].z>max.z) {
	      max.z=inverts[i].z;
	    }
	  }
	  inverts[i].id=i;
	}
	if(!strncmp((*pp_mesh)->mesh_path, match_mesh, PATH_LEN)) {
	  printf("min %s: %f %f %f\n", (*pp_mesh)->mesh_path, min.x, min.y, min.z);
	  printf("max: %f %f %f\n", max.x, max.y, max.z);
	  printf("mid: %f %f %f\n", mid.x, mid.y, mid.z);
	}			
	//printf("mid: %f %f %f\n", mid.x, mid.y, mid.z);
	//skip 1 lines
	while (fgetc(file)!=0x0a);
	//skip a comma
	while (fgetc(file)!=',');

	fscanf(file,"%i",&inprims_max); //scan in number of triangles in obj
	inprims= new obj_3dPrimitive[inprims_max];
	if(!inprims) {
	  goto noInprims;
	}

	//skip 2 lines
	while (fgetc(file)!=0x0a);
	while (fgetc(file)!=0x0a);
	
	//start reading in triangles
	for (i=0;i<inprims_max;i++) {
		for (j=0;j<3;j++) {
			while (fgetc(file)!=','); //skip comma
			fscanf(file,"%i",&temp);
			inprims[i].vert[j]=&inverts[temp-1];
		}

		//***************************************************
		obj_vector v1,v2,vector_normal,unit_vector_norm;
		float vector_mag;
		obj_vertex **vert=inprims[i].vert;
		//get two vector which point in the direction of the surface
		v1.x=vert[1]->x-vert[0]->x;
		v1.y=vert[1]->y-vert[0]->y;
		v1.z=vert[1]->z-vert[0]->z;
		
		v2.x=vert[2]->x-vert[0]->x;
		v2.y=vert[2]->y-vert[0]->y;
		v2.z=vert[2]->z-vert[0]->z;
		
		//find the normal to the surface ie. v1 x v2 (cross product)
		vector_normal.x=v1.y * v2.z  -  v1.z * v2.y;
		vector_normal.y=v1.z * v2.x  -  v1.x * v2.z;
		vector_normal.z=v1.x * v2.y  -  v1.y * v2.x;
		
		vector_mag=(float) sqrt(	sqr(vector_normal.x) + 
			sqr(vector_normal.y) +
			sqr(vector_normal.z)  );
		
		//normalise the normal
		if (vector_mag==0) vector_mag=1;//prevent div 0
		unit_vector_norm.x=vector_normal.x/vector_mag;
		unit_vector_norm.y=vector_normal.y/vector_mag;
		unit_vector_norm.z=vector_normal.z/vector_mag;
		
		if (!(flags&OBJ_NORMAL_POSITIVE)) {
			unit_vector_norm.x*=-1;
			unit_vector_norm.y*=-1;
			unit_vector_norm.z*=-1;	
		}
		
		for (j=0;j<3;j++) {
			vert[j]->norm.x*=vert[j]->shared;
			//if(!strncmp((*pp_mesh)->mesh_path, match_mesh, PATH_LEN)) {
			//}			
			vert[j]->norm.y*=vert[j]->shared;
			vert[j]->norm.z*=vert[j]->shared;

			vert[j]->norm.x+=unit_vector_norm.x;
			vert[j]->norm.y+=unit_vector_norm.y;
			vert[j]->norm.z+=unit_vector_norm.z;
			
			vert[j]->shared++;
			
			vert[j]->norm.x/=vert[j]->shared;
			vert[j]->norm.y/=vert[j]->shared;
			vert[j]->norm.z/=vert[j]->shared;
			
		}

		inprims[i].vertex_list=NULL; //only valid for first prim in list
		inprims[i].flags=0;
		inprims[i].uv_id=UNTEXTURED;
		checkAllRanges(&inprims[i].uv_id);
		while (fgetc(file)!=0x0a);
		inprims[i].id=i;
	}

	//skip to colours definitions
	while (fgetc(file)!=0x0a);
	while (fgetc(file)!=0x0a);
	while (fgetc(file)!=0x0a);

	//begin assigning colours to triangles
	for (i=0;i<inprims_max;i++) {
		
		while (fgetc(file)!=','); //skip comma
		fscanf(file,"%i",&temp); //read red value
		inprims[i].r=(float) temp/255.0f;

		while (fgetc(file)!=','); //skip comma
		fscanf(file,"%i",&temp); //read green value
		inprims[i].g=(float) temp/255.0f;

		while (fgetc(file)!=','); //skip comma
		fscanf(file,"%i",&temp); //read blue value
		inprims[i].b=(float) temp/255.0f;

		while (fgetc(file)!=0x0a);
	}

	//skip 1 lines
	while (fgetc(file)!=0x0a);
	//skip a comma
	while (fgetc(file)!=',');
	fscanf(file,"%i",&((*pp_mesh)->num_uv_maps));
	(*pp_mesh)->p_tex_ids=new uint32[(*pp_mesh)->num_uv_maps];
	if(!(*pp_mesh)->p_tex_ids) {
	  goto noTexIds;
	}
	(*pp_mesh)->p_tex_flags=new uint32[(*pp_mesh)->num_uv_maps];
	if(!(*pp_mesh)->p_tex_flags) {
	  goto noTexFlags;
	}
	(*pp_mesh)->pp_tex_paths=new uint8*[(*pp_mesh)->num_uv_maps];
	if(!(*pp_mesh)->pp_tex_paths) {
	  goto noTexPaths;
	}
	//skip 2 lines
	while (fgetc(file)!=0x0a);
	while (fgetc(file)!=0x0a);

	for (i=0;i<(*pp_mesh)->num_uv_maps;i++) {
	  fscanf(file,"%i",&uvId);
	  while (fgetc(file)!=','); //skip comma
	  fscanf(file,"%i",&texFlags);
	  (*pp_mesh)->p_tex_flags[uvId]=texFlags;
	  while (fgetc(file)!=','); //skip comma
	  fscanf(file, PATH_MATCH, path);
	  pathLen=strnlen(path, PATH_LEN-1);
	  (*pp_mesh)->pp_tex_paths[uvId]=new uint8[PATH_LEN];
	  if(!(*pp_mesh)->pp_tex_paths[uvId]) {
	    goto noPrim;
	  }
	  strncpy((*pp_mesh)->pp_tex_paths[uvId], path, pathLen+1);
	  while (fgetc(file)!=0x0a);
	}

	while (fgetc(file)!=0x0a);
	while (fgetc(file)!=',');
	fscanf(file,"%i",&num_uv_mapped_faces); //scan in number of triangles in obj
	while (fgetc(file)!=0x0a);
	while (fgetc(file)!=0x0a);
	for(uint32 face=0; face<num_uv_mapped_faces; face++) {
	  fscanf(file,"%i",&face_id);
	  while (fgetc(file)!=',');
	  fscanf(file,"%i",&map_id);
	  inprims[face_id-1].uv_id=map_id;
	  //printf("setting uv_id face %u (0x%x) to %u\n", face_id, &(inprims[face_id-1].uv_id), map_id);
	  for(uint32 vert_idx=0; vert_idx<3; vert_idx++) {
	    while (fgetc(file)!=',');
	    fscanf(file,"%f", &(*(inprims[face_id-1].vert[vert_idx])).u);
	    while (fgetc(file)!=',');
	    fscanf(file,"%f", &(*(inprims[face_id-1].vert[vert_idx])).v);
	  }
	  while (fgetc(file)!=0x0a);
	}

	fclose(file);
//-----------------------------------------------------------
	(*pp_mesh)->mid=Eigen::Vector3d(mid.x, mid.y, mid.z);
	(*pp_mesh)->min=min;
	(*pp_mesh)->max=max;
	*obj= new obj_3dPrimitive;
	if (*obj==NULL) {
	  goto noPrim;
	}
	(*obj)->flags=flags;
	(*obj)->type=empty;
	curr_obj=*obj;
	curr_obj->uv_id=UNTEXTURED;
	curr_obj->vertex_list=inverts;
	
	i=0;
	while (i<inprims_max) {
		curr_obj->next_ref=new obj_3dPrimitive[1];
		if (curr_obj->next_ref==NULL) { 
		  goto noNext;
		}
		curr_obj=curr_obj->next_ref;
		inprims[i].type=tri;
		*curr_obj=inprims[i];
		curr_obj->next_ref=NULL;
		i++;
	}
	
	(*pp_mesh)->vbo_group=vbo_group;
	(*pp_mesh)->num_prims=inprims_max;
	(*pp_mesh)->vbo.vbo=NO_VBO;
	(*pp_mesh)->vbo.ibo=NO_IBO;
	//(*pp_mesh)->ibo=NO_IBO;
	//createVBO(*pp_mesh);
	delete [] inprims;
	
	return ok;

 noNext:
	{
	  obj_3dPrimitive* p_next;
	  obj_3dPrimitive* p_obj=(*pp_mesh)->p_prim;
	  while (p_obj!=NULL) {
	    p_next=p_obj->next_ref;
	    delete p_obj; 
	    p_obj=p_next;
	  }
	}
 noPrim:
	for (i=0;i<(*pp_mesh)->num_uv_maps;i++) {
	  if((*pp_mesh)->pp_tex_paths[i]) {
	    delete [] (*pp_mesh)->pp_tex_paths[i];
	  } else {
	    break;
	  }
	}
 noTexPath:	  
	delete [] (*pp_mesh)->pp_tex_paths;
 noTexPaths:
	delete [] (*pp_mesh)->p_tex_flags;
 noTexFlags:
	delete [] (*pp_mesh)->p_tex_ids;
 noTexIds:
	delete [] inprims;
 noInprims:
	delete [] inverts;
 noInverts:
	delete *pp_mesh;
	return noMemory;
}

void col_objDelete(obj_3dMesh **pp_mesh) {
  obj_3dPrimitive *obj=(*pp_mesh)->p_prim;
#ifdef OPEN_GL
  glDeleteTextures((*pp_mesh)->num_uv_maps, (*pp_mesh)->p_tex_ids);
#endif
  obj_3dPrimitive *next;
  delete obj->vertex_list;
  while (obj!=NULL) {
    next=obj->next_ref;
    delete obj; 
    obj=next;
  }
  obj=NULL;
  for (uint32 i=0;i<(*pp_mesh)->num_uv_maps;i++) {
    if((*pp_mesh)->pp_tex_paths[i]) {
      delete [] (*pp_mesh)->pp_tex_paths[i];
    } else {
      break;
    }
  }
  delete [] (*pp_mesh)->pp_tex_paths;
  delete [] (*pp_mesh)->p_tex_flags;
  delete [] (*pp_mesh)->p_tex_ids;
  delete *pp_mesh;
  *pp_mesh=NULL;
}

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

  uint32 i=0, j=0;

  while(it.hasNext()) {
    uint32 itIdx=it.next();
    while(oIt.hasNext()) {
      if(!col_ColCollisionCheck(p_col, itIdx, p_other, oIt.next())) {
	oIt.result(it.result(false));
      } else {
	if(i!=0 || j!=0) {
	  //printf("col_CheckCollider. collided\n");
	  oIt.result(it.result(true));
	} else {
	  //printf("col_CheckCollider. collided %u %u\n", i, j);
	  oIt.result(it.result(false));	    
	  oIt.allowDeepInspection();
	}
      }
      j++;
    }
    oIt.reset();
    i++;
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
