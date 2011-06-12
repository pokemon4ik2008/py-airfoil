#include "objects.h"

bool obj_use_gl_lighting=true;
float obj_cut_off_dist = 100;
float obj_cut_off_angle = 20;
float obj_ambient_light=0.5f;
obj_plot_position pos={0};
obj_plot_position origin_offset={0};
obj_plot_position pov={0};
obj_light_source objlight={1.0f,0,0,0};

obj_3dPrimitive *testObj = NULL;
float rotAngle = 0;
float *rotAxis = NULL;

extern "C" 
{
	DLL_EXPORT void *load(char *filename)
	{
		oError err = oError::ok;		
		unsigned int objectflags=0;
		objectflags|=OBJ_NORMAL_POSITIVE;
		err = objCreate(&testObj, filename, 100.0f, objectflags);
		
		if (err != oError::ok)
		{
			printf("ERROR: when loading object: %i\n", err);
		}
		return testObj;
	}

	DLL_EXPORT void setAngleAxisRotation(float angle, float axis[]) 
	{
		rotAngle = angle;
		rotAxis = axis;
	}

	DLL_EXPORT void setPosition(float plotPos[])
	{
		objSetPlotPos(plotPos[0], plotPos[1], plotPos[2]);
	}

	DLL_EXPORT void draw(void *meshToPlot)
	{
		oError err = oError::ok;
		err = objPlot(static_cast<obj_3dPrimitive *>(meshToPlot));
		if (err != oError::ok)
		{
			printf("ERROR: when drawing object\n");
		}
	}

	DLL_EXPORT void deleteMesh(void *meshToDelete)
	{	
		obj_3dPrimitive *meshToDeletePtr = static_cast<obj_3dPrimitive *>(meshToDelete);
		objDelete(&meshToDeletePtr);			
	}	
}

void	objSetCutOff		(float dist, float angle) {
	obj_cut_off_dist=dist;
	obj_cut_off_angle=angle;
}



void objSetPlotPos(float x, float y, float z) {
	pos.x=x;
	pos.y=y;
	pos.z=z;
}

void objRotZ(obj_vector *unit_vector_norm,float az) {
	obj_vector unit_vector_norm2;
	unit_vector_norm2.x=(float)	(unit_vector_norm->x * ( cos(az) ) +
								unit_vector_norm->y *  ( sin(az) ) +
								unit_vector_norm->z *  ( 0 ));
	unit_vector_norm2.y=(float)	(unit_vector_norm->x * (-sin(az) ) +
								unit_vector_norm->y * ( cos(az) ) +
								unit_vector_norm->z * ( 0 ));
	unit_vector_norm2.z=(float)	(unit_vector_norm->x * ( 0 ) +
								unit_vector_norm->y * ( 0 ) +
								unit_vector_norm->z * ( 1 ));
	*unit_vector_norm=unit_vector_norm2;
}

void objRotY(obj_vector *unit_vector_norm,float ay) {
	obj_vector unit_vector_norm2;
	unit_vector_norm2.x=(float)	(unit_vector_norm->x * ( cos(ay) ) +
								unit_vector_norm->y *  ( 0 ) +
								unit_vector_norm->z *  (-sin(ay) ));
	unit_vector_norm2.y=(float)	(unit_vector_norm->x * ( 0 ) +
								unit_vector_norm->y * ( 1 ) +
								unit_vector_norm->z * ( 0 ));
	unit_vector_norm2.z=(float)	(unit_vector_norm->x * ( sin(ay) ) +
								unit_vector_norm->y * ( 0 ) +
								unit_vector_norm->z * ( cos(ay) ));
	*unit_vector_norm=unit_vector_norm2;
}

void objRotX(obj_vector *unit_vector_norm,float ax) {
	obj_vector unit_vector_norm2;
	unit_vector_norm2.x=(float)	(unit_vector_norm->x * ( 1 ) +
								unit_vector_norm->y *  ( 0 ) +
								unit_vector_norm->z *  ( 0 ));
	unit_vector_norm2.y=(float)	(unit_vector_norm->x * ( 0 ) +
								unit_vector_norm->y * ( cos(ax) ) +
								unit_vector_norm->z * ( sin(ax) ));
	unit_vector_norm2.z=(float)	(unit_vector_norm->x * ( 0 ) +
								unit_vector_norm->y * (-sin(ax) ) +
								unit_vector_norm->z * ( cos(ax) ));
	*unit_vector_norm=unit_vector_norm2;
}

void objSetVertexNormal(obj_vector unit_vector_norm,unsigned int flags) {
	float ax=-deg_to_rad*pos.ax;
	float ay=-deg_to_rad*pos.ay;
	float az=-deg_to_rad*pos.az;

	//Must rotate normal now same as objs rotation
	objRotZ(&unit_vector_norm,az);
	objRotY(&unit_vector_norm,ay);
	objRotX(&unit_vector_norm,ax);
	
	if (flags&OBJ_NORMAL_ABSOLUTE) {
		unit_vector_norm.x=absValue(unit_vector_norm.x);
		unit_vector_norm.y=absValue(unit_vector_norm.y);
		unit_vector_norm.z=absValue(unit_vector_norm.z);	
	}

	glNormal3f( -unit_vector_norm.x, -unit_vector_norm.y, -unit_vector_norm.z);
}


//Pre: call to objSetPlotPos/Angle to set plotting position
oError objPlot(obj_3dPrimitive *obj) {
	float intensity;
	oError error=ok;
	obj_3dPrimitive* curr_prim=obj;
	int i;
	
	unsigned int flags;

	glTranslatef(pos.x ,pos.y ,pos.z );

	if (rotAxis)
	{
		glRotatef(rotAngle, rotAxis[0], rotAxis[1], rotAxis[2]);		// Rotate On The X Axis
	}

 
	flags=curr_prim->flags;

	glEnable(GL_DEPTH_TEST);
	glEnable(GL_LIGHTING);
	while(curr_prim->next_ref!=NULL) {
		curr_prim=curr_prim->next_ref;
/*
		if ((flags&OBJ_USE_FAST_LIGHT)&&!(flags&OBJ_NO_LIGHTING)) {
			if (obj_use_gl_lighting)
				objSetVertexNormal(curr_prim->vert[0]->norm,flags);
		}
*/
		switch (curr_prim->type) {
		case line: 
			glBegin(  GL_LINES );
			for (i=0;i<2;i++) {
				glColor3f(curr_prim->r, curr_prim->g, curr_prim->b);
				glVertex3f(curr_prim->vert[i]->x, curr_prim->vert[i]->y, curr_prim->vert[i]->z);	
			}
			glEnd();
			break;
		case tri:
			glBegin(  GL_TRIANGLES );
			for (i=0;i<3;i++) {
				/*
				if (flags&OBJ_NO_LIGHTING) {
					intensity=1.0f;
					glDisable(GL_LIGHTING);
				}
				else {
					if (!(flags&OBJ_USE_FAST_LIGHT)) {
						if (obj_use_gl_lighting) 
							objSetVertexNormal(curr_prim->vert[i]->norm,flags);				
					}
				}*/

				intensity=1.0f;				
				glNormal3f( curr_prim->vert[i]->norm.x, curr_prim->vert[i]->norm.y, curr_prim->vert[i]->norm.z);				
				GLfloat diff[]={curr_prim->r,
							curr_prim->g,
							curr_prim->b,1.0f};
				glMaterialfv(GL_FRONT, GL_DIFFUSE, diff);
				glColor3f(curr_prim->r*intensity
							, curr_prim->g*intensity
							, curr_prim->b*intensity);
				glVertex3f(	curr_prim->vert[i]->x, 
							curr_prim->vert[i]->y, 
							curr_prim->vert[i]->z);	
			}
			glEnd();
			break;
		case quad:
			glBegin(  GL_QUADS );
			for (i=0;i<4;i++) {
				if (flags&OBJ_NO_LIGHTING) {
					intensity=1.0f;
					glDisable(GL_LIGHTING);
				}
				else {
					if (!(flags&OBJ_USE_FAST_LIGHT)) {
						if (obj_use_gl_lighting) 
							objSetVertexNormal(curr_prim->vert[i]->norm,flags);			
					}
				}

				GLfloat diff[]={curr_prim->r,
							curr_prim->g,
							curr_prim->b,1.0f};
				glMaterialfv(GL_FRONT, GL_DIFFUSE, diff);
				glColor3f(curr_prim->r*intensity
							, curr_prim->g*intensity
							, curr_prim->b*intensity);
				glVertex3f(	curr_prim->vert[i]->x, 
							curr_prim->vert[i]->y, 
							curr_prim->vert[i]->z);	
			}
			glEnd();			
			break;
		default: break;
		}
		
	}
	
	return error;
}

//Pre: call to objSetLoadPos.. angle not yet supported
oError objCreate(obj_3dPrimitive **obj, 
					char *fname,float obj_scaler
					, unsigned int flags) {
	oError error=ok;
	obj_3dPrimitive *curr_obj;
	FILE *file=fopen(fname,"rb");
	if (file==NULL) return nofile;
	int i,j;
	int temp;
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
	for (i=0;i<=temp;i++) {
		while (fgetc(file)!=0x0a);
	}

	//skip a comma
	while (fgetc(file)!=',');

	fscanf(file,"%i",&inverts_max); //scan in number of vertices in obj
	inverts= new obj_vertex[inverts_max];

	//skip 2 lines
	while (fgetc(file)!=0x0a);
	while (fgetc(file)!=0x0a);

	//begin reading in vertex coords
	for (i=0;i<inverts_max;i++) {
		while (fgetc(file)!=','); //skip first comma
		fscanf(file,"%f",&(inverts[i].x));
		inverts[i].x-=origin_offset.x;
		inverts[i].x*=obj_scaler;
		while (fgetc(file)!=','); //skip second comma
		fscanf(file,"%f",&(inverts[i].y));
		inverts[i].y-=origin_offset.y;
		inverts[i].y*=obj_scaler;
		while (fgetc(file)!=','); //skip third comma
		fscanf(file,"%f",&(inverts[i].z));
		inverts[i].z-=origin_offset.z;
		inverts[i].z*=obj_scaler;
		while (fgetc(file)!=0x0a);//skip to next line
		inverts[i].shared=0;
	}

	//skip 1 lines
	while (fgetc(file)!=0x0a);
	//skip a comma
	while (fgetc(file)!=',');

	fscanf(file,"%i",&inprims_max); //scan in number of triangles in obj
	inprims= new obj_3dPrimitive[inprims_max];

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
/*

		vert[0]->norm.x=unit_vector_norm.x;
		vert[0]->norm.y=unit_vector_norm.y;
		vert[0]->norm.z=unit_vector_norm.z;
		
		vert[1]->norm.x=unit_vector_norm.x;
		vert[1]->norm.y=unit_vector_norm.y;
		vert[1]->norm.z=unit_vector_norm.z;

		vert[2]->norm.x=unit_vector_norm.x;
		vert[2]->norm.y=unit_vector_norm.y;
		vert[2]->norm.z=unit_vector_norm.z;
*/
		inprims[i].vertex_list=NULL; //only valid for first prim in list
		inprims[i].flags=0;			//only valid for first prim in list
	//*************************************************
		while (fgetc(file)!=0x0a);
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

	fclose(file);

	
//-----------------------------------------------------------
 
	*obj= new obj_3dPrimitive;
	if (*obj==NULL) return noMemory;
	(*obj)->flags=flags;
	(*obj)->type=empty;
//	(*obj)->next_ref=NULL;
	curr_obj=*obj;
	curr_obj->vertex_list=inverts;
//	curr_obj->next_ref=inprims;
	
	
	i=0;

	while (i<inprims_max) {
		curr_obj->next_ref=new obj_3dPrimitive[1];
		if (curr_obj->next_ref==NULL) return noMemory;
		curr_obj=curr_obj->next_ref;

		*curr_obj=inprims[i];
		if ((curr_obj->vert[1]->x==curr_obj->vert[2]->x) &&
			(curr_obj->vert[1]->y==curr_obj->vert[2]->y) &&
			(curr_obj->vert[1]->z==curr_obj->vert[2]->z) )
			curr_obj->type=line;
		else curr_obj->type=tri;
		
		i++;
		curr_obj->next_ref=NULL;
	}

	delete [] inprims;
	
	return error;
}

void objDelete(obj_3dPrimitive **obj) {
	obj_3dPrimitive *next;
	delete (*obj)->vertex_list;
	while (*obj!=NULL) {
		next=(*obj)->next_ref;
		delete *obj; 
		*obj=next;
	}
	*obj=NULL;
}


