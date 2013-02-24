#ifndef types_h
#define types_h

typedef unsigned char ubyte;
typedef char uint8;
typedef unsigned int uint32;
typedef float float32;
typedef double float64;

typedef enum {ok, noMemory,invalidPrimitive,emptyObject,nofile, unsupported, glErr, failedAssert} oError;

#endif
