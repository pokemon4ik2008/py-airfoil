from os import getcwd, remove, sep

PYGAME='pygame'
PYGLET='pyglet'

FILE='compile_type.txt'

def setAPI(api):
        print 'setting api to '+api
        try:
                compileType=None
                compileType=open(FILE, 'w')
                compileType.write(api)
                compileType.close()
                print 'setting api success '+api
        except IOError:
                print 'failed to set compile type. attempting to default to pygame'
        finally:
                if compileType is not None:
                        compileType.close()

def setPyGame():
        setAPI(PYGAME)

def setPyglet():
        setAPI(PYGLET)

def getAPI():
        api=PYGAME
        try:
                compileType=None
                compileType=open(FILE, 'r')
                api=compileType.read()
        except IOError:
                print 'failed to read compile type. assuming pygame'                
        finally:
                if compileType is not None:
                        compileType.close()
                        
        return api
