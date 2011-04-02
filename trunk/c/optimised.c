#include <stdio.h>
static int maxIndices = 0;
static int *indices = NULL;
static unsigned int numIndices = 0;
static int wireframe = 0;
static int size = 100;

void Init(int *in, int max, int newSize)
{
  //printf("init %p %i %i\n", in, max, newSize);
  maxIndices = max;
  indices = in;
  size = newSize;  
}

int Reset()
{
  int numBak = numIndices;
  numIndices = 0;
  return numBak;
}

void DrawVertex(int x, int z)
{
  if (numIndices < maxIndices)
    {
      indices[numIndices++] = x * size + z;
      //printf("Draw vertex %i %i\n", x,z);
    }
  else
    printf("ERROR: out of space in index buffer.\n");
}

int DrawQuad(int x, int z)
{
  if (x < 0 || x >= size-1 || z < 0 || z >= size-1)
    {
      //printf("Quad out of bounds.\n");
      return 0;
    }

  if (wireframe)
    {
      DrawVertex(x,z);
      DrawVertex(x,z+1);
      DrawVertex(x,z+1);
      DrawVertex(x+1,z+1);
      DrawVertex(x+1,z+1);
      DrawVertex(x+1,z);
      DrawVertex(x+1,z);
      DrawVertex(x,z);
    }
  else
    {
      DrawVertex(x,z);
      DrawVertex(x,z+1);
      DrawVertex(x+1,z+1);
      DrawVertex(x+1,z);
    }

  return 1;
}

float CalcIndices(float topz, float botz, float leftx, float rightx, float leftm, float rightm)
{
  //printf("CDraw\n");
  //printf("Inputs %f %f %f %f %f %f\n", topz, botz, leftx, rightx, leftm, rightm);

	int drawn = 0;
	int inc;
	int x;
	float z;
	for (z = topz; z >= botz; z -= 1.0)
	  {
	    if (leftx < rightx)
	      inc = 1;
	    else
	      inc = -1;
	    int endi = (int) (rightx * inc);
	    int i;
	    for (i = (int) (leftx * inc); i < endi; i++)
	      {
		x = i * inc;
		if (DrawQuad(x, (int) z))
		  drawn++;
	      }
	    leftx -= leftm;
	    rightx -= rightm;
	  }
	//printf("%f", rightx);
	return rightx;
}
